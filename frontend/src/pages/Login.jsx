import { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import config from '../api/config';
import { useLang, useLangPath } from '../i18n/lang';
import { AUTH_STRINGS } from './authStrings';
import '../Auth.css';

// Helpers below produce localised inline error messages so they don't
// leak hardcoded English into the form when the user is on /tr/login.
function makePasswordValidator(passwordRules) {
  return (password) => {
    const errors = [];
    if (password.length < 8) errors.push(passwordRules.length);
    if (!/[A-Z]/.test(password)) errors.push(passwordRules.uppercase);
    if (!/[a-z]/.test(password)) errors.push(passwordRules.lowercase);
    if (!/[0-9]/.test(password)) errors.push(passwordRules.number);
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) errors.push(passwordRules.special);
    return errors;
  };
}

function Login() {
  const [mode, setMode] = useState('login'); // 'login' | 'forgot' | 'reset'
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [resetData, setResetData] = useState({ code: '', newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState([]);
  const navigate = useNavigate();
  const langPath = useLangPath();
  const { lang } = useLang();
  const t = useMemo(() => AUTH_STRINGS[lang] ?? AUTH_STRINGS.en, [lang]);
  const validatePassword = useMemo(() => makePasswordValidator(t.passwordRules), [t.passwordRules]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      navigate(u.isDoctor ? '/doctor' : u.isPatient ? '/patient' : '/chat');
    }
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Login failed');
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate(data.user.isDoctor ? '/doctor' : data.user.isPatient ? '/patient' : '/chat');
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
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed');
      setSuccess(t.forgot.subtitle);
      setMode('reset');
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');
    const pwErrors = validatePassword(resetData.newPassword);
    if (pwErrors.length > 0) {
      setError(t.passwordRules.heading);
      setPasswordErrors(pwErrors);
      return;
    }
    if (resetData.newPassword !== resetData.confirmPassword) {
      setError(lang === 'tr' ? 'Şifreler eşleşmiyor' : 'Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/auth/reset-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, code: resetData.code, new_password: resetData.newPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Reset failed');
      setSuccess(lang === 'tr' ? 'Şifre başarıyla sıfırlandı.' : 'Password reset successfully!');
      setTimeout(() => { setMode('login'); setSuccess(''); setError(''); setResetData({ code: '', newPassword: '', confirmPassword: '' }); }, 2000);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const leftPanel = (
    <div className="auth-left">
      <div className="auth-left-content">
        <Link to={langPath('/')} className="auth-left-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
            <circle cx="20" cy="10" r="2" />
          </svg>
          <span>{t.common.brand}</span>
        </Link>
        <h1>{t.common.heroTitleA}<br /><span className="gradient-text">{t.common.heroTitleB}</span></h1>
        <p>{t.common.heroSubtitle}</p>
        <div className="auth-features">
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>{t.common.featureEvidenceTitle}</h3><p>{t.common.featureEvidenceDesc}</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>{t.common.featureSafetyTitle}</h3><p>{t.common.featureSafetyDesc}</p></div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <div className="auth-feature-text"><h3>{t.common.featureFastTitle}</h3><p>{t.common.featureFastDesc}</p></div>
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
            <h2>{t.reset.title}</h2>
            <p className="auth-subtitle">{t.reset.subtitle}</p>
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            <form onSubmit={handleResetPassword}>
              <div className="input-group">
                <label>{t.reset.codeLabel}</label>
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
                <label htmlFor="new-password">{t.reset.newPasswordLabel}</label>
                <input id="new-password" type="password" placeholder={t.reset.newPasswordPlaceholder}
                  value={resetData.newPassword}
                  onChange={(e) => { setResetData({ ...resetData, newPassword: e.target.value }); setPasswordErrors(validatePassword(e.target.value)); }}
                  required minLength={8} />
                {resetData.newPassword && passwordErrors.length > 0 && (
                  <ul className="password-requirements">
                    {passwordErrors.map((err, i) => <li key={i} className="requirement-fail">{err}</li>)}
                  </ul>
                )}
                {resetData.newPassword && passwordErrors.length === 0 && (
                  <div className="requirement-pass">{lang === 'tr' ? 'Şifre tüm gereksinimleri karşılıyor' : 'Password meets all requirements'}</div>
                )}
              </div>
              <div className="input-group">
                <label htmlFor="confirm-password">{lang === 'tr' ? 'Şifreyi Onayla' : 'Confirm Password'}</label>
                <input id="confirm-password" type="password" placeholder={lang === 'tr' ? 'Yeni şifreyi tekrar girin' : 'Re-enter your new password'}
                  value={resetData.confirmPassword}
                  onChange={(e) => setResetData({ ...resetData, confirmPassword: e.target.value })}
                  required minLength={8} />
                {resetData.confirmPassword && resetData.newPassword !== resetData.confirmPassword && (
                  <div className="requirement-fail" style={{ marginTop: '6px', fontSize: '12px' }}>{lang === 'tr' ? 'Şifreler eşleşmiyor' : 'Passwords do not match'}</div>
                )}
                {resetData.confirmPassword && resetData.newPassword === resetData.confirmPassword && resetData.confirmPassword.length > 0 && (
                  <div className="requirement-pass">{lang === 'tr' ? 'Şifreler eşleşti' : 'Passwords match'}</div>
                )}
              </div>
              <button type="submit" disabled={loading || resetData.code.length !== 6 || (resetData.newPassword && passwordErrors.length > 0) || resetData.newPassword !== resetData.confirmPassword}>
                {loading ? t.reset.submitting : t.reset.submit}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#60a5fa' }} onClick={() => { setMode('login'); setError(''); setSuccess(''); }}>{t.reset.backToLogin}</span>
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
            <h2>{t.forgot.title}</h2>
            <p className="auth-subtitle">{t.forgot.subtitle}</p>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleForgotSend}>
              <div className="input-group">
                <label htmlFor="forgot-email">{t.forgot.emailLabel}</label>
                <input id="forgot-email" type="email" placeholder={t.forgot.emailPlaceholder}
                  value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required autoFocus />
              </div>
              <button type="submit" disabled={loading}>
                {loading ? t.forgot.submitting : t.forgot.submit}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#60a5fa' }} onClick={() => { setMode('login'); setError(''); }}>{t.forgot.backToLogin}</span>
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
          <h2>{t.login.title}</h2>
          <p className="auth-subtitle">{t.login.subtitle}</p>
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
          <form onSubmit={handleLogin}>
            <div className="input-group">
              <label htmlFor="email">{t.login.emailLabel}</label>
              <input id="email" type="email" placeholder={t.login.emailPlaceholder}
                value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required pattern="[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}" />
            </div>
            <div className="input-group">
              <label htmlFor="password">{t.login.passwordLabel}</label>
              <input id="password" type="password" placeholder={t.login.passwordPlaceholder}
                value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required />
            </div>
            <div style={{ textAlign: 'right', marginTop: '-8px' }}>
              <span className="forgot-link" onClick={() => { setMode('forgot'); setError(''); setSuccess(''); }}>
                {t.login.forgot}
              </span>
            </div>
            <button type="submit" disabled={loading}>
              {loading ? t.login.submitting : t.login.submit}
            </button>
          </form>
          <p className="toggle-text">{t.login.noAccount} <Link to={langPath('/register')}>{t.login.createOne}</Link></p>
          <p className="back-link"><Link to={langPath('/')}>{t.common.backHome}</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Login;
