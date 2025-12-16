import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import Patients from './pages/Patients';
import DrugSearch from './pages/DrugSearch';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/chat" element={<Chat />} />
        <Route path="/drug-search" element={<DrugSearch />} />
        <Route path="/patients" element={<Patients />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Navigate to="/chat" />} />
        <Route path="*" element={<Navigate to="/chat" />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
