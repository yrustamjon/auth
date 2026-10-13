import client from './client.js';
const root='/api/devices/browser-enrollment/';
export const createEnrollment=()=>client.post(root+'session/',{});
export const enrollmentStatus=id=>client.get(root+'session/'+id+'/');
export const cancelEnrollment=id=>client.post(root+'session/'+id+'/cancel/',{});
export const enrollmentHelper=(id,platform,scan_token,architecture)=>client.post(root+'session/'+id+'/helper/'+platform+'/',{scan_token,architecture},{responseType:'blob'});
export const claimEnrollment=token=>client.post(root+'claim/',{token});
export const getApproval=()=>client.get(root+'approval/');
export const resolveEnrollment=(id,action,location)=>client.post(root+'session/'+id+'/'+action+'/',{location});

