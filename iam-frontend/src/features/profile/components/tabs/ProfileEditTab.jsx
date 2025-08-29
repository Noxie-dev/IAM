/**
 * Profile Edit Tab - User profile information editing
 * IAM Application - Profile Component
 */

import React, { useState, useEffect } from 'react';
import { User, Building, Phone, Mail, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Input } from '../../../../components/ui/input';
import { useProfile } from '../../../../context/UserContext';

const ProfileEditTab = () => {
  const { user, loading, error, updateProfile, clearError } = useProfile();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    company_name: '',
    phone: ''
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Load user data into form when available
  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        company_name: user.company_name || '',
        phone: user.phone || ''
      });
    }
  }, [user]);

  // Clear success message after 3 seconds
  useEffect(() => {
    if (saveSuccess) {
      const timer = setTimeout(() => setSaveSuccess(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Basic input sanitization
    const sanitizedValue = value.replace(/<[^>]*>/g, '').substring(0, 255);
    
    setFormData(prev => ({
      ...prev,
      [name]: sanitizedValue
    }));

    // Clear field-specific error when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
    
    clearError();
  };

  const validateForm = () => {
    const errors = {};

    // First name validation
    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    } else if (formData.first_name.trim().length < 2) {
      errors.first_name = 'First name must be at least 2 characters';
    }

    // Last name validation
    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    } else if (formData.last_name.trim().length < 2) {
      errors.last_name = 'Last name must be at least 2 characters';
    }

    // Phone validation (optional but if provided, should be valid)
    if (formData.phone.trim()) {
      const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
      if (!phoneRegex.test(formData.phone.replace(/[\s\-\(\)]/g, ''))) {
        errors.phone = 'Please enter a valid phone number';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      clearError();
      
      // Prepare update payload (trim values and remove empty strings)
      const updateData = {};
      Object.keys(formData).forEach(key => {
        const value = formData[key].trim();
        if (value || key === 'company_name' || key === 'phone') {
          // Allow empty strings for optional fields
          updateData[key] = value || null;
        }
      });

      await updateProfile(updateData);
      setSaveSuccess(true);
    } catch (error) {
      console.error('Error updating profile:', error);
      // Error is handled by the context
    } finally {
      setSaving(false);
    }
  };

  if (loading && !user) {
    return (
      <div className="space-y-6">
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-white/10 rounded w-1/4"></div>
            <div className="h-10 bg-white/10 rounded"></div>
            <div className="h-4 bg-white/10 rounded w-1/4"></div>
            <div className="h-10 bg-white/10 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile Information Form */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-6 flex items-center">
          <User className="w-5 h-5 mr-2" />
          Profile Information
        </h3>

        <form onSubmit={handleSave} className="space-y-4">
          {/* Name Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                First Name *
              </label>
              <Input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                className="bg-white/10 border-white/20 text-white"
                placeholder="Enter first name"
                required
              />
              {formErrors.first_name && (
                <p className="text-red-400 text-xs mt-1">{formErrors.first_name}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Last Name *
              </label>
              <Input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                className="bg-white/10 border-white/20 text-white"
                placeholder="Enter last name"
                required
              />
              {formErrors.last_name && (
                <p className="text-red-400 text-xs mt-1">{formErrors.last_name}</p>
              )}
            </div>
          </div>

          {/* Email (Read-only) */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">
              <Mail className="w-4 h-4 inline mr-1" />
              Email Address
            </label>
            <Input
              type="email"
              value={user?.email || ''}
              disabled
              className="bg-white/5 border-white/10 text-gray-400 cursor-not-allowed"
              placeholder="Email cannot be changed"
            />
            <p className="text-gray-500 text-xs mt-1">
              Contact support to change your email address
            </p>
          </div>

          {/* Company */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">
              <Building className="w-4 h-4 inline mr-1" />
              Company Name
            </label>
            <Input
              type="text"
              name="company_name"
              value={formData.company_name}
              onChange={handleInputChange}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Enter company name (optional)"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">
              <Phone className="w-4 h-4 inline mr-1" />
              Phone Number
            </label>
            <Input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Enter phone number (optional)"
            />
            {formErrors.phone && (
              <p className="text-red-400 text-xs mt-1">{formErrors.phone}</p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Success Message */}
          {saveSuccess && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <p className="text-green-400 text-sm">Profile updated successfully!</p>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              type="submit"
              disabled={saving || loading}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </Button>
          </div>
        </form>
      </div>

      {/* Account Information */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Account Information</h3>
        
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Account Status:</span>
            <span className={`${user?.is_active ? 'text-green-400' : 'text-red-400'}`}>
              {user?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Subscription:</span>
            <span className="text-white">
              {user?.subscription_tier?.charAt(0).toUpperCase() + user?.subscription_tier?.slice(1) || 'Free'}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-400">Email Verified:</span>
            <span className={`${user?.email_verified ? 'text-green-400' : 'text-yellow-400'}`}>
              {user?.email_verified ? 'Verified' : 'Pending Verification'}
            </span>
          </div>
          
          {user?.created_at && (
            <div className="flex justify-between">
              <span className="text-gray-400">Member Since:</span>
              <span className="text-white">
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileEditTab;


