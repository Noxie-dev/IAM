from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import time
import logging
from openai import OpenAI
import openai
from src.models.meeting import Meeting, db

meeting_bp = Blueprint('meeting', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key or api_key == 'sk-demo-key-for-development':
    # For development without real API key, create a mock client
    client = None
    print("⚠️  Warning: Using demo mode without OpenAI API key")
else:
    client = OpenAI(api_key=api_key)

# Audio processing constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit for OpenAI Whisper
SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.mp4', '.mpeg', '.mpga', '.ogg', '.webm', '.flac'}
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1  # Base delay in seconds for exponential backoff

def validate_audio_file(audio_file):
    """Validate audio file format and size"""
    if not audio_file or audio_file.filename == '':
        return False, "No audio file provided"

    # Check file size
    audio_file.seek(0, os.SEEK_END)
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return False, f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {MAX_FILE_SIZE / (1024*1024)}MB"

    if file_size == 0:
        return False, "Audio file is empty"

    # Check file extension
    filename = secure_filename(audio_file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in SUPPORTED_FORMATS:
        return False, f"Unsupported audio format '{file_ext}'. Supported formats: {', '.join(SUPPORTED_FORMATS)}"

    return True, "Valid audio file"

def transcribe_with_retry(audio_file_path, max_retries=MAX_RETRY_ATTEMPTS):
    """Transcribe audio with retry logic for handling API failures"""
    
    # Handle demo mode without OpenAI client
    if client is None:
        logger.info("Demo mode: Returning mock transcription")
        return "This is a demo transcription. In production, this would be the actual transcribed text from your audio file.", None
    
    for attempt in range(max_retries):
        try:
            with open(audio_file_path, 'rb') as audio_file:
                logger.info(f"Attempting transcription (attempt {attempt + 1}/{max_retries})")

                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

                logger.info("Transcription successful")
                return transcript, None

        except openai.RateLimitError as e:
            logger.warning(f"Rate limit error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                # Extract retry-after header if available
                retry_after = getattr(e, 'retry_after', None) or (RETRY_DELAY_BASE * (2 ** attempt))
                logger.info(f"Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
            else:
                return None, "Rate limit exceeded. Please try again later."

        except openai.AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return None, "Authentication failed. Please check API configuration."

        except openai.BadRequestError as e:
            logger.error(f"Bad request error: {str(e)}")
            return None, f"Invalid audio file or request: {str(e)}"

        except openai.APIConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                return None, "Unable to connect to transcription service. Please try again later."

        except openai.APITimeoutError as e:
            logger.warning(f"Timeout error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                return None, "Transcription service timeout. Please try again with a shorter audio file."

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                return None, f"Transcription failed: {str(e)}"

    return None, "Transcription failed after multiple attempts"

@meeting_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    temp_file_path = None

    try:
        # Validate request
        if 'audio' not in request.files:
            logger.warning("Transcription request missing audio file")
            return jsonify({
                'success': False,
                'error': 'No audio file provided',
                'error_type': 'validation_error'
            }), 400

        audio_file = request.files['audio']
        title = request.form.get('title', 'Untitled Meeting')
        audio_id = request.form.get('audioId')

        logger.info(f"Processing transcription request for meeting: {title}")

        # Validate audio file
        is_valid, validation_message = validate_audio_file(audio_file)
        if not is_valid:
            logger.warning(f"Audio validation failed: {validation_message}")
            return jsonify({
                'success': False,
                'error': validation_message,
                'error_type': 'validation_error'
            }), 400

        # Check if OpenAI API key is configured
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OpenAI API key not configured")
            return jsonify({
                'success': False,
                'error': 'Transcription service not configured. Please contact support.',
                'error_type': 'configuration_error'
            }), 500

        # Save audio file temporarily for processing
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name
                logger.info(f"Audio file saved temporarily: {temp_file_path}")
        except Exception as e:
            logger.error(f"Failed to save temporary audio file: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to process audio file',
                'error_type': 'processing_error'
            }), 500

        # Transcribe audio with retry logic
        transcription_text, error_message = transcribe_with_retry(temp_file_path)

        if error_message:
            logger.error(f"Transcription failed: {error_message}")

            # Determine error type based on error message
            if "Rate limit" in error_message:
                error_type = 'rate_limit_error'
                status_code = 429
            elif "Authentication" in error_message:
                error_type = 'authentication_error'
                status_code = 500
            elif "connect" in error_message.lower() or "timeout" in error_message.lower():
                error_type = 'network_error'
                status_code = 503
            else:
                error_type = 'transcription_error'
                status_code = 500

            return jsonify({
                'success': False,
                'error': error_message,
                'error_type': error_type
            }), status_code

        # Save meeting to database
        try:
            meeting = Meeting(
                title=title,
                transcription_text=transcription_text,
                local_audio_id=str(audio_id) if audio_id else None
            )

            db.session.add(meeting)
            db.session.commit()

            logger.info(f"Meeting saved successfully with ID: {meeting.id}")

            return jsonify({
                'success': True,
                'meeting_id': meeting.id,
                'transcription': transcription_text,
                'message': 'Meeting transcribed and saved successfully'
            })

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Failed to save meeting to database',
                'error_type': 'database_error'
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error in transcribe_audio: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.',
            'error_type': 'server_error'
        }), 500

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file cleaned up: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {str(e)}")

@meeting_bp.route('/meetings', methods=['GET'])
def get_meetings():
    try:
        # Get query parameters for sorting and filtering
        sort_by = request.args.get('sort_by', 'date')  # date or title
        order = request.args.get('order', 'desc')  # asc or desc
        search = request.args.get('search', '')
        
        # Build query
        query = Meeting.query
        
        # Apply search filter
        if search:
            query = query.filter(
                Meeting.title.contains(search) | 
                Meeting.transcription_text.contains(search)
            )
        
        # Apply sorting
        if sort_by == 'title':
            if order == 'asc':
                query = query.order_by(Meeting.title.asc())
            else:
                query = query.order_by(Meeting.title.desc())
        else:  # sort by date
            if order == 'asc':
                query = query.order_by(Meeting.date.asc())
            else:
                query = query.order_by(Meeting.date.desc())
        
        meetings = query.all()
        
        return jsonify({
            'success': True,
            'meetings': [meeting.to_dict() for meeting in meetings]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@meeting_bp.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@meeting_bp.route('/meetings/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        db.session.delete(meeting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Meeting deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

