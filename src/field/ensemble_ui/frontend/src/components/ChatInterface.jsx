import React, { useState, useRef, useEffect } from 'react';
import { sendMessageToAgent } from '../services/api';

function ChatInterface({ agentId, messages = [] }) {
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      await sendMessageToAgent(agentId, newMessage);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mt-3 p-3 bg-cyan-500/20 border-l-4 border-cyan-500 rounded backdrop-blur-sm">
      <p className="font-semibold text-cyan-200 mb-2">💬 Conversation</p>

      {/* Messages display */}
      <div className="space-y-2 max-h-64 overflow-y-auto mb-3">
        {messages.length === 0 ? (
          <p className="text-xs text-cyan-300 italic">No messages yet. Start a conversation with the agent!</p>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-2 rounded text-xs ${
                msg.sender === 'user'
                  ? 'bg-blue-500/30 text-blue-100 ml-4'
                  : 'bg-cyan-500/30 text-cyan-100 mr-4'
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <span className="font-semibold">
                  {msg.sender === 'user' ? '👤 You' : '🤖 Agent'}
                </span>
                {msg.timestamp && (
                  <span className="text-xs opacity-70">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <p className="whitespace-pre-wrap">{msg.message}</p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message input */}
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Send a message to the agent..."
          className="flex-1 px-3 py-2 bg-white/5 border border-white/20 rounded text-white placeholder-gray-400 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-400"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={!newMessage.trim() || sending}
          className="px-4 py-2 bg-cyan-600 text-white rounded hover:bg-cyan-700 transition-colors text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {sending ? '⏳' : '📤'} Send
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;
