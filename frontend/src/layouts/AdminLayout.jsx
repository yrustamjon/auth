import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { createContext, useContext } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';

export const ToastContext = createContext(null);
export const useAdminToast = () => useContext(ToastContext);

function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { toasts, addToast, removeToast } = useToast();

  return (
    <ToastContext.Provider value={addToast}>
      <div className="app-shell" style={{ background: '#0f0f14' }}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(v => !v)} />
        <div className="app-content">
          <Header />
          <main className="app-main">
            <Outlet />
          </main>
        </div>
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </ToastContext.Provider>
  );
}

export default AdminLayout;
