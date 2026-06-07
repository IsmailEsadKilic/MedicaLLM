import React, { useEffect, useState } from 'react';
import { useLang } from '../i18n/lang';
import './CookieBanner.css';

/**
 * KVKK / GDPR-friendly cookie consent strip.
 *
 * What we actually store today
 * ----------------------------
 * The site uses localStorage (not cookies) for three things, all of
 * which are STRICTLY NECESSARY for the app to work:
 *
 *   - `token`               : authentication JWT (required to use the app)
 *   - `user`                : cached user profile to avoid an extra round-trip
 *   - `medicallm.lang`      : the user's chosen UI language
 *   - `medicallm.developerMode` : per-user power-user toggle
 *
 * No analytics, marketing, or third-party tracking storage is used. The
 * banner is therefore informational + a "got it" affordance rather than
 * a real opt-in/opt-out matrix. We still let the user decline; doing
 * so simply collapses the banner — it doesn't disable the app, and the
 * strictly-necessary localStorage entries continue to be written
 * because they're not an opt-in choice under KVKK / GDPR.
 *
 * The user's choice itself is stored under `medicallm.cookies` so the
 * banner doesn't reappear on every visit. This is the only storage
 * the banner itself controls.
 */
const STORAGE_KEY = 'medicallm.cookies';

const COPY = {
  en: {
    text: 'We use only essential storage to keep you signed in and remember your language and theme. We do not run analytics, marketing, or third-party trackers.',
    learn: 'Learn more',
    accept: 'Got it',
    decline: 'Decline non-essential',
    title: 'Cookie & storage notice',
    detailIntro: 'MedicaLLM uses your browser\u2019s localStorage to keep the app working. Specifically:',
    detailItems: [
      { key: 'token', text: 'Authentication token (signs you in)' },
      { key: 'user', text: 'Cached profile (your name and account type)' },
      { key: 'medicallm.lang', text: 'Selected interface language' },
      { key: 'medicallm.developerMode', text: 'Optional developer-mode toggle' },
      { key: 'medicallm.cookies', text: 'Your response to this notice' },
    ],
    detailFooter: 'No analytics, marketing, or third-party trackers are loaded. All entries above are technically required for a logged-in session to function and are subject to KVKK Art. 5/2(c) (necessary for the performance of a contract).',
    close: 'Close',
  },
  tr: {
    text: 'Yalnızca oturumu açık tutmak ve dil/tema tercihinizi hatırlamak için zorunlu depolama kullanırız. Analitik, pazarlama veya üçüncü taraf takip aracı çalıştırmayız.',
    learn: 'Detaylar',
    accept: 'Tamam',
    decline: 'Gerekli olmayanları reddet',
    title: 'Çerez ve depolama bildirimi',
    detailIntro: 'MedicaLLM uygulamanın çalışması için tarayıcınızın localStorage alanını kullanır. Saklanan veriler:',
    detailItems: [
      { key: 'token', text: 'Kimlik doğrulama tokenı (oturumu açık tutar)' },
      { key: 'user', text: 'Profil bilgisi (ad ve hesap tipi)' },
      { key: 'medicallm.lang', text: 'Seçilen arayüz dili' },
      { key: 'medicallm.developerMode', text: 'İsteğe bağlı geliştirici modu' },
      { key: 'medicallm.cookies', text: 'Bu bildirime verdiğiniz yanıt' },
    ],
    detailFooter: 'Analitik, pazarlama veya üçüncü taraf takip aracı yüklenmez. Yukarıdaki kayıtlar oturumun çalışması için teknik olarak gereklidir ve KVKK 5/2(c) kapsamında "sözleşmenin ifası için gereklilik" istisnası içinde değerlendirilir.',
    close: 'Kapat',
  },
};

export default function CookieBanner() {
  const { lang } = useLang();
  const t = COPY[lang] ?? COPY.en;
  const [visible, setVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    try {
      const choice = localStorage.getItem(STORAGE_KEY);
      if (!choice) setVisible(true);
    } catch {
      // localStorage unavailable (private mode quotas) — show the banner
      // as a courtesy but don't error.
      setVisible(true);
    }
  }, []);

  const dismiss = (choice) => {
    try {
      localStorage.setItem(STORAGE_KEY, choice);
    } catch {
      // ignored
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <>
      <div className="cookie-banner" role="region" aria-label={t.title}>
        <p className="cookie-banner-text">{t.text}</p>
        <div className="cookie-banner-actions">
          <button
            type="button"
            className="cookie-btn cookie-btn-link"
            onClick={() => setShowDetails(true)}
          >
            {t.learn}
          </button>
          <button
            type="button"
            className="cookie-btn cookie-btn-secondary"
            onClick={() => dismiss('declined')}
          >
            {t.decline}
          </button>
          <button
            type="button"
            className="cookie-btn cookie-btn-primary"
            onClick={() => dismiss('accepted')}
          >
            {t.accept}
          </button>
        </div>
      </div>

      {showDetails && (
        <div
          className="cookie-modal-overlay"
          onClick={() => setShowDetails(false)}
          role="presentation"
        >
          <div
            className="cookie-modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="cookie-modal-title"
          >
            <button
              type="button"
              className="cookie-modal-close"
              onClick={() => setShowDetails(false)}
              aria-label={t.close}
            >
              ×
            </button>
            <h3 id="cookie-modal-title">{t.title}</h3>
            <p>{t.detailIntro}</p>
            <ul>
              {t.detailItems.map((item) => (
                <li key={item.key}>
                  <code>{item.key}</code>
                  <span>{item.text}</span>
                </li>
              ))}
            </ul>
            <p className="cookie-modal-footer">{t.detailFooter}</p>
          </div>
        </div>
      )}
    </>
  );
}
