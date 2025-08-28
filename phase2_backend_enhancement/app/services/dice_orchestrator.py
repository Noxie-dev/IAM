"""
DICE™ - Dual Intelligence Context Engine
Main Orchestrator Service

Manages the complete DICE™ pipeline from file ingestion to final minutes generation
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.models.dice_job import DiceJob, DiceJobLog
from app.schemas.dice_schemas import (
    FileInfo, PreScanJSON, DraftTranscriptJSON, 
    ValidationReportJSON, FinalMinutes, DiceJobStatus
)

# Import DICE algorithm services
from .dice_algorithms.prescan_algorithm import PreScanAlgorithm
from .dice_algorithms.ai_layer_1 import AILayer1
from .dice_algorithms.validation_algorithm import ValidationAlgorithm
from .dice_algorithms.ai_layer_2 import AILayer2
from .dice_algorithms.tts_service import TTSService

logger = logging.getLogger(__name__)


class DICEOrchestrator:
    """
    Main orchestrator for the DICE™ processing pipeline
    
    This class manages the complete workflow from raw file processing
    through final minutes generation, including error handling, 
    progress tracking, and HITL integration.
    """
    
    def __init__(self, job_id: uuid.UUID, db_session: Optional[AsyncSession] = None):
        """
        Initialize the DICE orchestrator
        
        Args:
            job_id: UUID of the DICE job to process
            db_session: Optional database session (will create one if not provided)
        """
        self.job_id = job_id
        self.db = db_session
        self.job: Optional[DiceJob] = None
        
        # Algorithm instances
        self.prescan_algo = PreScanAlgorithm()
        self.ai_layer_1 = AILayer1()
        self.validator = ValidationAlgorithm()
        self.ai_layer_2 = AILayer2()
        self.tts_service = TTSService()
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.db:
            self.db = await get_async_session().__anext__()
        await self._load_job()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.db:
            await self.db.close()
    
    async def _load_job(self) -> None:
        """Load the DICE job from database"""
        result = await self.db.execute(
            select(DiceJob).where(DiceJob.id == self.job_id)
        )
        self.job = result.scalar_one_or_none()
        
        if not self.job:
            raise ValueError(f"DICE job {self.job_id} not found")
    
    async def _log_event(
        self, 
        level: str, 
        step: str, 
        message: str, 
        context_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """Log an event to the job log"""
        log_entry = DiceJobLog(
            job_id=self.job_id,
            level=level,
            step=step,
            message=message,
            context_data=context_data or {},
            execution_time=execution_time
        )
        
        self.db.add(log_entry)
        await self.db.commit()
        
        # Also log to application logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"DICE Job {self.job_id} - {step}: {message}", extra=context_data)
    
    async def _update_status(
        self, 
        status: str, 
        progress: Optional[float] = None, 
        step: Optional[str] = None
    ) -> None:
        """Update job status and progress"""
        self.job.status = status
        
        if progress is not None:
            self.job.progress_percentage = progress
        
        if step:
            self.job.current_step = step
        
        self.job.updated_at = datetime.utcnow()
        await self.db.commit()
        
        await self._log_event("INFO", step or status, f"Status updated to {status}")
    
    async def run_pipeline(self) -> DiceJob:
        """
        Execute the complete DICE™ pipeline
        
        Returns:
            Updated DiceJob with processing results
        """
        start_time = datetime.utcnow()
        
        try:
            await self._log_event("INFO", "pipeline_start", "Starting DICE™ pipeline")
            
            # Mark processing as started
            self.job.processing_started_at = start_time
            await self._update_status("processing_prescan", 5.0, "prescan")
            
            # Step 1: Pre-scan Algorithm
            prescan_result = await self._run_prescan()
            self.job.mark_step_complete("prescan", prescan_result.dict())
            await self.db.commit()
            
            # Step 2: AI Layer 1 - Draft Transcript
            await self._update_status("processing_ai_layer_1", 25.0, "ai_layer_1")
            draft_result = await self._run_ai_layer_1(prescan_result)
            self.job.mark_step_complete("ai_layer_1", draft_result.dict())
            await self.db.commit()
            
            # Step 3: Validation Algorithm
            await self._update_status("processing_validation", 50.0, "validation")
            validation_result = await self._run_validation(draft_result)
            self.job.mark_step_complete("validation", validation_result.dict())
            await self.db.commit()
            
            # Check if HITL is required
            if self.job.requires_hitl:
                await self._log_event(
                    "INFO", 
                    "hitl_required", 
                    "Job requires human-in-the-loop review",
                    {"validation_score": validation_result.scores.get("overall", 0)}
                )
                return self.job
            
            # Step 4: AI Layer 2 - Final Refinement
            await self._update_status("processing_ai_layer_2", 75.0, "ai_layer_2")
            final_result = await self._run_ai_layer_2(draft_result, validation_result)
            self.job.mark_step_complete("ai_layer_2", final_result.dict())
            await self.db.commit()
            
            # Step 5: TTS Generation (if enabled)
            if self.job.processing_config.get("generate_tts", True):
                await self._update_status("processing_tts", 90.0, "tts")
                tts_result = await self._run_tts(final_result)
                self.job.mark_step_complete("tts", tts_result)
                await self.db.commit()
            else:
                self.job.status = "complete"
                self.job.progress_percentage = 100.0
                self.job.processing_completed_at = datetime.utcnow()
                await self.db.commit()
            
            # Calculate total processing time
            end_time = datetime.utcnow()
            self.job.total_processing_time = (end_time - start_time).total_seconds()
            await self.db.commit()
            
            await self._log_event(
                "INFO", 
                "pipeline_complete", 
                "DICE™ pipeline completed successfully",
                {"processing_time": self.job.total_processing_time}
            )
            
            return self.job
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.job.mark_failed(error_msg)
            await self.db.commit()
            
            await self._log_event(
                "ERROR", 
                "pipeline_error", 
                error_msg,
                {"error_type": type(e).__name__, "error_details": str(e)}
            )
            
            raise
    
    async def _run_prescan(self) -> PreScanJSON:
        """Execute the pre-scan algorithm"""
        start_time = datetime.utcnow()
        
        try:
            # Get file information from job
            files = [FileInfo(**file_data) for file_data in self.job.files]
            
            # Run pre-scan algorithm
            result = await self.prescan_algo.process_files(files)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            await self._log_event(
                "INFO",
                "prescan_complete",
                f"Pre-scan completed with confidence {result.ocr_confidence:.2f}",
                {
                    "ocr_confidence": result.ocr_confidence,
                    "entities_detected": len(result.entities_detected),
                    "execution_time": execution_time
                },
                execution_time
            )
            
            return result
            
        except Exception as e:
            await self._log_event(
                "ERROR",
                "prescan_error",
                f"Pre-scan failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            raise
    
    async def _run_ai_layer_1(self, prescan_result: PreScanJSON) -> DraftTranscriptJSON:
        """Execute AI Layer 1 - Draft transcript generation"""
        start_time = datetime.utcnow()
        
        try:
            # Get file information
            files = [FileInfo(**file_data) for file_data in self.job.files]
            
            # Run AI Layer 1
            result = await self.ai_layer_1.generate_draft_transcript(files, prescan_result)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            await self._log_event(
                "INFO",
                "ai_layer_1_complete",
                f"Draft transcript generated with {len(result.segments)} segments",
                {
                    "segments_count": len(result.segments),
                    "word_count": result.word_count,
                    "confidence": result.confidence,
                    "execution_time": execution_time
                },
                execution_time
            )
            
            return result
            
        except Exception as e:
            await self._log_event(
                "ERROR",
                "ai_layer_1_error",
                f"AI Layer 1 failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            raise
    
    async def _run_validation(self, draft_transcript: DraftTranscriptJSON) -> ValidationReportJSON:
        """Execute validation algorithm"""
        start_time = datetime.utcnow()
        
        try:
            # Run validation
            result = await self.validator.validate_transcript(draft_transcript)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            await self._log_event(
                "INFO",
                "validation_complete",
                f"Validation completed with {len(result.issues)} issues found",
                {
                    "issues_count": len(result.issues),
                    "overall_score": result.scores.get("overall", 0),
                    "requires_hitl": result.requires_human_review,
                    "execution_time": execution_time
                },
                execution_time
            )
            
            return result
            
        except Exception as e:
            await self._log_event(
                "ERROR",
                "validation_error",
                f"Validation failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            raise
    
    async def _run_ai_layer_2(
        self, 
        draft_transcript: DraftTranscriptJSON, 
        validation_report: ValidationReportJSON
    ) -> FinalMinutes:
        """Execute AI Layer 2 - Final refinement"""
        start_time = datetime.utcnow()
        
        try:
            # Run AI Layer 2
            result = await self.ai_layer_2.refine_transcript(draft_transcript, validation_report)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            await self._log_event(
                "INFO",
                "ai_layer_2_complete",
                f"Final minutes generated with {len(result.action_items)} action items",
                {
                    "action_items_count": len(result.action_items),
                    "decisions_count": len(result.decisions),
                    "quality_score": result.quality_score,
                    "execution_time": execution_time
                },
                execution_time
            )
            
            return result
            
        except Exception as e:
            await self._log_event(
                "ERROR",
                "ai_layer_2_error",
                f"AI Layer 2 failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            raise
    
    async def _run_tts(self, final_minutes: FinalMinutes) -> Dict[str, str]:
        """Execute TTS generation"""
        start_time = datetime.utcnow()
        
        try:
            # Generate TTS for summary and full transcript
            tts_results = await self.tts_service.generate_audio(final_minutes)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            await self._log_event(
                "INFO",
                "tts_complete",
                "TTS generation completed",
                {
                    "audio_files_generated": len(tts_results),
                    "execution_time": execution_time
                },
                execution_time
            )
            
            return tts_results
            
        except Exception as e:
            await self._log_event(
                "ERROR",
                "tts_error",
                f"TTS generation failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
            raise
    
    async def continue_after_hitl(self, edited_transcript: DraftTranscriptJSON) -> DiceJob:
        """
        Continue processing after human-in-the-loop review
        
        Args:
            edited_transcript: Human-edited transcript
            
        Returns:
            Updated DiceJob
        """
        try:
            await self._log_event("INFO", "hitl_continue", "Continuing after HITL review")
            
            # Update the draft transcript with human edits
            self.job.draft_transcript = edited_transcript.dict()
            
            # Mark HITL as complete
            self.job.complete_hitl_review()
            await self.db.commit()
            
            # Re-run validation on edited transcript
            validation_result = await self._run_validation(edited_transcript)
            self.job.validation_report = validation_result.dict()
            await self.db.commit()
            
            # Continue with AI Layer 2
            await self._update_status("processing_ai_layer_2", 75.0, "ai_layer_2")
            final_result = await self._run_ai_layer_2(edited_transcript, validation_result)
            self.job.mark_step_complete("ai_layer_2", final_result.dict())
            await self.db.commit()
            
            # TTS if enabled
            if self.job.processing_config.get("generate_tts", True):
                await self._update_status("processing_tts", 90.0, "tts")
                tts_result = await self._run_tts(final_result)
                self.job.mark_step_complete("tts", tts_result)
                await self.db.commit()
            else:
                self.job.status = "complete"
                self.job.progress_percentage = 100.0
                self.job.processing_completed_at = datetime.utcnow()
                await self.db.commit()
            
            await self._log_event("INFO", "hitl_pipeline_complete", "Pipeline completed after HITL")
            
            return self.job
            
        except Exception as e:
            error_msg = f"Post-HITL processing failed: {str(e)}"
            self.job.mark_failed(error_msg)
            await self.db.commit()
            
            await self._log_event("ERROR", "hitl_continue_error", error_msg)
            raise
    
    @staticmethod
    async def create_job(
        user_id: uuid.UUID,
        files: List[FileInfo],
        title: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Create a new DICE job
        
        Args:
            user_id: ID of the user creating the job
            files: List of files to process
            title: Job title
            description: Optional job description
            config: Processing configuration
            
        Returns:
            UUID of the created job
        """
        async with get_async_session() as db:
            job = DiceJob(
                user_id=user_id,
                title=title,
                description=description,
                files=[file.dict() for file in files],
                processing_config=config or {}
            )
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            return job.id

