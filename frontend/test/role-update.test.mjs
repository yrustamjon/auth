import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../src/api/client.js';
import { updateRole } from '../src/api/admin.js';
test('role edit changes both name and active state using separate backend branches',async()=>{
 const calls=[];
 client.defaults.adapter=async config=>{calls.push({method:config.method,data:JSON.parse(config.data)});return {data:{ok:true},status:200,statusText:'OK',headers:{},config};};
 await updateRole(3,{name:'Xodim',is_active:false});
 assert.deepEqual(calls,[{method:'patch',data:{name:'Xodim'}},{method:'patch',data:{is_active:false}}]);
});
