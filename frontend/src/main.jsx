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
  const [lang, setLangState] = useState(urlLang);

  // Keep the state in sync with the URL when the user navigates via
  // back/forward or by typing a different path.
  useEffect(() => {
    if (urlLang !== lang) setLangState(urlLang);
  }, [urlLang, lang]);

  // Persist + reflect on <html lang> for screen readers.
  useEffect(() => {
    persistLang(lang);
    if (typeof document !== 'undefined') document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback(
    (next) => {
      if (!SUPPORTED_LANGS.includes(next)) return;
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
 * Authenticated routes — flat under '/' only, NOT mirrored under '/tr'.
 * The in-app UI is English-only for now; a future change would
 * promote these to the localised branch.
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
          {/* Localised public routes — Turkish branch. */}
          <Route path="/tr">
            {PublicRoutes()}
          </Route>

          {/* English (default) public routes + the rest of the app. */}
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
