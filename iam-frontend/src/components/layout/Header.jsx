import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings, Sun, Moon, Type, Eye, Zap } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../ui/button';
import ToggleSwitch from '../ui/toggle-switch';

const Header = () => {
  const navigate = useNavigate();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { 
    theme, setTheme, 
    fontSize, setFontSize, 
    highContrast, setHighContrast, 
    reducedMotion, setReducedMotion 
  } = useSettings();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="bg-white/5 backdrop-blur-md border-b border-white/10 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <button 
            onClick={() => navigate('/')}
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
            aria-label="Go to home page"
          >
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">IAM</span>
            </div>
            <span className="text-xl font-bold text-white">Profile</span>
          </button>

          {/* Settings Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className="text-gray-300 hover:text-white"
            >
              <Settings className="w-5 h-5" />
            </Button>

            {isSettingsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 shadow-xl">
                <h3 className="text-lg font-semibold text-white mb-4">Settings</h3>
                
                <div className="space-y-4">
                  {/* Theme Toggle */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                      <span className="text-sm text-gray-300">Theme</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={toggleTheme}
                      className="text-gray-300 hover:text-white"
                    >
                      {theme === 'dark' ? 'Dark' : 'Light'}
                    </Button>
                  </div>

                  {/* Font Size */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Type className="w-4 h-4" />
                      <span className="text-sm text-gray-300">Font Size</span>
                    </div>
                    <select
                      value={fontSize}
                      onChange={(e) => setFontSize(e.target.value)}
                      className="bg-white/10 border border-white/20 rounded-lg px-3 py-1 text-sm text-white"
                    >
                      <option value="small">Small</option>
                      <option value="medium">Medium</option>
                      <option value="large">Large</option>
                    </select>
                  </div>

                  {/* High Contrast */}
                  <div className="flex items-center space-x-2">
                    <Eye className="w-4 h-4" />
                    <ToggleSwitch
                      checked={highContrast}
                      onChange={setHighContrast}
                      label="High Contrast"
                    />
                  </div>

                  {/* Reduced Motion */}
                  <div className="flex items-center space-x-2">
                    <Zap className="w-4 h-4" />
                    <ToggleSwitch
                      checked={reducedMotion}
                      onChange={setReducedMotion}
                      label="Reduced Motion"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

