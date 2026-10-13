import { ToastContext } from '../contexts/toast';
import { Outlet } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';
export default function AdminLayout() {
  const { toasts, addToast, removeToast } = useToast();
  return <ToastContext.Provider value={addToast}><AppShell><Outlet /></AppShell><ToastContainer toasts={toasts} onRemove={removeToast} /></ToastContext.Provider>;
}
