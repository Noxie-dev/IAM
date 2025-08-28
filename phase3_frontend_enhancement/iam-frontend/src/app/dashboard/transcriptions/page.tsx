/**
 * Transcriptions Page
 * Phase 3: Frontend Enhancement
 * 
 * Manage and view all transcriptions
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import {
  DocumentTextIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { withAuth } from '@/contexts/AuthContext';
import { Meeting } from '@/lib/api';

function TranscriptionsPage() {
  const [transcriptions, setTranscriptions] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Mock data - in real app, this would come from API
  useEffect(() => {
    const fetchTranscriptions = async () => {
      try {
        setLoading(true);
        
        // Mock data for demonstration
        const mockTranscriptions: Meeting[] = [
          {
            id: '1',
            user_id: 'user1',
            title: 'Team Meeting - Q4 Planning',
            description: 'Quarterly planning session with the development team',
            meeting_date: '2024-12-26T10:00:00Z',
            duration_seconds: 2700,
            duration_minutes: 45,
            audio_file_url: 'https://example.com/audio1.mp3',
            audio_file_size: 25600000,
            file_size_mb: 24.4,
            audio_file_format: 'mp3',
            original_filename: 'team-meeting-q4.mp3',
            transcription_text: 'Welcome everyone to our Q4 planning meeting...',
            processing_status: 'completed',
            processing_started_at: '2024-12-26T10:05:00Z',
            processing_completed_at: '2024-12-26T10:12:00Z',
            model_used: 'whisper-1',
            provider_used: 'openai',
            language_detected: 'en',
            transcription_confidence: 0.96,
            transcription_cost: 0.25,
            has_audio_file: true,
            has_transcription: true,
            is_completed: true,
            is_failed: false,
            is_processing: false,
            created_at: '2024-12-26T10:00:00Z',
            updated_at: '2024-12-26T10:12:00Z',
          },
          {
            id: '2',
            user_id: 'user1',
            title: 'Client Interview - Product Feedback',
            description: 'User feedback session for the new product features',
            meeting_date: '2024-12-25T14:30:00Z',
            duration_seconds: 1920,
            duration_minutes: 32,
            audio_file_url: 'https://example.com/audio2.mp3',
            audio_file_size: 18400000,
            file_size_mb: 17.5,
            audio_file_format: 'mp3',
            original_filename: 'client-interview.mp3',
            transcription_text: 'Thank you for taking the time to speak with us...',
            processing_status: 'completed',
            processing_started_at: '2024-12-25T14:35:00Z',
            processing_completed_at: '2024-12-25T14:41:00Z',
            model_used: 'whisper-1',
            provider_used: 'openai',
            language_detected: 'en',
            transcription_confidence: 0.94,
            transcription_cost: 0.18,
            has_audio_file: true,
            has_transcription: true,
            is_completed: true,
            is_failed: false,
            is_processing: false,
            created_at: '2024-12-25T14:30:00Z',
            updated_at: '2024-12-25T14:41:00Z',
          },
          {
            id: '3',
            user_id: 'user1',
            title: 'Board Meeting - December',
            description: 'Monthly board meeting with stakeholders',
            meeting_date: '2024-12-24T09:00:00Z',
            duration_seconds: 4680,
            duration_minutes: 78,
            audio_file_url: 'https://example.com/audio3.mp3',
            audio_file_size: 44800000,
            file_size_mb: 42.7,
            audio_file_format: 'mp3',
            original_filename: 'board-meeting-dec.mp3',
            processing_status: 'processing',
            processing_started_at: '2024-12-24T09:05:00Z',
            model_used: 'whisper-1',
            provider_used: 'openai',
            transcription_cost: 0.0,
            has_audio_file: true,
            has_transcription: false,
            is_completed: false,
            is_failed: false,
            is_processing: true,
            created_at: '2024-12-24T09:00:00Z',
            updated_at: '2024-12-24T09:05:00Z',
          },
        ];

        setTranscriptions(mockTranscriptions);
      } catch (error) {
        console.error('Failed to fetch transcriptions:', error);
        toast.error('Failed to load transcriptions');
      } finally {
        setLoading(false);
      }
    };

    fetchTranscriptions();
  }, []);

  const filteredTranscriptions = transcriptions
    .filter((transcription) => {
      const matchesSearch = transcription.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (transcription.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
      const matchesStatus = statusFilter === 'all' || transcription.processing_status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      const aValue = a[sortBy as keyof Meeting];
      const bValue = b[sortBy as keyof Meeting];

      // Handle undefined/null values - put them at the end
      if ((aValue == null || aValue === undefined) && (bValue == null || bValue === undefined)) return 0;
      if (aValue == null || aValue === undefined) return 1;
      if (bValue == null || bValue === undefined) return -1;

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'processing':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this transcription?')) {
      return;
    }

    try {
      // In real app, this would call the API
      setTranscriptions(prev => prev.filter(t => t.id !== id));
      toast.success('Transcription deleted successfully');
    } catch {
      toast.error('Failed to delete transcription');
    }
  };

  const handleDownload = (transcription: Meeting) => {
    // In real app, this would download the transcription file
    toast.success(`Downloading ${transcription.title}...`);
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transcriptions</h1>
            <p className="text-sm text-gray-500">
              Manage and view all your transcription files
            </p>
          </div>
          <Link
            href="/dashboard/upload"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <DocumentTextIcon className="h-4 w-4 mr-2" />
            New Transcription
          </Link>
        </div>

        {/* Filters and Search */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            {/* Search */}
            <div className="sm:col-span-2">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search transcriptions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filter transcriptions by status"
                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field);
                  setSortOrder(order as 'asc' | 'desc');
                }}
                aria-label="Sort transcriptions"
                className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="created_at-desc">Newest First</option>
                <option value="created_at-asc">Oldest First</option>
                <option value="title-asc">Title A-Z</option>
                <option value="title-desc">Title Z-A</option>
                <option value="duration_minutes-desc">Longest First</option>
                <option value="duration_minutes-asc">Shortest First</option>
              </select>
            </div>
          </div>
        </div>

        {/* Transcriptions List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {filteredTranscriptions.length === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No transcriptions found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Get started by uploading your first audio file'
                }
              </p>
              {!searchTerm && statusFilter === 'all' && (
                <div className="mt-6">
                  <Link
                    href="/dashboard/upload"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <DocumentTextIcon className="h-4 w-4 mr-2" />
                    Upload Audio File
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredTranscriptions.map((transcription) => (
                <li key={transcription.id}>
                  <div className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1 min-w-0">
                        <div className="flex-shrink-0">
                          {getStatusIcon(transcription.processing_status)}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {transcription.title}
                            </h3>
                            <span className={getStatusBadge(transcription.processing_status)}>
                              {transcription.processing_status}
                            </span>
                          </div>
                          
                          <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                            <span>{formatDate(transcription.created_at)}</span>
                            {transcription.duration_minutes && (
                              <span>{transcription.duration_minutes} min</span>
                            )}
                            {transcription.file_size_mb && (
                              <span>{transcription.file_size_mb} MB</span>
                            )}
                            {transcription.language_detected && (
                              <span className="uppercase">{transcription.language_detected}</span>
                            )}
                          </div>
                          
                          {transcription.description && (
                            <p className="mt-1 text-sm text-gray-500 truncate">
                              {transcription.description}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {transcription.is_completed && (
                          <>
                            <Link
                              href={`/dashboard/transcriptions/${transcription.id}`}
                              className="p-2 text-gray-400 hover:text-gray-600"
                              title="View transcription"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </Link>
                            <button
                              type="button"
                              onClick={() => handleDownload(transcription)}
                              className="p-2 text-gray-400 hover:text-gray-600"
                              title="Download transcription"
                            >
                              <ArrowDownTrayIcon className="h-4 w-4" />
                            </button>
                          </>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDelete(transcription.id)}
                          className="p-2 text-gray-400 hover:text-red-600"
                          title="Delete transcription"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Stats */}
        {filteredTranscriptions.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {filteredTranscriptions.length}
                </div>
                <div className="text-sm text-gray-500">Total Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {filteredTranscriptions.filter(t => t.is_completed).length}
                </div>
                <div className="text-sm text-gray-500">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {filteredTranscriptions.filter(t => t.is_processing).length}
                </div>
                <div className="text-sm text-gray-500">Processing</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">
                  {filteredTranscriptions.reduce((sum, t) => sum + (t.duration_minutes || 0), 0)}
                </div>
                <div className="text-sm text-gray-500">Total Minutes</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

export default withAuth(TranscriptionsPage);
