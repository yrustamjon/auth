import axios from 'axios';
import { shouldRedirectUnauthorized } from './contracts.js';
const client = axios.create({ withCredentials:true, headers:{'Content-Type':'application/json'} });
function cookie(name) {
  if (typeof document === 'undefined') return null;
  const part = document.cookie.split('; ').find(item => item.startsWith(name + '='));
  return part ? decodeURIComponent(part.slice(name.length+1)) : null;
}
client.interceptors.request.use(config => {
  const token = cookie('csrftoken');
  if (token) config.headers['X-CSRFToken'] = token;
  return config;
});
let sessionCheck = null;
client.interceptors.response.use(response => response, async error => {
  if (shouldRedirectUnauthorized(error.response?.status, error.config?.url, window.location.pathname)) window.location.assign(window.location.pathname.startsWith('/system') ? '/system/login' : '/login');
  // DRF SessionAuthentication uses 403 for anonymous requests as well.
  // Verify the session so genuine permission failures do not cause logout.
  if (error.response?.status === 403 && error.config?.url !== '/api/session/' && !/\/login\/?$/.test(error.config?.url || '') && !window.location.pathname.includes('login') && !/^\/(device|mobile)/.test(window.location.pathname)) {
    try {
      sessionCheck ??= client.get('/api/session/').finally(() => { sessionCheck = null; });
      const response = await sessionCheck;
      if (!response.data.authenticated) window.location.assign(window.location.pathname.startsWith('/system') ? '/system/login' : '/login');
    } catch { /* Preserve the original error when the session check is offline. */ }
  }
  return Promise.reject(error);
});
export default client;
