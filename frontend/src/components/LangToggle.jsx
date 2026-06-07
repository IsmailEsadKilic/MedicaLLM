import React from 'react';
import { useLang, SUPPORTED_LANGS } from '../i18n/lang';
import './LangToggle.css';

const LANG_LABELS = { en: 'EN', tr: 'TR' };

/**
 * Compact language switcher used outside the Landing page (Login,
 * Register, eventually any standalone form). Cycles between supported
 * languages — same behaviour as the Landing nav button, just with a
 * smaller chrome that fits inside an auth corner.
 */
export default function LangToggle({ className = '' }) {
  const { lang, setLang } = useLang();
  const cycle = () => {
    const i = SUPPORTED_LANGS.indexOf(lang);
    setLang(SUPPORTED_LANGS[(i + 1) % SUPPORTED_LANGS.length]);
  };
  return (
    <button
      type="button"
      className={`lang-toggle ${className}`}
      onClick={cycle}
      aria-label={`Language: ${LANG_LABELS[lang]}`}
      title={`Language: ${LANG_LABELS[lang]}`}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
      <span>{LANG_LABELS[lang]}</span>
    </button>
  );
}
