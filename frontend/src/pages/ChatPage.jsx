import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/chat/Sidebar';
import Header from '../components/common/Header';
import DisplayChat from '../components/chat/DisplayChat';
import UsageStatus from '../components/common/UsageStatus';
import './Pages.css';

export default function ChatPage({ auth }) {
  const { session, userProfile, handleLogout, refreshProfile } = auth;
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [selectedChat, setSelectedChat] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  const handleSelectChat = (chat) => {
    setSelectedChat(chat);
  };

  const handleNewChat = () => {
    setSelectedChat(null);
  };

  const handleChatCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="chat-page">
      {/* Usage Status Modal Overlay — still a modal as it's a quick summary */}
      {isUsageModalOpen && (
        <UsageStatus 
          onClose={() => setIsUsageModalOpen(false)}
          userProfile={userProfile}
          onUpgradeClick={() => navigate('/subscription')}
        />
      )}

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
        session={session}
        userProfile={userProfile}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        refreshTrigger={refreshTrigger}
        onLoginClick={() => navigate('/login')}
        onSignUpClick={() => navigate('/login')}
        onLogout={handleLogout}
        onUpgradeClick={() => navigate('/subscription')}
        onUsageClick={() => {
          refreshProfile();
          setIsUsageModalOpen(true);
        }}
      />

      {/* Main content */}
      <div className={`main-content ${!isSidebarOpen ? 'sidebar-hidden' : ''}`}>
        <Header
          isSidebarOpen={isSidebarOpen}
          onLogout={handleLogout}
          onLoginClick={() => navigate('/login')}
          onSignUpClick={() => navigate('/login')}
          session={session}
        />
        <DisplayChat
          chatState={selectedChat ? 'old' : 'new'}
          session={session}
          initialChatId={selectedChat?.id}
          onAuthRequired={() => navigate('/login')}
          onChatCreated={handleChatCreated}
        />
      </div>
    </div>
  );
}
