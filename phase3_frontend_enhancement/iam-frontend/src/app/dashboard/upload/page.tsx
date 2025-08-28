/**
 * Upload Page
 * Phase 3: Frontend Enhancement
 * 
 * Audio file upload interface with transcription options
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'react-hot-toast';
import {
  MicrophoneIcon,
  Cog6ToothIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

import DashboardLayout from '@/components/layout/DashboardLayout';
import FileUpload from '@/components/upload/FileUpload';
import { withAuth, usePermissions } from '@/contexts/AuthContext';

// Form validation schema
const transcriptionSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title must be less than 200 characters'),
  description: z.string().max(1000, 'Description must be less than 1000 characters').optional(),
  language: z.string().default('auto'),
  provider: z.string().default('openai'),
  model: z.string().default('whisper-1'),
  speaker_detection: z.boolean().default(false),
  timestamps: z.boolean().default(true),
  word_timestamps: z.boolean().default(false),
  // Audio enhancement options
  enhance_audio: z.boolean().default(true),
  noise_reduction: z.boolean().default(true),
  vad_attenuation_db: z.number().min(0).max(30).default(12),
  high_pass_freq: z.number().min(0).max(500).default(80),
  lufs_target: z.number().min(-40).max(-10).default(-23),
  speaker_boost_db: z.number().min(0).max(10).default(3),
});

type TranscriptionFormData = z.infer<typeof transcriptionSchema>;

function UploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const router = useRouter();
  const { subscriptionTier, isPremium, remainingMinutes } = usePermissions();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<TranscriptionFormData>({
    resolver: zodResolver(transcriptionSchema),
    defaultValues: {
      language: 'auto',
      provider: 'openai',
      model: 'whisper-1',
      speaker_detection: false,
      timestamps: true,
      word_timestamps: false,
      // Audio enhancement defaults
      enhance_audio: true,
      noise_reduction: true,
      vad_attenuation_db: 12,
      high_pass_freq: 80,
      lufs_target: -23,
      speaker_boost_db: 3,
    },
  });

  const selectedProvider = watch('provider');

  const handleUploadComplete = (result: any) => {
    setUploadedFiles((prev) => [...prev, result]);
  };

  const handleUploadStart = () => {
    setIsProcessing(true);
  };

  const onSubmit = async (data: TranscriptionFormData) => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload at least one audio file');
      return;
    }

    try {
      setIsProcessing(true);
      
      // In a real app, this would start the transcription process
      // For now, we'll simulate the process
      toast.success('Transcription started! You will be notified when complete.');
      
      // Redirect to transcriptions page
      setTimeout(() => {
        router.push('/dashboard/transcriptions');
      }, 2000);
      
    } catch (error) {
      console.error('Transcription start error:', error);
      toast.error('Failed to start transcription. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const languageOptions = [
    { value: 'auto', label: 'Auto-detect' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Spanish' },
    { value: 'fr', label: 'French' },
    { value: 'de', label: 'German' },
    { value: 'it', label: 'Italian' },
    { value: 'pt', label: 'Portuguese' },
    { value: 'ru', label: 'Russian' },
    { value: 'ja', label: 'Japanese' },
    { value: 'ko', label: 'Korean' },
    { value: 'zh', label: 'Chinese' },
  ];

  const providerOptions = [
    { value: 'openai', label: 'OpenAI Whisper', description: 'High accuracy, good for general use' },
    { value: 'azure', label: 'Azure Speech', description: 'Enterprise-grade, good for business', premium: true },
    { value: 'google', label: 'Google Speech-to-Text', description: 'Fast processing, good for real-time', premium: true },
  ];

  const modelOptions = {
    openai: [
      { value: 'whisper-1', label: 'Whisper v1 (Recommended)' },
    ],
    azure: [
      { value: 'standard', label: 'Standard Model' },
      { value: 'premium', label: 'Premium Model' },
    ],
    google: [
      { value: 'latest_long', label: 'Latest Long Audio' },
      { value: 'latest_short', label: 'Latest Short Audio' },
    ],
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <MicrophoneIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Upload Audio</h1>
              <p className="text-sm text-gray-500">
                Upload your audio files and configure transcription settings
              </p>
            </div>
          </div>
        </div>

        {/* Usage Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-blue-900">
                Current Plan: {subscriptionTier.charAt(0).toUpperCase() + subscriptionTier.slice(1)}
              </h3>
              <p className="mt-1 text-sm text-blue-700">
                {isPremium 
                  ? 'You have unlimited transcription minutes'
                  : `You have ${remainingMinutes} transcription minutes remaining this month`
                }
              </p>
              {!isPremium && (
                <p className="mt-1 text-xs text-blue-600">
                  Need more minutes? <a href="/dashboard/settings" className="underline">Upgrade your plan</a>
                </p>
              )}
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {/* File Upload */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Files</h2>
            <FileUpload
              onUploadComplete={handleUploadComplete}
              onUploadStart={handleUploadStart}
              maxFiles={5}
              transcriptionSettings={{
                ...watch(),
                enhancement_options: watch('enhance_audio') ? {
                  noise_reduction: watch('noise_reduction'),
                  vad_attenuation_db: watch('vad_attenuation_db'),
                  high_pass_freq: watch('high_pass_freq'),
                  lufs_target: watch('lufs_target'),
                  speaker_boost_db: watch('speaker_boost_db'),
                } : undefined
              }}
            />
          </div>

          {/* Transcription Settings */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Cog6ToothIcon className="h-5 w-5 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">Transcription Settings</h2>
            </div>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {/* Title */}
              <div className="sm:col-span-2">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Title *
                </label>
                <input
                  {...register('title')}
                  type="text"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="e.g., Team Meeting - Q4 Planning"
                />
                {errors.title && (
                  <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
                )}
              </div>

              {/* Description */}
              <div className="sm:col-span-2">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description (optional)
                </label>
                <textarea
                  {...register('description')}
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Brief description of the audio content..."
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              {/* Language */}
              <div>
                <label htmlFor="language" className="block text-sm font-medium text-gray-700">
                  Language
                </label>
                <select
                  {...register('language')}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  {languageOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Provider */}
              <div>
                <label htmlFor="provider" className="block text-sm font-medium text-gray-700">
                  AI Provider
                </label>
                <select
                  {...register('provider')}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  {providerOptions.map((option) => (
                    <option 
                      key={option.value} 
                      value={option.value}
                      disabled={option.premium && !isPremium}
                    >
                      {option.label} {option.premium && !isPremium ? '(Premium)' : ''}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  {providerOptions.find(p => p.value === selectedProvider)?.description}
                </p>
              </div>

              {/* Model */}
              <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                  Model
                </label>
                <select
                  {...register('model')}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  {modelOptions[selectedProvider as keyof typeof modelOptions]?.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Advanced Options */}
              <div className="sm:col-span-2">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Advanced Options</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      {...register('timestamps')}
                      type="checkbox"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Include timestamps
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      {...register('word_timestamps')}
                      type="checkbox"
                      disabled={!isPremium}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Word-level timestamps {!isPremium && '(Premium)'}
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      {...register('speaker_detection')}
                      type="checkbox"
                      disabled={!isPremium}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Speaker detection {!isPremium && '(Premium)'}
                    </label>
                  </div>
                </div>
              </div>

              {/* Audio Enhancement */}
              <div className="sm:col-span-2">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Audio Enhancement</h3>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      {...register('enhance_audio')}
                      type="checkbox"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                      Enable audio enhancement for better transcription quality
                    </label>
                  </div>

                  {watch('enhance_audio') && (
                    <div className="ml-6 space-y-4 p-4 bg-gray-50 rounded-md">
                      <div className="flex items-center">
                        <input
                          {...register('noise_reduction')}
                          type="checkbox"
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Noise reduction
                        </label>
                      </div>

                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-700">
                            Background noise attenuation (dB)
                          </label>
                          <input
                            {...register('vad_attenuation_db', { valueAsNumber: true })}
                            type="range"
                            min="0"
                            max="30"
                            step="1"
                            className="mt-1 block w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>0</span>
                            <span>{watch('vad_attenuation_db')} dB</span>
                            <span>30</span>
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700">
                            High-pass filter (Hz)
                          </label>
                          <input
                            {...register('high_pass_freq', { valueAsNumber: true })}
                            type="range"
                            min="0"
                            max="500"
                            step="10"
                            className="mt-1 block w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>0</span>
                            <span>{watch('high_pass_freq')} Hz</span>
                            <span>500</span>
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700">
                            Loudness target (LUFS)
                          </label>
                          <input
                            {...register('lufs_target', { valueAsNumber: true })}
                            type="range"
                            min="-40"
                            max="-10"
                            step="1"
                            className="mt-1 block w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>-40</span>
                            <span>{watch('lufs_target')} LUFS</span>
                            <span>-10</span>
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700">
                            Speaker boost (dB)
                          </label>
                          <input
                            {...register('speaker_boost_db', { valueAsNumber: true })}
                            type="range"
                            min="0"
                            max="10"
                            step="0.5"
                            className="mt-1 block w-full"
                          />
                          <div className="flex justify-between text-xs text-gray-500">
                            <span>0</span>
                            <span>{watch('speaker_boost_db')} dB</span>
                            <span>10</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-xs text-gray-600 bg-blue-50 p-3 rounded-md">
                        <p className="font-medium text-blue-800 mb-1">Enhancement Features:</p>
                        <ul className="space-y-1 text-blue-700">
                          <li>• Noise reduction using advanced algorithms</li>
                          <li>• Voice activity detection for cleaner audio</li>
                          <li>• Frequency filtering to remove unwanted sounds</li>
                          <li>• Loudness normalization for consistent levels</li>
                          <li>• Speech frequency boost for clarity</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isProcessing || uploadedFiles.length === 0}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting Transcription...
                </div>
              ) : (
                'Start Transcription'
              )}
            </button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(UploadPage);
