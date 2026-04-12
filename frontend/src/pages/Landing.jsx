import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import './Landing.css';

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

/* ═══════════════════════════════════════════════════════════
   Data
   ═══════════════════════════════════════════════════════════ */

const NAV_LINKS = ['Features', 'How It Works', 'Pricing', 'Why Us', 'Contact'];

const FEATURES = [
  { icon: <IconPill />, title: 'Drug Information', desc: 'Access comprehensive drug data from DrugBank — indications, mechanisms, side effects, metabolism, and more.' },
  { icon: <IconWarning />, title: 'Interaction Checker', desc: 'Instantly check drug-drug and drug-food interactions with severity levels and safe alternative recommendations.' },
  { icon: <IconMicroscope />, title: 'PubMed Research', desc: 'Search published medical literature with confidence scoring based on citations, recency, and evidence level.' },
  { icon: <IconFileText />, title: 'RAG-Powered Docs', desc: 'Upload and query medical guidelines and PDFs using retrieval-augmented generation for precise answers.' },
  { icon: <IconHeartPulse />, title: 'Patient Analysis', desc: 'Healthcare professionals can run full medication safety analyses — pairwise interactions and allergy conflicts.' },
  { icon: <IconBot />, title: 'AI Conversational Agent', desc: 'Chat naturally with MedicaLLM. It understands context, remembers your conversation, and cites its sources.' },
];

const STEPS = [
  { num: '01', title: 'Create Your Account', desc: 'Sign up in seconds as a general user or healthcare professional.' },
  { num: '02', title: 'Ask a Question', desc: 'Type a drug name, describe symptoms, or ask about interactions — just like talking to a colleague.' },
  { num: '03', title: 'Get Evidence-Based Answers', desc: 'MedicaLLM searches DrugBank, PubMed, and your uploaded documents to deliver cited, reliable responses.' },
  { num: '04', title: 'Take Action', desc: 'Review alternatives, export reports, and make informed clinical or personal health decisions.' },
];

const PLANS = [
  {
    name: 'Starter',
    price: 'Free',
    period: '',
    features: ['Drug information lookup', 'Basic interaction checks', '30 queries / day', 'Community support'],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Professional',
    price: '$29',
    period: '/month',
    features: ['Everything in Starter', 'Unlimited queries', 'PubMed research access', 'Patient management', 'PDF document upload', 'Priority support'],
    cta: 'Start Free Trial',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    features: ['Everything in Professional', 'Dedicated instance', 'Custom LLM fine-tuning', 'SSO & HIPAA compliance', 'API access', 'Dedicated account manager'],
    cta: 'Contact Sales',
    highlighted: false,
  },
];

const REASONS = [
  { icon: <IconShield />, title: 'Privacy First', desc: 'Runs on local LLMs via Ollama — your data never leaves your infrastructure.' },
  { icon: <IconBookOpen />, title: 'Evidence-Based', desc: 'Every answer is grounded in DrugBank data, PubMed literature, and your own documents.' },
  { icon: <IconZap />, title: 'Real-Time Streaming', desc: "See answers as they're generated with live token streaming — no waiting for full responses." },
  { icon: <IconBrain />, title: 'Context-Aware', desc: 'Role-aware prompts adapt language for clinicians vs. general users. Patient context is injected per query.' },
];

/* ═══════════════════════════════════════════════════════════
   Component
   ═══════════════════════════════════════════════════════════ */

