import { defineConfig } from '@playwright/test';
export default defineConfig({
 testDir:'./e2e', fullyParallel:false, workers:1, timeout:30000,
 use:{baseURL:'http://127.0.0.1:5173',channel:'chrome',headless:true,screenshot:'only-on-failure'},
 webServer:{command:'npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort',url:'http://127.0.0.1:5173',reuseExistingServer:true,timeout:30000},
 reporter:'list',
});

