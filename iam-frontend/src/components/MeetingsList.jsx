import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Search, Calendar, FileText, Play, Trash2, SortAsc, SortDesc } from 'lucide-react';
import useToast from '../hooks/useToast';

const MeetingsList = () => {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);

  const { showError, showSuccess } = useToast();

  useEffect(() => {
    fetchMeetings();
  }, [sortBy, sortOrder, searchTerm]);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        sort_by: sortBy,
        order: sortOrder,
        search: searchTerm
      });
      
      const response = await fetch(`/api/meetings?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setMeetings(data.meetings);
      } else {
        console.error('Failed to fetch meetings:', data.error);
        showError('Failed to load meetings. Please refresh the page.');
      }
    } catch (error) {
      console.error('Error fetching meetings:', error);
      showError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteMeeting = async (meetingId) => {
    if (!confirm('Are you sure you want to delete this meeting?')) {
      return;
    }

    try {
      const response = await fetch(`/api/meetings/${meetingId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setMeetings(meetings.filter(m => m.id !== meetingId));
        if (selectedMeeting && selectedMeeting.id === meetingId) {
          setSelectedMeeting(null);
        }
        showSuccess('Meeting deleted successfully');
      } else {
        showError('Failed to delete meeting: ' + data.error);
      }
    } catch (error) {
      console.error('Error deleting meeting:', error);
      showError('Network error while deleting meeting. Please try again.');
    }
  };

  const playAudio = async (meeting) => {
    try {
      // Get audio from IndexedDB
      const audioBlob = await getAudioFromIndexedDB(meeting.local_audio_id);
      if (audioBlob) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
          setPlayingAudio(null);
          URL.revokeObjectURL(audioUrl);
        };
        
        audio.play();
        setPlayingAudio(meeting.id);
      } else {
        showError('Audio file not found in local storage');
      }
    } catch (error) {
      console.error('Error playing audio:', error);
      showError('Error playing audio. Please try again.');
    }
  };

  const getAudioFromIndexedDB = (audioId) => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('IAM_AudioDB', 1);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction(['audioRecordings'], 'readonly');
        const store = transaction.objectStore('audioRecordings');
        
        const getRequest = store.get(parseInt(audioId));
        
        getRequest.onsuccess = () => {
          const result = getRequest.result;
          resolve(result ? result.blob : null);
        };
        
        getRequest.onerror = () => reject(getRequest.error);
      };
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-lg">Loading meetings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-card p-6 rounded-lg border">
        <h2 className="text-2xl font-bold mb-4">Your Meetings</h2>
        
        {/* Search and Sort Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Search meetings..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => toggleSort('date')}
              className="flex items-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              Date
              {sortBy === 'date' && (
                sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
              )}
            </Button>
            
            <Button
              variant="outline"
              onClick={() => toggleSort('title')}
              className="flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Title
              {sortBy === 'title' && (
                sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Meetings List */}
        {meetings.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No meetings found. Record your first meeting to get started!
          </div>
        ) : (
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <div
                key={meeting.id}
                className="border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-2">{meeting.title}</h3>
                    <p className="text-sm text-muted-foreground mb-2">
                      {formatDate(meeting.date)}
                    </p>
                    <p className="text-sm text-foreground line-clamp-2">
                      {meeting.transcription_text ? 
                        meeting.transcription_text.substring(0, 150) + '...' : 
                        'Transcription not available'
                      }
                    </p>
                  </div>
                  
                  <div className="flex gap-2 ml-4">
                    {meeting.local_audio_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => playAudio(meeting)}
                        disabled={playingAudio === meeting.id}
                        className="flex items-center gap-1"
                      >
                        <Play className="w-4 h-4" />
                        {playingAudio === meeting.id ? 'Playing...' : 'Play'}
                      </Button>
                    )}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedMeeting(meeting)}
                      className="flex items-center gap-1"
                    >
                      <FileText className="w-4 h-4" />
                      View
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteMeeting(meeting.id)}
                      className="flex items-center gap-1 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Meeting Detail Modal */}
      {selectedMeeting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-card rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold">{selectedMeeting.title}</h2>
                <p className="text-muted-foreground">{formatDate(selectedMeeting.date)}</p>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelectedMeeting(null)}
              >
                Close
              </Button>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Transcription</h3>
              <div className="bg-muted p-4 rounded-lg">
                <p className="whitespace-pre-wrap">
                  {selectedMeeting.transcription_text || 'No transcription available'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeetingsList;

