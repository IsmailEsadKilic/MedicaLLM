import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect, useMemo } from 'react';
import './Landing.css';
import { STRINGS } from './landingStrings';
import { useLang, SUPPORTED_LANGS } from '../i18n/lang';
import HeroTerminal from '../components/HeroTerminal';

/* ═══════════════════════════════════════════════════════════
   SVG Icon Components (inline, no emoji)
   ═══════════════════════════════════════════════════════════ */

const Icon = ({ children, size = 32, className = '' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
    strokeLinejoin="round" className={`landing-icon ${className}`}>
    {children}
  </svg>
);

const IconPill = (p) => (
  <Icon {...p}>
    <path d="M10.5 1.5a4.5 4.5 0 0 0-4.5 4.5v12a4.5 4.5 0 0 0 9 0V6a4.5 4.5 0 0 0-4.5-4.5z" />
    <line x1="6" y1="12" x2="15" y2="12" />
  </Icon>
);

const IconWarning = (p) => (
  <Icon {...p}>
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </Icon>
);

const IconMicroscope = (p) => (
  <Icon {...p}>
    <path d="M6 18h8" />
    <path d="M3 22h18" />
    <path d="M14 22a7 7 0 1 0 0-14h-1" />
    <path d="M9 14h2" />
    <path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z" />
    <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3" />
  </Icon>
);

const IconFileText = (p) => (
  <Icon {...p}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </Icon>
);

const IconHeartPulse = (p) => (
  <Icon {...p}>
    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    <path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27" />
  </Icon>
);

const IconBot = (p) => (
  <Icon {...p}>
    <path d="M12 8V4H8" />
    <rect width="16" height="12" x="4" y="8" rx="2" />
    <path d="M2 14h2" />
    <path d="M20 14h2" />
    <path d="M15 13v2" />
    <path d="M9 13v2" />
  </Icon>
);

const IconShield = (p) => (
  <Icon {...p}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M9 12l2 2 4-4" />
  </Icon>
);

const IconBookOpen = (p) => (
  <Icon {...p}>
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
  </Icon>
);

const IconZap = (p) => (
  <Icon {...p}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </Icon>
);

const IconBrain = (p) => (
  <Icon {...p}>
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </Icon>
);

const IconDna = (p) => (
  <Icon {...p}>
    <path d="M2 15c6.667-6 13.333 0 20-6" />
    <path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993" />
    <path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993" />
    <path d="M17 6l-2.5-2.5" />
    <path d="M14 8l-1-1" />
    <path d="M7 18l2.5 2.5" />
    <path d="M3.5 14.5l.5.5" />
    <path d="M20 9l.5.5" />
    <path d="M6.5 12.5l1 1" />
    <path d="M16.5 10.5l1 1" />
    <path d="M10 16l1.5 1.5" />
  </Icon>
);

const IconMail = (p) => (
  <Icon {...p}>
    <rect width="20" height="16" x="2" y="4" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </Icon>
);

const IconMessageCircle = (p) => (
  <Icon {...p}>
    <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
  </Icon>
);

const IconMapPin = (p) => (
  <Icon {...p}>
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
    <circle cx="12" cy="10" r="3" />
  </Icon>
);

const IconMenu = (p) => (
  <Icon size={24} {...p}>
    <line x1="4" x2="20" y1="12" y2="12" />
    <line x1="4" x2="20" y1="6" y2="6" />
    <line x1="4" x2="20" y1="18" y2="18" />
  </Icon>
);

const IconX = (p) => (
  <Icon size={24} {...p}>
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </Icon>
);

const IconCheck = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
    strokeLinejoin="round" className="check-icon">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const IconStethoscope = (p) => (
  <Icon {...p}>
    <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
    <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
    <circle cx="20" cy="10" r="2" />
  </Icon>
);

const IconGlobe = (p) => (
  <Icon size={16} {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </Icon>
);

/* ═══════════════════════════════════════════════════════════
   Static visual data (icons live in JSX so they aren't language-bound)
   ═══════════════════════════════════════════════════════════ */

const FEATURE_ICONS = [
  <IconPill key="pill" />,
  <IconWarning key="warn" />,
  <IconMicroscope key="micro" />,
  <IconFileText key="file" />,
  <IconHeartPulse key="heart" />,
  <IconBot key="bot" />,
];

const REASON_ICONS = [
  <IconShield key="shield" />,
  <IconBookOpen key="book" />,
  <IconZap key="zap" />,
  <IconBrain key="brain" />,
];

const STEP_NUMS = ['01', '02', '03', '04'];

const LANG_LABELS = {
  en: 'EN',
  tr: 'TR',
};

/* ═══════════════════════════════════════════════════════════
   Contact form
   ═══════════════════════════════════════════════════════════ */

/**
 * Lightweight contact form. Today the site has no backend mail
 * endpoint (the SMTP integration is gated on DigitalOcean unblocking
 * outbound 465/587), so the form composes a `mailto:` URL and hands
 * off to the user's mail client. As soon as we have a /api/contact
 * endpoint we'll switch the action without changing the markup.
 */
function ContactForm({ t, lang }) {
  const [name, setName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [subject, setSubject] = React.useState('');
  const [message, setMessage] = React.useState('');
  const [status, setStatus] = React.useState(null); // null | 'sent' | 'error'

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) return;
    const composedSubject = subject.trim() || (
      lang === 'tr'
        ? `MedicaLLM iletişim — ${name}`
        : `MedicaLLM inquiry — ${name}`
    );
    const composedBody =
      lang === 'tr'
        ? `Ad: ${name}\nE-posta: ${email}\n\n${message}`
        : `Name: ${name}\nEmail: ${email}\n\n${message}`;
    const href =
      `mailto:contact@medicallm.com.tr` +
      `?subject=${encodeURIComponent(composedSubject)}` +
      `&body=${encodeURIComponent(composedBody)}`;
    window.location.href = href;
    setStatus('sent');
  };

  return (
    <form className="contact-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <input type="text" placeholder={t.formNamePlaceholder} value={name} onChange={(e) => setName(e.target.value)} required />
        <input type="email" placeholder={t.formEmailPlaceholder} value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <input type="text" placeholder={t.formSubjectPlaceholder} value={subject} onChange={(e) => setSubject(e.target.value)} />
      <textarea rows="5" placeholder={t.formMessagePlaceholder} value={message} onChange={(e) => setMessage(e.target.value)} required />
      <button type="submit" className="btn-primary full">{t.formSubmit}</button>
      {status === 'sent' && (
        <p className="contact-sent-note">
          {lang === 'tr'
            ? 'E-posta uygulamanız açıldı. Mesajı oradan göndermeyi unutmayın.'
            : 'Your mail app has been opened. Don\u2019t forget to hit send there.'}
        </p>
      )}
    </form>
  );
}

/* ═══════════════════════════════════════════════════════════
   Component
   ═══════════════════════════════════════════════════════════ */

export default function Landing() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { lang, setLang } = useLang();

  // Resolve once per render so nested templates don't re-look-up.
  const t = useMemo(() => STRINGS[lang] ?? STRINGS.en, [lang]);

  useEffect(() => {
    // Redirect logged-in users to their home page
    const token = localStorage.getItem('token');
    if (token) {
      // Authed visitors hitting the landing page always go to /chat.
      navigate('/chat', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollTo = (id) => {
    setMobileMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  const cycleLang = () => {
    const i = SUPPORTED_LANGS.indexOf(lang);
    setLang(SUPPORTED_LANGS[(i + 1) % SUPPORTED_LANGS.length]);
  };

  // Login/register live at bare URLs now — language is stored, not in
  // the URL.
  const goLogin = () => navigate('/login');
  const goRegister = () => navigate('/register');

  return (
    <div className="landing">
      {/* ─── Navbar ─── */}
      <nav className={`landing-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="nav-inner">
          <div className="nav-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <IconStethoscope size={24} className="logo-svg" /> MedicaLLM
          </div>
          <div className={`nav-links${mobileMenuOpen ? ' open' : ''}`}>
            {t.nav.links.map((l) => (
              <button key={l.id} className="nav-link" onClick={() => scrollTo(l.id)}>
                {l.label}
              </button>
            ))}
          </div>
          <div className="nav-actions">
            <button
              className="nav-btn lang-btn"
              onClick={cycleLang}
              aria-label={`${t.nav.languageLabel}: ${LANG_LABELS[lang]}`}
              title={`${t.nav.languageLabel}: ${LANG_LABELS[lang]}`}
            >
              <IconGlobe />
              <span>{LANG_LABELS[lang]}</span>
            </button>
            <button className="nav-btn ghost" onClick={goLogin}>{t.nav.signIn}</button>
            <button className="nav-btn primary" onClick={goRegister}>{t.nav.getStarted}</button>
          </div>
          <button className="hamburger" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} aria-label="Toggle menu">
            {mobileMenuOpen ? <IconX /> : <IconMenu />}
          </button>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <header className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <h1>{t.hero.titleLine1}<br /><span className="gradient-text">{t.hero.titleLine2}</span></h1>
          <p className="hero-sub">{t.hero.subtitle}</p>
          <div className="hero-ctas">
            <button className="btn-primary" onClick={goRegister}>{t.hero.ctaPrimary}</button>
            <button className="btn-outline" onClick={() => scrollTo('features')}>{t.hero.ctaSecondary}</button>
          </div>
          <p className="hero-note">{t.hero.note}</p>
        </div>
        <div className="hero-visual">
          <HeroTerminal
            conversations={t.hero.conversations}
            labels={{ you: t.hero.labelYou, ai: t.hero.labelAI }}
            zapIcon={<IconZap size={14} className="inline-icon" />}
          />
        </div>
      </header>

      {/* ─── Features ─── */}
      <section id="features" className="section">
        <div className="section-inner">
          <h2 className="section-title">{t.features.titleLine1}<br /><span className="gradient-text">{t.features.titleLine2}</span></h2>
          <p className="section-sub">{t.features.subtitle}</p>
          <div className="features-grid">
            {t.features.items.map((f, i) => (
              <div key={f.title} className="feature-card">
                <span className="feature-icon">{FEATURE_ICONS[i]}</span>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="section alt">
        <div className="section-inner">
          <h2 className="section-title">{t.steps.title}</h2>
          <p className="section-sub">{t.steps.subtitle}</p>
          <div className="steps-grid">
            {t.steps.items.map((s, i) => (
              <div key={s.title} className="step-card">
                <span className="step-num">{STEP_NUMS[i]}</span>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pricing ─── */}
      <section id="pricing" className="section">
        <div className="section-inner">
          <h2 className="section-title">{t.pricing.title}</h2>
          <p className="section-sub">{t.pricing.subtitle}</p>
          <div className="pricing-grid">
            {t.pricing.plans.map((p, i) => {
              const highlighted = i === 1; // middle plan visually featured
              const isComingSoon = p.status === 'coming-soon';
              const isContact = p.status === 'contact';

              const handleClick = () => {
                if (isComingSoon || isContact) {
                  // Both routes funnel to email — we don't have a sales
                  // contact form yet, and a "Notify me" inbox is good
                  // enough to gauge demand pre-launch.
                  const subject = encodeURIComponent(
                    isComingSoon
                      ? `Notify me: MedicaLLM ${p.name} plan`
                      : `MedicaLLM Enterprise inquiry`,
                  );
                  window.location.href = `mailto:contact@medicallm.com.tr?subject=${subject}`;
                  return;
                }
                goRegister();
              };

              return (
                <div key={p.name} className={`pricing-card${highlighted ? ' highlighted' : ''}${isComingSoon ? ' coming-soon' : ''}`}>
                  {highlighted && !isComingSoon && (
                    <span className="popular-badge">{t.pricing.popularBadge}</span>
                  )}
                  {isComingSoon && (
                    <span className="popular-badge coming-soon-badge">{t.pricing.comingSoonBadge}</span>
                  )}
                  <h3>{p.name}</h3>
                  <div className="price">
                    <span className="amount">{p.price}</span>
                    {p.period && <span className="period">{p.period}</span>}
                  </div>
                  <ul>
                    {p.features.map((feat) => (
                      <li key={feat}><IconCheck /> {feat}</li>
                    ))}
                  </ul>
                  <button
                    className={highlighted && !isComingSoon ? 'btn-primary full' : 'btn-outline full'}
                    onClick={handleClick}
                  >
                    {p.cta}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Why Us ─── */}
      <section id="why-us" className="section alt">
        <div className="section-inner">
          <h2 className="section-title">{t.why.title}</h2>
          <p className="section-sub">{t.why.subtitle}</p>
          <div className="reasons-grid">
            {t.why.items.map((r, i) => (
              <div key={r.title} className="reason-card">
                <span className="reason-icon">{REASON_ICONS[i]}</span>
                <h3>{r.title}</h3>
                <p>{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Contact ─── */}
      <section id="contact" className="section">
        <div className="section-inner contact-section">
          <div className="contact-info">
            <h2 className="section-title">{t.contact.title}</h2>
            <p className="section-sub">{t.contact.subtitle}</p>
            <div className="contact-details">
              <div className="contact-item">
                <IconMail size={24} />
                <div>
                  <strong>{t.contact.emailLabel}</strong>
                  <p>{t.contact.emailValue}</p>
                </div>
              </div>
              <div className="contact-item">
                <IconMapPin size={24} />
                <div>
                  <strong>{t.contact.locationLabel}</strong>
                  <p>{t.contact.locationValue}</p>
                </div>
              </div>
            </div>
          </div>
          <ContactForm
            t={t.contact}
            lang={lang}
          />
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <div className="nav-logo"><IconStethoscope size={24} className="logo-svg" /> MedicaLLM</div>
            <p style={{ whiteSpace: 'pre-line' }}>{t.footer.tagline}</p>
          </div>
          <div className="footer-links">
            <div>
              <h4>{t.footer.productHeading}</h4>
              {t.footer.productLinks.map((l) => (
                <button
                  key={l.label}
                  onClick={() => l.target && scrollTo(l.target)}
                  disabled={!l.target}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div>
              <h4>{t.footer.companyHeading}</h4>
              {t.footer.companyLinks.map((l) => (
                <button
                  key={l.label}
                  onClick={() => l.target && scrollTo(l.target)}
                  disabled={!l.target}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div>
              <h4>{t.footer.legalHeading}</h4>
              {t.footer.legalLinks.map((l) => (
                <button key={l.label} disabled={!l.target}>{l.label}</button>
              ))}
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>{t.footer.copyright}</p>
        </div>
      </footer>
    </div>
  );
}
