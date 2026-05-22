import React, { useState } from 'react';
import { authApi } from '../../api/authApi';
import './Subscription.css';

export default function Subscription({ onClose, session, userProfile, onSubscriptionUpdated, isPage = false }) {
  const [loading, setLoading] = useState(false);
  const currentPlan = userProfile?.subscription || 'free';

  const handleUpgrade = async (plan) => {
    if (!session?.user?.id) {
      alert("Please log in to upgrade your subscription!");
      return;
    }
    setLoading(true);
    try {
      await authApi.upgradeSubscription(session.user.id, plan);
      if (onSubscriptionUpdated) onSubscriptionUpdated();
      alert(`Successfully updated to the ${plan.toUpperCase()} plan!`);
      if (onClose) onClose();
    } catch (e) {
      console.error(e);
      alert("Failed to update subscription. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const cards = (
    <div className="upgrade-cards-container">
      {/* Free Plan */}
      <div className={`upgrade-card free-plan ${currentPlan === 'free' ? 'active-plan' : ''}`}>
        <div className="plan-header"><h3>Free</h3></div>
        <div className="plan-price">
          <span className="currency">₹</span>
          <span className="amount">0</span>
          <span className="period">/ month</span>
        </div>
        <p className="plan-subtitle">See what AI can do</p>
        <button
          className={`plan-btn ${currentPlan === 'free' ? 'current-plan-btn' : ''}`}
          disabled={currentPlan === 'free' || loading}
          onClick={() => handleUpgrade('free')}
        >
          {currentPlan === 'free' ? 'Your current plan' : 'Downgrade to Free'}
        </button>
        <ul className="plan-features">
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Core model</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>10 chats per month</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Limited image creation</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Limited memory</li>
        </ul>
      </div>

      {/* Plus Plan */}
      <div className={`upgrade-card plus-plan ${currentPlan === 'plus' ? 'active-plan' : ''}`}>
        <div className="plan-header">
          <h3>Plus</h3>
          <span className="popular-badge">POPULAR</span>
        </div>
        <div className="plan-price">
          <span className="currency">₹</span>
          <span className="amount">150</span>
          <span className="period">/ month (inclusive of GST)</span>
        </div>
        <p className="plan-subtitle">Unlock the full experience</p>
        <button
          className={`plan-btn upgrade-plus-btn ${currentPlan === 'plus' ? 'current-plan-btn' : ''}`}
          disabled={currentPlan === 'plus' || loading}
          onClick={() => handleUpgrade('plus')}
        >
          {currentPlan === 'plus' ? 'Your current plan' : 'Upgrade to Plus'}
        </button>
        <ul className="plan-features">
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Advanced models</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>100 chats per month</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Advanced image creation with Thinking</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Expanded memory across chats</li>
        </ul>
      </div>

      {/* Pro Plan */}
      <div className={`upgrade-card pro-plan ${currentPlan === 'pro' ? 'active-plan' : ''}`}>
        <div className="plan-header"><h3>Pro</h3></div>
        <div className="plan-price">
          <span className="currency">₹</span>
          <span className="amount">500</span>
          <span className="period">/ month (inclusive of GST)</span>
        </div>
        <p className="plan-subtitle">Maximize your productivity</p>
        <button
          className={`plan-btn upgrade-pro-btn ${currentPlan === 'pro' ? 'current-plan-btn' : ''}`}
          disabled={currentPlan === 'pro' || loading}
          onClick={() => handleUpgrade('pro')}
        >
          {currentPlan === 'pro' ? 'Your current plan' : 'Upgrade to Pro'}
        </button>
        <ul className="plan-features">
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Everything in Plus, and:</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Unlimited chats</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Frontier Pro model</li>
          <li><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12l5 5L20 7" /></svg>Maximum deep research</li>
        </ul>
      </div>
    </div>
  );

  // Full page mode — no overlay, no close button
  if (isPage) {
    return <>{cards}</>;
  }

  // Modal mode — with overlay and close button
  return (
    <div className="upgrade-modal-overlay" onClick={onClose}>
      <div className="upgrade-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="upgrade-modal-close" onClick={onClose}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <h2 className="upgrade-modal-title">Upgrade your plan</h2>
        {cards}
      </div>
    </div>
  );
}
