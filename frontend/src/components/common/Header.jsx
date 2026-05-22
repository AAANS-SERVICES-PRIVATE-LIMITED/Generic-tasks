import React from 'react';
import './Header.css';

function Header({ isSidebarOpen, onLogout, onLoginClick, onSignUpClick, session }) {
  return (
    <header className={`header ${!isSidebarOpen ? 'sidebar-closed' : ''}`}>
      {/* Center: Model name dropdown (ChatGPT style) */}
      <div className="header-center">
        <button className="model-dropdown-trigger">
          <span className="model-name">ChatGpt</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
      </div>

      {/* Right: Bell icon */}
      <div className="header-right">
        <button className="header-icon-btn" title="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        </button>
      </div>
    </header>
  );
}

export default Header;
