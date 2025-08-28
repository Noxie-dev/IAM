/**
 * File Upload Component
 * Phase 3: Frontend Enhancement
 * 
 * Drag-and-drop file upload with progress indicators
 */

'use client';

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { toast } from 'react-hot-toast';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { usePermissions } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';
import styles from './FileUpload.module.css';

interface UploadResult {
  id: string;
  title: string;
  original_filename: string;
  audio_file_size: number;
  audio_file_format: string;
  processing_status: string;
  created_at: string;
  // Additional fields that may be present in the upload response
  message?: string;
  [key: string]: unknown; // Allow for additional fields during development
}

interface TranscriptionSettings {
  title?: string;
  description?: string;
  language?: string;
  provider?: string;
  model?: string;
  speaker_detection?: boolean;
  timestamps?: boolean;
  word_timestamps?: boolean;
  enhance_audio?: boolean;
  enhancement_options?: {
    noise_reduction?: boolean;
    vad_attenuation_db?: number;
    high_pass_freq?: number;
    lufs_target?: number;
    speaker_boost_db?: number;
  };
}

interface FileUploadProps {
  onUploadComplete?: (result: UploadResult) => void;
  onUploadStart?: () => void;
  maxFiles?: number;
  className?: string;
  transcriptionSettings?: TranscriptionSettings;
}

interface UploadFile {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
  result?: UploadResult;
}

// Progress Bar Component to avoid inline styles
const ProgressBar = ({ progress }: { progress: number }) => {
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (progressRef.current) {
      progressRef.current.style.setProperty('--progress-width', `${progress}%`);
    }
  }, [progress]);

  return (
    <div className={`mt-1 bg-gray-200 rounded-full h-1 ${styles.progressContainer}`} ref={progressRef}>
      <div className={styles.progressBar} />
    </div>
  );
};

