import React, { useState } from 'react';
import ProfileCard from './components/ProfileCard';
import ProfileTabs from './components/ProfileTabs';
import PreferencesTab from './components/tabs/PreferencesTab';
import ProfileEditTab from './components/tabs/ProfileEditTab';
import TeamTab from './components/tabs/team/TeamTab';
import InboxTab from './components/tabs/InboxTab';
import NotificationsTab from './components/tabs/NotificationsTab';
import SecurityTab from './components/tabs/SecurityTab';

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState('profile');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile': return <ProfileEditTab />;
      case 'preferences': return <PreferencesTab />;
      case 'team': return <TeamTab />;
      case 'inbox': return <InboxTab />;
      case 'notifications': return <NotificationsTab />;
      case 'security': return <SecurityTab />;
      default: return <ProfileEditTab />;
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <ProfileCard />
        <div className="lg:col-span-3">
          <ProfileTabs activeTab={activeTab} setActiveTab={setActiveTab} />
          <div>{renderTabContent()}</div>
        </div>
      </div>
    </main>
  );
};

export default ProfilePage;

