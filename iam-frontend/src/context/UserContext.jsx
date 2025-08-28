/**
 * User Context - Global state management for user data
 * IAM Application - React Context
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { userService, authService, userUtils } from '../services/userService';

/**
 * User Context
 */
const UserContext = createContext(null);

/**
 * User Provider Component
 */
const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Load user data on mount and when token changes
   */
  useEffect(() => {
    loadUserData();
  }, []);

  /**
   * Load user data from localStorage and API
   */
  const loadUserData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check for existing token and user data
      const token = localStorage.getItem('iam_access_token');
      const storedUser = localStorage.getItem('iam_user');

      if (!token) {
        setUser(null);
        setUserStats(null);
        setPreferences(null);
        return;
      }

      // Use stored user data first for immediate UI response
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
        } catch (error) {
          console.error('Error parsing stored user data:', error);
          localStorage.removeItem('iam_user');
        }
      }

      // Fetch fresh user data from API
      const freshUser = await userService.getProfile();
      setUser(freshUser);
      
      // Update localStorage with fresh data
      localStorage.setItem('iam_user', JSON.stringify(freshUser));

      // Load user stats and preferences in parallel
      await Promise.all([
        loadUserStats(),
        loadUserPreferences()
      ]);

    } catch (error) {
      console.error('Error loading user data:', error);
      setError(error.message);
      
      // If unauthorized, clear user data
      if (error.message.includes('401') || error.message.includes('unauthorized')) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load user statistics
   */
  const loadUserStats = async () => {
    try {
      const stats = await userService.getUserStats();
      setUserStats(stats);
    } catch (error) {
      console.error('Error loading user stats:', error);
      // Don't set error state for stats failure
    }
  };

  /**
   * Load user preferences
   */
  const loadUserPreferences = async () => {
    try {
      const prefs = await userService.getPreferences();
      setPreferences(prefs);
    } catch (error) {
      console.error('Error loading user preferences:', error);
      // Set default preferences if loading fails
      setPreferences({
        language: 'English',
        timezone: 'Pacific Standard Time',
        email_notifications: true,
        push_notifications: false,
        sound_enabled: true,
        auto_save: true,
        dark_mode: true,
        compact_view: false
      });
    }
  };

  /**
   * Update user profile
   */
  const updateProfile = async (profileData) => {
    try {
      setLoading(true);
      const updatedUser = await userService.updateProfile(profileData);
      setUser(updatedUser);
      localStorage.setItem('iam_user', JSON.stringify(updatedUser));
      return updatedUser;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Save user preferences
   */
  const savePreferences = async (newPreferences) => {
    try {
      await userService.savePreferences(newPreferences);
      setPreferences(newPreferences);
      return true;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  /**
   * Change password
   */
  const changePassword = async (passwordData) => {
    try {
      await userService.changePassword(passwordData);
      return true;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  /**
   * Refresh user data
   */
  const refreshUser = async () => {
    try {
      setError(null);
      const freshUser = await userService.getProfile();
      setUser(freshUser);
      localStorage.setItem('iam_user', JSON.stringify(freshUser));
      
      // Also refresh stats
      await loadUserStats();
      return freshUser;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  /**
   * Handle user logout
   */
  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      setUser(null);
      setUserStats(null);
      setPreferences(null);
      setError(null);
    }
  };

  /**
   * Handle successful authentication
   */
  const handleAuthSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('iam_user', JSON.stringify(userData));
    setError(null);
    
    // Load additional data
    loadUserStats();
    loadUserPreferences();
  };

  /**
   * Context value
   */
  const value = {
    // State
    user,
    userStats,
    preferences,
    loading,
    error,
    
    // Computed values
    isAuthenticated: !!user,
    isPremium: user ? userUtils.isPremium(user) : false,
    fullName: user ? userUtils.getFullName(user) : null,
    displayName: user ? userUtils.getDisplayName(user) : null,
    initials: user ? userUtils.getInitials(user) : null,
    
    // Actions
    updateProfile,
    savePreferences,
    changePassword,
    refreshUser,
    handleLogout,
    handleAuthSuccess,
    loadUserData,
    
    // Utilities
    clearError: () => setError(null)
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

/**
 * Custom hook to use user context
 */
const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

/**
 * Hook for user authentication status
 */
const useAuth = () => {
  const { isAuthenticated, user, handleLogout, handleAuthSuccess, refreshUser } = useUser();
  
  return {
    isAuthenticated,
    user,
    logout: handleLogout,
    onAuthSuccess: handleAuthSuccess,
    refreshUser
  };
};

/**
 * Hook for user profile management
 */
const useProfile = () => {
  const { 
    user, 
    userStats, 
    loading, 
    error, 
    updateProfile, 
    refreshUser,
    clearError 
  } = useUser();
  
  return {
    user,
    userStats,
    loading,
    error,
    updateProfile,
    refreshUser,
    clearError
  };
};

/**
 * Hook for user preferences
 */
const useUserPreferences = () => {
  const { 
    preferences, 
    loading, 
    error, 
    savePreferences, 
    clearError 
  } = useUser();
  
  return {
    preferences,
    loading,
    error,
    savePreferences,
    clearError
  };
};

// Named exports for better compatibility with React Fast Refresh
export { UserProvider, useUser, useAuth, useProfile, useUserPreferences };
