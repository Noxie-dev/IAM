import React from 'react';
import { BarChart3, TrendingUp, Users, Clock } from 'lucide-react';

const analyticsData = {
  meetingsThisMonth: 24,
  totalHours: 48,
  averageDuration: 120, // minutes
  participationRate: 87,
  monthlyTrend: '+12%',
  mostActiveDay: 'Tuesday',
  peakTime: '2:00 PM',
  teamGrowth: '+3 members'
};

const meetingTypes = [
  { type: 'Team Sync', count: 8, percentage: 33 },
  { type: 'Project Review', count: 6, percentage: 25 },
  { type: 'Planning', count: 5, percentage: 21 },
  { type: 'Training', count: 3, percentage: 13 },
  { type: 'Other', count: 2, percentage: 8 }
];

const weeklyActivity = [
  { day: 'Mon', meetings: 3, hours: 6 },
  { day: 'Tue', meetings: 5, hours: 10 },
  { day: 'Wed', meetings: 4, hours: 8 },
  { day: 'Thu', meetings: 6, hours: 12 },
  { day: 'Fri', meetings: 3, hours: 6 },
  { day: 'Sat', meetings: 1, hours: 2 },
  { day: 'Sun', meetings: 2, hours: 4 }
];

const TeamAnalytics = () => {
  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-blue-400 mb-2">
            {analyticsData.meetingsThisMonth}
          </div>
          <div className="text-sm text-gray-400">Meetings This Month</div>
          <div className="text-xs text-green-400 mt-1">{analyticsData.monthlyTrend}</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-purple-400 mb-2">
            {analyticsData.totalHours}h
          </div>
          <div className="text-sm text-gray-400">Total Hours</div>
          <div className="text-xs text-gray-400 mt-1">This Month</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-green-400 mb-2">
            {analyticsData.averageDuration}m
          </div>
          <div className="text-sm text-gray-400">Avg Duration</div>
          <div className="text-xs text-gray-400 mt-1">Per Meeting</div>
        </div>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 text-center">
          <div className="text-3xl font-bold text-yellow-400 mb-2">
            {analyticsData.participationRate}%
          </div>
          <div className="text-sm text-gray-400">Participation Rate</div>
          <div className="text-xs text-green-400 mt-1">+5% from last month</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Meeting Types */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Meeting Types
          </h3>
          
          <div className="space-y-4">
            {meetingTypes.map((item, index) => (
              <div key={index} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">{item.type}</span>
                  <span className="text-white font-medium">{item.count}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Activity */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Weekly Activity
          </h3>
          
          <div className="space-y-3">
            {weeklyActivity.map((day, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-300 w-8">{day.day}</span>
                  <div className="flex space-x-2">
                    <div className="w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-xs text-white">{day.meetings}</span>
                    </div>
                    <span className="text-xs text-gray-400">meetings</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-sm text-gray-300">{day.hours}h</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Users className="w-5 h-5 mr-2" />
          Team Insights
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-white/5 rounded-lg">
            <div className="text-lg font-semibold text-blue-400 mb-2">
              {analyticsData.mostActiveDay}
            </div>
            <div className="text-sm text-gray-400">Most Active Day</div>
          </div>
          
          <div className="text-center p-4 bg-white/5 rounded-lg">
            <div className="text-lg font-semibold text-purple-400 mb-2">
              {analyticsData.peakTime}
            </div>
            <div className="text-sm text-gray-400">Peak Meeting Time</div>
          </div>
          
          <div className="text-center p-4 bg-white/5 rounded-lg">
            <div className="text-lg font-semibold text-green-400 mb-2">
              {analyticsData.teamGrowth}
            </div>
            <div className="text-sm text-gray-400">Team Growth</div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">💡 Recommendations</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
            <p className="text-sm text-gray-300">
              Consider shorter meetings - your average duration is above the recommended 90 minutes.
            </p>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-purple-400 rounded-full mt-2"></div>
            <p className="text-sm text-gray-300">
              Tuesday is your most productive day - schedule important meetings then.
            </p>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
            <p className="text-sm text-gray-300">
              Great participation rate! Keep up the team engagement.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamAnalytics;



