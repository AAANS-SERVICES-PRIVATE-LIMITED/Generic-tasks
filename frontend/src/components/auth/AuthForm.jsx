import { useState } from 'react';
import './AuthForm.css';
import { authApi } from '../../api/authApi';

export default function AuthForm({ view = 'sign_in', onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      if (view === 'sign_up') {
        await authApi.signUp(email, password);
        setMessage('Check your email for the confirmation link!');
      } else {
        await authApi.signIn(email, password);
        if (onSuccess) onSuccess();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2>{view === 'sign_up' ? 'Create Account' : 'Sign In'}</h2>
      <form onSubmit={handleAuth}>
        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : (view === 'sign_up' ? 'Sign Up' : 'Sign In')}
        </button>
      </form>
    </div>
  );
}
