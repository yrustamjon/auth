import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../src/api/client.js';
import { updateRole } from '../src/api/admin.js';
import { attachAdminToOrg } from '../src/api/superadmin.js';
client.defaults.adapter=async config=>({data:{},status:200,statusText:'OK',headers:{},config});
test('role edit uses backend PATCH contract',async()=>{
 const response=await updateRole(7,{name:'Reader'});
 assert.equal(response.config.method,'patch');
 assert.equal(response.config.url,'/api/roles/7/');
});
test('organization attachment passes organization_id query',async()=>{
 const response=await attachAdminToOrg(9,3);
 assert.equal(response.config.params.organization_id,3);
 assert.equal(response.config.method,'patch');
});
