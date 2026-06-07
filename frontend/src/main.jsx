import React, { useEffect, useState, useMemo, useCallback } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
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
  persistLang,
  readPersistedLang,
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
  // Single source of truth = localStorage. URL prefixes added complexity
  // (redirects, race conditions, two-way sync) without delivering value
  // for a two-language MVP. The toggle just flips state + persists; URL
  // is never touched.
  const [lang, setLangState] = useState(() => readPersistedLang() || DEFAULT_LANG);

  useEffect(() => {
    persistLang(lang);
    if (typeof document !== 'undefined') document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next) => {
    if (!SUPPORTED_LANGS.includes(next)) return;
    setLangState(next);
  }, []);

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
          {/* Legacy aliases — older bookmarks and Google indices may still
              point at /en/* or /tr/*. Redirect to the bare URL; language
              now lives in localStorage only. */}
          <Route path="/en" element={<Navigate to="/" replace />} />
          <Route path="/en/login" element={<Navigate to="/login" replace />} />
          <Route path="/en/register" element={<Navigate to="/register" replace />} />
          <Route path="/tr" element={<Navigate to="/" replace />} />
          <Route path="/tr/login" element={<Navigate to="/login" replace />} />
          <Route path="/tr/register" element={<Navigate to="/register" replace />} />

          {/* Public routes — single, language-agnostic URL space. */}
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
