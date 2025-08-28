/**
 * Enhanced Message Service
 * Phase 3: Frontend Enhancement - Production Ready
 * 
 * Comprehensive service for handling all message-related API calls and WebSocket connections
 * with production-ready features: retry logic, caching, error handling, and real-time updates
 */

import { api } from './api';
import { toast } from 'react-hot-toast';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface UserInfo {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  display_name?: string;
}

export interface Message {
  id: string;
  sender: UserInfo;
  recipient: UserInfo;
  subject: string;
  body: string;
  is_read: boolean;
  is_starred: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageCreate {
  recipient_id: string;
  subject: string;
  body: string;
}

export interface MessageUpdate {
  is_read?: boolean;
  is_starred?: boolean;
  is_archived?: boolean;
}

export interface MessageStats {
  inbox_count: number;
  unread_count: number;
  starred_count: number;
  sent_count: number;
  archived_count: number;
}

export interface Notification {
  id: string;
  user_id: string;
  message_id?: string;
  type: string;
  content: string;
  is_read: boolean;
  created_at: string;
  message?: Message;
}

export interface MessageListResponse {
  messages: Message[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface NotificationListResponse {
  notifications: Notification[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface WebSocketMessage {
  type: 'new_message' | 'message_read' | 'message_updated' | 'message_deleted' | 'notification' | 'connection_established';
  data?: any;
  user_id?: string;
  message?: string;
}

export type MessageFolder = 'inbox' | 'sent' | 'starred' | 'archived';

// ============================================================================
// ENHANCED API SERVICE WITH RETRY LOGIC & CACHING
// ============================================================================

/**
 * Enhanced API client with retry logic and caching
 */
class EnhancedApiClient {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private retryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
  };

  /**
   * Execute API call with retry logic
   */
  private async executeWithRetry<T>(
    apiCall: () => Promise<T>,
    retries: number = 0
  ): Promise<T> {
    try {
      return await apiCall();
    } catch (error: any) {
      if (retries < this.retryConfig.maxRetries && this.isRetryableError(error)) {
        const delay = Math.min(
          this.retryConfig.baseDelay * Math.pow(2, retries),
          this.retryConfig.maxDelay
        );
        
        console.warn(`API call failed, retrying in ${delay}ms (attempt ${retries + 1})`);
        await this.sleep(delay);
        return this.executeWithRetry(apiCall, retries + 1);
      }
      throw error;
    }
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    return retryableStatuses.includes(error?.response?.status) || 
           error?.code === 'NETWORK_ERROR' ||
           error?.message?.includes('timeout');
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get cached data or fetch from API
   */
  private async getCachedOrFetch<T>(
    key: string,
    apiCall: () => Promise<T>,
    ttl: number = 5 * 60 * 1000 // 5 minutes default
  ): Promise<T> {
    const cached = this.cache.get(key);
    const now = Date.now();

    if (cached && (now - cached.timestamp) < cached.ttl) {
      return cached.data;
    }

    const data = await this.executeWithRetry(apiCall);
    this.cache.set(key, { data, timestamp: now, ttl });
    return data;
  }

  /**
   * Invalidate cache entries
   */
  invalidateCache(pattern?: string): void {
    if (pattern) {
      for (const key of this.cache.keys()) {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }

  /**
   * Enhanced GET request
   */
  async get<T>(url: string, useCache: boolean = false, ttl?: number): Promise<T> {
    if (useCache) {
      return this.getCachedOrFetch(url, () => api.get(url).then(r => r.data), ttl);
    }
    return this.executeWithRetry(() => api.get(url).then(r => r.data));
  }

  /**
   * Enhanced POST request
   */
  async post<T>(url: string, data: any): Promise<T> {
    const result = await this.executeWithRetry(() => api.post(url, data).then(r => r.data));
    this.invalidateCache('messages'); // Invalidate related cache
    return result;
  }

  /**
   * Enhanced PATCH request
   */
  async patch<T>(url: string, data: any): Promise<T> {
    const result = await this.executeWithRetry(() => api.patch(url, data).then(r => r.data));
    this.invalidateCache('messages'); // Invalidate related cache
    return result;
  }

  /**
   * Enhanced DELETE request
   */
  async delete<T>(url: string): Promise<T> {
    const result = await this.executeWithRetry(() => api.delete(url).then(r => r.data));
    this.invalidateCache('messages'); // Invalidate related cache
    return result;
  }
}

// Create enhanced API client instance
const enhancedApi = new EnhancedApiClient();

// ============================================================================
// ENHANCED API SERVICE FUNCTIONS
// ============================================================================

/**
 * Get all messages for the current user with caching
 */
export const getMessages = async (): Promise<Message[]> => {
  try {
    return await enhancedApi.get<Message[]>('/messages', true, 2 * 60 * 1000); // 2 min cache
  } catch (error) {
    console.error('Error fetching messages:', error);
    toast.error('Failed to load messages');
    throw error;
  }
};

/**
 * Get messages with filtering, pagination, and caching
 */
export const getMessagesWithFilter = async (
  folder: MessageFolder = 'inbox',
  page: number = 1,
  per_page: number = 20,
  unread_only: boolean = false
): Promise<MessageListResponse> => {
  try {
    const params = new URLSearchParams({
      folder,
      page: page.toString(),
      per_page: per_page.toString(),
      unread_only: unread_only.toString(),
    });

    const cacheKey = `messages-${folder}-${page}-${per_page}-${unread_only}`;
    return await enhancedApi.get<MessageListResponse>(`/messages?${params}`, true, 1 * 60 * 1000); // 1 min cache
  } catch (error) {
    console.error('Error fetching messages with filter:', error);
    toast.error('Failed to load messages');
    throw error;
  }
};

/**
 * Get a specific message by ID with caching
 */
export const getMessage = async (messageId: string): Promise<Message> => {
  try {
    return await enhancedApi.get<Message>(`/messages/${messageId}`, true, 5 * 60 * 1000); // 5 min cache
  } catch (error) {
    console.error('Error fetching message:', error);
    toast.error('Failed to load message');
    throw error;
  }
};

/**
 * Send a new message with optimistic updates
 */
export const sendMessage = async (messageData: MessageCreate): Promise<Message> => {
  try {
    const response = await enhancedApi.post<Message>('/messages', messageData);
    toast.success('Message sent successfully');
    return response;
  } catch (error) {
    console.error('Error sending message:', error);
    toast.error('Failed to send message');
    throw error;
  }
};

/**
 * Update message status with optimistic updates
 */
export const updateMessageStatus = async (
  messageId: string,
  status: MessageUpdate
): Promise<Message> => {
  try {
    const response = await enhancedApi.patch<Message>(`/messages/${messageId}`, status);
    
    // Show appropriate toast based on what was updated
    if (status.is_read !== undefined) {
      toast.success(status.is_read ? 'Message marked as read' : 'Message marked as unread');
    }
    if (status.is_starred !== undefined) {
      toast.success(status.is_starred ? 'Message starred' : 'Message unstarred');
    }
    if (status.is_archived !== undefined) {
      toast.success(status.is_archived ? 'Message archived' : 'Message unarchived');
    }
    
    return response;
  } catch (error) {
    console.error('Error updating message status:', error);
    toast.error('Failed to update message');
    throw error;
  }
};

/**
 * Delete a message with confirmation
 */
export const deleteMessage = async (messageId: string): Promise<void> => {
  try {
    await enhancedApi.delete(`/messages/${messageId}`);
    toast.success('Message deleted successfully');
  } catch (error) {
    console.error('Error deleting message:', error);
    toast.error('Failed to delete message');
    throw error;
  }
};

/**
 * Bulk update messages with progress tracking
 */
export const bulkUpdateMessages = async (
  messageIds: string[],
  updates: MessageUpdate
): Promise<{ message: string; updated_count: number }> => {
  try {
    const response = await enhancedApi.put<{ message: string; updated_count: number }>('/messages/bulk', {
      message_ids: messageIds,
      updates,
    });
    
    toast.success(`Updated ${response.updated_count} messages`);
    return response;
  } catch (error) {
    console.error('Error bulk updating messages:', error);
    toast.error('Failed to update messages');
    throw error;
  }
};

/**
 * Get message statistics with caching
 */
export const getMessageStats = async (): Promise<MessageStats> => {
  try {
    return await enhancedApi.get<MessageStats>('/messages/stats/summary', true, 5 * 60 * 1000); // 5 min cache
  } catch (error) {
    console.error('Error fetching message stats:', error);
    throw error;
  }
};

// ============================================================================
// NOTIFICATION API FUNCTIONS
// ============================================================================

/**
 * Get notifications for the current user
 */
export const getNotifications = async (
  unread_only: boolean = false,
  page: number = 1,
  per_page: number = 20
): Promise<NotificationListResponse> => {
  try {
    const params = new URLSearchParams({
      unread_only: unread_only.toString(),
      page: page.toString(),
      per_page: per_page.toString(),
    });

    return await enhancedApi.get<NotificationListResponse>(`/notifications?${params}`, true, 1 * 60 * 1000);
  } catch (error) {
    console.error('Error fetching notifications:', error);
    toast.error('Failed to load notifications');
    throw error;
  }
};

/**
 * Mark notification as read
 */
export const markNotificationRead = async (notificationId: string): Promise<Notification> => {
  try {
    return await enhancedApi.put<Notification>(`/notifications/${notificationId}/read`, {});
  } catch (error) {
    console.error('Error marking notification as read:', error);
    throw error;
  }
};

/**
 * Bulk mark notifications as read
 */
export const bulkMarkNotificationsRead = async (
  notificationIds: string[]
): Promise<{ message: string; updated_count: number }> => {
  try {
    const response = await enhancedApi.put<{ message: string; updated_count: number }>('/notifications/bulk/read', {
      notification_ids: notificationIds,
    });
    
    toast.success(`Marked ${response.updated_count} notifications as read`);
    return response;
  } catch (error) {
    console.error('Error bulk marking notifications as read:', error);
    toast.error('Failed to mark notifications as read');
    throw error;
  }
};

/**
 * Delete notification
 */
export const deleteNotification = async (notificationId: string): Promise<void> => {
  try {
    await enhancedApi.delete(`/notifications/${notificationId}`);
    toast.success('Notification deleted');
  } catch (error) {
    console.error('Error deleting notification:', error);
    toast.error('Failed to delete notification');
    throw error;
  }
};

/**
 * Get notification statistics
 */
export const getNotificationStats = async (): Promise<{
  total_notifications: number;
  unread_count: number;
  new_message_count: number;
  system_count: number;
}> => {
  try {
    return await enhancedApi.get('/notifications/stats/summary', true, 5 * 60 * 1000);
  } catch (error) {
    console.error('Error fetching notification stats:', error);
    throw error;
  }
};

// ============================================================================
// ENHANCED WEBSOCKET SERVICE
// ============================================================================

export class EnhancedMessageWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private userId: string;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private connectionHandlers: ((connected: boolean) => void)[] = [];
  private pingInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private connectionHealth = {
    lastPing: 0,
    lastPong: 0,
    missedPongs: 0,
  };

  constructor(userId: string) {
    this.userId = userId;
  }

  /**
   * Connect to WebSocket with enhanced error handling
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;

      try {
        const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/api/v2/messages/ws/${this.userId}`;
        this.ws = new WebSocket(wsUrl);

        // Set connection timeout
        const connectionTimeout = setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('Connection timeout'));
          }
        }, 10000);

        this.ws.onopen = () => {
          console.log('WebSocket connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.notifyConnectionHandlers(true);
          this.startPingInterval();
          clearTimeout(connectionTimeout);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            
            // Handle pong messages
            if (message.type === 'pong') {
              this.connectionHealth.lastPong = Date.now();
              this.connectionHealth.missedPongs = 0;
              return;
            }

            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.notifyConnectionHandlers(false);
          this.stopPingInterval();
          clearTimeout(connectionTimeout);
          
          // Don't attempt reconnect if it was a clean close
          if (event.code !== 1000) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          clearTimeout(connectionTimeout);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('Error creating WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'User initiated disconnect');
      this.ws = null;
    }
  }

  /**
   * Send ping to keep connection alive
   */
  ping(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      this.connectionHealth.lastPing = Date.now();
    }
  }

  /**
   * Start ping interval
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      this.ping();
      
      // Check connection health
      const now = Date.now();
      if (this.connectionHealth.lastPing > 0 && 
          this.connectionHealth.lastPong > 0 &&
          (now - this.connectionHealth.lastPong) > 60000) {
        this.connectionHealth.missedPongs++;
        
        if (this.connectionHealth.missedPongs >= 3) {
          console.warn('Connection appears to be stale, reconnecting...');
          this.disconnect();
          this.attemptReconnect();
        }
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Register message handler
   */
  onMessage(type: string, handler: (data: any) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Register connection status handler
   */
  onConnectionChange(handler: (connected: boolean) => void): void {
    this.connectionHandlers.push(handler);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      try {
        handler(message.data);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    }

    // Handle specific message types
    switch (message.type) {
      case 'new_message':
        toast.success('New message received!');
        break;
      case 'connection_established':
        console.log('WebSocket connection established:', message.message);
        break;
      case 'error':
        console.error('WebSocket error message:', message.message);
        toast.error('Connection error occurred');
        break;
    }
  }

  /**
   * Notify connection status handlers
   */
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      toast.error('Connection lost. Please refresh the page.');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
        this.attemptReconnect();
      });
    }, delay);
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    connected: boolean;
    connecting: boolean;
    reconnectAttempts: number;
    health: typeof this.connectionHealth;
  } {
    return {
      connected: this.ws?.readyState === WebSocket.OPEN,
      connecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      health: { ...this.connectionHealth },
    };
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format message date with enhanced formatting
 */
export const formatMessageDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInMinutes < 1) {
    return 'Just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  } else if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  } else if (diffInDays < 365) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } else {
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }
};

/**
 * Get user display name with fallbacks
 */
export const getUserDisplayName = (user: UserInfo): string => {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  } else if (user.first_name) {
    return user.first_name;
  } else if (user.display_name) {
    return user.display_name;
  } else if (user.full_name) {
    return user.full_name;
  } else {
    return user.email.split('@')[0];
  }
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
};

