import test from 'node:test';
import assert from 'node:assert/strict';
import { readCollection, readMetric, loginDestination, shouldRedirectUnauthorized } from '../src/api/contracts.js';
import { mobileFingerprintUrl } from '../src/api/public-links.js';
import { isTerminalEnrollment, readEnrollmentToken } from '../src/api/enrollment-state.js';
test('collections accept bare and named arrays, reject unexpected data', () => {
 assert.deepEqual(readCollection([{id:1}]), [{id:1}]);
 assert.deepEqual(readCollection({users:[]}, 'users'), []);
 assert.throws(() => readCollection({unexpected:3}), /Ma/);
});
test('failed metrics are unavailable, successful empty metrics are zero', () => {
 assert.equal(readMetric({status:'rejected',reason:new Error('offline')}).value, null);
 assert.equal(readMetric({status:'fulfilled',value:{data:[]}}).value, 0);
});
test('login continues enrollment but rejects external or wrong-panel redirects', () => {
 assert.equal(loginDestination('admin','/device-enroll/approval/'), '/device-enroll/approval/');
 assert.equal(loginDestination('admin','https://outside.example'), '/dashboard');
 assert.equal(loginDestination('admin','//outside.example'), '/dashboard');
 assert.equal(loginDestination('admin','/system/dashboard/'), '/dashboard');
 assert.equal(loginDestination('superadmin','/dashboard/'), '/system/dashboard');
});
test('incorrect login stays on form; session expiry redirects protected pages', () => {
 assert.equal(shouldRedirectUnauthorized(401,'/api/admin/login','/login'),false);
 assert.equal(shouldRedirectUnauthorized(401,'/api/users/','/users'),true);
 assert.equal(shouldRedirectUnauthorized(403,'/api/users/','/users'),false);
});
test('phone links use public origin', () => {
 assert.equal(mobileFingerprintUrl('https://auth.example','abc-123'), 'https://auth.example/mobile/fingerprint/abc-123/');
});
test('terminal enrollment stops polling and QR parser accepts only same-origin tokens', () => {
 for (const status of ['approved','rejected','cancelled','expired']) assert.equal(isTerminalEnrollment(status),true);
 assert.equal(isTerminalEnrollment('pending'),false);
 assert.equal(readEnrollmentToken('https://auth.example/device-enroll/abc-123','https://auth.example'),'abc-123');
 assert.throws(() => readEnrollmentToken('https://outside.example/device-enroll/token','https://auth.example'));
 assert.throws(() => readEnrollmentToken('https://auth.example/login','https://auth.example'));
});
