/**
 * Language helpers — single source of truth for the URL-based locale
 * prefix used on the public marketing surface.
 *
 * Convention
 * ----------
 *   /              → English (default, no prefix)
 *   /tr            → Turkish
 *   /tr/login      → Turkish login
 *   /tr/register   → Turkish register
 *
 * Authenticated routes (chat, doctor panel, patient panel, admin) keep
 * their flat URL because the in-app UI hasn't been localised yet —
 * showing `/tr/chat` would be misleading.
 *
 * Helpers below are pure so they can be imported from any component
 * (LangProvider, Landing, Login, Register, NavBar, ...).
 */
import React from 'react';

export const SUPPORTED_LANGS = ['en', 'tr'];
export const DEFAULT_LANG = 'en';

const STORAGE_KEY = 'medicallm.lang';

/**
 * Strip the leading `/` and return the first path segment, or '' if
 * the path is just '/'.
 */
function firstSegment(pathname) {
  const trimmed = (pathname || '').replace(/^\/+/, '');
  if (!trimmed) return '';
  return trimmed.split('/')[0];
}

/**
 * Read the language out of the URL pathname. Returns 'en' (default)
 * when the first segment isn't a recognised lang code.
 */
export function langFromPath(pathname) {
  const seg = firstSegment(pathname);
  return SUPPORTED_LANGS.includes(seg) ? seg : DEFAULT_LANG;
}

/**
 * Strip the lang segment off a pathname so we can re-prefix it under a
 * different language without compounding `/tr/tr/...`.
 */
export function stripLangFromPath(pathname) {
  const seg = firstSegment(pathname);
  if (!SUPPORTED_LANGS.includes(seg)) return pathname || '/';
  // Drop '/<lang>' off the front. If the result is empty the user was
  // on '/<lang>' itself, which maps to '/'.
  const rest = pathname.slice(1 + seg.length);
  return rest || '/';
}

/**
 * Build a URL that points at the given path under the given language.
 * `path` is always given without the lang prefix (e.g. '/login').
 */
export function buildLangPath(path, lang) {
  const normalised = path && path.startsWith('/') ? path : `/${path || ''}`;
  if (lang === DEFAULT_LANG) return normalised || '/';
  if (normalised === '/') return `/${lang}`;
  return `/${lang}${normalised}`;
}

/**
 * Persist the user's language choice. Same storage key as the older
 * landingStrings helper so a user landing without a URL prefix still
 * gets their last picked language.
 */
export function persistLang(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // localStorage may be unavailable in incognito quotas — ignore.
  }
}

export function readPersistedLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;
  } catch {
    // ignored
  }
  return null;
}

/**
 * Bridge helper used by the Landing nav button: figure out where the
 * user "should" land when no URL hint is available.
 *
 * Priority: persisted choice → browser default → English.
 */
export function detectInitialLang() {
  const saved = readPersistedLang();
  if (saved) return saved;
  if (typeof navigator !== 'undefined') {
    const nav = (navigator.language || '').toLowerCase();
    if (nav.startsWith('tr')) return 'tr';
  }
  return DEFAULT_LANG;
}

/**
 * React context exposing the active language and a switcher to children.
 * Provided once at the top of the app (main.jsx) so any page can
 * consume it via `useLang()`.
 */
export const LangContext = React.createContext({
  lang: DEFAULT_LANG,
  setLang: () => {},
});

export function useLang() {
  return React.useContext(LangContext);
}


/**
 * Convenience hook: returns a callback that prefixes a path with the
 * currently active language (or no prefix when the active language is
 * the default). Use it from public-facing pages that link to other
 * public pages so the user doesn't fall back to English mid-flow.
 *
 *   const lp = useLangPath();
 *   navigate(lp('/login'));
 *   <Link to={lp('/register')} />
 */
export function useLangPath() {
  const { lang } = useLang();
  return React.useCallback((path) => buildLangPath(path, lang), [lang]);
}
