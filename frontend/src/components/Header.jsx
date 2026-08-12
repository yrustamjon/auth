import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bell, ChevronDown, LogOut, User, Settings, Search } from 'lucide-react';
import { adminLogout } from '../api/auth';

const routeTitles = {
  '/dashboard': 'Dashboard',
  '/users': 'Users',
  '/roles': 'Roles',
  '/devices': 'Devices',
  '/logs': 'Access Logs',
};

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const title = routeTitles[location.pathname] || 'Admin Panel';

  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = async () => {
    try { await adminLogout(); } catch (_) {}
    navigate('/login');
  };

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 40, flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 1.5rem', height: '64px',
      background: 'rgba(15, 15, 20, 0.85)',
      backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      {/* Title */}
      <div>
        <h1 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#f1f5f9' }}>{title}</h1>
        <p style={{ fontSize: '0.75rem', color: '#475569' }}>
          {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Search */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.5rem 0.75rem', borderRadius: '0.75rem',
          fontSize: '0.75rem', color: '#64748b', cursor: 'pointer',
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <Search size={15} />
          <span>Quick search...</span>
          <kbd style={{ marginLeft: '0.5rem', fontSize: '0.7rem', padding: '0.125rem 0.375rem', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', color: '#475569' }}>⌘K</kbd>
        </div>

        {/* Bell */}
        <button style={{
          position: 'relative', padding: '0.5rem', borderRadius: '0.75rem',
          color: '#64748b', background: 'transparent', border: 'none', cursor: 'pointer',
        }}>
          <Bell size={18} />
          <span style={{
            position: 'absolute', top: '6px', right: '6px',
            width: '8px', height: '8px', borderRadius: '50%',
            background: '#6366f1', boxShadow: '0 0 6px #6366f1',
          }} />
        </button>

        {/* Profile */}
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(v => !v)}
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
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            }}>A</div>
            <div style={{ textAlign: 'left' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#e2e8f0' }}>Admin</p>
              <p style={{ fontSize: '0.75rem', color: '#475569' }}>Administrator</p>
            </div>
            <ChevronDown size={14} style={{ color: '#64748b', transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
          </button>

          {dropdownOpen && (
            <div className="animate-fade-in" style={{
              position: 'absolute', right: 0, top: '100%', marginTop: '0.5rem',
              width: '208px', borderRadius: '0.75rem', padding: '0.25rem',
              background: '#141420', border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0 16px 40px rgba(0,0,0,0.4)', zIndex: 50,
            }}>
              <div style={{ padding: '0.625rem 0.75rem', marginBottom: '0.25rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#f1f5f9' }}>Admin</p>
                <p style={{ fontSize: '0.75rem', color: '#475569' }}>Logged in</p>
              </div>
              {[
                { icon: <User size={15} />, label: 'Profile' },
                { icon: <Settings size={15} />, label: 'Settings' },
              ].map(({ icon, label }) => (
                <button key={label} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '0.625rem',
                  padding: '0.5rem 0.75rem', fontSize: '0.875rem', color: '#94a3b8',
                  background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: '0.5rem',
                }}>
                  {icon} {label}
                </button>
              ))}
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: '0.25rem', paddingTop: '0.25rem' }}>
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
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
