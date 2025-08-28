import React, { useState } from 'react';
import { Shield, Key, Smartphone, AlertTriangle } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Input } from '../../../../components/ui/input';
import ToggleSwitch from '../../../../components/ui/toggle-switch';

const SecurityTab = () => {
  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: ''
  });
  
  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    loginAlerts: true,
    sessionTimeout: 30
  });

  const handlePasswordChange = (field, value) => {
    setPasswords(prev => ({ ...prev, [field]: value }));
  };

  const handleSecurityChange = (field, value) => {
    setSecurity(prev => ({ ...prev, [field]: value }));
  };

  const handlePasswordUpdate = () => {
    // Password update logic
    console.log('Updating password...');
  };

  const handleEnable2FA = () => {
    // 2FA setup logic
    console.log('Setting up 2FA...');
  };

  return (
    <div className="space-y-6">
      {/* Password Change */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Key className="w-5 h-5 mr-2" />
          Change Password
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-2">Current Password</label>
            <Input
              type="password"
              value={passwords.current}
              onChange={(e) => handlePasswordChange('current', e.target.value)}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Enter current password"
            />
          </div>
          
          <div>
            <label className="block text-sm text-gray-300 mb-2">New Password</label>
            <Input
              type="password"
              value={passwords.new}
              onChange={(e) => handlePasswordChange('new', e.target.value)}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Enter new password"
            />
          </div>
          
          <div>
            <label className="block text-sm text-gray-300 mb-2">Confirm Password</label>
            <Input
              type="password"
              value={passwords.confirm}
              onChange={(e) => handlePasswordChange('confirm', e.target.value)}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Confirm new password"
            />
          </div>
          
          <Button
            onClick={handlePasswordUpdate}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
          >
            Update Password
          </Button>
        </div>
      </div>

      {/* Two-Factor Authentication */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Smartphone className="w-5 h-5 mr-2" />
          Two-Factor Authentication
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-300">
                Add an extra layer of security to your account
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Status: {security.twoFactorEnabled ? 'Enabled' : 'Disabled'}
              </p>
            </div>
            <Button
              onClick={handleEnable2FA}
              variant={security.twoFactorEnabled ? "destructive" : "default"}
              className={security.twoFactorEnabled 
                ? "bg-red-600 hover:bg-red-700" 
                : "bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
              }
            >
              {security.twoFactorEnabled ? 'Disable 2FA' : 'Enable 2FA'}
            </Button>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Shield className="w-5 h-5 mr-2" />
          Security Settings
        </h3>
        
        <div className="space-y-4">
          <ToggleSwitch
            checked={security.loginAlerts}
            onChange={(value) => handleSecurityChange('loginAlerts', value)}
            label="Login Alerts - Get notified of new logins"
          />
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Session Timeout (minutes)</span>
            <select
              value={security.sessionTimeout}
              onChange={(e) => handleSecurityChange('sessionTimeout', parseInt(e.target.value))}
              className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={60}>1 hour</option>
              <option value={120}>2 hours</option>
            </select>
          </div>
        </div>
      </div>

      {/* Security Alert */}
      <div className="bg-orange-500/10 border border-orange-500/20 rounded-2xl p-6">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-orange-400 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-orange-300 mb-1">Security Tip</h4>
            <p className="text-sm text-orange-200">
              Use a strong, unique password and enable two-factor authentication for better account security.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityTab;

