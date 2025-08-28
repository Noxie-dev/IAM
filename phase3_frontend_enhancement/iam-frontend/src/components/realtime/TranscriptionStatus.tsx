/**
 * Transcription Status Component
 * Phase 3: Frontend Enhancement
 * 
 * Real-time transcription status updates with WebSocket
 */

'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  WifiIcon,
} from '@heroicons/react/24/outline';
import { useTranscriptionUpdates } from '@/hooks/useWebSocket';

// Helper functions shared between components
const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'processing':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'failed':
      return 'text-red-600 bg-red-50 border-red-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon className="h-5 w-5" />;
    case 'processing':
      return (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        >
          <ClockIcon className="h-5 w-5" />
        </motion.div>
      );
    case 'failed':
      return <ExclamationTriangleIcon className="h-5 w-5" />;
    default:
      return <ClockIcon className="h-5 w-5" />;
  }
};

const formatProgress = (progress?: number) => {
  if (progress === undefined) return '';
  return `${Math.round(progress)}%`;
};

interface TranscriptionStatusProps {
  transcriptionId?: string;
  showGlobalStatus?: boolean;
  className?: string;
}

export default function TranscriptionStatus({
  transcriptionId,
  showGlobalStatus = false,
  className = '',
}: TranscriptionStatusProps) {
  const {
    isConnected,
    isConnecting,
    error,
    transcriptionUpdates,
    clearTranscriptionUpdate,
  } = useTranscriptionUpdates();

  const [dismissedUpdates, setDismissedUpdates] = useState<Set<string>>(new Set());

  // Get specific transcription status or all updates
  const relevantUpdates = transcriptionId
    ? transcriptionUpdates.filter(u => u.transcription_id === transcriptionId)
    : transcriptionUpdates.filter(u => !dismissedUpdates.has(u.transcription_id));

  const dismissUpdate = (updateId: string) => {
    setDismissedUpdates(prev => new Set([...prev, updateId]));
    clearTranscriptionUpdate(updateId);
  };



  // Connection status indicator
  const ConnectionStatus = () => (
    <div className="flex items-center space-x-2 text-xs">
      <div className="flex items-center space-x-1">
        <WifiIcon className={`h-3 w-3 ${isConnected ? 'text-green-500' : 'text-gray-400'}`} />
        <span className={isConnected ? 'text-green-600' : 'text-gray-500'}>
          {isConnecting ? 'Connecting...' : isConnected ? 'Live' : 'Offline'}
        </span>
      </div>
      {error && (
        <span className="text-red-500 text-xs">
          Connection error
        </span>
      )}
    </div>
  );

  if (!showGlobalStatus && !transcriptionId) {
    return null;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Connection Status */}
      {showGlobalStatus && (
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-medium text-gray-900">Real-time Updates</h3>
          <ConnectionStatus />
        </div>
      )}

      {/* Transcription Updates */}
      <AnimatePresence mode="popLayout">
        {relevantUpdates.map((update) => (
          <motion.div
            key={update.transcription_id}
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className={`border rounded-lg p-4 ${getStatusColor(update.status)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(update.status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium">
                      Transcription {update.transcription_id.slice(0, 8)}...
                    </p>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-white bg-opacity-50">
                      {update.status}
                    </span>
                  </div>
                  
                  {update.status === 'processing' && update.progress !== undefined && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs">
                        <span>Processing...</span>
                        <span>{formatProgress(update.progress)}</span>
                      </div>
                      <div className="mt-1 bg-white bg-opacity-50 rounded-full h-2">
                        <motion.div
                          className="bg-current h-2 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${update.progress || 0}%` }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {update.status === 'completed' && (
                    <p className="mt-1 text-xs">
                      Transcription completed successfully
                    </p>
                  )}
                  
                  {update.status === 'failed' && update.error && (
                    <p className="mt-1 text-xs">
                      Error: {update.error}
                    </p>
                  )}
                </div>
              </div>
              
              {showGlobalStatus && (
                <button
                  type="button"
                  onClick={() => dismissUpdate(update.transcription_id)}
                  className="flex-shrink-0 ml-2 p-1 rounded-full hover:bg-white hover:bg-opacity-50 transition-colors"
                  title="Dismiss notification"
                  aria-label="Dismiss notification"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Empty State */}
      {showGlobalStatus && relevantUpdates.length === 0 && isConnected && (
        <div className="text-center py-6 text-gray-500">
          <ClockIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
          <p className="text-sm">No active transcriptions</p>
          <p className="text-xs">Real-time updates will appear here</p>
        </div>
      )}

      {/* Offline State */}
      {showGlobalStatus && !isConnected && !isConnecting && (
        <div className="text-center py-6 text-gray-500 border border-gray-200 rounded-lg bg-gray-50">
          <WifiIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
          <p className="text-sm">Real-time updates unavailable</p>
          <p className="text-xs">
            {error ? 'Connection error occurred' : 'Not connected to live updates'}
          </p>
        </div>
      )}
    </div>
  );
}

// Floating notification component for global updates
export function FloatingTranscriptionUpdates() {
  const { transcriptionUpdates, clearTranscriptionUpdate } = useTranscriptionUpdates();
  const [visibleUpdates, setVisibleUpdates] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Show new updates
    transcriptionUpdates.forEach(update => {
      if (!visibleUpdates.has(update.transcription_id)) {
        setVisibleUpdates(prev => new Set([...prev, update.transcription_id]));
        
        // Auto-hide completed/failed updates after 5 seconds
        if (update.status === 'completed' || update.status === 'failed') {
          setTimeout(() => {
            setVisibleUpdates(prev => {
              const newSet = new Set(prev);
              newSet.delete(update.transcription_id);
              return newSet;
            });
            clearTranscriptionUpdate(update.transcription_id);
          }, 5000);
        }
      }
    });
  }, [transcriptionUpdates, visibleUpdates, clearTranscriptionUpdate]);

  const visibleTranscriptions = transcriptionUpdates.filter(u => 
    visibleUpdates.has(u.transcription_id)
  );

  if (visibleTranscriptions.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      <AnimatePresence>
        {visibleTranscriptions.map((update) => (
          <motion.div
            key={update.transcription_id}
            initial={{ opacity: 0, x: 300, scale: 0.8 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 300, scale: 0.8 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className={`border rounded-lg p-4 shadow-lg backdrop-blur-sm ${getStatusColor(update.status)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(update.status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">
                    Transcription Update
                  </p>
                  <p className="text-xs opacity-75">
                    ID: {update.transcription_id.slice(0, 8)}...
                  </p>
                  
                  {update.status === 'processing' && update.progress !== undefined && (
                    <div className="mt-2">
                      <div className="text-xs">{formatProgress(update.progress)} complete</div>
                      <div className="mt-1 bg-white bg-opacity-50 rounded-full h-1">
                        <motion.div
                          className="bg-current h-1 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${update.progress || 0}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <button
                type="button"
                onClick={() => {
                  setVisibleUpdates(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(update.transcription_id);
                    return newSet;
                  });
                  clearTranscriptionUpdate(update.transcription_id);
                }}
                className="flex-shrink-0 ml-2 p-1 rounded-full hover:bg-white hover:bg-opacity-50 transition-colors"
                title="Dismiss notification"
                aria-label="Dismiss notification"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