export default function Landing() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollTo = (id) => {
    setMobileMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="landing">
      {/* ─── Navbar ─── */}
      <nav className={`landing-nav${scrolled ? ' scrolled' : ''}`}>
        <div className="nav-inner">
          <div className="nav-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <IconStethoscope size={24} className="logo-svg" /> MedicaLLM
          </div>
          <div className={`nav-links${mobileMenuOpen ? ' open' : ''}`}>
            {NAV_LINKS.map((l) => (
              <button key={l} className="nav-link" onClick={() => scrollTo(l.toLowerCase().replace(/ /g, '-'))}>
                {l}
              </button>
            ))}
          </div>
          <div className="nav-actions">
            <button className="nav-btn ghost" onClick={() => navigate('/login')}>Sign In</button>
            <button className="nav-btn primary" onClick={() => navigate('/register')}>Get Started</button>
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
          <span className="hero-badge"><IconDna size={16} /> AI-Powered Medical Intelligence</span>
          <h1>Your Intelligent<br /><span className="gradient-text">Medical Companion</span></h1>
          <p className="hero-sub">
            MedicaLLM combines a comprehensive drug database, real-time PubMed research,
            and a privacy-first AI agent to deliver evidence-based medical insights — instantly.
          </p>
          <div className="hero-ctas">
            <button className="btn-primary" onClick={() => navigate('/register')}>Start For Free</button>
            <button className="btn-outline" onClick={() => scrollTo('features')}>See Features</button>
          </div>
          <p className="hero-note">No credit card required · Free tier available</p>
        </div>
        <div className="hero-visual">
          <div className="terminal-mock">
            <div className="terminal-bar"><span /><span /><span /></div>
            <div className="terminal-body">
              <p className="t-user"><span className="t-label">You</span> Does Warfarin interact with Ibuprofen?</p>
              <p className="t-ai"><span className="t-label">MedicaLLM</span> Yes — concurrent use increases bleeding risk significantly. Ibuprofen inhibits platelet aggregation and may displace Warfarin from protein binding sites, raising free Warfarin levels…</p>
              <p className="t-ai-alt"><IconZap size={14} className="inline-icon" /> Searching for safe alternatives…</p>
              <p className="t-ai"><span className="t-label">MedicaLLM</span> Consider <strong>Acetaminophen</strong> as a safer analgesic alternative. It does not affect platelet function or anticoagulant activity.</p>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Features ─── */}
      <section id="features" className="section">
        <div className="section-inner">
          <h2 className="section-title">Everything You Need for<br /><span className="gradient-text">Smarter Medical Decisions</span></h2>
          <p className="section-sub">From quick drug lookups to full patient safety analyses — MedicaLLM has you covered.</p>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="feature-card">
                <span className="feature-icon">{f.icon}</span>
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
          <h2 className="section-title">How It Works</h2>
          <p className="section-sub">Get from question to answer in four simple steps.</p>
          <div className="steps-grid">
            {STEPS.map((s) => (
              <div key={s.num} className="step-card">
                <span className="step-num">{s.num}</span>
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
          <h2 className="section-title">Simple, Transparent Pricing</h2>
          <p className="section-sub">Start free. Upgrade when you're ready.</p>
          <div className="pricing-grid">
            {PLANS.map((p) => (
              <div key={p.name} className={`pricing-card${p.highlighted ? ' highlighted' : ''}`}>
                {p.highlighted && <span className="popular-badge">Most Popular</span>}
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
                  className={p.highlighted ? 'btn-primary full' : 'btn-outline full'}
                  onClick={() => navigate('/register')}
                >
                  {p.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Why Us ─── */}
      <section id="why-us" className="section alt">
        <div className="section-inner">
          <h2 className="section-title">Why MedicaLLM?</h2>
          <p className="section-sub">Built different — by design.</p>
          <div className="reasons-grid">
            {REASONS.map((r) => (
              <div key={r.title} className="reason-card">
                <span className="reason-icon">{r.icon}</span>
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
            <h2 className="section-title">Get In Touch</h2>
            <p className="section-sub">Have questions, need a demo, or want to discuss enterprise plans? We'd love to hear from you.</p>
            <div className="contact-details">
              <div className="contact-item">
                <IconMail size={24} />
                <div>
                  <strong>Email</strong>
                  <p>contact@medicallm.ai</p>
                </div>
              </div>
              <div className="contact-item">
                <IconMessageCircle size={24} />
                <div>
                  <strong>Live Chat</strong>
                  <p>Available Mon–Fri, 9am–6pm EST</p>
                </div>
              </div>
              <div className="contact-item">
                <IconMapPin size={24} />
                <div>
                  <strong>Location</strong>
                  <p>Istanbul, Turkey </p>
                </div>
              </div>
            </div>
          </div>
          <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
            <div className="form-row">
              <input type="text" placeholder="Your Name" required />
              <input type="email" placeholder="Your Email" required />
            </div>
            <input type="text" placeholder="Subject" />
            <textarea rows="5" placeholder="Your Message" required />
            <button type="submit" className="btn-primary full">Send Message</button>
          </form>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <div className="nav-logo"><IconStethoscope size={24} className="logo-svg" /> MedicaLLM</div>
            <p>AI-powered medical intelligence.<br />Evidence-based. Privacy-first.</p>
          </div>
          <div className="footer-links">
            <div>
              <h4>Product</h4>
              <button onClick={() => scrollTo('features')}>Features</button>
              <button onClick={() => scrollTo('pricing')}>Pricing</button>
              <button onClick={() => scrollTo('how-it-works')}>How It Works</button>
            </div>
            <div>
              <h4>Company</h4>
              <button onClick={() => scrollTo('why-us')}>About</button>
              <button onClick={() => scrollTo('contact')}>Contact</button>
              <button>Careers</button>
            </div>
            <div>
              <h4>Legal</h4>
              <button>Privacy Policy</button>
              <button>Terms of Service</button>
              <button>HIPAA Compliance</button>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 MedicaLLM. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
