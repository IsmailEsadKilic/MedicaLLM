import { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import config from '../api/config';
import { useLang } from '../i18n/lang';
import { AUTH_STRINGS } from './authStrings';
import LangToggle from '../components/LangToggle';
import '../Auth.css';

function Register() {
  const [step, setStep] = useState(1); // 1 = form, 2 = verify code
  const [formData, setFormData] = useState({ email: '', password: '', name: '', account_type: 'user' });
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState([]);
  const navigate = useNavigate();
  const { lang } = useLang();
  const t = useMemo(() => AUTH_STRINGS[lang] ?? AUTH_STRINGS.en, [lang]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Always send authenticated visitors straight to /chat — the chat
      // surface is the product's home, regardless of account type. The
      // role-specific panels (/doctor, /patient) remain reachable from
      // the in-app sidebar.
      navigate('/chat');
    }
  }, [navigate]);

  const validatePassword = useMemo(() => {
    const r = t.passwordRules;
    return (password) => {
      const errors = [];
      if (password.length < 8) errors.push(r.length);
      if (!/[A-Z]/.test(password)) errors.push(r.uppercase);
      if (!/[a-z]/.test(password)) errors.push(r.lowercase);
      if (!/[0-9]/.test(password)) errors.push(r.number);
      if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) errors.push(r.special);
      return errors;
    };
  }, [t.passwordRules]);

  const handlePasswordChange = (password) => {
    setFormData({ ...formData, password });
    setPasswordErrors(validatePassword(password));
  };

  const handleSendCode = async (e) => {
    e.preventDefault();
    setError('');
    const pwErrors = validatePassword(formData.password);
    if (pwErrors.length > 0) {
      setError(t.passwordRules.heading);
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
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const message =
          typeof data.detail === 'string'
            ? data.detail
            : data.detail?.message ||
              (res.status === 429
                ? (lang === 'tr' ? 'Çok fazla istek. Lütfen biraz bekleyin.' : 'Too many requests. Please slow down and try again.')
                : (lang === 'tr' ? 'Kod gönderilemedi' : 'Failed to send code'));
        throw new Error(message);
      }
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
      const res = await fetch(`${config.API_URL}/api/auth/verification-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, code }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const message =
          typeof data.detail === 'string'
            ? data.detail
            : data.detail?.message || (lang === 'tr' ? 'Doğrulama başarısız' : 'Verification failed');
        throw new Error(message);
      }
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      // After signup, always land on /chat regardless of account type —
      // the role-specific surfaces (/doctor, /patient) are reachable
      // from the in-app sidebar once the user gets oriented.
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
        <Link to={"/"} className="auth-left-logo">
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

  // ── Step 2: Verification Code ──
  if (step === 2) {
    return (
      <div className="auth-container">
        <LangToggle />
        {leftPanel}
        <div className="auth-right">
          <div className="auth-box">
            <h2>{t.verify.title}</h2>
            <p className="auth-subtitle">
              {t.verify.subtitle.replace('{email}', '')}
              {' '}
              <strong>{formData.email}</strong>
            </p>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleVerifyCode}>
              <div className="input-group">
                <label>{t.verify.codeLabel}</label>
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
                        if (!val && !e.target.value) return;
                        const newCode = code.split('');
                        newCode[idx] = val.slice(-1);
                        const joined = newCode.join('').slice(0, 6);
                        setCode(joined);
                        if (val && idx < 5) document.getElementById(`code-${idx + 1}`)?.focus();
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
                {loading ? t.verify.submitting : t.verify.submit}
              </button>
            </form>
            <p className="toggle-text" style={{ marginTop: '16px' }}>
              <span style={{ cursor: 'pointer', color: '#60a5fa' }} onClick={() => { setStep(1); setError(''); setCode(''); }}>
                {t.verify.back}
              </span>
            </p>
            <p className="back-link"><Link to={"/"}>{t.common.backHome}</Link></p>
          </div>
        </div>
      </div>
    );
  }

  // ── Step 1: Registration Form ──
  return (
    <div className="auth-container">
      <LangToggle />
      {leftPanel}
      <div className="auth-right">
        <div className="auth-box">
          <h2>{t.register.title}</h2>
          <p className="auth-subtitle">{t.register.subtitle}</p>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={handleSendCode}>
            <div className="input-group">
              <label htmlFor="name">{t.register.nameLabel}</label>
              <input id="name" type="text" placeholder={t.register.namePlaceholder}
                value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
            </div>
            <div className="input-group">
              <label htmlFor="email">{t.register.emailLabel}</label>
              <input id="email" type="email" placeholder={t.register.emailPlaceholder}
                value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required pattern="[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}" />
            </div>
            <div className="input-group">
              <label>{t.register.accountTypeLabel}</label>
              <div className="account-type-grid">
                <label className={`account-type-option${formData.account_type === 'user' ? ' selected' : ''}`}>
                  <input type="radio" name="account_type" value="user"
                    checked={formData.account_type === 'user'}
                    onChange={(e) => setFormData({ ...formData, account_type: e.target.value })} />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                  </svg>
                  {t.register.accountUser}
                </label>
                <label className={`account-type-option${formData.account_type === 'doctor' ? ' selected' : ''}`}>
                  <input type="radio" name="account_type" value="doctor"
                    checked={formData.account_type === 'doctor'}
                    onChange={(e) => setFormData({ ...formData, account_type: e.target.value })} />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
                    <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" /><circle cx="20" cy="10" r="2" />
                  </svg>
                  {t.register.accountDoctor}
                </label>
                <label className={`account-type-option${formData.account_type === 'patient' ? ' selected' : ''}`}>
                  <input type="radio" name="account_type" value="patient"
                    checked={formData.account_type === 'patient'}
                    onChange={(e) => setFormData({ ...formData, account_type: e.target.value })} />
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                  </svg>
                  {t.register.accountPatient}
                </label>
              </div>
            </div>
            <div className="input-group">
              <label htmlFor="password">{t.register.passwordLabel}</label>
              <input id="password" type="password" placeholder={t.register.passwordPlaceholder}
                value={formData.password} onChange={(e) => handlePasswordChange(e.target.value)}
                required minLength={8} />
              {formData.password && passwordErrors.length > 0 && (
                <ul className="password-requirements">
                  {passwordErrors.map((err, i) => <li key={i} className="requirement-fail">{err}</li>)}
                </ul>
              )}
              {formData.password && passwordErrors.length === 0 && (
                <div className="requirement-pass">{lang === 'tr' ? 'Şifre tüm gereksinimleri karşılıyor' : 'Password meets all requirements'}</div>
              )}
            </div>
            <button type="submit" disabled={loading || (formData.password && passwordErrors.length > 0)}>
              {loading ? t.register.submitting : t.register.submit}
            </button>
          </form>
          <p className="toggle-text">{t.register.haveAccount} <Link to={"/login"}>{t.register.signInLink}</Link></p>
          <p className="back-link"><Link to={"/"}>{t.common.backHome}</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Register;
