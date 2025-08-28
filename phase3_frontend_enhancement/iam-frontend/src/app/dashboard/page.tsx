/**
 * Dashboard Page
 * Phase 3: Frontend Enhancement
 * 
 * Main dashboard with overview and quick actions
 */

'use client';

import { useAuth, usePermissions, withAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import TranscriptionStatus from '@/components/realtime/TranscriptionStatus';
import Link from 'next/link';
import {
  MicrophoneIcon,
  DocumentTextIcon,
  ClockIcon,
  ChartBarIcon,
  PlusIcon,
  ArrowUpIcon,
} from '@heroicons/react/24/outline';

function DashboardPage() {
  const { user } = useAuth();
  const { subscriptionTier, remainingMinutes, isPremium } = usePermissions();

  // Mock data - in real app, this would come from API
  const stats = {
    totalTranscriptions: 12,
    thisMonth: 8,
    totalMinutes: 450,
    averageAccuracy: 96.5,
  };

  const recentTranscriptions = [
    {
      id: '1',
      title: 'Team Meeting - Q4 Planning',
      date: '2024-12-26',
      duration: '45 min',
      status: 'completed',
    },
    {
      id: '2',
      title: 'Client Interview - Product Feedback',
      date: '2024-12-25',
      duration: '32 min',
      status: 'completed',
    },
    {
      id: '3',
      title: 'Board Meeting - December',
      date: '2024-12-24',
      duration: '78 min',
      status: 'processing',
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.first_name || user?.display_name}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here's what's happening with your transcriptions today.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Link
                href="/dashboard/upload"
                className="relative group bg-blue-50 p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg hover:bg-blue-100 transition-colors"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-blue-600 text-white">
                    <PlusIcon className="h-6 w-6" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Upload Audio
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Start a new transcription by uploading your audio file.
                  </p>
                </div>
              </Link>

              <Link
                href="/dashboard/transcriptions"
                className="relative group bg-green-50 p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-green-500 rounded-lg hover:bg-green-100 transition-colors"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-green-600 text-white">
                    <DocumentTextIcon className="h-6 w-6" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    View Transcriptions
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Browse and manage all your transcription files.
                  </p>
                </div>
              </Link>

              <Link
                href="/dashboard/settings"
                className="relative group bg-purple-50 p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-purple-500 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <div>
                  <span className="rounded-lg inline-flex p-3 bg-purple-600 text-white">
                    <ChartBarIcon className="h-6 w-6" aria-hidden="true" />
                  </span>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Upgrade Plan
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Get more minutes and premium features.
                  </p>
                </div>
              </Link>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Transcriptions
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.totalTranscriptions}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      This Month
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.thisMonth}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <MicrophoneIcon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Minutes Remaining
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {isPremium ? 'Unlimited' : remainingMinutes}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg. Accuracy
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.averageAccuracy}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Updates */}
        <div className="bg-white shadow rounded-lg p-6">
          <TranscriptionStatus showGlobalStatus={true} />
        </div>

        {/* Recent Transcriptions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Recent Transcriptions</h2>
              <Link
                href="/dashboard/transcriptions"
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {recentTranscriptions.map((transcription) => (
              <div key={transcription.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {transcription.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {transcription.date} • {transcription.duration}
                    </p>
                  </div>
                  <div className="flex items-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        transcription.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {transcription.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Subscription Status */}
        {!isPremium && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ArrowUpIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-blue-800">
                  Upgrade to Premium
                </h3>
                <p className="mt-1 text-sm text-blue-700">
                  Get unlimited transcription minutes, priority processing, and advanced features.
                </p>
              </div>
              <div className="ml-3 flex-shrink-0">
                <Link
                  href="/dashboard/settings"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                >
                  Upgrade Now
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default withAuth(DashboardPage);
