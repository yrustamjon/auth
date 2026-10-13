const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

for (const file of ['static/js/api.js', 'static/js/superadmin/api.js']) {
  for (const origin of ['http://127.0.0.1:8000', 'http://localhost:8000', 'https://new-tunnel.ngrok-free.dev']) {
    test(`${file} sends requests to ${origin}`, async () => {
      let requested;
      const context = vm.createContext({
        window: { location: { origin } },
        document: { cookie: 'csrftoken=test-token' },
        getCookie: () => 'test-token',
        fetch: async (url) => { requested = url; return { status: 200 }; },
      });
      vm.runInContext(fs.readFileSync(file, 'utf8'), context);
      await vm.runInContext("fetchWithAuth('/api/users')", context);
      assert.equal(requested, `${origin}/api/users`);
    });
  }
}
