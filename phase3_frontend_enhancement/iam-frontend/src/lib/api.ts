/**
 * API Client for IAM SaaS Platform
 * Phase 3: Frontend Enhancement
 * 
 * Axios-based client for communicating with FastAPI backend
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';

// Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  error_type?: string;
  status_code?: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  session_id: string;
}

export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  display_name: string;
  company_name?: string;
  subscription_tier: string;
  subscription_status: string;
  monthly_transcription_minutes: number;
  total_transcription_minutes: number;
  remaining_minutes: number;
  email_verified: boolean;
  is_active: boolean;
  is_admin: boolean;
  is_premium: boolean;
  created_at: string;
  updated_at: string;
}

export interface Meeting {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  meeting_date?: string;
  duration_seconds?: number;
  duration_minutes?: number;
  audio_file_url?: string;
  audio_file_size?: number;
  file_size_mb?: number;
  audio_file_format?: string;
  original_filename?: string;
  transcription_text?: string;
  processing_status: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  processing_error?: string;
  model_used?: string;
  provider_used?: string;
  language_detected?: string;
  transcription_confidence?: number;
  transcription_cost: number;
  has_audio_file: boolean;
  has_transcription: boolean;
  is_completed: boolean;
  is_failed: boolean;
  is_processing: boolean;
  created_at: string;
  updated_at: string;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors (token expired)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await this.refreshAccessToken(refreshToken);
              if (response.success) {
                this.setTokens(response.data.access_token, refreshToken);
                originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
                return this.client(originalRequest);
              }
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError);
          }

          // If refresh fails, redirect to login
          this.clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }

        // Handle rate limiting
        if (error.response?.status === 429) {
          const retryAfter = error.response.headers['retry-after'];
          toast.error(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
        }

        // Handle other errors
        if (error.response?.data?.error) {
          console.error('API Error:', error.response.data);
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await this.client.post('/api/v2/auth/login', credentials);
      const data = response.data;
      
      if (data.success) {
        this.setTokens(data.access_token, data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      return { success: true, data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await this.client.post('/api/v2/auth/register', userData);
      const data = response.data;
      
      if (data.success) {
        this.setTokens(data.access_token, data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      return { success: true, data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async logout(): Promise<ApiResponse> {
    try {
      const sessionId = localStorage.getItem('session_id');
      if (sessionId) {
        await this.client.post('/api/v2/auth/logout', { session_id: sessionId });
      }
      
      this.clearTokens();
      return { success: true };
    } catch (error: any) {
      this.clearTokens(); // Clear tokens even if logout fails
      return this.handleError(error);
    }
  }

  async refreshAccessToken(refreshToken: string): Promise<ApiResponse> {
    try {
      const response = await this.client.post('/api/v2/auth/refresh', {
        refresh_token: refreshToken
      });
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    try {
      const response = await this.client.get('/api/v2/auth/me');
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  // Meeting endpoints
  async getMeetings(): Promise<ApiResponse<Meeting[]>> {
    try {
      const response = await this.client.get('/api/v2/meetings');
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async getMeeting(id: string): Promise<ApiResponse<Meeting>> {
    try {
      const response = await this.client.get(`/api/v2/meetings/${id}`);
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async createMeeting(meetingData: Partial<Meeting>): Promise<ApiResponse<Meeting>> {
    try {
      const response = await this.client.post('/api/v2/meetings', meetingData);
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    try {
      const response = await this.client.get('/health');
      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  // File upload with transcription settings
  async uploadFile(
    file: File,
    transcriptionSettings?: any,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Add transcription settings if provided
      if (transcriptionSettings) {
        Object.keys(transcriptionSettings).forEach(key => {
          if (transcriptionSettings[key] !== undefined && transcriptionSettings[key] !== null) {
            if (key === 'enhancement_options') {
              // Send enhancement options as JSON string
              formData.append(key, JSON.stringify(transcriptionSettings[key]));
            } else {
              formData.append(key, transcriptionSettings[key].toString());
            }
          }
        });
      }

      const response = await this.client.post('/api/v2/transcription/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });

      return { success: true, data: response.data };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  // Error handling
  private handleError(error: any): ApiResponse {
    if (error.response?.data) {
      return {
        success: false,
        error: error.response.data.error || 'An error occurred',
        error_type: error.response.data.error_type,
        status_code: error.response.status,
      };
    }

    return {
      success: false,
      error: error.message || 'Network error occurred',
      error_type: 'network_error',
    };
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
