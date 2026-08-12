import client from './client';

// Organizations
export const getOrganizations = () => client.get('/api/organizations/');
export const getOrganization = (id) => client.get(`/api/organizations/${id}/`);
export const createOrganization = (data) => client.post('/api/organizations/', data);
export const updateOrganization = (id, data) => client.patch(`/api/organizations/${id}/`, data);
export const deleteOrganization = (id) => client.delete(`/api/organizations/${id}/`);

// System admins
export const getSystemAdmins = () => client.get('/api/system/admins/');
export const getOrgAdmins = (orgId) => client.get(`/api/system/admins/?organization_id=${orgId}`);
export const createSystemAdmin = (data) => client.post('/api/system/admins/', data);
export const updateSystemAdmin = (id, data) => client.patch(`/api/system/admins/${id}/`, data);
export const deleteSystemAdmin = (id) => client.delete(`/api/system/admins/${id}/`);
export const forceLogoutAdmin = (id) => client.post(`/api/system/admins/${id}/force-logout/`);
export const attachAdminToOrg = (adminId, orgId) => client.patch(`/api/system/admins/${adminId}/`, { organization_id: orgId });
export const resetAdminAttempts = (id) => client.post(`/api/system/admins/${id}/reset-attempts/`);
export const toggleAdminLock = (id, locked) => client.patch(`/api/system/admins/${id}/`, { locked });
