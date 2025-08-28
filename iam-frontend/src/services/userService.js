/**
 * User Service - API operations for user profile management
 * IAM Application - Frontend Service Layer
 */

/**
 * Base API configuration
 */
const API_BASE = '/api/v2';
const REQUEST_TIMEOUT = 30000; // 30 seconds

/**
 * Common request headers
 */
const getHeaders = () => {
  const token = localStorage.getItem('iam_access_token');
  return {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * Generic API request handler with error handling
 */
const apiRequest = async (endpoint, options = {}) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: getHeaders(),
      signal: controller.signal,
      ...options
    });

    clearTimeout(timeoutId);
    
    // Handle empty responses
    const responseText = await response.text();
    if (!responseText || responseText.trim() === '') {
      throw new Error('Server returned an empty response. Please try again.');
    }

    let data;
    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      throw new Error('Invalid response format received from server. Please try again.');
    }

    if (!response.ok) {
      throw new Error(data.detail || `Request failed with status ${response.status}`);
    }

    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your connection and try again.');
    }
    
    // Handle network errors
    if (!navigator.onLine) {
      throw new Error('No internet connection. Please check your network and try again.');
    }
    
    throw error;
  }
};

/**
 * User Profile API Operations
 */
export const userService = {
  /**
   * Get current user profile
   */
  async getProfile() {
    return await apiRequest('/users/me');
  },

  /**
   * Update user profile
   */
  async updateProfile(profileData) {
    return await apiRequest('/users/me', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  },

  /**
   * Get user statistics
   */
  async getUserStats() {
    return await apiRequest('/users/me/stats');
  },

  /**
   * Get user preferences
   */
  async getPreferences() {
    return await apiRequest('/users/me/preferences');
  },

  /**
   * Save user preferences
   */
  async savePreferences(preferences) {
    return await apiRequest('/users/me/preferences', {
      method: 'POST',
      body: JSON.stringify(preferences)
    });
  },

  /**
   * Change password
   */
  async changePassword(passwordData) {
    return await apiRequest('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData)
    });
  }
};

/**
 * Auth Service for profile-related auth operations
 */
export const authService = {
  /**
   * Get current user info (refresh user data)
   */
  async getCurrentUser() {
    return await apiRequest('/auth/me');
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } finally {
      // Clear local storage even if API call fails
      localStorage.removeItem('iam_access_token');
      localStorage.removeItem('iam_refresh_token');
      localStorage.removeItem('iam_user');
    }
  }
};

/**
 * Utility functions for user data
 */
export const userUtils = {
  /**
   * Get user's full name
   */
  getFullName(user) {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    if (user?.first_name) return user.first_name;
    if (user?.last_name) return user.last_name;
    return user?.email?.split('@')[0] || 'User';
  },

  /**
   * Get user's display name
   */
  getDisplayName(user) {
    return this.getFullName(user) || user?.email || 'User';
  },

  /**
   * Get user's initials for avatar
   */
  getInitials(user) {
    const fullName = this.getFullName(user);
    if (fullName === user?.email?.split('@')[0]) {
      // If no real name, use first two letters of email
      return user.email.substring(0, 2).toUpperCase();
    }
    return fullName.split(' ').map(n => n[0]).join('').toUpperCase();
  },

  /**
   * Format subscription tier for display
   */
  formatSubscriptionTier(tier) {
    const tiers = {
      free: 'Free',
      basic: 'Basic',
      premium: 'Premium',
      enterprise: 'Enterprise'
    };
    return tiers[tier?.toLowerCase()] || 'Free';
  },

  /**
   * Check if user is premium
   */
  isPremium(user) {
    return user?.subscription_tier && ['premium', 'enterprise'].includes(user.subscription_tier.toLowerCase());
  },

  /**
   * Format remaining minutes for display
   */
  formatRemainingMinutes(minutes) {
    if (minutes === -1) return 'Unlimited';
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMins = minutes % 60;
      return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
    }
    return `${minutes}m`;
  }
};

export default userService;
