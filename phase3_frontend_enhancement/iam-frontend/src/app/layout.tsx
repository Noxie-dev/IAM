import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { Toaster } from "react-hot-toast";
import { FloatingTranscriptionUpdates } from "@/components/realtime/TranscriptionStatus";
import { QueryProvider } from "@/lib/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "IAM SaaS Platform - AI-Powered Transcription",
  description: "Professional transcription services with AI-powered accuracy. Transform your meetings, interviews, and audio content into searchable text.",
  keywords: "transcription, AI, speech-to-text, meetings, audio, SaaS",
  authors: [{ name: "IAM SaaS Platform" }],
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full antialiased bg-gray-50`}>
        <QueryProvider>
          <AuthProvider>
            {children}
            <FloatingTranscriptionUpdates />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
