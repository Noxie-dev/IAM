import React, { useState } from 'react';
import { Globe, Clock, Volume2, Monitor } from 'lucide-react';
import ToggleSwitch from '../../../../components/ui/toggle-switch';
import { Button } from '../../../../components/ui/button';

const PreferencesTab = () => {
  const [preferences, setPreferences] = useState({
    language: 'English',
    timezone: 'Pacific Standard Time',
    emailNotifications: true,
    pushNotifications: false,
    soundEnabled: true,
    autoSave: true,
    darkMode: true,
    compactView: false
  });

  const updatePreference = (key, value) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    // Save preferences logic here
    console.log('Saving preferences:', preferences);
  };

  return (
    <div className="space-y-6">
      {/* General Settings */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Monitor className="w-5 h-5 mr-2" />
          General Settings
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-300">Language</span>
            </div>
            <select
              value={preferences.language}
              onChange={(e) => updatePreference('language', e.target.value)}
              className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="English">English</option>
              <option value="Spanish">Spanish</option>
              <option value="French">French</option>
              <option value="German">German</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-300">Timezone</span>
            </div>
            <select
              value={preferences.timezone}
              onChange={(e) => updatePreference('timezone', e.target.value)}
              className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="Pacific Standard Time">PST</option>
              <option value="Mountain Standard Time">MST</option>
              <option value="Central Standard Time">CST</option>
              <option value="Eastern Standard Time">EST</option>
            </select>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Notification Settings</h3>
        
        <div className="space-y-4">
          <ToggleSwitch
            checked={preferences.emailNotifications}
            onChange={(value) => updatePreference('emailNotifications', value)}
            label="Email Notifications"
          />
          
          <ToggleSwitch
            checked={preferences.pushNotifications}
            onChange={(value) => updatePreference('pushNotifications', value)}
            label="Push Notifications"
          />
          
          <div className="flex items-center space-x-3">
            <Volume2 className="w-4 h-4 text-gray-400" />
            <ToggleSwitch
              checked={preferences.soundEnabled}
              onChange={(value) => updatePreference('soundEnabled', value)}
              label="Sound Notifications"
            />
          </div>
        </div>
      </div>

      {/* Application Settings */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Application Settings</h3>
        
        <div className="space-y-4">
          <ToggleSwitch
            checked={preferences.autoSave}
            onChange={(value) => updatePreference('autoSave', value)}
            label="Auto-save Documents"
          />
          
          <ToggleSwitch
            checked={preferences.compactView}
            onChange={(value) => updatePreference('compactView', value)}
            label="Compact View"
          />
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2"
        >
          Save Preferences
        </Button>
      </div>
    </div>
  );
};

export default PreferencesTab;