export default function FileUpload({
  onUploadComplete,
  onUploadStart,
  maxFiles = 5,
  className = '',
  transcriptionSettings,
}: FileUploadProps) {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const { canUpload, canTranscribe, remainingMinutes } = usePermissions();

  // Supported audio formats
  const supportedFormats = useMemo(() => ['mp3', 'wav', 'm4a', 'mp4', 'mpeg', 'mpga', 'ogg', 'webm', 'flac'], []);
  const maxFileSize = 250 * 1024 * 1024; // 250MB

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize) {
      return `File size must be less than 250MB. Current size: ${(file.size / 1024 / 1024).toFixed(1)}MB`;
    }

    // Check file format
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !supportedFormats.includes(extension)) {
      return `Unsupported file format. Supported formats: ${supportedFormats.join(', ')}`;
    }

    // Check permissions
    if (!canUpload) {
      return 'Your account does not have upload permissions';
    }

    if (!canTranscribe) {
      return `Insufficient transcription minutes remaining: ${remainingMinutes} minutes left`;
    }

    return null;
  }, [maxFileSize, supportedFormats, canUpload, canTranscribe, remainingMinutes]);

  const startUpload = useCallback(async (uploadFile: UploadFile) => {
    setUploadFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 0 } : f
      )
    );

    onUploadStart?.();

    try {
      const result = await apiClient.uploadFile(
        uploadFile.file,
        transcriptionSettings,
        (progress: number) => {
          setUploadFiles((prev) =>
            prev.map((f) =>
              f.id === uploadFile.id ? { ...f, progress } : f
            )
          );
        }
      );

      if (result.success) {
        setUploadFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id
              ? { ...f, status: 'completed', progress: 100, result: result.data }
              : f
          )
        );

        toast.success(`${uploadFile.file.name} uploaded successfully!`);
        onUploadComplete?.(result.data);
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';

      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: 'error', error: errorMessage }
            : f
        )
      );

      toast.error(`${uploadFile.file.name}: ${errorMessage}`);
    }
  }, [onUploadStart, onUploadComplete, transcriptionSettings]);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      // Handle rejected files
      rejectedFiles.forEach((rejection) => {
        const error = rejection.errors[0]?.message || 'File rejected';
        toast.error(`${rejection.file.name}: ${error}`);
      });

      // Process accepted files
      const newFiles: UploadFile[] = acceptedFiles.map((file) => {
        const validationError = validateFile(file);
        
        return {
          file,
          id: `${file.name}-${Date.now()}-${Math.random()}`,
          progress: 0,
          status: validationError ? 'error' : 'pending',
          error: validationError || undefined,
        };
      });

      // Check total file limit
      const totalFiles = uploadFiles.length + newFiles.length;
      if (totalFiles > maxFiles) {
        toast.error(`Maximum ${maxFiles} files allowed. Please remove some files first.`);
        return;
      }

      setUploadFiles((prev) => [...prev, ...newFiles]);

      // Auto-start upload for valid files
      newFiles.forEach((uploadFile) => {
        if (uploadFile.status === 'pending') {
          startUpload(uploadFile);
        }
      });
    },
    [uploadFiles.length, maxFiles, startUpload, validateFile]
  );

  const removeFile = (fileId: string) => {
    setUploadFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const retryUpload = (uploadFile: UploadFile) => {
    const validationError = validateFile(uploadFile.file);
    if (validationError) {
      toast.error(validationError);
      return;
    }
    startUpload(uploadFile);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': supportedFormats.map((format) => `.${format}`),
    },
    maxSize: maxFileSize,
    multiple: true,
    disabled: !canUpload,
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'uploading':
        return (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        );
      default:
        return <DocumentIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
          isDragActive
            ? 'border-blue-400 bg-blue-50'
            : canUpload
            ? 'border-gray-300 hover:border-gray-400'
            : 'border-gray-200 bg-gray-50'
        } ${!canUpload ? 'cursor-not-allowed' : 'cursor-pointer'}`}
      >
        <input {...getInputProps()} />
        
        <div className="text-center">
          <CloudArrowUpIcon
            className={`mx-auto h-12 w-12 ${
              canUpload ? 'text-gray-400' : 'text-gray-300'
            }`}
          />
          
          <div className="mt-4">
            {!canUpload ? (
              <p className="text-sm text-gray-500">
                Upload not available. Please check your account permissions.
              </p>
            ) : !canTranscribe ? (
              <div className="space-y-2">
                <p className="text-sm text-red-600 font-medium">
                  Insufficient transcription minutes
                </p>
                <p className="text-xs text-gray-500">
                  You have {remainingMinutes} minutes remaining. Upgrade your plan for more minutes.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500">
                  Audio files up to 250MB ({supportedFormats.join(', ')})
                </p>
                <p className="text-xs text-gray-400">
                  Maximum {maxFiles} files • {remainingMinutes} minutes remaining
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* File List */}
      {uploadFiles.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-900">
            Files ({uploadFiles.length}/{maxFiles})
          </h3>
          
          <div className="space-y-2">
            {uploadFiles.map((uploadFile) => (
              <div
                key={uploadFile.id}
                className="flex items-center space-x-3 p-3 bg-white border border-gray-200 rounded-lg"
              >
                <div className="flex-shrink-0">
                  {getStatusIcon(uploadFile.status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {uploadFile.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(uploadFile.file.size)}
                    </p>
                  </div>
                  
                  {uploadFile.status === 'uploading' && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Uploading...</span>
                        <span>{uploadFile.progress}%</span>
                      </div>
                      <ProgressBar progress={uploadFile.progress} />
                    </div>
                  )}
                  
                  {uploadFile.status === 'error' && (
                    <div className="mt-1">
                      <p className="text-xs text-red-600">{uploadFile.error}</p>
                      <button
                        type="button"
                        onClick={() => retryUpload(uploadFile)}
                        className="mt-1 text-xs text-blue-600 hover:text-blue-500"
                      >
                        Retry upload
                      </button>
                    </div>
                  )}
                  
                  {uploadFile.status === 'completed' && (
                    <p className="mt-1 text-xs text-green-600">
                      Upload completed successfully
                    </p>
                  )}
                </div>
                
                <button
                  type="button"
                  onClick={() => removeFile(uploadFile.id)}
                  className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600"
                  aria-label="Remove file"
                  title="Remove file"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
