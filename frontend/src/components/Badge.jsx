export default function Badge({ children, variant = 'default', dot = false }) {
  return <span className={`badge badge-${variant}`}>{dot && <span className="badge-dot" />}{children}</span>;
}
