import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { getSession } from '../api/auth';
export default function ProtectedRoute({ panel, children }) {
  const [state,setState] = useState({loading:true,data:null,error:false});
  const location = useLocation();
  useEffect(() => {
    let alive=true;
    getSession().then(r => { if(alive) setState({loading:false,data:r.data,error:false}); }).catch(() => { if(alive) setState({loading:false,data:null,error:true}); });
    return () => {alive=false;};
  }, []);
  if(state.loading) return <div className="empty-state" role="status"><Loader2 size={24} className="animate-spin" />Sessiya tekshirilmoqda...</div>;
  if(state.error) return <div className="public-card"><div className="alert-error">Server bilan bog‘lanib bo‘lmadi. Django serveri ishlayotganini tekshiring.</div><button className="btn-secondary mt-4" onClick={() => window.location.reload()}>Qayta urinish</button></div>;
  if(!state.data?.authenticated) return <Navigate to={panel === 'superadmin' ? '/system/login' : '/login'} state={{from:location.pathname}} replace />;
  if(state.data.panel==='admin' && state.data.workspace && (state.data.workspace.status!=='approved'||!state.data.workspace.active)) return <Navigate to="/registration/status" replace/>;
  if(state.data.panel !== panel) return <Navigate to={state.data.panel === 'superadmin' ? '/system/dashboard' : '/dashboard'} replace />;
  if(panel==='admin' && state.data.workspace?.kind==='personal' && !location.pathname.startsWith('/personal/')) return <Navigate to="/personal/computer" replace/>;
  if(panel==='admin' && state.data.workspace?.kind!=='personal' && location.pathname.startsWith('/personal/')) return <Navigate to="/dashboard" replace/>;
  return children;
}

