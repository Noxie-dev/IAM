import React, { useState } from 'react';
import { Bell, Mail, MessageSquare, Calendar, Users } from 'lucide-react';
import ToggleSwitch from '../../../../components/ui/toggle-switch';
import { Button } from '../../../../components/ui/button';

const NotificationsTab = () => {
  const [notifications, setNotifications] = useState({
    email: {
      meetingReminders: true,
      teamInvites: true,
      weeklyDigest: false,
      productUpdates: true
    },
    push: {
      meetingAlerts: true,
      messageNotifications: false,
      taskDeadlines: true,
      teamActivity: false
    },
    inApp: {
      realTimeUpdates: true,
      soundAlerts: true,
      desktopNotifications: false
    }
  });

  const updateNotification = (category, key, value) => {
    setNotifications(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const handleSave = () => {
    console.log('Saving notification preferences:', notifications);
  };

  return (
    <div className="space-y-6">
      {/* Email Notifications */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Mail className="w-5 h-5 mr-2" />
          Email Notifications
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <Calendar className="w-4 h-4 text-gray-400" />
            <ToggleSwitch
              checked={notifications.email.meetingReminders}
              onChange={(value) => updateNotification('email', 'meetingReminders', value)}
              label="Meeting Reminders"
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <Users className="w-4 h-4 text-gray-400" />
            <ToggleSwitch
              checked={notifications.email.teamInvites}
              onChange={(value) => updateNotification('email', 'teamInvites', value)}
              label="Team Invitations"
            />
          </div>
          
          <ToggleSwitch
            checked={notifications.email.weeklyDigest}
            onChange={(value) => updateNotification('email', 'weeklyDigest', value)}
            label="Weekly Activity Digest"
          />
          
          <ToggleSwitch
            checked={notifications.email.productUpdates}
            onChange={(value) => updateNotification('email', 'productUpdates', value)}
            label="Product Updates & News"
          />
        </div>
      </div>

      {/* Push Notifications */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Bell className="w-5 h-5 mr-2" />
          Push Notifications
        </h3>
        
        <div className="space-y-4">
          <ToggleSwitch
            checked={notifications.push.meetingAlerts}
            onChange={(value) => updateNotification('push', 'meetingAlerts', value)}
            label="Meeting Alerts (5 min before)"
          />
          
          <div className="flex items-center space-x-3">
            <MessageSquare className="w-4 h-4 text-gray-400" />
            <ToggleSwitch
              checked={notifications.push.messageNotifications}
              onChange={(value) => updateNotification('push', 'messageNotifications', value)}
              label="Message Notifications"
            />
          </div>
          
          <ToggleSwitch
            checked={notifications.push.taskDeadlines}
            onChange={(value) => updateNotification('push', 'taskDeadlines', value)}
            label="Task Deadlines"
          />
          
          <ToggleSwitch
            checked={notifications.push.teamActivity}
            onChange={(value) => updateNotification('push', 'teamActivity', value)}
            label="Team Activity Updates"
          />
        </div>
      </div>

      {/* In-App Notifications */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">In-App Notifications</h3>
        
        <div className="space-y-4">
          <ToggleSwitch
            checked={notifications.inApp.realTimeUpdates}
            onChange={(value) => updateNotification('inApp', 'realTimeUpdates', value)}
            label="Real-time Updates"
          />
          
          <ToggleSwitch
            checked={notifications.inApp.soundAlerts}
            onChange={(value) => updateNotification('inApp', 'soundAlerts', value)}
            label="Sound Alerts"
          />
          
          <ToggleSwitch
            checked={notifications.inApp.desktopNotifications}
            onChange={(value) => updateNotification('inApp', 'desktopNotifications', value)}
            label="Desktop Notifications"
          />
        </div>
      </div>

      {/* Notification Schedule */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Notification Schedule</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Quiet Hours</span>
            <div className="flex items-center space-x-2">
              <select className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white">
                <option value="22:00">10:00 PM</option>
                <option value="23:00">11:00 PM</option>
                <option value="00:00">12:00 AM</option>
              </select>
              <span className="text-gray-400">to</span>
              <select className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white">
                <option value="07:00">7:00 AM</option>
                <option value="08:00">8:00 AM</option>
                <option value="09:00">9:00 AM</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-6 py-2"
        >
          Save Notification Settings
        </Button>
      </div>
    </div>
  );
};

export default NotificationsTab;



