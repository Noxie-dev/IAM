import React from 'react';
import { User, MapPin, Calendar, Award } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../../../components/ui/avatar';
import { Badge } from '../../../components/ui/badge';

const ProfileCard = () => {
  const user = {
    name: 'Alex Johnson',
    email: 'alex.johnson@company.com',
    role: 'Senior Product Manager',
    location: 'San Francisco, CA',
    joinDate: 'January 2022',
    avatar: null,
    stats: {
      meetings: 245,
      hours: 1280,
      projects: 12
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 sticky top-24">
      {/* Profile Header */}
      <div className="text-center mb-6">
        <Avatar className="w-24 h-24 mx-auto mb-4">
          <AvatarImage src={user.avatar} alt={user.name} />
          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xl">
            {user.name.split(' ').map(n => n[0]).join('')}
          </AvatarFallback>
        </Avatar>
        
        <h2 className="text-xl font-bold text-white mb-1">{user.name}</h2>
        <p className="text-gray-400 text-sm mb-2">{user.role}</p>
        <Badge variant="secondary" className="bg-blue-500/20 text-blue-300">
          Premium Member
        </Badge>
      </div>

      {/* Profile Details */}
      <div className="space-y-3 mb-6">
        <div className="flex items-center space-x-3 text-sm">
          <User className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300">{user.email}</span>
        </div>
        
        <div className="flex items-center space-x-3 text-sm">
          <MapPin className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300">{user.location}</span>
        </div>
        
        <div className="flex items-center space-x-3 text-sm">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300">Joined {user.joinDate}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="border-t border-white/10 pt-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center">
          <Award className="w-4 h-4 mr-2" />
          Activity Stats
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-blue-400">{user.stats.meetings}</div>
            <div className="text-xs text-gray-400">Meetings</div>
          </div>
          
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">{user.stats.hours}</div>
            <div className="text-xs text-gray-400">Hours</div>
          </div>
          
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-green-400">{user.stats.projects}</div>
            <div className="text-xs text-gray-400">Projects</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;

