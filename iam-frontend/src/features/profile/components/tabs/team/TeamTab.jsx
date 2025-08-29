import React, { useState } from 'react';
import { Users, CalendarPlus, BarChart2 } from 'lucide-react';
import TeamMembers from './TeamMembers';
import MeetingScheduler from './MeetingScheduler';
import TeamAnalytics from './TeamAnalytics';

const TABS = [
  { id: 'members', label: 'Members', icon: Users },
  { id: 'scheduler', label: 'Scheduler', icon: CalendarPlus },
  { id: 'analytics', label: 'Analytics', icon: BarChart2 },
];

const TeamTab = () => {
  const [activeSubTab, setActiveSubTab] = useState('members');

  const renderContent = () => {
    switch(activeSubTab) {
      case 'members': return <TeamMembers />;
      case 'scheduler': return <MeetingScheduler />;
      case 'analytics': return <TeamAnalytics />;
      default: return <TeamMembers />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2 bg-white/5 rounded-lg p-1">
        {TABS.map(tab => (
          <button 
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
              activeSubTab === tab.id 
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md' 
                : 'text-gray-400 hover:text-white hover:bg-white/10'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
      <div>{renderContent()}</div>
    </div>
  );
};

export default TeamTab;




