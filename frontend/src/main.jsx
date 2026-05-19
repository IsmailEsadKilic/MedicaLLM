import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
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

/**
 * Audit F4: protect routes that require an authenticated session so each
 * page no longer has to invent its own auth-redirect logic. The token is
 * still kept in `localStorage` (legacy contract); we only check for its
 * presence here. A full session-validity check is done by the backend on
 * every request.
 */
function RequireAuth({ children }) {
  const location = useLocation();
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');
  if (!token || !user) {
    // Send the user back to Login and remember where they were heading.
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
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

        {/*
          The Admin page handles its own login form; once the user is
          authenticated it stores `admin_token` in localStorage. We don't
          gate the page itself with RequireAdmin, since the page IS the
          gate. (Keeping this comment for the next reader.)
        */}
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

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
