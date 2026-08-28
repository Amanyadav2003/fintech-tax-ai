import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import './chat.css';
import api from '../services/api';
import ChatHistory from './ChatHistory';
import { containsPanOrAadhaar, PII_FIELD_MESSAGE } from '../utils/piiValidator';

const messageVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
};

function Chat({ analysis, onClose }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: 'Hi! 👋 I\'m your AI tax assistant. Ask me anything about your tax analysis, deductions, strategies, or filing requirements. I\'m here to help!',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    if (containsPanOrAadhaar(inputValue)) {
      setError(PII_FIELD_MESSAGE);
      return;
    }

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);
    setError('');

    try {
      // Send to backend
      const response = await api.post('tax/chat', {
        message: inputValue,
        context: { session_id: sessionId, ...analysis }
      });

      const responseData = response.data;
      const botMessage = {
        id: messages.length + 2,
        type: 'bot',
        text: responseData.response || 'I understand your question. Let me help you with that.',
        mode: responseData.mode,
        module: responseData.module,
        response_type: responseData.response_type,
        next_steps: responseData.next_steps,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = {
        id: messages.length + 2,
        type: 'bot',
        text: 'Sorry, I encountered an error. Please try again. Make sure you have completed a tax analysis first.',
        isError: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setError('Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <motion.div 
        className="chat-container"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="chat-header">
          <div className="chat-title">
            <div className="chat-icon">🤖</div>
            <div>
              <h2>Tax Assistant Chat</h2>
              <p>Ask questions about your tax analysis</p>
            </div>
          </div>
          <div className="chat-header-buttons">
            <button 
              className="history-btn"
              onClick={() => setShowHistory(true)}
              title="View chat history"
            >
              📚 History
            </button>
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            className={`message ${msg.type} ${msg.isError ? 'error' : ''}`}
            variants={messageVariants}
            initial="hidden"
            animate="visible"
          >
            <div className="message-avatar">
              {msg.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <p className="message-text">{msg.text}</p>
            {msg.mode && (
              <div className="message-meta">
                <span className="mode-badge">{msg.mode}</span>
                {msg.module && <span className="module-badge">{msg.module}</span>}
              </div>
            )}
            {msg.next_steps && msg.next_steps.length > 0 && (
              <div className="next-steps">
                <strong>Next steps:</strong>
                <ul>
                  {msg.next_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
            )}
            <span className="message-time">
              {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </motion.div>
      ))}
      {loading && (
        <motion.div
          className="message bot loading"
          variants={messageVariants}
          initial="hidden"
          animate="visible"
        >
          <div className="message-avatar">🤖</div>
          <div className="message-content">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </motion.div>
      )}
      <div ref={messagesEndRef} />
    </div>

    <form className="chat-input-form" onSubmit={handleSendMessage}>
      {error && <div className="chat-error">{error}</div>}
      <div className="input-wrapper">
        <input
          type="text"
          className="chat-input"
          placeholder="Ask me about your taxes, deductions, filing, strategies..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={loading}
        />
        <button 
          type="submit" 
          className="send-btn"
          disabled={loading || !inputValue.trim()}
          title="Send message"
        >
          {loading ? '⏳' : '➤'}
        </button>
      </div>
    </form>
  </motion.div>
  <ChatHistory 
    isOpen={showHistory}
    onClose={() => setShowHistory(false)}
    sessionId={sessionId}
  />
  </>
);
}

export default Chat;