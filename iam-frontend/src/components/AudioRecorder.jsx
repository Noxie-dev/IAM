import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Mic, Square, Play, Pause } from 'lucide-react';

const AudioRecorder = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [validationError, setValidationError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const chunksRef = useRef([]);

  // Audio validation constants
  const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
  const MAX_RECORDING_TIME = 30 * 60; // 30 minutes in seconds
  const MIN_RECORDING_TIME = 1; // 1 second minimum

  const validateAudioBlob = (blob) => {
    if (!blob) {
      return { isValid: false, error: 'No audio data recorded' };
    }

    if (blob.size === 0) {
      return { isValid: false, error: 'Audio recording is empty' };
    }

    if (blob.size > MAX_FILE_SIZE) {
      const sizeMB = (blob.size / (1024 * 1024)).toFixed(1);
      return { isValid: false, error: `Recording too large (${sizeMB}MB). Maximum size is 25MB.` };
    }

    if (recordingTime < MIN_RECORDING_TIME) {
      return { isValid: false, error: 'Recording too short. Minimum duration is 1 second.' };
    }

    return { isValid: true, error: null };
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });

        // Validate the recorded audio
        const validation = validateAudioBlob(blob);
        if (!validation.isValid) {
          setValidationError(validation.error);
          setAudioBlob(null);
          setRecordedAudio(null);
          return;
        }

        // Clear any previous validation errors
        setValidationError(null);

        const audioUrl = URL.createObjectURL(blob);
        setRecordedAudio(audioUrl);
        setAudioBlob(blob);

        if (onRecordingComplete) {
          onRecordingComplete(blob);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          // Auto-stop recording if maximum time reached
          if (newTime >= MAX_RECORDING_TIME) {
            stopRecording();
            return newTime;
          }
          return newTime;
        });
      }, 1000);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  };

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col items-center space-y-4 p-6 bg-card rounded-lg border">
      <div className="text-2xl font-bold text-center">
        {isRecording ? 'Recording...' : 'Ready to Record'}
      </div>
      
      <div className="text-lg font-mono">
        {formatTime(recordingTime)}
      </div>

      <div className="flex space-x-4">
        {!isRecording ? (
          <Button
            onClick={startRecording}
            className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white"
            size="lg"
          >
            <Mic className="w-5 h-5" />
            <span>Start Recording</span>
          </Button>
        ) : (
          <Button
            onClick={stopRecording}
            className="flex items-center space-x-2 bg-gray-500 hover:bg-gray-600 text-white"
            size="lg"
          >
            <Square className="w-5 h-5" />
            <span>Stop Recording</span>
          </Button>
        )}

        {recordedAudio && !isRecording && (
          <Button
            onClick={togglePlayback}
            className="flex items-center space-x-2"
            variant="outline"
            size="lg"
          >
            {isPlaying ? (
              <>
                <Pause className="w-5 h-5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Play</span>
              </>
            )}
          </Button>
        )}
      </div>

      {recordedAudio && (
        <audio
          ref={audioRef}
          src={recordedAudio}
          onEnded={() => setIsPlaying(false)}
          className="hidden"
        />
      )}

      {isRecording && (
        <div className="flex items-center space-x-2 text-red-500">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span>Recording in progress...</span>
          {recordingTime >= MAX_RECORDING_TIME - 60 && (
            <span className="text-orange-500 text-sm">
              ({Math.floor((MAX_RECORDING_TIME - recordingTime) / 60)}:{((MAX_RECORDING_TIME - recordingTime) % 60).toString().padStart(2, '0')} remaining)
            </span>
          )}
        </div>
      )}

      {validationError && (
        <div className="flex items-center space-x-2 text-red-500 bg-red-50 p-3 rounded-lg border border-red-200">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-sm">{validationError}</span>
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;

