import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import config from '../api/config';
import '../Auth.css';

function Register() {
  const [formData, setFormData] = useState({ email: '', password: '', name: '', accountType: 'general_user' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${config.API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.errors?.[0]?.msg || 'Registration failed');
      }

      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h1>MedicaLLM</h1>
        <h2>Create your account</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              placeholder="Enter your full name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="input-group">
            <label>Account Type</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px' }}>
              <label
                style={{
                  padding: '12px',
                  border: formData.accountType === 'general_user' ? '2px solid #10a37f' : '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: formData.accountType === 'general_user' ? 'rgba(16,163,127,0.08)' : 'transparent',
                  textAlign: 'center',
                  fontWeight: '500',
                  fontSize: '14px',
                  position: 'relative'
                }}
              >
                <input
                  type="radio"
                  name="accountType"
                  value="general_user"
                  checked={formData.accountType === 'general_user'}
                  onChange={(e) => setFormData({ ...formData, accountType: e.target.value })}
                  style={{ position: 'absolute', opacity: 0 }}
                />
                Patient
              </label>
              <label
                style={{
                  padding: '12px',
                  border: formData.accountType === 'healthcare_professional' ? '2px solid #10a37f' : '1px solid rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: formData.accountType === 'healthcare_professional' ? 'rgba(16,163,127,0.08)' : 'transparent',
                  textAlign: 'center',
                  fontWeight: '500',
                  fontSize: '14px',
                  position: 'relative'
                }}
              >
                <input
                  type="radio"
                  name="accountType"
                  value="healthcare_professional"
                  checked={formData.accountType === 'healthcare_professional'}
                  onChange={(e) => setFormData({ ...formData, accountType: e.target.value })}
                  style={{ position: 'absolute', opacity: 0 }}
                />
                Healthcare Professional
              </label>
            </div>
          </div>

          <div className="input-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Minimum 6 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              minLength={6}
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Sign up'}
          </button>
        </form>

        <p className="toggle-text">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
