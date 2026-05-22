import React from 'react';
import Subscription from '../components/common/Subscription';
import './SubscriptionPage.css';

export default function SubscriptionPage({ auth }) {
  const { session, userProfile, refreshProfile } = auth;

  const handleBack = () => {
    window.history.back();
  };

  return (
    <div className="subscription-page">
      <div className="subscription-page-header">
        <button className="back-btn" onClick={handleBack}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Back to Chat
        </button>
        <h1>Upgrade Your Plan</h1>
      </div>

      <Subscription
        onClose={handleBack}
        session={session}
        userProfile={userProfile}
        onSubscriptionUpdated={refreshProfile}
        isPage={true}
      />
    </div>
  );
}
