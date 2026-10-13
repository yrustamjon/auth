import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../src/api/client.js';
let redirects=[];
globalThis.window={location:{pathname:'/users',assign:path=>redirects.push(path)}};
client.defaults.adapter=async config=>{
 if(config.url==='/api/session/') return {data:{authenticated:false},status:200,statusText:'OK',headers:{},config};
 throw {config,response:{status:403,data:{detail:'Authentication credentials were not provided.'}},message:'Forbidden'};
};
test('DRF 403 caused by expired session sends protected page to login',async()=>{
 redirects=[];
 await assert.rejects(client.get('/api/users/'));
 assert.deepEqual(redirects,['/login']);
});
test('a real permission denial does not log out authenticated users',async()=>{
 redirects=[];
 client.defaults.adapter=async config=>{
  if(config.url==='/api/session/')return {data:{authenticated:true,panel:'admin'},status:200,statusText:'OK',headers:{},config};
  throw {config,response:{status:403,data:{detail:'Forbidden'}},message:'Forbidden'};
 };
 await assert.rejects(client.get('/api/users/'));
 assert.deepEqual(redirects,[]);
});
