import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import config from '../api/config';
import '../Auth.css';

function Login() {
  const [mode, setMode] = useState('login'); // 'login' | 'forgot' | 'reset'
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [resetData, setResetData] = useState({ code: '', newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
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

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/chat');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleForgotSend = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/forgot-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      setSuccess('If this email is registered, a reset code has been sent.');
      setMode('reset');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    const pwErrors = validatePassword(resetData.newPassword);
    if (pwErrors.length > 0) {
      setError('Password does not meet requirements');
      setPasswordErrors(pwErrors);
      return;
    }
    if (resetData.newPassword !== resetData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/reset-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, code: resetData.code, new_password: resetData.newPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Reset failed');
      setSuccess('Password reset successfully!');
      setTimeout(() => { setMode('login'); setSuccess(''); setError(''); setResetData({ code: '', newPassword: '', confirmPassword: '' }); }, 2000);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
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
        <h1>Your Intelligent<br /><span className="gradient-text">Medical Companion</span></h1>
        <p>Access comprehensive drug information, check interactions, search published research, and get evidence-based answers — all powered by AI.</p>
        <div className="auth-features">
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.5 1.5a4.5 4.5 0 0 0-4.5 4.5v12a4.5 4.5 0 0 0 9 0V6a4.5 4.5 0 0 0-4.5-4.5z" /><line x1="6" y1="12" x2="15" y2="12" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>17,430 Drugs</h3><p>Complete DrugBank database with interactions, food warnings, and alternatives</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 18h8" /><path d="M3 22h18" /><path d="M14 22a7 7 0 1 0 0-14h-1" /><path d="M9 14h2" />
                <path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z" /><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>PubMed Research</h3><p>Confidence-scored literature search with citation and evidence-level ranking</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>Privacy First</h3><p>Runs on local LLMs — your data never leaves your infrastructure</p></div>
          </div>
        </div>
      </div>
    </div>
  );

  // ── Reset Password: Enter Code + New Password ──
  if (mode === 'reset') {
    return (
      <div className="auth-container">
        {leftPanel}
        <div className="auth-right">
          <div className="auth-box">
            <h2>Reset your password</h2>
            <p className="auth-subtitle">Enter the code sent to <strong>{formData.email}</strong> and your new password</p>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleResetPassword}>
              <div className="input-group">
                <label>Reset Code</label>
                <div className="code-inputs">
                  {[0,1,2,3,4,5].map((idx) => (
                    <input key={idx} id={`reset-code-${idx}`} type="text" inputMode="numeric"
                      maxLength={1} value={resetData.code[idx] || ''} autoFocus={idx === 0} className="code-box"
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, '');
                        const newCode = resetData.code.split('');
                        newCode[idx] = val.slice(-1);
                        setResetData({ ...resetData, code: newCode.join('').slice(0, 6) });
                        if (val && idx < 5) document.getElementById(`reset-code-${idx + 1}`)?.focus();
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && !resetData.code[idx] && idx > 0) {
                          const newCode = resetData.code.split(''); newCode[idx - 1] = '';
                          setResetData({ ...resetData, code: newCode.join('') });
                          document.getElementById(`reset-code-${idx - 1}`)?.focus();
                        }
                      }}
                      onPaste={(e) => {
                        e.preventDefault();
                        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
                        setResetData({ ...resetData, code: pasted });
                        document.getElementById(`reset-code-${Math.min(pasted.length, 5)}`)?.focus();
                      }}
                    />
                  ))}
                </div>
              </div>
              <div className="input-group">
                <label htmlFor="new-password">New Password</label>
                <input id="new-password" type="password" placeholder="Min 8 chars, upper, lower, number, special"
                  value={resetData.newPassword}
                  onChange={(e) => { setResetData({ ...resetData, newPassword: e.target.value }); setPasswordErrors(validatePassword(e.target.value)); }}
                  required minLength={8} />
                {resetData.newPassword && passwordErrors.length > 0 && (
                  <ul className="password-requirements">
                    {passwordErrors.map((err, i) => <li key={i} className="requirement-fail">{err}</li>)}
                  </ul>
                )}
                {resetData.newPassword && passwordErrors.length === 0 && (
                  <div className="requirement-pass">Password meets all requirements</div>
                )}
              </div>
              <div className="input-group">
                <label htmlFor="confirm-password">Confirm Password</label>
                <input id="confirm-password" type="password" placeholder="Re-enter your new password"
                  value={resetData.confirmPassword}
                  onChange={(e) => setResetData({ ...resetData, confirmPassword: e.target.value })}
                  required minLength={8} />
                {resetData.confirmPassword && resetData.newPassword !== resetData.confirmPassword && (
                  <div className="requirement-fail" style={{ marginTop: '6px', fontSize: '12px' }}>Passwords do not match</div>
                )}
                {resetData.confirmPassword && resetData.newPassword === resetData.confirmPassword && resetData.confirmPassword.length > 0 && (
                  <div className="requirement-pass">Passwords match</div>
                )}
              </div>
              <button type="submit" disabled={loading || resetData.code.length !== 6 || (resetData.newPassword && passwordErrors.length > 0) || resetData.newPassword !== resetData.confirmPassword}>
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#a78bfa' }} onClick={() => { setMode('login'); setError(''); setSuccess(''); }}>Back to sign in</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Forgot Password: Enter Email ──
  if (mode === 'forgot') {
    return (
      <div className="auth-container">
        {leftPanel}
        <div className="auth-right">
          <div className="auth-box">
            <h2>Forgot your password?</h2>
            <p className="auth-subtitle">Enter your email and we'll send you a reset code</p>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleForgotSend}>
              <div className="input-group">
                <label htmlFor="forgot-email">Email Address</label>
                <input id="forgot-email" type="email" placeholder="you@example.com"
                  value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required autoFocus />
              </div>
              <button type="submit" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Code'}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#a78bfa' }} onClick={() => { setMode('login'); setError(''); }}>Back to sign in</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Login ──
  return (
    <div className="auth-container">
      {leftPanel}
      <div className="auth-right">
        <div className="auth-box">
          <h2>Welcome back</h2>
          <p className="auth-subtitle">Sign in to continue to your medical assistant</p>
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
          <form onSubmit={handleLogin}>
            <div className="input-group">
              <label htmlFor="email">Email Address</label>
              <input id="email" type="email" placeholder="you@example.com"
                value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required pattern="[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}" />
            </div>
            <div className="input-group">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" placeholder="Enter your password"
                value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required />
            </div>
            <div style={{ textAlign: 'right', marginTop: '-8px' }}>
              <span className="forgot-link" onClick={() => { setMode('forgot'); setError(''); setSuccess(''); }}>
                Forgot password?
              </span>
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
          <p className="toggle-text">Don't have an account? <Link to="/register">Create one</Link></p>
          <p className="back-link"><Link to="/">Back to home</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Login;
