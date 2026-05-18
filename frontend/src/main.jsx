import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Landing from './pages/Landing';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import Patients from './pages/Patients';
import DrugSearch from './pages/DrugSearch';
import Admin from './pages/Admin';
import DoctorLayout from './pages/doctor/DoctorLayout';
import Dashboard from './pages/doctor/Dashboard';
import DoctorPatients from './pages/doctor/DoctorPatients';
import PatientDetail from './pages/doctor/PatientDetail';
import Research from './pages/doctor/Research';
import DrugMatrix from './pages/doctor/DrugMatrix';

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

/**
 * Admin pages additionally require a valid admin token (kept under
 * `admin_token`). This is set by the admin login flow.
 */
function RequireAdmin({ children }) {
  const adminToken = localStorage.getItem('admin_token');
  if (!adminToken) {
    return <Navigate to="/admin" replace />;
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
        <Route
          path="/patients"
          element={
            <RequireAuth>
              <Patients />
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

        {/* Doctor Panel */}
        <Route
          path="/doctor"
          element={
            <RequireAuth>
              <DoctorLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="patients" element={<DoctorPatients />} />
          <Route path="patients/:patientId" element={<PatientDetail />} />
          <Route path="drugs" element={<DrugMatrix />} />
          <Route path="research" element={<Research />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
