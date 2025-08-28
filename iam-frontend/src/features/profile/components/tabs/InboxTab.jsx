import React, { useState } from 'react';
import { Mail, Star, Trash2, Reply, Archive, Search } from 'lucide-react';
import { Button } from '../../../../components/ui/button';
import { Input } from '../../../../components/ui/input';

const initialMessages = [
  {
    id: 1,
    from: 'Sarah Chen',
    subject: 'Q4 Strategy Meeting Follow-up',
    preview: 'Thanks for the productive meeting today. I\'ve attached the action items...',
    time: '2 hours ago',
    read: false,
    starred: true
  },
  {
    id: 2,
    from: 'Team Notifications',
    subject: 'Weekly Team Digest',
    preview: 'Here\'s your weekly summary of team activities and achievements...',
    time: '1 day ago',
    read: true,
    starred: false
  },
  {
    id: 3,
    from: 'Product Team',
    subject: 'New Feature Release',
    preview: 'We\'re excited to announce the launch of our new collaboration features...',
    time: '3 days ago',
    read: true,
    starred: false
  },
  {
    id: 4,
    from: 'HR Department',
    subject: 'Benefits Enrollment Reminder',
    preview: 'This is a friendly reminder that benefits enrollment closes on...',
    time: '1 week ago',
    read: false,
    starred: false
  }
];

const InboxTab = () => {
  const [messages, setMessages] = useState(initialMessages);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredMessages = messages.filter(message =>
    message.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    message.from.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleMessageClick = (message) => {
    setSelectedMessage(message);
    // Mark as read
    if (!message.read) {
      setMessages(prev => 
        prev.map(m => m.id === message.id ? { ...m, read: true } : m)
      );
    }
  };

  const toggleStar = (messageId) => {
    setMessages(prev =>
      prev.map(m => m.id === messageId ? { ...m, starred: !m.starred } : m)
    );
  };

  const deleteMessage = (messageId) => {
    setMessages(prev => prev.filter(m => m.id !== messageId));
    if (selectedMessage?.id === messageId) {
      setSelectedMessage(null);
    }
  };

  const unreadCount = messages.filter(m => !m.read).length;

  return (
    <div className="space-y-6">
      {/* Inbox Header */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Mail className="w-5 h-5 mr-2" />
            Inbox ({unreadCount} unread)
          </h3>
          
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search messages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white/10 border-white/20 text-white"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Message List */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h4 className="font-semibold text-white">Messages</h4>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {filteredMessages.map(message => (
              <div
                key={message.id}
                onClick={() => handleMessageClick(message)}
                className={`p-4 border-b border-white/5 cursor-pointer transition-colors hover:bg-white/5 ${
                  selectedMessage?.id === message.id ? 'bg-white/10' : ''
                } ${!message.read ? 'border-l-4 border-l-blue-500' : ''}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${!message.read ? 'text-white' : 'text-gray-300'}`}>
                      {message.from}
                    </p>
                    <p className={`text-sm truncate ${!message.read ? 'text-white' : 'text-gray-400'}`}>
                      {message.subject}
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleStar(message.id);
                      }}
                      className={`text-sm ${message.starred ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'}`}
                    >
                      <Star className="w-4 h-4" fill={message.starred ? 'currentColor' : 'none'} />
                    </button>
                    
                    <span className="text-xs text-gray-400">{message.time}</span>
                  </div>
                </div>
                
                <p className="text-xs text-gray-400 truncate">{message.preview}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Message Detail */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10">
          {selectedMessage ? (
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="font-semibold text-white">{selectedMessage.subject}</h4>
                  <p className="text-sm text-gray-400">From: {selectedMessage.from}</p>
                  <p className="text-xs text-gray-400">{selectedMessage.time}</p>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleStar(selectedMessage.id)}
                    className="text-gray-400 hover:text-yellow-400"
                  >
                    <Star className="w-4 h-4" fill={selectedMessage.starred ? 'currentColor' : 'none'} />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-white"
                  >
                    <Reply className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-white"
                  >
                    <Archive className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMessage(selectedMessage.id)}
                    className="text-gray-400 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="border-t border-white/10 pt-4">
                <p className="text-gray-300 text-sm leading-relaxed">
                  {selectedMessage.preview}
                  <br /><br />
                  This is a sample message content. In a real application, this would contain the full message body with proper formatting, attachments, and other details.
                  <br /><br />
                  Best regards,<br />
                  {selectedMessage.from}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center">
              <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400">Select a message to view its content</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InboxTab;

