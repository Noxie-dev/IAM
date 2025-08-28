/**
 * Settings Page
 * Phase 3: Frontend Enhancement
 * 
 * User settings and subscription management
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'react-hot-toast';
import {
  UserCircleIcon,
  CreditCardIcon,
  BellIcon,
  ShieldCheckIcon,
  CogIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { withAuth, useAuth, usePermissions } from '@/contexts/AuthContext';

// Form validation schemas
const profileSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  company_name: z.string().optional(),
});

const notificationSchema = z.object({
  email_notifications: z.boolean(),
  transcription_complete: z.boolean(),
  transcription_failed: z.boolean(),
  weekly_summary: z.boolean(),
  marketing_emails: z.boolean(),
});

type ProfileFormData = z.infer<typeof profileSchema>;
type NotificationFormData = z.infer<typeof notificationSchema>;

function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { subscriptionTier, isPremium, remainingMinutes } = usePermissions();
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(false);

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
      company_name: user?.company_name || '',
    },
  });

  const notificationForm = useForm<NotificationFormData>({
    resolver: zodResolver(notificationSchema),
    defaultValues: {
      email_notifications: true,
      transcription_complete: true,
      transcription_failed: true,
      weekly_summary: false,
      marketing_emails: false,
    },
  });

  const onProfileSubmit = async (data: ProfileFormData) => {
    try {
      setIsLoading(true);
      // In real app, this would call the API
      console.log('Updating profile:', data);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      toast.success('Profile updated successfully');
      refreshUser();
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const onNotificationSubmit = async (data: NotificationFormData) => {
    try {
      setIsLoading(true);
      // In real app, this would call the API
      console.log('Updating notifications:', data);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      toast.success('Notification preferences updated');
    } catch (error) {
      toast.error('Failed to update notification preferences');
    } finally {
      setIsLoading(false);
    }
  };

  const subscriptionPlans = [
    {
      name: 'Free',
      price: '$0',
      period: 'month',
      features: [
        '60 minutes per month',
        'Basic transcription',
        'Standard accuracy',
        'Email support',
      ],
      current: subscriptionTier === 'free',
      popular: false,
    },
    {
      name: 'Pro',
      price: '$19',
      period: 'month',
      features: [
        '500 minutes per month',
        'High-accuracy transcription',
        'Speaker identification',
        'Word-level timestamps',
        'Priority support',
        'Multiple AI providers',
      ],
      current: subscriptionTier === 'pro',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: '$99',
      period: 'month',
      features: [
        'Unlimited minutes',
        'Premium AI models',
        'Custom vocabulary',
        'API access',
        'Dedicated support',
        'Advanced analytics',
        'Team collaboration',
      ],
      current: subscriptionTier === 'enterprise',
      popular: false,
    },
  ];

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserCircleIcon },
    { id: 'subscription', name: 'Subscription', icon: CreditCardIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
  ];

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <CogIcon className="h-6 w-6 text-gray-600" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
              <p className="text-sm text-gray-500">
                Manage your account settings and preferences
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon
                  className={`-ml-0.5 mr-2 h-5 w-5 ${
                    activeTab === tab.id ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                  }`}
                />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white shadow rounded-lg">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Update your personal information and account details.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    First name
                  </label>
                  <input
                    {...profileForm.register('first_name')}
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {profileForm.formState.errors.first_name && (
                    <p className="mt-1 text-sm text-red-600">
                      {profileForm.formState.errors.first_name.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Last name
                  </label>
                  <input
                    {...profileForm.register('last_name')}
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {profileForm.formState.errors.last_name && (
                    <p className="mt-1 text-sm text-red-600">
                      {profileForm.formState.errors.last_name.message}
                    </p>
                  )}
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Email address
                  </label>
                  <input
                    {...profileForm.register('email')}
                    type="email"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  {profileForm.formState.errors.email && (
                    <p className="mt-1 text-sm text-red-600">
                      {profileForm.formState.errors.email.message}
                    </p>
                  )}
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Company name (optional)
                  </label>
                  <input
                    {...profileForm.register('company_name')}
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}

          {/* Subscription Tab */}
          {activeTab === 'subscription' && (
            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Subscription Plan</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose the plan that best fits your transcription needs.
                </p>
              </div>

              {/* Current Usage */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-blue-900">Current Usage</h4>
                    <p className="text-sm text-blue-700">
                      {isPremium 
                        ? 'Unlimited transcription minutes'
                        : `${remainingMinutes} minutes remaining this month`
                      }
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-900 capitalize">
                      {subscriptionTier} Plan
                    </div>
                  </div>
                </div>
              </div>

              {/* Plans */}
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                {subscriptionPlans.map((plan) => (
                  <div
                    key={plan.name}
                    className={`relative border rounded-lg p-6 ${
                      plan.current
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } ${plan.popular ? 'ring-2 ring-blue-500' : ''}`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span className="bg-blue-500 text-white px-3 py-1 text-xs font-medium rounded-full">
                          Most Popular
                        </span>
                      </div>
                    )}

                    <div className="text-center">
                      <h3 className="text-lg font-medium text-gray-900">{plan.name}</h3>
                      <div className="mt-4">
                        <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
                        <span className="text-gray-500">/{plan.period}</span>
                      </div>
                    </div>

                    <ul className="mt-6 space-y-3">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-center">
                          <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
                          <span className="text-sm text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="mt-6">
                      {plan.current ? (
                        <button
                          disabled
                          className="w-full py-2 px-4 border border-blue-500 rounded-md text-sm font-medium text-blue-600 bg-blue-50 cursor-not-allowed"
                        >
                          Current Plan
                        </button>
                      ) : (
                        <button
                          onClick={() => toast.info(`Upgrading to ${plan.name} plan...`)}
                          className="w-full py-2 px-4 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          {subscriptionTier === 'free' ? 'Upgrade' : 'Change Plan'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <form onSubmit={notificationForm.handleSubmit(onNotificationSubmit)} className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Notification Preferences</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose how you want to be notified about your transcriptions.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900">
                      Email notifications
                    </label>
                    <p className="text-sm text-gray-500">
                      Receive notifications via email
                    </p>
                  </div>
                  <input
                    {...notificationForm.register('email_notifications')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900">
                      Transcription completed
                    </label>
                    <p className="text-sm text-gray-500">
                      Get notified when transcriptions are ready
                    </p>
                  </div>
                  <input
                    {...notificationForm.register('transcription_complete')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900">
                      Transcription failed
                    </label>
                    <p className="text-sm text-gray-500">
                      Get notified when transcriptions fail
                    </p>
                  </div>
                  <input
                    {...notificationForm.register('transcription_failed')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900">
                      Weekly summary
                    </label>
                    <p className="text-sm text-gray-500">
                      Receive weekly usage summaries
                    </p>
                  </div>
                  <input
                    {...notificationForm.register('weekly_summary')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-900">
                      Marketing emails
                    </label>
                    <p className="text-sm text-gray-500">
                      Receive updates about new features
                    </p>
                  </div>
                  <input
                    {...notificationForm.register('marketing_emails')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Security Settings</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Manage your account security and privacy settings.
                </p>
              </div>

              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Change Password</h4>
                      <p className="text-sm text-gray-500">
                        Update your account password
                      </p>
                    </div>
                    <button
                      onClick={() => toast.info('Password change functionality coming soon')}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Change
                    </button>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
                      <p className="text-sm text-gray-500">
                        Add an extra layer of security to your account
                      </p>
                    </div>
                    <button
                      onClick={() => toast.info('2FA setup coming soon')}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Enable
                    </button>
                  </div>
                </div>

                <div className="border border-red-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-red-900">Delete Account</h4>
                      <p className="text-sm text-red-600">
                        Permanently delete your account and all data
                      </p>
                    </div>
                    <button
                      onClick={() => toast.error('Account deletion requires confirmation')}
                      className="px-4 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(SettingsPage);
