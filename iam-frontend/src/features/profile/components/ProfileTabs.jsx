import React from 'react';
import { User, Settings, Users, Mail, Bell, Shield } from 'lucide-react';

const TABS = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'preferences', label: 'Preferences', icon: Settings },
  { id: 'team', label: 'Team', icon: Users },
  { id: 'inbox', label: 'Inbox', icon: Mail },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
];

const ProfileTabs = ({ activeTab, setActiveTab }) => {
  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 mb-6">
      <div className="flex flex-wrap gap-2">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105'
                : 'text-gray-400 hover:text-white hover:bg-white/10'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ProfileTabs;

