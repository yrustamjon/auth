import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

const icons = {
  success: <CheckCircle size={18} className="text-emerald-400" />,
  error: <XCircle size={18} className="text-red-400" />,
  warning: <AlertCircle size={18} className="text-amber-400" />,
  info: <Info size={18} className="text-blue-400" />,
};

const borderColors = {
  success: 'border-l-emerald-500',
  error: 'border-l-red-500',
  warning: 'border-l-amber-500',
  info: 'border-l-blue-500',
};

function Toast({ id, message, type = 'success', onRemove }) {
  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border-l-4 ${borderColors[type]} glass-dark shadow-2xl min-w-72 max-w-sm animate-fade-in`}
      style={{ borderTopColor: 'rgba(255,255,255,0.06)', borderRightColor: 'rgba(255,255,255,0.06)', borderBottomColor: 'rgba(255,255,255,0.06)' }}
    >
      <span className="shrink-0">{icons[type]}</span>
      <span className="text-sm text-slate-200 flex-1">{message}</span>
      <button
        onClick={() => onRemove(id)}
        className="shrink-0 text-slate-500 hover:text-slate-300 transition-colors"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, onRemove }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onRemove={onRemove} />
      ))}
    </div>
  );
}

export default Toast;
