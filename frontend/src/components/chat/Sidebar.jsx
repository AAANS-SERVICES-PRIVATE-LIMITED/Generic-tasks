import { useState } from 'react'
import './Sidebar.css'
import ConversationList from './ConversationList'

function Sidebar({ isOpen, onToggle, session, userProfile, onSelectChat, onNewChat, refreshTrigger, onLoginClick, onSignUpClick, onLogout, onUpgradeClick, onUsageClick }) {
  const [isSearching, setIsSearching] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  
  const userEmail = session?.user?.email || ''
  const username = userEmail ? userEmail.split('@')[0] : ''

  return (
    <>
      {/* Sidebar */}
      <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
        
        {/* Top: Logo + Toggle */}
        <div className="sidebar-top">
          {/* Logo placeholder (empty for now) */}
          <div className="sidebar-logo">
            <div className="logo-placeholder" />
          </div>
          {isOpen && (
            <button className="sidebar-icon-btn" onClick={onToggle} title="Collapse sidebar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
              </svg>
            </button>
          )}
        </div>

        {isOpen && (
          <div className="sidebar-nav">
            {/* New Chat */}
            <button className="sidebar-nav-item new-chat-item" onClick={onNewChat}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              <span>New chat</span>
            </button>

            {/* Search Chats */}
            <button 
              className={`sidebar-nav-item ${isSearching ? 'active-search' : ''}`}
              onClick={() => setIsSearching(!isSearching)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <span>{isSearching ? 'Hide search' : 'Search chats'}</span>
            </button>

            {/* Projects */}
            <button className="sidebar-nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              <span>Projects</span>
            </button>

            {/* Codex */}
            <button className="sidebar-nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6"/>
                <polyline points="8 6 2 12 8 18"/>
              </svg>
              <span>Codex</span>
            </button>

            {/* More */}
            <button className="sidebar-nav-item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
              </svg>
              <span>More</span>
            </button>

            {/* Search Input field inside the nav list */}
            {isSearching && (
              <div className="sidebar-search-box">
                <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search chats..."
                  className="sidebar-search-input"
                  autoFocus
                />
                <button className="clear-search-btn" onClick={() => { setSearchQuery(''); setIsSearching(false); }} title="Clear search">
                  &times;
                </button>
              </div>
            )}

            {/* Recents */}
            {session && (
              <div className="sidebar-recents">
                <div className="recents-label">Recents</div>
                <ConversationList
                  session={session}
                  onSelectChat={onSelectChat}
                  isOpen={isOpen}
                  refreshTrigger={refreshTrigger}
                  searchQuery={searchQuery}
                />
              </div>
            )}
          </div>
        )}

        {/* Bottom User Profile */}
        {isOpen && (
          <div className="sidebar-bottom">
            {session ? (
              <div className="user-profile-container">
                <button 
                  className="user-profile-btn" 
                  onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                >
                  <div className="user-avatar">
                    {username.charAt(0).toUpperCase()}
                  </div>
                  <div className="user-info">
                    <span className="user-name">{username}</span>
                  </div>
                </button>

                {isProfileMenuOpen && (
                  <div className="profile-menu">
                    <div className="profile-menu-header">
                      <div className="user-avatar-small">
                        {username.charAt(0).toUpperCase()}
                      </div>
                      <div className="menu-user-info">
                        <span className="menu-user-name">{username}</span>
                        <span className="menu-user-plan">{userProfile?.subscription ? userProfile.subscription.charAt(0).toUpperCase() + userProfile.subscription.slice(1) : 'Free'}</span>
                      </div>
                    </div>
                    
                    <div className="profile-menu-divider"></div>
                    
                    <button className="profile-menu-item" onClick={() => {
                      setIsProfileMenuOpen(false);
                      if (onUpgradeClick) onUpgradeClick();
                    }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                      </svg>
                      Upgrade plan
                    </button>
                    
                    <button className="profile-menu-item" onClick={() => {
                      setIsProfileMenuOpen(false);
                      if (onUsageClick) onUsageClick();
                    }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="20" x2="18" y2="10" />
                        <line x1="12" y1="20" x2="12" y2="4" />
                        <line x1="6" y1="20" x2="6" y2="14" />
                      </svg>
                      Use status
                    </button>
                    
                    <button className="profile-menu-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                      Profile
                    </button>
                    
                    <button className="profile-menu-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                      </svg>
                      Settings
                    </button>
                    
                    <div className="profile-menu-divider"></div>
                    
                    <button className="profile-menu-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                      </svg>
                      Help
                    </button>
                    
                    <button className="profile-menu-item" onClick={onLogout}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                      </svg>
                      Log out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="auth-buttons-bottom">
                <button className="btn-login" onClick={onLoginClick}>Log in</button>
                <button className="btn-signup" onClick={onSignUpClick}>Sign up</button>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Collapsed: show toggle button in top-left of main */}
      {!isOpen && (
        <div className="sidebar-collapsed-icons">
          <button className="sidebar-icon-btn" onClick={onToggle} title="Expand sidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </button>
          <button className="sidebar-icon-btn" onClick={onNewChat} title="New chat">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
          </button>
        </div>
      )}
    </>
  )
}

export default Sidebar
