/**
 * Landing Page
 * Phase 3: Frontend Enhancement
 *
 * Public landing page with authentication redirect
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { MicrophoneIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <div className="bg-white min-h-screen">
      {/* Header */}
      <header className="absolute inset-x-0 top-0 z-50">
        <nav className="flex items-center justify-between p-6 lg:px-8">
          <div className="flex lg:flex-1">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <MicrophoneIcon className="h-5 w-5 text-white" />
              </div>
              <span className="ml-2 text-xl font-bold text-gray-900">IAM SaaS Platform</span>
            </div>
          </div>
          <div className="flex lg:flex-1 lg:justify-end gap-x-4">
            <Link
              href="/auth/login"
              className="text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600"
            >
              Log in
            </Link>
            <Link
              href="/auth/register"
              className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
            >
              Sign up
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Transform Audio into{' '}
              <span className="text-blue-600">Searchable Text</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Professional AI-powered transcription services for meetings, interviews, and audio content.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/auth/register"
                className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
              >
                Get started free
              </Link>
              <Link
                href="/auth/login"
                className="text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600"
              >
                Sign in <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
