import React from 'react';
import './UsageStatus.css';

export default function UsageStatus({ onClose, userProfile, onUpgradeClick }) {
  const currentPlan = userProfile?.subscription || 'free';
  const messageCount = userProfile?.message_count || 0;
  const messageLimit = userProfile?.message_limit;

  // Calculate percentage used
  const isUnlimited = messageLimit === null;
  const percentage = isUnlimited ? 0 : Math.min(100, Math.round((messageCount / messageLimit) * 100));

  // Get next month reset date string
  const getNextMonthResetDate = () => {
    const nextMonth = new Date();
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    nextMonth.setDate(1);
    return nextMonth.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="usage-modal-overlay" onClick={onClose}>
      <div className="usage-modal-content" onClick={(e) => e.stopPropagation()}>
        
        {/* Close Button */}
        <button className="usage-modal-close" onClick={onClose} title="Close dashboard">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Dashboard Title */}
        <h2 className="usage-modal-title">Use Status</h2>

        {/* Usage Card Content */}
        <div className="usage-dashboard-card">
          <div className="usage-header-section">
            <div className="plan-badge-wrapper">
              <span className={`plan-badge-large ${currentPlan}`}>
                {currentPlan.toUpperCase()} PLAN
              </span>
            </div>
            <p className="usage-subtitle">Your monthly AI message and resource usage</p>
          </div>

          <div className="usage-stats-section">
            <div className="stats-header">
              <span className="stats-label">Monthly Usage</span>
              <span className="stats-values">
                {isUnlimited ? (
                  <span className="unlimited-text">∞ chats used</span>
                ) : (
                  <span><strong>{messageCount}</strong> / {messageLimit} chats used</span>
                )}
              </span>
            </div>

            {/* Glowing Gradient Progress Bar */}
            {!isUnlimited && (
              <div className="progress-bar-container">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${percentage}%` }}
                >
                  <div className="progress-bar-glow" />
                </div>
              </div>
            )}

            {isUnlimited ? (
              <p className="progress-subtext">You have unlimited usage under the Pro plan. Thank you for subscribing!</p>
            ) : (
              <div className="progress-meta">
                <span className="percentage-text">{percentage}% of your limit reached</span>
                <span className="reset-date-text">Resets on {getNextMonthResetDate()}</span>
              </div>
            )}
          </div>

          {/* Promotion / Action Section */}
          {currentPlan !== 'pro' && (
            <div className="usage-promo-box">
              <div className="promo-details">
                <h4>Running out of chats?</h4>
                <p>Unlock advanced reasoning, frontier AI models, and higher usage limits.</p>
              </div>
              <button className="promo-btn" onClick={() => {
                onClose();
                if (onUpgradeClick) onUpgradeClick();
              }}>
                Upgrade Plan
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
