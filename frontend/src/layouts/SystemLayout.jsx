import { useState } from 'react';
import { createContext, useContext } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Outlet } from 'react-router-dom';
import { LayoutDashboard, Building2, UserCog, Zap, ChevronRight, Bell, LogOut, ChevronDown } from 'lucide-react';
import { ToastContainer } from '../components/Toast';
import { useToast } from '../hooks/useToast';
import { systemLogout } from '../api/auth';

export const SystemToastContext = createContext(null);
export const useSystemToast = () => useContext(SystemToastContext);

const navItems = [
  { to: '/system/dashboard', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
  { to: '/system/organizations', icon: <Building2 size={18} />, label: 'Organizations' },
  { to: '/system/admins', icon: <UserCog size={18} />, label: 'Admins' },
];

function SystemSidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside
      className="app-sidebar"
      style={{
        width: collapsed ? '72px' : '240px',
        background: '#0a0a10',
        borderRight: '1px solid rgba(139,92,246,0.08)',
      }}
    >
      {/* Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        padding: '0 1rem', height: '64px', flexShrink: 0,
        borderBottom: '1px solid rgba(139,92,246,0.08)',
      }}>
        <div style={{
          width: '36px', height: '36px', borderRadius: '10px', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
          boxShadow: '0 0 20px rgba(139,92,246,0.4)',
        }}>
          <Zap size={18} color="white" fill="white" />
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <span style={{ display: 'block', fontSize: '0.875rem', fontWeight: 700, color: '#f1f5f9', whiteSpace: 'nowrap' }}>
              SuperAdmin
            </span>
            <span style={{ display: 'block', fontSize: '0.75rem', color: '#7c3aed', whiteSpace: 'nowrap' }}>
              System Control
            </span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '1rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {!collapsed && (
          <p style={{ padding: '0 0.75rem', marginBottom: '0.5rem', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#2e1065' }}>
            System
          </p>
        )}
        {navItems.map(({ to, icon, label }) => {
          const isActive = location.pathname === to;
          return (
            <NavLink
              key={to}
              to={to}
              className={`nav-item-violet${isActive ? ' active' : ''}`}
              style={collapsed ? { justifyContent: 'center', padding: '0.625rem 0.5rem' } : {}}
              title={collapsed ? label : undefined}
            >
              <span style={{ flexShrink: 0 }}>{icon}</span>
              {!collapsed && <span style={{ flex: 1 }}>{label}</span>}
              {!collapsed && isActive && <ChevronRight size={14} style={{ color: '#a78bfa' }} />}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div style={{ padding: '1rem 0.5rem', borderTop: '1px solid rgba(139,92,246,0.08)', flexShrink: 0 }}>
        <button
          onClick={onToggle}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: '0.75rem',
            fontSize: '0.75rem', color: '#475569', background: 'transparent', border: 'none',
            cursor: 'pointer', transition: 'all 0.2s',
          }}
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

function SystemHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const titles = {
    '/system/dashboard': 'System Dashboard',
    '/system/organizations': 'Organizations',
    '/system/admins': 'System Admins',
  };

  const handleLogout = async () => {
    try { await systemLogout(); } catch (_) {}
    navigate('/system/login');
  };

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 40,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 1.5rem', height: '64px', flexShrink: 0,
      background: 'rgba(10, 10, 16, 0.85)',
      backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(139,92,246,0.08)',
    }}>
      <div>
        <h1 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#f1f5f9' }}>
          {titles[location.pathname] || 'System'}
        </h1>
        <p style={{ fontSize: '0.75rem', color: '#6d28d9' }}>Superadmin Portal</p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button style={{
          position: 'relative', padding: '0.5rem', borderRadius: '0.75rem',
          color: '#64748b', background: 'transparent', border: 'none', cursor: 'pointer',
        }}>
          <Bell size={18} />
          <span style={{
            position: 'absolute', top: '6px', right: '6px',
            width: '8px', height: '8px', borderRadius: '50%',
            background: '#8b5cf6', boxShadow: '0 0 6px #8b5cf6',
          }} />
        </button>

        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setOpen(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.625rem',
              padding: '0.5rem 0.75rem', borderRadius: '0.75rem',
              background: 'transparent', border: 'none', cursor: 'pointer',
            }}
          >
            <div style={{
              width: '32px', height: '32px', borderRadius: '10px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.75rem', fontWeight: 700, color: 'white',
              background: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
            }}>S</div>
            <div style={{ textAlign: 'left' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#e2e8f0' }}>Super Admin</p>
              <p style={{ fontSize: '0.75rem', color: '#6d28d9' }}>System</p>
            </div>
            <ChevronDown size={14} style={{ color: '#64748b', transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
          </button>

          {open && (
            <div className="animate-fade-in" style={{
              position: 'absolute', right: 0, top: '100%', marginTop: '0.5rem',
              width: '192px', borderRadius: '0.75rem', padding: '0.25rem',
              background: '#0f0f1a', border: '1px solid rgba(139,92,246,0.12)',
              boxShadow: '0 16px 40px rgba(0,0,0,0.5)', zIndex: 50,
            }}>
              <div style={{ padding: '0.625rem 0.75rem 0.625rem', marginBottom: '0.25rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#f1f5f9' }}>Super Admin</p>
                <p style={{ fontSize: '0.75rem', color: '#64748b' }}>System access</p>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '0.625rem',
                  padding: '0.5rem 0.75rem', fontSize: '0.875rem', color: '#f87171',
                  background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: '0.5rem',
                }}
              >
                <LogOut size={15} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function SystemLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { toasts, addToast, removeToast } = useToast();

  return (
    <SystemToastContext.Provider value={addToast}>
      <div className="app-shell" style={{ background: '#0a0a10' }}>
        <SystemSidebar collapsed={collapsed} onToggle={() => setCollapsed(v => !v)} />
        <div className="app-content">
          <SystemHeader />
          <main className="app-main">
            <Outlet />
          </main>
        </div>
        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </SystemToastContext.Provider>
  );
}

export default SystemLayout;
