function StatCard({ icon, title, value, subtitle, trend, color = 'indigo' }) {
  const colorMap = {
    indigo: {
      bg: 'rgba(99,102,241,0.12)',
      iconColor: '#6366f1',
      border: 'rgba(99,102,241,0.15)',
    },
    violet: {
      bg: 'rgba(139,92,246,0.12)',
      iconColor: '#8b5cf6',
      border: 'rgba(139,92,246,0.15)',
    },
    emerald: {
      bg: 'rgba(52,211,153,0.12)',
      iconColor: '#34d399',
      border: 'rgba(52,211,153,0.15)',
    },
    amber: {
      bg: 'rgba(251,191,36,0.12)',
      iconColor: '#fbbf24',
      border: 'rgba(251,191,36,0.15)',
    },
    rose: {
      bg: 'rgba(251,113,133,0.12)',
      iconColor: '#fb7185',
      border: 'rgba(251,113,133,0.15)',
    },
    blue: {
      bg: 'rgba(96,165,250,0.12)',
      iconColor: '#60a5fa',
      border: 'rgba(96,165,250,0.15)',
    },
  };

  const c = colorMap[color] || colorMap.indigo;

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div
          className="p-3 rounded-xl shrink-0"
          style={{ background: c.bg, border: `1px solid ${c.border}` }}
        >
          <span style={{ color: c.iconColor }}>{icon}</span>
        </div>
        {trend !== undefined && (
          <span
            className={`text-xs font-medium px-2 py-1 rounded-lg ${
              trend >= 0
                ? 'bg-emerald-500/10 text-emerald-400'
                : 'bg-red-500/10 text-red-400'
            }`}
          >
            {trend >= 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <div
          className="text-3xl font-bold tracking-tight"
          style={{ color: '#f1f5f9' }}
        >
          {value ?? '—'}
        </div>
        <div className="text-sm font-medium text-slate-400 mt-1">{title}</div>
        {subtitle && (
          <div className="text-xs text-slate-600 mt-1">{subtitle}</div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
