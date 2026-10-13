import { SystemToastContext } from '../contexts/toast';
import { Outlet } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';
export default function SystemLayout() {
  const { toasts, addToast, removeToast } = useToast();
  return <SystemToastContext.Provider value={addToast}><AppShell panel="superadmin"><Outlet /></AppShell><ToastContainer toasts={toasts} onRemove={removeToast} /></SystemToastContext.Provider>;
}
