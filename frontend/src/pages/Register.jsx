import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import config from '../api/config';
import '../Auth.css';

function Register() {
  const [step, setStep] = useState(1); // 1 = form, 2 = verify code
  const [formData, setFormData] = useState({ email: '', password: '', name: '', account_type: 'general_user' });
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) navigate('/chat');
  }, [navigate]);

  const validatePassword = (password) => {
    const errors = [];
    if (password.length < 8) errors.push('At least 8 characters');
    if (!/[A-Z]/.test(password)) errors.push('1 uppercase letter');
    if (!/[a-z]/.test(password)) errors.push('1 lowercase letter');
    if (!/[0-9]/.test(password)) errors.push('1 number');
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) errors.push('1 special character');
    return errors;
  };

  const handlePasswordChange = (password) => {
    setFormData({ ...formData, password });
    setPasswordErrors(validatePassword(password));
  };

  const handleSendCode = async (e) => {
    e.preventDefault();
    setError('');
    const pwErrors = validatePassword(formData.password);
    if (pwErrors.length > 0) {
      setError('Password does not meet requirements');
      setPasswordErrors(pwErrors);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/send-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to send code');
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/verify-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Verification failed');
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/chat');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const leftPanel = (
    <div className="auth-left">
      <div className="auth-left-content">
        <Link to="/" className="auth-left-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
            <circle cx="20" cy="10" r="2" />
          </svg>
          <span>MedicaLLM</span>
        </Link>
        <h1>Start Making<br /><span className="gradient-text">Smarter Decisions</span></h1>
        <p>Join healthcare professionals and patients using AI-powered medical intelligence to understand drugs, check interactions, and access the latest research.</p>
        <div className="auth-features">
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>Interaction Checker</h3><p>Check drug-drug and drug-food interactions with severity classification</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                <path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>Patient Management</h3><p>Healthcare professionals can manage patients and run medication safety analyses</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>Real-Time Streaming</h3><p>See answers as they're generated — no waiting for full responses</p></div>
          </div>
        </div>
      </div>
    </div>
  );

  // ── Step 2: Verification Code ──
  if (step === 2) {
    return (
      <div className="auth-container">
        {leftPanel}
        <div className="auth-right">
          <div className="auth-box">
            <h2>Verify your email</h2>
            <p className="auth-subtitle">We sent a 6-digit code to <strong>{formData.email}</strong></p>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleVerifyCode}>
              <div className="input-group">
                <label>Verification Code</label>
                <div className="code-inputs">
                  {[0,1,2,3,4,5].map((idx) => (
                    <input
                      key={idx}
                      id={`code-${idx}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={code[idx] || ''}
                      autoFocus={idx === 0}
                      className="code-box"
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, '');
                        if (!val && !e.target.value) {
                          // backspace on empty — handled by onKeyDown
                          return;
                        }
                        const newCode = code.split('');
                        newCode[idx] = val.slice(-1);
                        const joined = newCode.join('').slice(0, 6);
                        setCode(joined);
                        // Auto-focus next
                        if (val && idx < 5) {
                          document.getElementById(`code-${idx + 1}`)?.focus();
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && !code[idx] && idx > 0) {
                          const newCode = code.split('');
                          newCode[idx - 1] = '';
                          setCode(newCode.join(''));
                          document.getElementById(`code-${idx - 1}`)?.focus();
                        }
                      }}
                      onPaste={(e) => {
                        e.preventDefault();
                        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
                        setCode(pasted);
                        const focusIdx = Math.min(pasted.length, 5);
                        document.getElementById(`code-${focusIdx}`)?.focus();
                      }}
                    />
                  ))}
                </div>
              </div>
              <button type="submit" disabled={loading || code.length !== 6}>
                {loading ? 'Verifying...' : 'Verify & Create Account'}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#a78bfa' }} onClick={() => { setStep(1); setError(''); setCode(''); }}>
                Back to registration
              </span>
            </p>
            <p className="back-link"><Link to="/">Back to home</Link></p>
          </div>
        </div>
      </div>
    );
  }

  // ── Step 1: Registration Form ──
  return (
    <div className="auth-container">
      {leftPanel}
      <div className="auth-right">
        <div className="auth-box">
          <h2>Create your account</h2>
          <p className="auth-subtitle">Get started with evidence-based medical intelligence</p>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={handleSendCode}>
            <div className="input-group">
              <label htmlFor="name">Full Name</label>
              <input id="name" type="text" placeholder="Enter your full name"
                value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
            </div>
            <div className="input-group">
              <label htmlFor="email">Email Address</label>
              <input id="email" type="email" placeholder="you@example.com"
                value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required pattern="[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}" />
            </div>
            <div className="input-group">
              <label>I am a</label>
              <div className="account-type-grid">
                <label className={`account-type-option${formData.account_type === 'general_user' ? ' selected' : ''}`}>
                  <input type="radio" name="account_type" value="general_user"
                    checked={formData.account_type === 'general_user'}
                    onChange={(e) => setFormData({ ...formData, account_type: e.target.value })} />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                  </svg>
                  General User
                </label>
                <label className={`account-type-option${formData.account_type === 'healthcare_professional' ? ' selected' : ''}`}>
                  <input type="radio" name="account_type" value="healthcare_professional"
                    checked={formData.account_type === 'healthcare_professional'}
                    onChange={(e) => setFormData({ ...formData, account_type: e.target.value })} />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
                    <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" /><circle cx="20" cy="10" r="2" />
                  </svg>
                  Healthcare Pro
                </label>
              </div>
            </div>
            <div className="input-group">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" placeholder="Min 8 chars, upper, lower, number, special"
                value={formData.password} onChange={(e) => handlePasswordChange(e.target.value)}
                required minLength={8} />
              {formData.password && passwordErrors.length > 0 && (
                <ul className="password-requirements">
                  {passwordErrors.map((err, i) => <li key={i} className="requirement-fail">{err}</li>)}
                </ul>
              )}
              {formData.password && passwordErrors.length === 0 && (
                <div className="requirement-pass">Password meets all requirements</div>
              )}
            </div>
            <button type="submit" disabled={loading || (formData.password && passwordErrors.length > 0)}>
              {loading ? 'Sending code...' : 'Continue'}
            </button>
          </form>
          <p className="toggle-text">Already have an account? <Link to="/login">Sign in</Link></p>
          <p className="back-link"><Link to="/">Back to home</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Register;
