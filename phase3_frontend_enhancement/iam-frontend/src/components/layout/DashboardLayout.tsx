/**
 * Dashboard Layout Component
 * Phase 3: Frontend Enhancement
 *
 * Main layout for authenticated dashboard pages
 */

'use client';

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import {
  Bars3Icon,
  HomeIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  CogIcon,
  XMarkIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useAuth, usePermissions } from '@/contexts/AuthContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './DashboardLayout.module.css';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const { subscriptionTier, remainingMinutes, isPremium } = usePermissions();
  const pathname = usePathname();

  // Calculate progress bar width and round to nearest 5%
  const progressWidth = Math.max(0, Math.min(100, (remainingMinutes / 1200) * 100));
  const roundedProgressWidth = Math.round(progressWidth / 5) * 5;

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Transcriptions', href: '/dashboard/transcriptions', icon: DocumentTextIcon },
    { name: 'Upload Audio', href: '/dashboard/upload', icon: MicrophoneIcon },
    { name: 'Settings', href: '/dashboard/settings', icon: CogIcon },
  ];

  const isCurrentPage = (href: string) => {
    if (href === '/dashboard') {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <div className="h-full">
      <Transition.Root show={sidebarOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button
                      type="button"
                      className="-m-2.5 p-2.5"
                      onClick={() => setSidebarOpen(false)}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                
                {/* Mobile sidebar content */}
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-2">
                  <div className="flex h-16 shrink-0 items-center">
                    <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                      <MicrophoneIcon className="h-5 w-5 text-white" />
                    </div>
                    <span className="ml-2 text-xl font-bold text-gray-900">IAM SaaS</span>
                  </div>
                  <nav className="flex flex-1 flex-col">
                    <ul role="list" className="flex flex-1 flex-col gap-y-7">
                      <li>
                        <ul role="list" className="-mx-2 space-y-1">
                          {navigation.map((item) => (
                            <li key={item.name}>
                              <Link
                                href={item.href}
                                className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold ${
                                  isCurrentPage(item.href)
                                    ? 'bg-blue-50 text-blue-600'
                                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                                }`}
                                onClick={() => setSidebarOpen(false)}
                              >
                                <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                                {item.name}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </li>
                    </ul>
                  </nav>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6">
          <div className="flex h-16 shrink-0 items-center">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <MicrophoneIcon className="h-5 w-5 text-white" />
            </div>
            <span className="ml-2 text-xl font-bold text-gray-900">IAM SaaS</span>
          </div>
          
          {/* User info */}
          <div className="flex items-center gap-x-4 px-2 py-3 bg-gray-50 rounded-lg">
            <UserCircleIcon className="h-8 w-8 text-gray-400" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.display_name}
              </p>
              <p className="text-xs text-gray-500 capitalize">
                {subscriptionTier} Plan
              </p>
            </div>
          </div>

          {/* Usage info */}
          <div className="px-2 py-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-900">
                Transcription Minutes
              </span>
              <span className="text-sm text-blue-700">
                {isPremium ? 'Unlimited' : `${remainingMinutes} left`}
              </span>
            </div>
            {!isPremium && (
              <div className={styles.progressContainer}>
                <div
                  className={styles.progressBar}
                  data-width={roundedProgressWidth}
                />
              </div>
            )}
          </div>

          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-1">
                  {navigation.map((item) => (
                    <li key={item.name}>
                      <Link
                        href={item.href}
                        className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold ${
                          isCurrentPage(item.href)
                            ? 'bg-blue-50 text-blue-600'
                            : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                        }`}
                      >
                        <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                        {item.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
              <li className="-mx-6 mt-auto">
                <button
                  type="button"
                  onClick={logout}
                  className="flex items-center gap-x-4 px-6 py-3 text-sm font-semibold leading-6 text-gray-900 hover:bg-gray-50 w-full text-left"
                >
                  <ArrowRightOnRectangleIcon className="h-6 w-6 text-gray-400" />
                  Sign out
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-72">
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          <div className="h-6 w-px bg-gray-200 lg:hidden" aria-hidden="true" />

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1"></div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-200" aria-hidden="true" />
              
              {/* User menu */}
              <div className="flex items-center gap-x-2">
                <UserCircleIcon className="h-8 w-8 text-gray-400" />
                <div className="hidden lg:block">
                  <p className="text-sm font-medium text-gray-900">{user?.display_name}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <main className="py-10">
          <div className="px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
