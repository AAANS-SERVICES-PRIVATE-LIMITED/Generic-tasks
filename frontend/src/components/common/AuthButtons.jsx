import React from 'react';
import './AuthButtons.css';

const AuthButtons = ({ session, onLogout, onLoginClick, onSignUpClick }) => {
  if (session) {
    return (
      <div className="auth-buttons-container">
        <span className="user-email">{session.user.email}</span>
        <button className="auth-btn logout-btn" onClick={onLogout}>
          Log out
        </button>
      </div>
    );
  }

  return (
    <div className="auth-buttons-container">
      <button className="auth-btn login-btn" onClick={onLoginClick}>
        Log in
      </button>
      <button className="auth-btn signup-btn" onClick={onSignUpClick}>
        Sign up
      </button>
    </div>
  );
};
 
export default AuthButtons;
