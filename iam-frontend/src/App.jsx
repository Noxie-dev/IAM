import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './components/LandingPage'
import MainApp from './components/MainApp'
import AuthModal from './components/AuthModal'
import FAQPage from './features/faq'
import './App.css'

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('iam_access_token');
      const userData = localStorage.getItem('iam_user');

      if (token && userData) {
        try {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
        } catch (error) {
          console.error('Error parsing user data:', error);
          // Clear invalid data
          localStorage.removeItem('iam_access_token');
          localStorage.removeItem('iam_refresh_token');
          localStorage.removeItem('iam_user');
        }
      }

      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // Authentication handlers
  const handleLogin = () => {
    setAuthMode('login');
    setShowAuthModal(true);
  };

  const handleSignup = () => {
    setAuthMode('register');
    setShowAuthModal(true);
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setUser(null);
  };

  const closeAuthModal = () => {
    setShowAuthModal(false);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Landing page route - only show if not authenticated */}
          <Route
            path="/"
            element={
              user ? (
                <Navigate to="/app" replace />
              ) : (
                <LandingPage
                  onLogin={handleLogin}
                  onSignup={handleSignup}
                />
              )
            }
          />

          {/* FAQ page route - accessible to everyone */}
          <Route
            path="/faq"
            element={<FAQPage />}
          />

          {/* Main application route - only show if authenticated */}
          <Route
            path="/app"
            element={
              user ? (
                <MainApp
                  user={user}
                  onLogout={handleLogout}
                />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />

          {/* Catch all route - redirect to appropriate page */}
          <Route
            path="*"
            element={<Navigate to={user ? "/app" : "/"} replace />}
          />
        </Routes>

        {/* Authentication Modal */}
        <AuthModal
          isOpen={showAuthModal}
          onClose={closeAuthModal}
          mode={authMode}
          onSuccess={handleAuthSuccess}
        />
      </div>
    </Router>
  );
}



export default App

