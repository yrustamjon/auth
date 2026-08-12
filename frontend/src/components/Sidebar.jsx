import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Shield, Monitor, FileText, Zap, ChevronRight } from 'lucide-react';

const navItems = [
  { to: '/dashboard', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
  { to: '/users', icon: <Users size={18} />, label: 'Users' },
  { to: '/roles', icon: <Shield size={18} />, label: 'Roles' },
  { to: '/devices', icon: <Monitor size={18} />, label: 'Devices' },
  { to: '/logs', icon: <FileText size={18} />, label: 'Access Logs' },
];

function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside
      className="app-sidebar"
      style={{
        width: collapsed ? '72px' : '240px',
        background: '#0d0d12',
        borderRight: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {/* Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        padding: '0 1rem', height: '64px', flexShrink: 0,
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div
          className="animate-pulse-glow"
          style={{
            width: '36px', height: '36px', borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            boxShadow: '0 0 16px rgba(99,102,241,0.4)',
          }}
        >
          <Zap size={18} color="white" fill="white" />
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <span style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, color: '#f1f5f9', whiteSpace: 'nowrap' }}>
              AdminPanel
            </span>
            <span style={{ display: 'block', fontSize: '0.75rem', color: '#475569', whiteSpace: 'nowrap' }}>
              Management Console
            </span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '1rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {!collapsed && (
          <p style={{ padding: '0 0.75rem', marginBottom: '0.5rem', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#1e293b' }}>
            Main Menu
          </p>
        )}
        {navItems.map(({ to, icon, label }) => {
          const isActive = location.pathname === to;
          return (
            <NavLink
              key={to}
              to={to}
              className={`nav-item${isActive ? ' active' : ''}`}
              style={collapsed ? { justifyContent: 'center', padding: '0.625rem 0.5rem' } : {}}
              title={collapsed ? label : undefined}
            >
              <span style={{ flexShrink: 0 }}>{icon}</span>
              {!collapsed && <span style={{ flex: 1 }}>{label}</span>}
              {!collapsed && isActive && <ChevronRight size={14} style={{ color: '#818cf8' }} />}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div style={{ padding: '1rem 0.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', flexShrink: 0 }}>
        <button
          onClick={onToggle}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem',
            fontSize: '0.75rem', color: '#475569', background: 'transparent', border: 'none',
            cursor: 'pointer', transition: 'all 0.2s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = '#94a3b8'}
          onMouseLeave={e => e.currentTarget.style.color = '#475569'}
        >
          <ChevronRight
            size={14}
            style={{ transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)', transition: 'transform 0.3s' }}
          />
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
