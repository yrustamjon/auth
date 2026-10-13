import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';
const icons = { success:CheckCircle, error:XCircle, warning:AlertCircle, info:Info };
export default function Toast({ id, message, type = 'success', onRemove }) {
  const Icon = icons[type] || Info;
  return <div className={`toast toast-${type}`} role={type === 'error' ? 'alert' : 'status'}><Icon size={18} /><span className="flex-1">{message}</span><button className="icon-button" aria-label="Xabarni yopish" onClick={() => onRemove(id)}><X size={14} /></button></div>;
}
export function ToastContainer({ toasts, onRemove }) { return <div className="toast-container">{toasts.map(t => <Toast key={t.id} {...t} onRemove={onRemove} />)}</div>; }
