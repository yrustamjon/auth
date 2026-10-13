export default function StatCard({ icon, title, value, subtitle, color = 'indigo' }) {
  return <div className="stat-card"><div className="stat-top"><div className={`stat-icon stat-icon-${color}`}>{icon}</div><span>UMUMIY</span></div><div className="stat-value">{value ?? '—'}</div><div className="stat-label">{title}</div>{subtitle && <div className="stat-subtitle">{subtitle}</div>}</div>;
}
