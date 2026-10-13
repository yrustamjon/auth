import client from './client.js';

export const getSession = () => client.get('/api/session/');
export const getAccountProfile = () => client.get('/api/profile/');
export const changeAccountPassword = data => client.post('/api/profile/password/', data);
export const registerAccount = data => client.post('/api/register/',data);
export const getRegistrationStatus = () => client.get('/api/registration/status/');

export const adminLogin = (username, password) =>
  client.post('/api/admin/login', { username, password });

export const adminLogout = () =>
  client.post('/api/admin/logout');

export const systemLogin = (username, password) =>
  client.post('/api/system/login', { username, password });

export const systemLogout = () =>
  client.post('/api/system/logout');

export const getToken = () =>
  client.get('/api/token/');

export const switchOrganization = (organization_id) =>
  client.post('/api/switch-organization/', { organization_id });
