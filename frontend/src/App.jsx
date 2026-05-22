import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import SubscriptionPage from './pages/SubscriptionPage';
import { useAuth } from './hooks/useAuth';
import './index.css';

function App() {
  const auth = useAuth();

  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          {/* Main chat page — also handles /chat/123 */}
          <Route path="/" element={<ChatPage auth={auth} />} />
          <Route path="/chat/:chatId" element={<ChatPage auth={auth} />} />

          {/* Login page — redirect to chat if already logged in */}
          <Route
            path="/login"
            element={auth.session ? <Navigate to="/" replace /> : <LoginPage />}
          />

          {/* Subscription page — redirect to login if not logged in */}
          <Route
            path="/subscription"
            element={auth.session ? <SubscriptionPage auth={auth} /> : <Navigate to="/login" replace />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
