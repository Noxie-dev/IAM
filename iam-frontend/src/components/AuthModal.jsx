import { useState } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { X, Eye, EyeOff, Loader2 } from 'lucide-react';

const AuthModal = ({ isOpen, onClose, mode, onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    companyName: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [attemptCount, setAttemptCount] = useState(0);
  const [lastAttemptTime, setLastAttemptTime] = useState(0);

  const isLogin = mode === 'login';
  const title = isLogin ? 'Sign In' : 'Create Account';

  const handleInputChange = (e) => {
    const { name, value } = e.target;

    // Sanitize input to prevent XSS
    const sanitizedValue = value.replace(/<[^>]*>/g, '').substring(0, 255);

    setFormData(prev => ({
      ...prev,
      [name]: sanitizedValue
    }));

    // Clear errors when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    // Clear previous errors
    setError('');

    // Trim whitespace from inputs
    const trimmedEmail = formData.email.trim();
    const trimmedPassword = formData.password.trim();

    if (!trimmedEmail || !trimmedPassword) {
      setError('Email and password are required');
      return false;
    }

    // Enhanced email validation
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!emailRegex.test(trimmedEmail)) {
      setError('Please enter a valid email address');
      return false;
    }

    // Email length validation
    if (trimmedEmail.length > 254) {
      setError('Email address is too long');
      return false;
    }

    if (!isLogin) {
      const trimmedFirstName = formData.firstName.trim();
      const trimmedLastName = formData.lastName.trim();

      if (!trimmedFirstName || !trimmedLastName) {
        setError('First name and last name are required');
        return false;
      }

      // Name validation
      if (trimmedFirstName.length > 50 || trimmedLastName.length > 50) {
        setError('Names must be less than 50 characters');
        return false;
      }

      // Password strength validation
      if (trimmedPassword.length < 8) {
        setError('Password must be at least 8 characters long');
        return false;
      }

      if (trimmedPassword.length > 128) {
        setError('Password must be less than 128 characters');
        return false;
      }

      // Check for password complexity
      const hasUpperCase = /[A-Z]/.test(trimmedPassword);
      const hasLowerCase = /[a-z]/.test(trimmedPassword);
      const hasNumbers = /\d/.test(trimmedPassword);
      const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(trimmedPassword);

      if (!hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecialChar) {
        setError('Password must contain uppercase, lowercase, number, and special character');
        return false;
      }

      // Company name validation (optional field)
      if (formData.companyName && formData.companyName.trim().length > 100) {
        setError('Company name must be less than 100 characters');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Rate limiting protection (client-side)
    const now = Date.now();
    const timeSinceLastAttempt = now - lastAttemptTime;

    if (attemptCount >= 5 && timeSinceLastAttempt < 300000) { // 5 minutes
      setError('Too many attempts. Please wait 5 minutes before trying again.');
      return;
    }

    if (timeSinceLastAttempt < 1000) { // 1 second between attempts
      setError('Please wait a moment before trying again.');
      return;
    }

    if (!validateForm()) return;

    setIsLoading(true);
    setError('');
    setSuccess('');
    setLastAttemptTime(now);

    try {
      const endpoint = isLogin ? '/api/v2/auth/login' : '/api/v2/auth/register';

      // Sanitize and prepare payload
      const payload = isLogin
        ? {
            email: formData.email.trim().toLowerCase(),
            password: formData.password.trim()
          }
        : {
            email: formData.email.trim().toLowerCase(),
            password: formData.password.trim(),
            first_name: formData.firstName.trim(),
            last_name: formData.lastName.trim(),
            company_name: formData.companyName ? formData.companyName.trim() : null
          };

      // Create AbortController for request timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest', // CSRF protection
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const responseText = await response.text();

      let data;
      if (!responseText || responseText.trim() === '') {
        throw new Error('Server returned an empty response. Please try again.');
      }

      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        throw new Error('Invalid response format received from server. Please try again.');
      }

      if (!response.ok) {
        // Increment attempt count on failed authentication
        setAttemptCount(prev => prev + 1);
        throw new Error(data.detail || `${isLogin ? 'Login' : 'Registration'} failed`);
      }

      if (data.success) {
        // Reset attempt count on successful authentication
        setAttemptCount(0);

        // Store authentication data securely
        localStorage.setItem('iam_access_token', data.access_token);
        localStorage.setItem('iam_refresh_token', data.refresh_token);
        localStorage.setItem('iam_user', JSON.stringify(data.user));

        setSuccess(isLogin ? 'Login successful!' : 'Account created successfully!');

        // Call success callback after a brief delay to show success message
        setTimeout(() => {
          onSuccess(data.user);
        }, 1000);
      } else {
        setAttemptCount(prev => prev + 1);
        throw new Error(data.message || `${isLogin ? 'Login' : 'Registration'} failed`);
      }
    } catch (err) {
      // Handle different types of errors
      if (err.name === 'AbortError') {
        setError('Request timeout: The server is taking too long to respond. Please try again.');
      } else if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setError('Network error: Unable to connect to server. Please check your connection.');
      } else if (err.message.includes('Invalid response format')) {
        setError('Server error: Invalid response received. Please try again.');
      } else if (err.message.includes('Failed to fetch')) {
        setError('Connection error: Please check your internet connection and try again.');
      } else {
        // Sanitize error message to prevent XSS
        const sanitizedMessage = err.message ? err.message.replace(/<[^>]*>/g, '') : '';
        setError(sanitizedMessage || 'An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      firstName: '',
      lastName: '',
      companyName: ''
    });
    setError('');
    setSuccess('');
    setShowPassword(false);
    setAttemptCount(0);
    setLastAttemptTime(0);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email"
              disabled={isLoading}
              required
            />
          </div>

          {/* First Name and Last Name (Register only) */}
          {!isLogin && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="First name"
                  disabled={isLoading}
                  required
                />
              </div>
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Last name"
                  disabled={isLoading}
                  required
                />
              </div>
            </div>
          )}

          {/* Company Name (Register only, optional) */}
          {!isLogin && (
            <div>
              <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-1">
                Company Name (Optional)
              </label>
              <input
                type="text"
                id="companyName"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your company name"
                disabled={isLoading}
              />
            </div>
          )}

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={isLogin ? "Enter your password" : "Create a password (min 8 characters)"}
                disabled={isLoading}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-sm text-green-600">{success}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {isLogin ? 'Signing In...' : 'Creating Account...'}
              </div>
            ) : (
              title
            )}
          </Button>
        </form>

        {/* Footer */}
        <div className="px-6 pb-6 text-center">
          <p className="text-sm text-gray-600">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => {
                resetForm();
                // This would switch between login/register modes
                // For now, we'll just close and let parent handle mode switching
                handleClose();
              }}
              className="text-blue-600 hover:text-blue-700 font-medium"
              disabled={isLoading}
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
