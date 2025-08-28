/**
 * Authentication Context
 * Phase 3: Frontend Enhancement
 * 
 * React context for managing authentication state and user data
 */

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import apiClient, { User, LoginRequest, RegisterRequest } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<boolean>;
  register: (userData: RegisterRequest) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user && apiClient.isAuthenticated();

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      // Check if user is stored locally
      const storedUser = apiClient.getStoredUser();
      
      if (storedUser && apiClient.isAuthenticated()) {
        // Verify token is still valid by fetching current user
        const response = await apiClient.getCurrentUser();
        
        if (response.success && response.data) {
          setUser(response.data);
          // Update stored user data
          localStorage.setItem('user', JSON.stringify(response.data));
        } else {
          // Token is invalid, clear stored data
          clearAuthData();
        }
      } else {
        clearAuthData();
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      clearAuthData();
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginRequest): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await apiClient.login(credentials);

      if (response.success && response.data) {
        setUser(response.data.user);
        toast.success('Login successful!');
        return true;
      } else {
        toast.error(response.error || 'Login failed');
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await apiClient.register(userData);

      if (response.success && response.data) {
        setUser(response.data.user);
        toast.success('Registration successful! Welcome to IAM SaaS Platform!');
        return true;
      } else {
        toast.error(response.error || 'Registration failed');
        return false;
      }
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('Registration failed. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setLoading(true);
      await apiClient.logout();
      clearAuthData();
      toast.success('Logged out successfully');
      router.push('/auth/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Clear data even if logout request fails
      clearAuthData();
      router.push('/auth/login');
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      if (!apiClient.isAuthenticated()) return;

      const response = await apiClient.getCurrentUser();
      
      if (response.success && response.data) {
        setUser(response.data);
        localStorage.setItem('user', JSON.stringify(response.data));
      } else {
        // If refresh fails, user might need to re-authenticate
        clearAuthData();
        router.push('/auth/login');
      }
    } catch (error) {
      console.error('User refresh error:', error);
    }
  };

  const clearAuthData = () => {
    setUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Higher-order component for protecting routes
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!loading && !isAuthenticated) {
        router.push('/auth/login');
      }
    }, [isAuthenticated, loading, router]);

    if (loading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}

// Hook for checking specific permissions
export function usePermissions() {
  const { user } = useAuth();

  return {
    isAdmin: user?.is_admin || false,
    isPremium: user?.is_premium || false,
    canUpload: user?.is_active || false,
    canTranscribe: (user?.remaining_minutes || 0) > 0 || user?.is_premium || false,
    subscriptionTier: user?.subscription_tier || 'free',
    remainingMinutes: user?.remaining_minutes || 0,
  };
}
