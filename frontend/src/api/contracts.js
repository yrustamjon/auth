export function readCollection(payload, key) {
  if (Array.isArray(payload)) return payload;
  if (key && Array.isArray(payload?.[key])) return payload[key];
  throw new Error('Ma’lumot formati noto‘g‘ri');
}
export function readMetric(result, key) {
  if (result.status !== 'fulfilled') return {value:null,error:result.reason?.message || 'Yuklashda xato'};
  try { return {value:readCollection(result.value.data,key).length,error:null}; }
  catch(error) { return {value:null,error:error.message}; }
}
export function loginDestination(panel, requested, kind) {
  const fallback = panel === 'superadmin' ? '/system/dashboard' : kind==='personal' ? '/personal/computer' : '/dashboard';
  if (typeof requested !== 'string' || !requested.startsWith('/') || requested.startsWith('//') || requested.includes('\\')) return fallback;
  const allowed = panel === 'superadmin' ? ['/system/dashboard','/system/organizations','/system/admins','/system/applications'] : ['/personal/computer','/personal/biometrics','/personal/history','/personal/agent-events',...(kind==='personal'?[]:['/dashboard','/users','/roles','/devices','/logs','/agent-events']),'/device-enroll/approval/','/device-enroll/'];
  return allowed.some(path => requested === path || requested === path + '/' || (path === '/device-enroll/' && /^\/device-enroll\/[A-Za-z0-9_-]+\/?$/.test(requested))) ? requested : fallback;
}
export function shouldRedirectUnauthorized(status, requestUrl, pathname) {
  return status === 401 && !/\/login\/?$/.test(requestUrl || '') && !pathname.includes('login') && !/\/api\/(session|fingerprint\/phone|face\/phone|devices\/browser-enrollment)/.test(requestUrl || '');
}
export function errorMessage(error, fallback='Amalni bajarib bo‘lmadi') {
  const data = error?.response?.data;
  return data?.detail || data?.error || error?.message || fallback;
}

