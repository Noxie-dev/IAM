"""
Transcription Service Endpoints
Phase 2: Backend Enhancement

Audio transcription processing endpoints with audio enhancement
"""

import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models.meeting import Meeting
from app.services.auth_service import get_current_user
from app.services.websocket_manager import connection_manager as websocket_manager
from app.services.audio_enhancement import AudioEnhancementService
from app.services.transcription_service import TranscriptionService
from app.services.storage_service import StorageService

router = APIRouter()
settings = get_settings()

# Initialize services
audio_enhancer = AudioEnhancementService()
transcription_service = TranscriptionService()
storage_service = StorageService()

@router.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    language: str = Form("auto"),
    provider: str = Form("openai"),
    model: str = Form("whisper-1"),
    speaker_detection: bool = Form(False),
    timestamps: bool = Form(True),
    word_timestamps: bool = Form(False),
    enhance_audio: bool = Form(True),
    enhancement_options: Optional[str] = Form(None),  # JSON string of enhancement options
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload audio file for transcription with optional audio enhancement

    Args:
        file: Audio file to upload
        title: Meeting title
        description: Optional meeting description
        language: Language for transcription (auto-detect by default)
        provider: Transcription provider (openai, azure, google)
        model: Model to use for transcription
        speaker_detection: Enable speaker diarization
        timestamps: Include timestamps in transcription
        word_timestamps: Include word-level timestamps
        enhance_audio: Whether to apply audio enhancement
        enhancement_options: JSON string with enhancement parameters
        current_user: Authenticated user
        db: Database session

    Returns:
        Upload result with meeting ID and processing status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size (250MB limit)
        max_size = 250 * 1024 * 1024
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds 250MB limit"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")

        # Validate file format
        supported_formats = {'.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.ogg', '.webm', '.flac'}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_extension}. Supported: {', '.join(supported_formats)}"
            )

        # Create meeting record
        meeting_id = str(uuid.uuid4())
        meeting = Meeting(
            id=meeting_id,
            title=title,
            description=description,
            user_id=current_user.id,
            original_filename=file.filename,
            audio_file_size=file_size,
            audio_file_format=file_extension[1:],  # Remove the dot
            processing_status="uploading",
            transcription_settings={
                "language": language,
                "provider": provider,
                "model": model,
                "speaker_detection": speaker_detection,
                "timestamps": timestamps,
                "word_timestamps": word_timestamps,
                "enhance_audio": enhance_audio,
                "enhancement_options": enhancement_options
            }
        )

        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        # Start background processing
        background_tasks.add_task(
            process_audio_file,
            meeting_id=meeting_id,
            file_content=content,
            filename=file.filename,
            user_id=current_user.id,
            enhance_audio=enhance_audio,
            enhancement_options=enhancement_options
        )

        # Send initial WebSocket update
        await websocket_manager.send_transcription_update(
            user_id=current_user.id,
            transcription_id=meeting_id,
            status="processing",
            progress=0
        )

        return {
            "success": True,
            "id": meeting_id,
            "title": title,
            "original_filename": file.filename,
            "audio_file_size": file_size,
            "audio_file_format": file_extension[1:],
            "processing_status": "processing",
            "created_at": meeting.created_at.isoformat(),
            "message": "File uploaded successfully. Processing started."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_audio_file(
    meeting_id: str,
    file_content: bytes,
    filename: str,
    user_id: str,
    enhance_audio: bool = True,
    enhancement_options: Optional[str] = None
):
    """
    Background task to process uploaded audio file

    Args:
        meeting_id: Meeting UUID
        file_content: Raw file content
        filename: Original filename
        user_id: User UUID
        enhance_audio: Whether to apply audio enhancement
        enhancement_options: JSON string with enhancement parameters
    """
    db = next(get_db())
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        return

    try:
        # Update status to processing
        meeting.processing_status = "processing"
        meeting.processing_started_at = datetime.utcnow()
        db.commit()

        await websocket_manager.send_transcription_update(
            user_id=user_id,
            transcription_id=meeting_id,
            status="processing",
            progress=10
        )

        # Save original file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(file_content)
            original_path = temp_file.name

        try:
            # Upload original file to storage
            original_key = f"audio/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{meeting_id}_original{Path(filename).suffix}"
            original_result = await storage_service.upload_file(
                file_content=file_content,
                file_key=original_key,
                content_type=f"audio/{Path(filename).suffix[1:]}",
                metadata={
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                    "original_filename": filename,
                    "file_type": "audio_original"
                }
            )

            if not original_result["success"]:
                raise Exception(f"Failed to upload original file: {original_result.get('error')}")

            meeting.audio_file_url = original_result["file_url"]
            db.commit()

            await websocket_manager.send_transcription_update(
                user_id=user_id,
                transcription_id=meeting_id,
                status="processing",
                progress=30
            )

            # Apply audio enhancement if requested
            enhanced_path = original_path
            if enhance_audio:
                try:
                    enhanced_path = await audio_enhancer.enhance_audio(
                        input_path=original_path,
                        output_dir=tempfile.gettempdir(),
                        options=enhancement_options
                    )

                    # Upload enhanced file
                    with open(enhanced_path, 'rb') as enhanced_file:
                        enhanced_content = enhanced_file.read()

                    enhanced_key = f"audio/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{meeting_id}_enhanced.wav"
                    enhanced_result = await storage_service.upload_file(
                        file_content=enhanced_content,
                        file_key=enhanced_key,
                        content_type="audio/wav",
                        metadata={
                            "user_id": user_id,
                            "meeting_id": meeting_id,
                            "original_filename": filename,
                            "file_type": "audio_enhanced"
                        }
                    )

                    if enhanced_result["success"]:
                        meeting.add_metadata("enhanced_audio_url", enhanced_result["file_url"])
                        meeting.add_metadata("audio_enhanced", True)

                    await websocket_manager.send_transcription_update(
                        user_id=user_id,
                        transcription_id=meeting_id,
                        status="processing",
                        progress=60
                    )

                except Exception as e:
                    # Enhancement failed, continue with original
                    meeting.add_metadata("enhancement_error", str(e))
                    meeting.add_metadata("audio_enhanced", False)
                    enhanced_path = original_path

            # Transcribe audio (use enhanced version if available)
            transcription_result = await transcription_service.transcribe_audio(
                audio_path=enhanced_path,
                meeting=meeting
            )

            if transcription_result["success"]:
                meeting.transcription_text = transcription_result["text"]
                meeting.processing_status = "completed"
                meeting.processing_completed_at = datetime.utcnow()

                if "segments" in transcription_result:
                    meeting.add_metadata("transcription_segments", transcription_result["segments"])

                await websocket_manager.send_transcription_update(
                    user_id=user_id,
                    transcription_id=meeting_id,
                    status="completed",
                    progress=100,
                    result={
                        "transcription": transcription_result["text"],
                        "segments": transcription_result.get("segments"),
                        "enhanced": enhance_audio and meeting.transcription_metadata.get("audio_enhanced", False)
                    }
                )
            else:
                raise Exception(transcription_result["error"])

        finally:
            # Clean up temporary files
            for path in [original_path, enhanced_path]:
                if path and os.path.exists(path):
                    os.unlink(path)

        db.commit()

    except Exception as e:
        # Update meeting with error status
        meeting.processing_status = "failed"
        meeting.processing_completed_at = datetime.utcnow()
        meeting.add_metadata("error", str(e))
        db.commit()

        await websocket_manager.send_transcription_update(
            user_id=user_id,
            transcription_id=meeting_id,
            status="failed",
            error=str(e)
        )

    finally:
        db.close()


@router.get("/{transcription_id}")
async def get_transcription(
    transcription_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get transcription result"""
    meeting = db.query(Meeting).filter(
        Meeting.id == transcription_id,
        Meeting.user_id == current_user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return {
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "transcription_text": meeting.transcription_text,
        "processing_status": meeting.processing_status,
        "created_at": meeting.created_at.isoformat(),
        "processing_started_at": meeting.processing_started_at.isoformat() if meeting.processing_started_at else None,
        "processing_completed_at": meeting.processing_completed_at.isoformat() if meeting.processing_completed_at else None,
        "original_filename": meeting.original_filename,
        "audio_file_size": meeting.audio_file_size,
        "audio_file_format": meeting.audio_file_format,
        "audio_file_url": meeting.audio_file_url,
        "metadata": meeting.transcription_metadata
    }
