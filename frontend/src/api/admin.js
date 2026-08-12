import client from './client';

// Users
export const getUsers = () => client.get('/api/users/');
export const createUser = (data) => client.post('/api/users/', data);
export const updateUser = (id, data) => client.patch(`/api/users/${id}/`, data);
export const deleteUser = (id) => client.delete(`/api/users/${id}/`);

// Roles
export const getRoles = () => client.get('/api/roles');
export const createRole = (data) => client.post('/api/roles', data);
export const updateRole = (id, data) => client.put(`/api/roles/${id}/`, data);
export const deleteRole = (id) => client.delete(`/api/roles/${id}/`);

// Devices
export const getDevices = () => client.get('/api/devices');
export const createDevice = (data) => client.post('/api/devices', data);
export const updateDevice = (id, data) => client.put(`/api/devices/${id}/`, data);
export const deleteDevice = (id) => client.delete(`/api/devices/${id}/`);

// Logs
export const getLogs = () => client.get('/api/access-logs');

// Biometric — Face
export const getBiometricStatus = (id) => client.get(`/api/users/${id}/biometric-status/`);
export const uploadFace = (id, file) => {
  const fd = new FormData();
  fd.append('image', file);
  return client.post(`/api/users/${id}/face/`, fd, { headers: { 'Content-Type': undefined } });
};
export const deleteFace = (id) => client.delete(`/api/users/${id}/face/`);

// Biometric — Fingerprint
export const getFingerprints = (id) => client.get(`/api/users/${id}/fingerprint/`);
export const deleteFingerprint = (userId, id) => client.delete(`/api/users/${userId}/fingerprint/${id}/`);
export const startFingerprintSession = (userId) =>
  client.post('/api/fingerprint/phone/start/', { user_id: userId });
export const getFingerprintSessionStatus = (sessionId) =>
  client.get(`/api/fingerprint/phone/status/${sessionId}/`);
