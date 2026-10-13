import { useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';
export default function Modal({ isOpen, onClose, title, children, footer, size = 'md' }) {
  const ref = useRef(null);
  const titleId = useId();
  const closeRef = useRef(onClose); closeRef.current = onClose;
  useEffect(() => {
    if (!isOpen) return;
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const el = ref.current;
    const focusables = () => [...el.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex="0"]')].filter(node => node.getClientRects().length);
    (focusables()[0] || el).focus();
    function handleKey(e) {
      if (e.key === 'Escape') { e.stopPropagation(); closeRef.current(); }
      if (e.key === 'Tab') {
        const nodes = focusables(); const first = nodes[0]; const last = nodes[nodes.length-1];
        if (!nodes.length) { e.preventDefault(); el.focus(); }
        else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }
    el.addEventListener('keydown', handleKey);
    return () => { document.body.style.overflow = overflow; el.removeEventListener('keydown', handleKey); previous?.focus(); };
  }, [isOpen]);
  if (!isOpen) return null;
  const widths = { sm:440, md:520, lg:700, xl:860 };
  return <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}><div ref={ref} className="modal-card animate-scale-in" style={{maxWidth:widths[size] || 520}} role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1}><div className="modal-header"><h3 id={titleId}>{title}</h3><button className="icon-button" aria-label="Oynani yopish" onClick={onClose}><X size={18} /></button></div><div className="modal-body">{children}</div>{footer && <div className="modal-footer">{footer}</div>}</div></div>;
}
