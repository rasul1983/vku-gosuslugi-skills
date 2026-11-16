import {defineConfig}from'@playwright/test';
process.env.VKU_RUN_DIR||=new URL('./artifacts/'+new Date().toISOString().replace(/[:.]/g,'-')+'/',import.meta.url).pathname;
export default defineConfig({testMatch:'scenarios.spec.mjs',workers:1,retries:0,timeout:300000,expect:{timeout:15000},outputDir:process.env.VKU_RUN_DIR,reporter:[['list'],['html',{open:'never'}],['./lib/reporter.mjs']]});
