import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',testMatch:['desktop/*.spec.js','release/*.spec.js'],fullyParallel:false,workers:1,retries:0,timeout:60000,
 reporter:[['list'],['json',{outputFile:'../artifacts/verification/release-browser.json'}]],
 use:{baseURL:'http://127.0.0.1:4173/',...(process.platform==='win32'?{channel:'chrome'}:{}),viewport:{width:1440,height:1000},trace:'retain-on-failure'},
 webServer:{command:'npm run preview',url:'http://127.0.0.1:4173/',reuseExistingServer:!process.env.CI}});
