import React, { useEffect, useState, useMemo, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import Landing from './pages/Landing';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import DrugSearch from './pages/DrugSearch';
import Admin from './pages/Admin';
import PatientLayout from './pages/patient/PatientLayout';
import PatientDashboard from './pages/patient/PatientDashboard';
import PatientProfile from './pages/patient/PatientProfile';
import PatientMedications from './pages/patient/PatientMedications';
import PatientDoctors from './pages/patient/PatientDoctors';
import CookieBanner from './components/CookieBanner';
import {
  LangContext,
  SUPPORTED_LANGS,
  DEFAULT_LANG,
  langFromPath,
  stripLangFromPath,
  buildLangPath,
  persistLang,
  readPersistedLang,
  isPublicLocalisedPath,
} from './i18n/lang';

/**
 * Audit F4: protect routes that require an authenticated session so each
 * page no longer has to invent its own auth-redirect logic.
 */
function RequireAuth({ children }) {
  const location = useLocation();
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');
  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

/**
 * Reads lang from the URL on every navigation, exposes it via context,
 * and provides a setLang() that swaps the prefix in-place without
 * losing the rest of the path or hash. Lives inside the Router so it
 * can call useLocation / useNavigate.
 */
function LangProvider({ children }) {
  const location = useLocation();
  const navigate = useNavigate();

  const urlLang = langFromPath(location.pathname);
  // The URL only carries lang on public marketing routes (/, /en, /login,
  // /en/login, /register, /en/register). Authed routes like /chat or /admin
  // are NOT mirrored under /en — the in-app surface is one URL space and
  // the language is purely a stored preference. Detect which kind of
  // route we're on so we know whether to round-trip language changes
  // through the URL or just through localStorage.
  const isPublicRoute = isPublicLocalisedPath(location.pathname);
  // Did the URL explicitly carry the /en prefix? Bare paths like /login
  // are ambiguous — they could mean "TR (default)" or "EN with persistence
  // suppressed". We treat bare as default UNLESS persistence says otherwise,
  // in which case we redirect to the explicit /en/... form so the URL
  // stays canonical.
  const urlIsExplicit =
    location.pathname === '/en' || location.pathname.startsWith('/en/');

  const [lang, setLangState] = useState(() => {
    if (isPublicRoute) {
      // Explicit /en/... wins. Otherwise honour persisted choice so a
      // user who picked English previously isn't silently dropped back
      // to Turkish when they type a bare URL.
      if (urlIsExplicit) return urlLang;
      return readPersistedLang() || DEFAULT_LANG;
    }
    return readPersistedLang() || urlLang;
  });

  // Keep the state in sync with the URL when the user navigates via
  // back/forward or by typing a different path — but only on public
  // routes where the URL is the source of truth.
  useEffect(() => {
    if (!isPublicRoute) return;
    if (urlIsExplicit && urlLang !== lang) setLangState(urlLang);
  }, [urlLang, urlIsExplicit, lang, isPublicRoute]);

  // If the URL is a bare public path but the user's persisted choice is
  // English, re-prefix the URL so /login becomes /en/login. This keeps
  // language sticky across direct URL access without losing the user's
  // earlier choice the next time the persistLang() effect fires.
  useEffect(() => {
    if (!isPublicRoute || urlIsExplicit) return;
    if (lang === DEFAULT_LANG) return;
    const newPath = buildLangPath(location.pathname, lang);
    if (newPath === location.pathname) return;
    navigate(`${newPath}${location.search || ''}${location.hash || ''}`, { replace: true });
  }, [isPublicRoute, urlIsExplicit, lang, location.pathname, location.search, location.hash, navigate]);

  // Persist + reflect on <html lang> for screen readers.
  useEffect(() => {
    persistLang(lang);
    if (typeof document !== 'undefined') document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback(
    (next) => {
      if (!SUPPORTED_LANGS.includes(next)) return;
      // In-app routes: just flip state + persist. No navigation.
      if (!isPublicLocalisedPath(location.pathname)) {
        setLangState(next);
        return;
      }
      // Public routes: flip state immediately AND re-prefix the URL.
      // The state update matters because if `next` is the default lang
      // we navigate to a bare URL (e.g. /en → /), and the redirect-to-
      // canonical-form effect below would otherwise bounce us back to
      // /en (because the URL alone can't disambiguate bare-default vs
      // bare-with-persistence). Updating state first lets that effect
      // see lang === DEFAULT_LANG and skip the bounce.
      setLangState(next);
      const bare = stripLangFromPath(location.pathname);
      const newPath = buildLangPath(bare, next);
      navigate(`${newPath}${location.search || ''}${location.hash || ''}`, { replace: true });
    },
    [location.pathname, location.search, location.hash, navigate],
  );

  const value = useMemo(() => ({ lang, setLang }), [lang, setLang]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

/**
 * The set of public routes that we mirror under both `/...` (English)
 * and `/tr/...` (Turkish). Pages read their language from the LangContext
 * provider above, so the same component is reused for both branches.
 */
function PublicRoutes() {
  return (
    <>
      <Route index element={<Landing />} />
      <Route path="login" element={<Login />} />
      <Route path="register" element={<Register />} />
    </>
  );
}

/**
 * Authenticated routes — flat under '/' only, NOT mirrored under '/en'.
 * In-app UI flips its strings via the stored language preference rather
 * than the URL.
 */
function AuthedRoutes() {
  return (
    <>
      <Route
        path="/chat"
        element={
          <RequireAuth>
            <Chat />
          </RequireAuth>
        }
      />
      <Route
        path="/drug-search"
        element={
          <RequireAuth>
            <DrugSearch />
          </RequireAuth>
        }
      />
      {/* Admin handles its own login form, no RequireAuth wrapper. */}
      <Route path="/admin" element={<Admin />} />

      {/* Legacy aliases — the entire doctor panel lives inside /chat now. */}
      <Route path="/drug-matrix" element={<Navigate to="/chat" replace />} />
      <Route path="/patients" element={<Navigate to="/chat" replace />} />
      <Route path="/doctor/*" element={<Navigate to="/chat" replace />} />

      {/* Patient Panel */}
      <Route
        path="/patient"
        element={
          <RequireAuth>
            <PatientLayout />
          </RequireAuth>
        }
      >
        <Route index element={<PatientDashboard />} />
        <Route path="profile" element={<PatientProfile />} />
        <Route path="medications" element={<PatientMedications />} />
        <Route path="doctors" element={<PatientDoctors />} />
      </Route>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <LangProvider>
        <Routes>
          {/* Localised public routes — English branch. Turkish lives at
              the bare path (it is the default language for this Turkey-
              first product), so /en/* is the only explicit lang prefix. */}
          <Route path="/en">
            {PublicRoutes()}
          </Route>

          {/* Legacy alias: anyone hitting /tr after the default flip still
              lands on the (now bare) Turkish surface instead of 404'ing. */}
          <Route path="/tr" element={<Navigate to="/" replace />} />
          <Route path="/tr/login" element={<Navigate to="/login" replace />} />
          <Route path="/tr/register" element={<Navigate to="/register" replace />} />

          {/* Default (Turkish) public routes + the rest of the app. */}
          <Route path="/">
            {PublicRoutes()}
          </Route>

          {AuthedRoutes()}

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <CookieBanner />
      </LangProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
