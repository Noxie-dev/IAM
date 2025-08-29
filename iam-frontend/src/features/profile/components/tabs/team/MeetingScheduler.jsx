import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Users, Sparkles } from 'lucide-react';
import { useGemini } from '../../../hooks/useGemini';
import Modal from '../../../../../components/ui/modal';
import { Button } from '../../../../../components/ui/button';
import { Input } from '../../../../../components/ui/input';

const initialMeetings = [
  { 
    id: 1, 
    title: 'Q4 Product Strategy', 
    datetime: new Date(Date.now() + 1000 * 60 * 60 * 2).toISOString(),
    attendees: ['Sarah Chen', 'Mike Rodriguez']
  },
  { 
    id: 2, 
    title: 'Weekly Team Sync', 
    datetime: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    attendees: ['Team']
  }
];

const Countdown = ({ datetime }) => {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      const diff = new Date(datetime) - new Date();
      if (diff <= 0) {
        setTimeLeft('Meeting Started');
        clearInterval(interval);
        return;
      }
      const h = Math.floor((diff / (1000 * 60 * 60)) % 24).toString().padStart(2, '0');
      const m = Math.floor((diff / 1000 / 60) % 60).toString().padStart(2, '0');
      const s = Math.floor((diff / 1000) % 60).toString().padStart(2, '0');
      setTimeLeft(`${h}h ${m}m ${s}s`);
    }, 1000);
    return () => clearInterval(interval);
  }, [datetime]);

  return (
    <div className="text-sm">
      {timeLeft.includes('Started') ? (
        <span className="text-green-400">🔴 {timeLeft}</span>
      ) : (
        <span className="text-yellow-400">⏰ Starts in {timeLeft}</span>
      )}
    </div>
  );
};

const MeetingScheduler = () => {
  const [meetings, setMeetings] = useState(initialMeetings);
  const [title, setTitle] = useState('');
  const [datetime, setDatetime] = useState('');
  const [attendees, setAttendees] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const { generateContent, loading } = useGemini();

  const handleSchedule = () => {
    if (!title || !datetime) return;
    
    const newMeeting = { 
      id: Date.now(), 
      title, 
      datetime,
      attendees: attendees.split(',').map(a => a.trim()).filter(a => a)
    };
    
    setMeetings([...meetings, newMeeting].sort((a, b) => new Date(a.datetime) - new Date(b.datetime)));
    setTitle('');
    setDatetime('');
    setAttendees('');
  };

  const handleGenerateTitles = async () => {
    if (!prompt) return;
    const response = await generateContent(
      `Generate 5 concise and professional meeting titles based on this description: "${prompt}". 
       Return only the titles, one per line, without numbers or bullet points.`
    );
    setSuggestions(response.split('\n').filter(t => t.trim() !== '').slice(0, 5));
  };

  const selectSuggestion = (suggestion) => {
    setTitle(suggestion.replace(/^[*\-\d\.]\s*/, '').trim());
    setIsModalOpen(false);
    setSuggestions([]);
    setPrompt('');
  };

  return (
    <div className="space-y-6">
      {/* Schedule New Meeting */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Calendar className="w-5 h-5 mr-2" />
          Schedule a Meeting
        </h3>
        
        <div className="space-y-4">
          <div className="flex space-x-2">
            <Input
              placeholder="Meeting title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="flex-1 bg-white/10 border-white/20 text-white placeholder-gray-400"
            />
            <Button
              onClick={() => setIsModalOpen(true)}
              variant="ghost"
              size="sm"
              className="text-purple-400 hover:text-purple-300"
              title="AI Suggest Title"
            >
              <Sparkles className="w-4 h-4" />
            </Button>
          </div>
          
          <Input
            type="datetime-local"
            value={datetime}
            onChange={(e) => setDatetime(e.target.value)}
            className="bg-white/10 border-white/20 text-white"
          />
          
          <Input
            placeholder="Attendees (comma separated)"
            value={attendees}
            onChange={(e) => setAttendees(e.target.value)}
            className="bg-white/10 border-white/20 text-white placeholder-gray-400"
          />
          
          <Button
            onClick={handleSchedule}
            disabled={!title || !datetime}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Schedule Meeting
          </Button>
        </div>
      </div>

      {/* Upcoming Meetings */}
      <div className="bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2" />
          Upcoming Meetings ({meetings.length})
        </h3>
        
        <div className="space-y-4">
          {meetings.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400">No upcoming meetings scheduled</p>
            </div>
          ) : (
            meetings.map(meeting => (
              <div key={meeting.id} className="p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-white mb-1">{meeting.title}</h4>
                    <p className="text-sm text-gray-400 mb-2">
                      📅 {new Date(meeting.datetime).toLocaleDateString()} at {new Date(meeting.datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    {meeting.attendees && meeting.attendees.length > 0 && (
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-400">
                          {meeting.attendees.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                  <Countdown datetime={meeting.datetime} />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* AI Title Suggestion Modal */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        title="✨ AI Meeting Title Suggestions"
      >
        <div className="space-y-4">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe your meeting (e.g., 'Discuss Q4 sales targets with the marketing team')"
            className="w-full h-24 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-gray-400 resize-none"
          />
          
          <Button
            onClick={handleGenerateTitles}
            disabled={loading || !prompt.trim()}
            className="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate Titles'}
          </Button>
          
          {suggestions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-white">Choose a title:</h4>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => selectSuggestion(suggestion)}
                  className="block w-full text-left p-3 rounded-lg bg-white/5 hover:bg-white/10 text-white text-sm transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default MeetingScheduler;



