import React, { useState, useEffect } from 'react';
import { Globe, Clock, Volume2, Monitor, CheckCircle } from 'lucide-react';
import ToggleSwitch from '../../../../components/ui/toggle-switch';
import { Button } from '../../../../components/ui/button';
import { useUserPreferences } from '../../../../context/UserContext';

const PreferencesTab = () => {
  const { preferences: userPreferences, loading, error, savePreferences, clearError } = useUserPreferences();
  const [preferences, setPreferences] = useState({
    language: 'English',
    timezone: 'Pacific Standard Time',
    email_notifications: true,
    push_notifications: false,
    sound_enabled: true,
    auto_save: true,
    dark_mode: true,
    compact_view: false
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load user preferences when they become available
  useEffect(() => {
    if (userPreferences) {
      setPreferences(userPreferences);
    }
  }, [userPreferences]);

  // Clear success message after 3 seconds
  useEffect(() => {
    if (saveSuccess) {
      const timer = setTimeout(() => setSaveSuccess(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess]);

  const updatePreference = (key, value) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    clearError(); // Clear any previous errors
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      clearError();
      await savePreferences(preferences);
      setSaveSuccess(true);
    } catch (error) {
      console.error('Error saving preferences:', error);
      // Error is handled by the context
    } finally {
      setSaving(false);
    }
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
            checked={preferences.email_notifications}
            onChange={(value) => updatePreference('email_notifications', value)}
            label="Email Notifications"
          />
          
          <ToggleSwitch
            checked={preferences.push_notifications}
            onChange={(value) => updatePreference('push_notifications', value)}
            label="Push Notifications"
          />
          
          <div className="flex items-center space-x-3">
            <Volume2 className="w-4 h-4 text-gray-400" />
            <ToggleSwitch
              checked={preferences.sound_enabled}
              onChange={(value) => updatePreference('sound_enabled', value)}
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
            checked={preferences.auto_save}
            onChange={(value) => updatePreference('auto_save', value)}
            label="Auto-save Documents"
          />
          
          <ToggleSwitch
            checked={preferences.compact_view}
            onChange={(value) => updatePreference('compact_view', value)}
            label="Compact View"
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {saveSuccess && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <p className="text-green-400 text-sm">Preferences saved successfully!</p>
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={saving || loading}
          className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </div>
    </div>
  );
};

export default PreferencesTab;

