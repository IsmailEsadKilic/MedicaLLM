/**
 * Language helpers — single source of truth for the URL-based locale
 * prefix used on the public marketing surface.
 *
 * Convention
 * ----------
 *   /              → Turkish (default, no prefix — Turkey-first product)
 *   /en            → English landing
 *   /en/login      → English login
 *   /en/register   → English register
 *
 * Authenticated routes (chat, doctor panel, patient panel, admin) keep
 * their flat URL because the in-app UI flips language via stored
 * preference rather than the URL — `/en/chat` would imply a separate
 * surface, which it isn't.
 *
 * Helpers below are pure so they can be imported from any component
 * (LangProvider, Landing, Login, Register, NavBar, ...).
 */
import React from 'react';

export const SUPPORTED_LANGS = ['en', 'tr'];
// MedicaLLM is a Turkey-first product on a .tr domain — default to Turkish
// when the user has no recorded preference. English remains a one-click
// switch in Settings / the auth corner toggle.
export const DEFAULT_LANG = 'tr';

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
 * Priority: persisted choice → DEFAULT_LANG (Turkish, since the product
 * is Turkey-first). We deliberately don't fall back to navigator.language
 * any more — letting the browser locale flip the default surprises the
 * majority of users coming from a Turkish marketing channel.
 */
export function detectInitialLang() {
  const saved = readPersistedLang();
  if (saved) return saved;
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


/**
 * Convenience hook: pulls the right language tree out of a strings
 * table. Each strings module exports an object shaped like
 *   { en: { ...keys }, tr: { ...keys } }
 * and pages call `const t = useT(STRINGS)` to get the active tree.
 *
 * Falls back to English when the active language is missing from the
 * table (which would happen if a translation hasn't been written yet).
 */
export function useT(strings) {
  const { lang } = useLang();
  return strings[lang] ?? strings.en;
}


/**
 * The set of public route paths that we mirror under /tr. Everything else
 * (chat, admin, doctor panel, patient panel) is authenticated UI without
 * a localised URL twin — the language for those pages comes purely from
 * persisted state. Used by LangProvider to decide whether a setLang()
 * call should re-route the URL or just flip the in-memory preference.
 */
const PUBLIC_PATHS = ['', 'login', 'register'];

export function isPublicLocalisedPath(pathname) {
  const stripped = stripLangFromPath(pathname || '/');
  // Look at just the first segment of the lang-stripped path.
  const seg = stripped.replace(/^\/+/, '').split('/')[0];
  return PUBLIC_PATHS.includes(seg);
}
