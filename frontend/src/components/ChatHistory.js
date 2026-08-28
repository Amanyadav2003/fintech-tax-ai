import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import '../styles/ChatHistory.css';

const ChatHistory = ({ isOpen, onClose, sessionId }) => {
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(sessionId);
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (isOpen) {
      fetchSessions();
      fetchAnalytics();
    }
  }, [isOpen]);

  const fetchMessages = useCallback(async (sessionId) => {
    setLoading(true);
    try {
      const response = await api.get('tax/history/chat', {
        params: {
          session_id: sessionId,
          limit: 100,
          module_filter: filter !== 'all' ? filter : undefined
        }
      });
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    if (currentSession) {
      fetchMessages(currentSession);
    }
  }, [currentSession, fetchMessages]);

  const fetchSessions = async () => {
    try {
      const response = await api.get('tax/history/sessions');
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('tax/history/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const deleteMessage = async (messageId) => {
    try {
      await api.delete(`tax/history/chat/${messageId}`);
      fetchMessages(currentSession);
    } catch (error) {
      console.error('Error deleting message:', error);
    }
  };

  const deleteSession = async (sessionId) => {
    if (window.confirm('Delete entire chat session?')) {
      try {
        await api.delete(`tax/history/session/${sessionId}`);
        fetchSessions();
        setMessages([]);
      } catch (error) {
        console.error('Error deleting session:', error);
      }
    }
  };

  const exportHistory = async () => {
    try {
      const response = await api.post('tax/history/export', {});
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
    } catch (error) {
      console.error('Error exporting history:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chat-history-modal">
      <div className="chat-history-content">
        <button className="close-btn" onClick={onClose}>✕</button>
        
        <h2>📚 Chat History & Analytics</h2>
        
        {/* Analytics Section */}
        {analytics && (
          <div className="analytics-section">
            <h3>Your Chat Activity</h3>
            <div className="analytics-grid">
              <div className="stat">
                <div className="stat-value">{analytics.total_conversations}</div>
                <div className="stat-label">Conversations</div>
              </div>
              <div className="stat">
                <div className="stat-value">{analytics.total_messages}</div>
                <div className="stat-label">Messages</div>
              </div>
              <div className="stat">
                <div className="stat-value">{analytics.user_engagement_score}%</div>
                <div className="stat-label">Engagement</div>
              </div>
            </div>
            
            {analytics.popular_modules.length > 0 && (
              <div className="interests">
                <h4>Your Interests</h4>
                <div className="tag-cloud">
                  {analytics.popular_modules.map((module, idx) => (
                    <span key={idx} className="tag">{module}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Sessions Section */}
        <div className="sessions-section">
          <h3>Sessions</h3>
          <div className="sessions-list">
            {sessions.length === 0 ? (
              <p className="empty">No chat sessions yet</p>
            ) : (
              sessions.map((session, idx) => (
                <div 
                  key={idx}
                  className={`session-item ${currentSession === session.session_id ? 'active' : ''}`}
                >
                  <button
                    className="session-btn"
                    onClick={() => setCurrentSession(session.session_id)}
                  >
                    <div className="session-header">
                      <span className="session-date">
                        {new Date(session.first_message_time).toLocaleDateString()}
                      </span>
                      <span className="message-count">{session.message_count} messages</span>
                    </div>
                    <small>
                      {new Date(session.last_message_time).toLocaleTimeString()}
                    </small>
                  </button>
                  <button
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.session_id);
                    }}
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Messages Section */}
        {messages.length > 0 && (
          <div className="messages-section">
            <div className="messages-header">
              <h3>Messages</h3>
              <select 
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="module-filter"
              >
                <option value="all">All Modules</option>
                <option value="income_tax">Income Tax</option>
                <option value="gst">GST</option>
                <option value="accounting">Accounting</option>
              </select>
            </div>
            
            {loading ? (
              <p>Loading messages...</p>
            ) : (
              <div className="messages-list">
                {messages.map((msg) => (
                  <div key={msg.id} className={`message ${msg.message_type}`}>
                    <div className="message-content">
                      <div className="message-text">{msg.message_content}</div>
                      {msg.operating_mode && (
                        <div className="message-meta">
                          <span className="mode-badge">{msg.operating_mode}</span>
                          {msg.tax_module && (
                            <span className="module-badge">{msg.tax_module}</span>
                          )}
                        </div>
                      )}
                      <small className="timestamp">
                        {new Date(msg.created_at).toLocaleString()}
                      </small>
                    </div>
                    {msg.message_type === 'bot' && (
                      <button
                        className="delete-msg-btn"
                        onClick={() => deleteMessage(msg.id)}
                        title="Delete message"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="action-buttons">
          <button className="export-btn" onClick={exportHistory}>
            📥 Export History
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatHistory;
