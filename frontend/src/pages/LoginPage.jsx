import React, { useState } from 'react';
import AuthForm from '../components/auth/AuthForm';
import './LoginPage.css';

export default function LoginPage() {
  const [view, setView] = useState('sign_in');

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>ChatGpt</h1>
          <p>The smartest way to chat.</p>
        </div>
        
        <AuthForm view={view} />

        <div className="auth-toggle">
          <button onClick={() => setView(view === 'sign_in' ? 'sign_up' : 'sign_in')}>
            {view === 'sign_in' 
              ? "Don't have an account? Sign Up" 
              : "Already have an account? Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}
