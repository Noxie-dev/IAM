import { useState } from 'react'
import AudioRecorder from './AudioRecorder'
import MeetingsList from './MeetingsList'
import PaymentModal from './PaymentModal'
import { ToastContainer } from './Toast'
import useToast from '../hooks/useToast'
import { Button } from '@/components/ui/button.jsx'
import { Mic, List, Crown, LogOut } from 'lucide-react'

function MainApp({ user, onLogout }) {
  const [audioBlob, setAudioBlob] = useState(null);
  const [meetingTitle, setMeetingTitle] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('record'); // 'record' or 'meetings'
  const [refreshMeetings, setRefreshMeetings] = useState(0);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [isPremium, setIsPremium] = useState(user?.is_premium || false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const { toasts, removeToast, showSuccess, showError, showWarning } = useToast();

  const handleRecordingComplete = (blob) => {
    setAudioBlob(blob);
    setErrorMessage(''); // Clear any previous errors
    setSuccessMessage('');
    console.log('Recording completed, blob size:', blob.size);
  };

  const clearMessages = () => {
    setErrorMessage('');
    setSuccessMessage('');
  };

  const getErrorMessage = (error, errorType) => {
    switch (errorType) {
      case 'validation_error':
        return `Invalid audio file: ${error}`;
      case 'rate_limit_error':
        return 'Too many requests. Please wait a moment and try again.';
      case 'authentication_error':
        return 'Service authentication failed. Please contact support.';
      case 'network_error':
        return 'Network connection failed. Please check your internet connection and try again.';
      case 'transcription_error':
        return `Transcription failed: ${error}`;
      case 'database_error':
        return 'Failed to save meeting. Please try again.';
      case 'configuration_error':
        return 'Service temporarily unavailable. Please contact support.';
      default:
        return error || 'An unexpected error occurred. Please try again.';
    }
  };

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const uploadWithProgress = async (formData, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          onProgress(Math.round(percentComplete));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid response format'));
          }
        } else {
          try {
            const errorResponse = JSON.parse(xhr.responseText);
            reject({
              status: xhr.status,
              error: errorResponse.error || 'Request failed',
              errorType: errorResponse.error_type || 'unknown_error'
            });
          } catch (e) {
            reject({
              status: xhr.status,
              error: 'Request failed',
              errorType: 'network_error'
            });
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject({
          status: 0,
          error: 'Network connection failed',
          errorType: 'network_error'
        });
      });

      xhr.addEventListener('timeout', () => {
        reject({
          status: 0,
          error: 'Request timeout',
          errorType: 'network_error'
        });
      });

      // Add authorization header
      const token = localStorage.getItem('iam_access_token');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.open('POST', '/api/transcribe');
      xhr.timeout = 300000; // 5 minute timeout
      xhr.send(formData);
    });
  };

  const handleSaveMeeting = async (retryCount = 0) => {
    const maxRetries = 3;

    // Validation
    if (!audioBlob || !meetingTitle.trim()) {
      showError('Please record audio and provide a meeting title');
      return;
    }

    // Clear previous messages
    clearMessages();
    setIsProcessing(true);
    setUploadProgress(0);
    setProcessingStatus('Preparing audio file...');

    try {
      // Store audio in IndexedDB
      setProcessingStatus('Saving audio locally...');
      const audioId = await storeAudioInIndexedDB(audioBlob, meetingTitle);

      // Prepare form data
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('title', meetingTitle);
      formData.append('audioId', audioId);

      // Upload with progress tracking
      setProcessingStatus('Uploading audio for transcription...');

      try {
        const result = await uploadWithProgress(formData, (progress) => {
          setUploadProgress(progress);
          if (progress === 100) {
            setProcessingStatus('Processing transcription...');
          }
        });

        if (result.success) {
          console.log('Meeting saved successfully:', result);
          showSuccess('Meeting saved and transcribed successfully!');

          // Reset form
          setAudioBlob(null);
          setMeetingTitle('');
          setUploadProgress(0);
          setProcessingStatus('');

          // Refresh meetings list
          setRefreshMeetings(prev => prev + 1);

          // Switch to meetings tab to show the new meeting
          setActiveTab('meetings');
        } else {
          throw {
            error: result.error || 'Unknown error',
            errorType: result.error_type || 'unknown_error',
            status: 500
          };
        }
      } catch (uploadError) {
        // Handle specific error types with retry logic
        const shouldRetry = retryCount < maxRetries && (
          uploadError.errorType === 'network_error' ||
          uploadError.errorType === 'rate_limit_error' ||
          (uploadError.status >= 500 && uploadError.status < 600)
        );

        if (shouldRetry) {
          const delay = Math.pow(2, retryCount) * 1000; // Exponential backoff
          setProcessingStatus(`Retrying in ${delay / 1000} seconds... (Attempt ${retryCount + 1}/${maxRetries})`);
          showWarning(`Retrying... (Attempt ${retryCount + 1}/${maxRetries})`);

          await sleep(delay);
          return handleSaveMeeting(retryCount + 1);
        } else {
          // Show user-friendly error message
          const userMessage = getErrorMessage(uploadError.error, uploadError.errorType);
          showError(userMessage);
          console.error('Error saving meeting:', uploadError);
        }
      }
    } catch (error) {
      console.error('Error in handleSaveMeeting:', error);
      showError('Failed to prepare audio file. Please try again.');
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
      setProcessingStatus('');
    }
  };

  const handlePaymentSuccess = () => {
    setIsPremium(true);
    localStorage.setItem('iam_premium', 'true');
  };

  const storeAudioInIndexedDB = (blob, title) => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('IAM_AudioDB', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('audioRecordings')) {
          db.createObjectStore('audioRecordings', { keyPath: 'id', autoIncrement: true });
        }
      };
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction(['audioRecordings'], 'readwrite');
        const store = transaction.objectStore('audioRecordings');
        
        const audioData = {
          title: title,
          blob: blob,
          timestamp: new Date().toISOString(),
        };
        
        const addRequest = store.add(audioData);
        
        addRequest.onsuccess = () => {
          resolve(addRequest.result); // This is the auto-generated ID
        };
        
        addRequest.onerror = () => reject(addRequest.error);
      };
    });
  };

  const handleLogout = () => {
    // Clear authentication data
    localStorage.removeItem('iam_access_token');
    localStorage.removeItem('iam_refresh_token');
    localStorage.removeItem('iam_user');
    localStorage.removeItem('iam_premium');
    
    // Call parent logout handler
    onLogout();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h1 className="text-4xl font-bold text-foreground">
                IAM - In A Meeting
              </h1>
              {isPremium && (
                <div className="flex items-center gap-1 bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  <Crown className="w-4 h-4" />
                  Premium
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.first_name || user?.email}
              </span>
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          </div>
          
          <p className="text-muted-foreground text-lg">
            Record, transcribe, and organize your meetings with AI
          </p>
          {!isPremium && (
            <Button
              onClick={() => setShowPaymentModal(true)}
              className="mt-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
            >
              <Crown className="w-4 h-4 mr-2" />
              Upgrade to Premium
            </Button>
          )}
        </header>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-muted rounded-lg p-1">
            <Button
              variant={activeTab === 'record' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('record')}
              className="flex items-center gap-2"
            >
              <Mic className="w-4 h-4" />
              Record Meeting
            </Button>
            <Button
              variant={activeTab === 'meetings' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('meetings')}
              className="flex items-center gap-2"
            >
              <List className="w-4 h-4" />
              My Meetings
            </Button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'record' ? (
          <div className="space-y-6">
            <AudioRecorder onRecordingComplete={handleRecordingComplete} />
            
            {audioBlob && (
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="text-lg font-semibold mb-4">Meeting Details</h3>

                <div className="space-y-4">
                  <div>
                    <label htmlFor="meetingTitle" className="block text-sm font-medium mb-2">
                      Meeting Title
                    </label>
                    <input
                      id="meetingTitle"
                      type="text"
                      value={meetingTitle}
                      onChange={(e) => setMeetingTitle(e.target.value)}
                      placeholder="Enter meeting title..."
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      disabled={isProcessing}
                    />
                  </div>

                  {/* Progress and Status Display */}
                  {isProcessing && (
                    <div className="space-y-3">
                      {uploadProgress > 0 && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Upload Progress</span>
                            <span>{uploadProgress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${uploadProgress}%` }}
                            ></div>
                          </div>
                        </div>
                      )}

                      {processingStatus && (
                        <div className="flex items-center space-x-2 text-blue-600">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          <span className="text-sm">{processingStatus}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Error Message */}
                  {errorMessage && (
                    <div className="flex items-start space-x-2 text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                      <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Error</p>
                        <p className="text-sm">{errorMessage}</p>
                      </div>
                      <button
                        onClick={clearMessages}
                        className="text-red-400 hover:text-red-600"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  )}

                  {/* Success Message */}
                  {successMessage && (
                    <div className="flex items-start space-x-2 text-green-600 bg-green-50 p-3 rounded-lg border border-green-200">
                      <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Success</p>
                        <p className="text-sm">{successMessage}</p>
                      </div>
                      <button
                        onClick={clearMessages}
                        className="text-green-400 hover:text-green-600"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  )}

                  <Button
                    onClick={handleSaveMeeting}
                    disabled={isProcessing || !meetingTitle.trim()}
                    className="w-full"
                    size="lg"
                  >
                    {isProcessing ? (
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Processing...</span>
                      </div>
                    ) : (
                      'Save & Transcribe Meeting'
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <MeetingsList key={refreshMeetings} />
        )}

        {/* Payment Modal */}
        <PaymentModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          onPaymentSuccess={handlePaymentSuccess}
        />

        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} removeToast={removeToast} />
      </div>
    </div>
  )
}

export default MainApp
