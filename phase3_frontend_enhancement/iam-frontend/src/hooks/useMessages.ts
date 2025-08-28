/**
 * Messages Hook
 * Phase 3: Frontend Enhancement
 * 
 * React hook for managing messages state with real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  Message,
  MessageCreate,
  MessageUpdate,
  MessageStats,
  MessageFolder,
  MessageListResponse,
  getMessages,
  getMessagesWithFilter,
  getMessage,
  sendMessage,
  updateMessageStatus,
  deleteMessage,
  bulkUpdateMessages,
  getMessageStats,
  EnhancedMessageWebSocketService,
  WebSocketMessage,
} from '@/lib/messageService';

interface UseMessagesOptions {
  folder?: MessageFolder;
  page?: number;
  per_page?: number;
  unread_only?: boolean;
  autoRefresh?: boolean;
  enableWebSocket?: boolean;
}

interface UseMessagesReturn {
  // State
  messages: Message[];
  selectedMessage: Message | null;
  stats: MessageStats | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  } | null;
  
  // Actions
  loadMessages: () => Promise<void>;
  loadMessage: (messageId: string) => Promise<void>;
  sendNewMessage: (messageData: MessageCreate) => Promise<void>;
  updateMessage: (messageId: string, updates: MessageUpdate) => Promise<void>;
  deleteMessageById: (messageId: string) => Promise<void>;
  bulkUpdate: (messageIds: string[], updates: MessageUpdate) => Promise<void>;
  loadStats: () => Promise<void>;
  
  // Pagination
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (page: number) => void;
  
  // Selection
  selectMessage: (message: Message | null) => void;
  
  // WebSocket
  isConnected: boolean;
  reconnect: () => void;
}

export const useMessages = (options: UseMessagesOptions = {}): UseMessagesReturn => {
  const {
    folder = 'inbox',
    page = 1,
    per_page = 20,
    unread_only = false,
    autoRefresh = true,
    enableWebSocket = true,
  } = options;

  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [stats, setStats] = useState<MessageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<{
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  } | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Refs
  const wsServiceRef = useRef<EnhancedMessageWebSocketService | null>(null);
  const currentPageRef = useRef(page);
  const currentFolderRef = useRef(folder);

  // Initialize WebSocket
  useEffect(() => {
    if (enableWebSocket && user?.id) {
      wsServiceRef.current = new EnhancedMessageWebSocketService(user.id);
      
      // Set up WebSocket handlers
      wsServiceRef.current.onMessage('new_message', (data: Message) => {
        setMessages(prev => [data, ...prev]);
        setStats(prev => prev ? {
          ...prev,
          inbox_count: prev.inbox_count + 1,
          unread_count: prev.unread_count + 1,
        } : null);
      });

      wsServiceRef.current.onMessage('message_updated', (data: Message) => {
        setMessages(prev => prev.map(msg => 
          msg.id === data.id ? data : msg
        ));
        
        // Update stats if needed
        if (data.is_read !== selectedMessage?.is_read) {
          setStats(prev => prev ? {
            ...prev,
            unread_count: prev.unread_count + (data.is_read ? -1 : 1),
          } : null);
        }
      });

      wsServiceRef.current.onMessage('message_deleted', (data: { message_id: string }) => {
        setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
        setSelectedMessage(prev => prev?.id === data.message_id ? null : prev);
        loadStats(); // Refresh stats
      });

      wsServiceRef.current.onConnectionChange((connected) => {
        setIsConnected(connected);
      });

      // Connect to WebSocket
      wsServiceRef.current.connect().catch(console.error);

      return () => {
        wsServiceRef.current?.disconnect();
      };
    }
  }, [enableWebSocket, user?.id]);

  // Load messages
  const loadMessages = useCallback(async () => {
    if (!user?.id) return;

    setLoading(true);
    setError(null);

    try {
      const response: MessageListResponse = await getMessagesWithFilter(
        currentFolderRef.current,
        currentPageRef.current,
        per_page,
        unread_only
      );

      setMessages(response.messages);
      setPagination(response.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  }, [user?.id, per_page, unread_only]);

  // Load specific message
  const loadMessage = useCallback(async (messageId: string) => {
    setLoading(true);
    setError(null);

    try {
      const message = await getMessage(messageId);
      setSelectedMessage(message);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load message');
    } finally {
      setLoading(false);
    }
  }, []);

  // Send new message
  const sendNewMessage = useCallback(async (messageData: MessageCreate) => {
    if (!user?.id) return;

    setLoading(true);
    setError(null);

    try {
      const newMessage = await sendMessage(messageData);
      
      // Add to sent messages if we're in sent folder
      if (currentFolderRef.current === 'sent') {
        setMessages(prev => [newMessage, ...prev]);
      }
      
      // Update stats
      setStats(prev => prev ? {
        ...prev,
        sent_count: prev.sent_count + 1,
      } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  // Update message
  const updateMessage = useCallback(async (messageId: string, updates: MessageUpdate) => {
    setLoading(true);
    setError(null);

    try {
      const updatedMessage = await updateMessageStatus(messageId, updates);
      
      // Update in messages list
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? updatedMessage : msg
      ));
      
      // Update selected message if it's the same
      setSelectedMessage(prev => 
        prev?.id === messageId ? updatedMessage : prev
      );
      
      // Update stats if needed
      if (updates.is_read !== undefined) {
        setStats(prev => prev ? {
          ...prev,
          unread_count: prev.unread_count + (updates.is_read ? -1 : 1),
        } : null);
      }
      
      if (updates.is_starred !== undefined) {
        setStats(prev => prev ? {
          ...prev,
          starred_count: prev.starred_count + (updates.is_starred ? 1 : -1),
        } : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update message');
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete message
  const deleteMessageById = useCallback(async (messageId: string) => {
    setLoading(true);
    setError(null);

    try {
      await deleteMessage(messageId);
      
      // Remove from messages list
      setMessages(prev => prev.filter(msg => msg.id !== messageId));
      
      // Clear selection if it's the deleted message
      setSelectedMessage(prev => 
        prev?.id === messageId ? null : prev
      );
      
      // Refresh stats
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete message');
    } finally {
      setLoading(false);
    }
  }, [loadStats]);

  // Bulk update messages
  const bulkUpdate = useCallback(async (messageIds: string[], updates: MessageUpdate) => {
    setLoading(true);
    setError(null);

    try {
      await bulkUpdateMessages(messageIds, updates);
      
      // Update messages in list
      setMessages(prev => prev.map(msg => 
        messageIds.includes(msg.id) ? { ...msg, ...updates } : msg
      ));
      
      // Update selected message if it's in the bulk update
      if (selectedMessage && messageIds.includes(selectedMessage.id)) {
        setSelectedMessage(prev => prev ? { ...prev, ...updates } : null);
      }
      
      // Refresh stats
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update messages');
    } finally {
      setLoading(false);
    }
  }, [selectedMessage, loadStats]);

  // Load stats
  const loadStats = useCallback(async () => {
    if (!user?.id) return;

    try {
      const messageStats = await getMessageStats();
      setStats(messageStats);
    } catch (err) {
      console.error('Failed to load message stats:', err);
    }
  }, [user?.id]);

  // Pagination functions
  const nextPage = useCallback(() => {
    if (pagination?.has_next) {
      currentPageRef.current = pagination.page + 1;
      loadMessages();
    }
  }, [pagination, loadMessages]);

  const prevPage = useCallback(() => {
    if (pagination?.has_prev) {
      currentPageRef.current = pagination.page - 1;
      loadMessages();
    }
  }, [pagination, loadMessages]);

  const goToPage = useCallback((page: number) => {
    currentPageRef.current = page;
    loadMessages();
  }, [loadMessages]);

  // Select message
  const selectMessage = useCallback((message: Message | null) => {
    setSelectedMessage(message);
  }, []);

  // Reconnect WebSocket
  const reconnect = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect();
      wsServiceRef.current.connect().catch(console.error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    if (user?.id) {
      loadMessages();
      loadStats();
    }
  }, [user?.id, loadMessages, loadStats]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && user?.id) {
      const interval = setInterval(() => {
        loadMessages();
        loadStats();
      }, 60000); // Refresh every minute

      return () => clearInterval(interval);
    }
  }, [autoRefresh, user?.id, loadMessages, loadStats]);

  // Update current folder when it changes
  useEffect(() => {
    currentFolderRef.current = folder;
    currentPageRef.current = 1;
    loadMessages();
  }, [folder, loadMessages]);

  return {
    // State
    messages,
    selectedMessage,
    stats,
    loading,
    error,
    pagination,
    
    // Actions
    loadMessages,
    loadMessage,
    sendNewMessage,
    updateMessage,
    deleteMessageById,
    bulkUpdate,
    loadStats,
    
    // Pagination
    nextPage,
    prevPage,
    goToPage,
    
    // Selection
    selectMessage,
    
    // WebSocket
    isConnected,
    reconnect,
  };
};
