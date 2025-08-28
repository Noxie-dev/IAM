import React from 'react';
import { User, MapPin, Calendar, Award, Phone, Mail } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../../../components/ui/avatar';
import { Badge } from '../../../components/ui/badge';
import { useProfile } from '../../../context/UserContext';
import { userUtils } from '../../../services/userService';

const ProfileCard = () => {
  const { user, userStats, loading, error } = useProfile();

  if (loading) {
    return (
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 sticky top-24">
        <div className="animate-pulse">
          <div className="w-24 h-24 bg-white/10 rounded-full mx-auto mb-4"></div>
          <div className="h-4 bg-white/10 rounded mb-2"></div>
          <div className="h-3 bg-white/10 rounded mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-white/10 rounded"></div>
            <div className="h-3 bg-white/10 rounded"></div>
            <div className="h-3 bg-white/10 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 sticky top-24">
        <div className="text-center text-gray-400">
          <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Unable to load profile</p>
          {error && <p className="text-xs mt-1 text-red-400">{error}</p>}
        </div>
      </div>
    );
  }

  const displayName = userUtils.getDisplayName(user);
  const initials = userUtils.getInitials(user);
  const subscriptionLabel = userUtils.formatSubscriptionTier(user.subscription_tier);
  const isPremium = userUtils.isPremium(user);
  const joinDate = user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long' 
  }) : 'Unknown';

  const stats = {
    meetings: userStats?.total_meetings || 0,
    hours: Math.round(userStats?.total_hours || 0),
    projects: userStats?.projects_count || 0
  };

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 sticky top-24">
      {/* Profile Header */}
      <div className="text-center mb-6">
        <Avatar className="w-24 h-24 mx-auto mb-4">
          <AvatarImage src={user.avatar_url} alt={displayName} />
          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xl">
            {initials}
          </AvatarFallback>
        </Avatar>
        
        <h2 className="text-xl font-bold text-white mb-1">{displayName}</h2>
        {user.company_name && (
          <p className="text-gray-400 text-sm mb-2">{user.company_name}</p>
        )}
        <Badge 
          variant="secondary" 
          className={`${isPremium ? 'bg-blue-500/20 text-blue-300' : 'bg-gray-500/20 text-gray-300'}`}
        >
          {subscriptionLabel} Member
        </Badge>
      </div>

      {/* Profile Details */}
      <div className="space-y-3 mb-6">
        <div className="flex items-center space-x-3 text-sm">
          <Mail className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300">{user.email}</span>
        </div>
        
        {user.phone && (
          <div className="flex items-center space-x-3 text-sm">
            <Phone className="w-4 h-4 text-gray-400" />
            <span className="text-gray-300">{user.phone}</span>
          </div>
        )}
        
        <div className="flex items-center space-x-3 text-sm">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-gray-300">Joined {joinDate}</span>
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
            <div className="text-2xl font-bold text-blue-400">{stats.meetings}</div>
            <div className="text-xs text-gray-400">Meetings</div>
          </div>
          
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">{stats.hours}</div>
            <div className="text-xs text-gray-400">Hours</div>
          </div>
          
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-green-400">{stats.projects}</div>
            <div className="text-xs text-gray-400">Projects</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;

