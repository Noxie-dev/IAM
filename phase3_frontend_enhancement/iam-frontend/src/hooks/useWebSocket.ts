/**
 * WebSocket Hook
 * Phase 3: Frontend Enhancement
 * 
 * Custom hook for WebSocket connections and real-time updates
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface TranscriptionUpdate {
  transcription_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
  result?: any;
}

interface UseWebSocketOptions {
  url?: string;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onTranscriptionUpdate?: (update: TranscriptionUpdate) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onTranscriptionUpdate,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const { user, isAuthenticated } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const mountedRef = useRef(true);

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const connect = useCallback(() => {
    if (!isAuthenticated || !user || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Get auth token for WebSocket connection
      const token = localStorage.getItem('access_token');
      const wsUrl = `${url}?token=${token}&user_id=${user.id}`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCountRef.current = 0;
        
        console.log('WebSocket connected');
        onConnect?.();
        
        // Send initial message to identify the client
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'identify',
            data: {
              user_id: user.id,
              timestamp: new Date().toISOString(),
            },
          }));
        }
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle different message types
          switch (message.type) {
            case 'transcription_update':
              const update = message.data as TranscriptionUpdate;
              onTranscriptionUpdate?.(update);
              
              // Show toast notifications for status changes
              if (update.status === 'completed') {
                toast.success(`Transcription completed: ${update.transcription_id}`);
              } else if (update.status === 'failed') {
                toast.error(`Transcription failed: ${update.error || 'Unknown error'}`);
              }
              break;
              
            case 'system_notification':
              toast(message.data.message);
              break;
              
            case 'error':
              toast.error(message.data.message || 'WebSocket error occurred');
              break;
              
            default:
              console.log('Received WebSocket message:', message);
          }
          
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        if (!mountedRef.current) return;
        
        setIsConnected(false);
        setIsConnecting(false);
        
        console.log('WebSocket disconnected:', event.code, event.reason);
        onDisconnect?.();
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectCountRef.current < reconnectAttempts) {
          const delay = reconnectInterval * Math.pow(1.5, reconnectCountRef.current);
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectCountRef.current + 1}/${reconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              reconnectCountRef.current++;
              connect();
            }
          }, delay);
        } else if (reconnectCountRef.current >= reconnectAttempts) {
          setError('Failed to reconnect after multiple attempts');
          toast.error('Connection lost. Please refresh the page.');
        }
      };

      wsRef.current.onerror = (event) => {
        if (!mountedRef.current) return;

        console.error('WebSocket error:', {
          event,
          url: wsUrl,
          readyState: wsRef.current?.readyState,
          timestamp: new Date().toISOString(),
        });

        const errorMessage = `WebSocket connection failed to ${wsUrl}`;
        setError(errorMessage);
        setIsConnecting(false);
        toast.error('Failed to connect to real-time updates');
        onError?.(event);
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [url, user, isAuthenticated, reconnectAttempts, reconnectInterval, onConnect, onDisconnect, onError, onMessage, onTranscriptionUpdate]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
    reconnectCountRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messageWithTimestamp = {
        ...message,
        timestamp: new Date().toISOString(),
      };
      
      wsRef.current.send(JSON.stringify(messageWithTimestamp));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
      toast.error('Connection lost. Please refresh the page.');
    }
  }, []);

  // Auto-connect when authenticated
  useEffect(() => {
    if (isAuthenticated && user && process.env.NEXT_PUBLIC_ENABLE_WEBSOCKETS === 'true') {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [isAuthenticated, user, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [disconnect]);

  // Ping/pong to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping' });
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    connect,
    disconnect,
    lastMessage,
  };
}

// Hook specifically for transcription updates
export function useTranscriptionUpdates() {
  const [transcriptionUpdates, setTranscriptionUpdates] = useState<TranscriptionUpdate[]>([]);

  const handleTranscriptionUpdate = useCallback((update: TranscriptionUpdate) => {
    setTranscriptionUpdates(prev => {
      // Remove any existing update for the same transcription
      const filtered = prev.filter(u => u.transcription_id !== update.transcription_id);
      return [...filtered, update];
    });
  }, []);

  const { isConnected, isConnecting, error, sendMessage } = useWebSocket({
    onTranscriptionUpdate: handleTranscriptionUpdate,
  });

  const getTranscriptionStatus = useCallback((transcriptionId: string) => {
    return transcriptionUpdates.find(u => u.transcription_id === transcriptionId);
  }, [transcriptionUpdates]);

  const clearTranscriptionUpdate = useCallback((transcriptionId: string) => {
    setTranscriptionUpdates(prev => prev.filter(u => u.transcription_id !== transcriptionId));
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    transcriptionUpdates,
    getTranscriptionStatus,
    clearTranscriptionUpdate,
    sendMessage,
  };
}
