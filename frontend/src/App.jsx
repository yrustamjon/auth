import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import AdminLayout from './layouts/AdminLayout';
import SystemLayout from './layouts/SystemLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Roles from './pages/Roles';
import Devices from './pages/Devices';
import Logs from './pages/Logs';

import SystemLogin from './pages/system/SystemLogin';
import SystemDashboard from './pages/system/SystemDashboard';
import Organizations from './pages/system/Organizations';
import Admins from './pages/system/Admins';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/system/login" element={<SystemLogin />} />

        {/* Admin panel */}
        <Route path="/" element={<AdminLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="users" element={<Users />} />
          <Route path="roles" element={<Roles />} />
          <Route path="devices" element={<Devices />} />
          <Route path="logs" element={<Logs />} />
        </Route>

        {/* Superadmin panel */}
        <Route path="/system" element={<SystemLayout />}>
          <Route index element={<Navigate to="/system/dashboard" replace />} />
          <Route path="dashboard" element={<SystemDashboard />} />
          <Route path="organizations" element={<Organizations />} />
          <Route path="admins" element={<Admins />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