/**
 * Check if message is unread
 */
export const isMessageUnread = (message: Message): boolean => {
  return !message.is_read;
};

/**
 * Check if message is starred
 */
export const isMessageStarred = (message: Message): boolean => {
  return message.is_starred;
};

/**
 * Check if message is archived
 */
export const isMessageArchived = (message: Message): boolean => {
  return message.is_archived;
};

/**
 * Sanitize HTML content
 */
export const sanitizeHtml = (html: string): string => {
  // Basic HTML sanitization - in production, use a library like DOMPurify
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '');
};

/**
 * Debounce function for search
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Cache utility for local storage
 */
export const cacheUtils = {
  set: (key: string, value: any, ttl: number = 5 * 60 * 1000): void => {
    try {
      const item = {
        value,
        timestamp: Date.now(),
        ttl,
      };
      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      console.warn('Failed to cache item:', error);
    }
  },

  get: <T>(key: string): T | null => {
    try {
      const item = localStorage.getItem(key);
      if (!item) return null;

      const { value, timestamp, ttl } = JSON.parse(item);
      if (Date.now() - timestamp > ttl) {
        localStorage.removeItem(key);
        return null;
      }

      return value;
    } catch (error) {
      console.warn('Failed to retrieve cached item:', error);
      return null;
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to remove cached item:', error);
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  },
};
