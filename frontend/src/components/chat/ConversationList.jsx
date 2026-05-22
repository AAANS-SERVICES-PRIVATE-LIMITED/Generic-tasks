import React, { useEffect, useState } from 'react';
import { chatApi } from '../../api/chatApi';
import './Sidebar.css';

const ConversationList = ({ session, onSelectChat, isOpen, refreshTrigger, searchQuery = "" }) => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;

    const getConversations = async () => {
      const data = await chatApi.fetchUserChats(session.user.id);
      setConversations(data);
      setLoading(false);
    };

    getConversations();
  }, [session, refreshTrigger]);

  const handleDelete = async (e, chatId) => {
    e.stopPropagation(); 
    const confirmed = window.confirm("Are you sure you want to delete this chat?");
    if (!confirmed) return;

    const success = await chatApi.deleteChat(chatId, session.user.id);
    if (success) {
      setConversations(prev => prev.filter(c => c.id !== chatId));
    }
  };

  // Filter conversations in real time based on active search queries
  const filteredConversations = conversations.filter(chat => 
    (chat.title || 'Untitled Chat').toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading && isOpen) return <div className="sidebar-loading">Loading...</div>;
  if (!isOpen) return null;

  return (
    <div className="conversation-list">
      {filteredConversations.length === 0 ? (
        <div className="no-chats">
          {searchQuery ? 'No matching chats found' : 'No chats yet'}
        </div>
      ) : (
        filteredConversations.map((chat) => (
          <div 
            key={chat.id} 
            className="conversation-item"
            onClick={() => onSelectChat(chat)}
          >
            <div className="conversation-title">
              {chat.title || 'Untitled Chat'}
            </div>
            <button 
              className="delete-chat-btn" 
              onClick={(e) => handleDelete(e, chat.id)}
              title="Delete chat"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        ))
      )}
    </div>
  );
};

export default ConversationList;
