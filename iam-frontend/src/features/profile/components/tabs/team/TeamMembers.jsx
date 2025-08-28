import React, { useState } from 'react';
import { UserPlus, MoreVertical, Crown, Shield, User } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../../../../../components/ui/avatar';
import { Badge } from '../../../../../components/ui/badge';
import { Button } from '../../../../../components/ui/button';

const initialMembers = [
  {
    id: 1,
    name: 'Sarah Chen',
    email: 'sarah.chen@company.com',
    role: 'Admin',
    status: 'active',
    avatar: null,
    joinDate: '2022-01-15'
  },
  {
    id: 2,
    name: 'Mike Rodriguez',
    email: 'mike.rodriguez@company.com',
    role: 'Manager',
    status: 'active',
    avatar: null,
    joinDate: '2022-03-20'
  },
  {
    id: 3,
    name: 'Emily Watson',
    email: 'emily.watson@company.com',
    role: 'Member',
    status: 'active',
    avatar: null,
    joinDate: '2022-06-10'
  },
  {
    id: 4,
    name: 'David Kim',
    email: 'david.kim@company.com',
    role: 'Member',
    status: 'pending',
    avatar: null,
    joinDate: '2023-01-05'
  }
];

const TeamMembers = () => {
  const [members, setMembers] = useState(initialMembers);
  const [inviteEmail, setInviteEmail] = useState('');

  const getRoleIcon = (role) => {
    switch (role) {
      case 'Admin': return <Crown className="w-4 h-4 text-yellow-400" />;
      case 'Manager': return <Shield className="w-4 h-4 text-blue-400" />;
      default: return <User className="w-4 h-4 text-gray-400" />;
    }
  };

  const getRoleBadge = (role) => {
    const colors = {
      Admin: 'bg-yellow-500/20 text-yellow-300',
      Manager: 'bg-blue-500/20 text-blue-300',
      Member: 'bg-gray-500/20 text-gray-300'
    };
    return colors[role] || colors.Member;
  };

  const getStatusBadge = (status) => {
    return status === 'active' 
      ? 'bg-green-500/20 text-green-300' 
      : 'bg-orange-500/20 text-orange-300';
  };

  const handleInvite = () => {
    if (!inviteEmail) return;
    
    const newMember = {
      id: Date.now(),
      name: inviteEmail.split('@')[0].replace('.', ' '),
      email: inviteEmail,
      role: 'Member',
      status: 'pending',
      avatar: null,
      joinDate: new Date().toISOString().split('T')[0]
    };
    
    setMembers([...members, newMember]);
    setInviteEmail('');
  };

  const removeMember = (memberId) => {
    setMembers(members.filter(m => m.id !== memberId));
  };

  return (
    <div className="space-y-6">
      {/* Invite New Member */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <UserPlus className="w-5 h-5 mr-2" />
          Invite Team Member
        </h3>
        
        <div className="flex space-x-3">
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="Enter email address"
            className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-gray-400"
          />
          <Button
            onClick={handleInvite}
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
          >
            Send Invite
          </Button>
        </div>
      </div>

      {/* Team Members List */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-6">Team Members ({members.length})</h3>
        
        <div className="space-y-4">
          {members.map(member => (
            <div key={member.id} className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10">
              <div className="flex items-center space-x-4">
                <Avatar className="w-12 h-12">
                  <AvatarImage src={member.avatar} alt={member.name} />
                  <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <h4 className="font-semibold text-white">{member.name}</h4>
                    {getRoleIcon(member.role)}
                  </div>
                  <p className="text-sm text-gray-400">{member.email}</p>
                  <p className="text-xs text-gray-500">Joined {new Date(member.joinDate).toLocaleDateString()}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Badge className={getRoleBadge(member.role)}>
                  {member.role}
                </Badge>
                
                <Badge className={getStatusBadge(member.status)}>
                  {member.status}
                </Badge>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeMember(member.id)}
                  className="text-gray-400 hover:text-red-400"
                >
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Team Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-blue-400 mb-2">
            {members.filter(m => m.status === 'active').length}
          </div>
          <div className="text-sm text-gray-400">Active Members</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-orange-400 mb-2">
            {members.filter(m => m.status === 'pending').length}
          </div>
          <div className="text-sm text-gray-400">Pending Invites</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-green-400 mb-2">
            {members.filter(m => m.role === 'Admin' || m.role === 'Manager').length}
          </div>
          <div className="text-sm text-gray-400">Admins & Managers</div>
        </div>
      </div>
    </div>
  );
};

export default TeamMembers;

