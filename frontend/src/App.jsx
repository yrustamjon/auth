import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';

import AdminLayout from './layouts/AdminLayout';
import SystemLayout from './layouts/SystemLayout';
import ProtectedRoute from './components/ProtectedRoute';

import ProductSite from './pages/ProductSite';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Roles from './pages/Roles';
import Devices from './pages/Devices';
import Logs from './pages/Logs';

import SystemDashboard from './pages/system/SystemDashboard';
import Organizations from './pages/system/Organizations';
import Admins from './pages/system/Admins';
import DeviceScan from './pages/DeviceScan';
import DeviceScanner from './pages/DeviceScanner';
import DeviceApproval from './pages/DeviceApproval';
import MobileFingerprint from './pages/MobileFingerprint';
import RegistrationStatus from './pages/RegistrationStatus';
import Applications from './pages/system/Applications';
import PersonalWorkspace from './pages/PersonalWorkspace';
import Profile from './pages/Profile';
import AgentEvents from './pages/AgentEvents';

function LoginRedirect({ panel }) {
  const location=useLocation();
  const params=new URLSearchParams(location.search);
  params.set('login',panel);
  return <Navigate to={'/?'+params.toString()} state={location.state} replace/>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/" element={<ProductSite />} />
        <Route path="/product" element={<ProductSite section="product" />} />
        <Route path="/downloads" element={<ProductSite section="downloads" />} />
        <Route path="/guide" element={<ProductSite section="guide" />} />
        <Route path="/registration/status" element={<RegistrationStatus />} />
        <Route path="/login" element={<LoginRedirect panel="admin" />} />
        <Route path="/system/login" element={<LoginRedirect panel="superadmin" />} />
        <Route path="/device/scan" element={<DeviceScan />} />
        <Route path="/device-enroll/:token" element={<DeviceApproval />} />
        <Route path="/device-enroll/approval/" element={<DeviceApproval />} />
        <Route path="/mobile/fingerprint/:sessionId/" element={<MobileFingerprint />} />

        {/* Admin panel */}
        <Route element={<ProtectedRoute panel="admin"><AdminLayout /></ProtectedRoute>}>
          <Route path="personal/computer" element={<PersonalWorkspace section="computer" />} />
          <Route path="personal/biometrics" element={<PersonalWorkspace section="biometrics" />} />
          <Route path="personal/history" element={<PersonalWorkspace section="history" />} />
          <Route path="personal/agent-events" element={<AgentEvents />} />
          <Route path="personal/profile" element={<Profile />} />
          <Route path="profile" element={<Profile />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="users" element={<Users />} />
          <Route path="roles" element={<Roles />} />
          <Route path="devices" element={<Devices />} />
          <Route path="devices/scan-qr" element={<DeviceScanner />} />
          <Route path="devices/add/qr" element={<DeviceScanner />} />
          <Route path="logs" element={<Logs />} />
          <Route path="agent-events" element={<AgentEvents />} />
        </Route>

        {/* Superadmin panel */}
        <Route path="/system" element={<ProtectedRoute panel="superadmin"><SystemLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/system/dashboard" replace />} />
          <Route path="dashboard" element={<SystemDashboard />} />
          <Route path="organizations" element={<Organizations />} />
          <Route path="admins" element={<Admins />} />
          <Route path="applications" element={<Applications />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
