import{test as base,expect,chromium}from'@playwright/test';
import{readFile,writeFile}from'node:fs/promises';import{resolve}from'node:path';
import{cases}from'./cases.mjs';import{configuration,observe}from'./lib/runtime.mjs';
if(!cases.length)throw new Error('AUTHOR: cases.mjs is empty; write service-specific cases before running');
const config=await configuration(),inventory=JSON.parse(await readFile(new URL('./inventory.json',import.meta.url),'utf8'));
const test=base.extend({vkuContext:[async({},use)=>{const ctx=await chromium.launchPersistentContext(resolve(config.profileDirectory),{channel:config.channel,headless:config.headless,acceptDownloads:true});try{await use(ctx);}finally{await ctx.close();}},{scope:'worker'}]});
for(const plan of cases)test(plan.id+' '+plan.title,async({vkuContext},info)=>{
 info.annotations.push({type:'case',description:plan.id},{type:'settings-sha256',description:config.settingsSHA256});
 const page=await vkuContext.newPage(),state=observe(page);await vkuContext.tracing.start({screenshots:true,snapshots:true,sources:true});
 try{
  await page.goto(config.url,{waitUntil:'domcontentloaded',timeout:90000});
  if(plan.precondition)await plan.precondition({page,config,inventory,state,info});
  for(const step of plan.steps){
   await test.step((step.name||step.screen||'External step'),async()=>{
    const screen=inventory.screens.find(s=>s.id===step.screen);const heading=step.heading||screen?.header;
    if(step.check)await step.check({page,config,inventory,state,info});
    else if(heading&&!String(heading).includes('${'))await expect(page.getByRole('heading',{name:heading,exact:true}).filter({visible:true})).toBeVisible();
    else throw new Error('AUTHOR: provide an exact personalized heading or check for '+step.screen);
    for(const label of step.expectedButtons||[])await expect(page.getByRole('button',{name:label,exact:true}).filter({visible:true})).toHaveCount(1);
    if(step.effect){if(!['sign','send'].includes(step.effect))throw new Error('AUTHOR: unknown effect');if(!config.mutations?.[step.effect]||!config.mutationOrigins?.includes(new URL(page.url()).origin))throw new Error('BLOCKED_MUTATION: '+step.effect+' is not authorized here');}
    if(step.run)await step.run({page,config,inventory,state,info,expect});
   });
  }
  const outcome=plan.outcome;if(!outcome)throw new Error('AUTHOR: explicit observed outcome required');
  if(outcome.check)await outcome.check({page,config,inventory,state,info,expect});
  else if(outcome.heading)await expect(page.getByRole('heading',{name:outcome.heading,exact:true}).filter({visible:true})).toBeVisible();
  else throw new Error('AUTHOR: outcome assertion required');
  for(const label of outcome.absentButtons||[])await expect(page.getByRole('button',{name:label,exact:true}).filter({visible:true})).toHaveCount(0);
  if(!['sent','refused','probe','signing-only'].includes(outcome.kind))throw new Error('AUTHOR: unsupported outcome');
  await Promise.all(state.pending);for(const id of plan.observedScreens||[])expect(state.screens,'Observed '+id).toContain(id);
  info.annotations.push({type:'outcome',description:outcome.kind});
 }catch(error){await page.screenshot({path:info.outputPath('failure.png'),fullPage:true}).catch(()=>{});await writeFile(info.outputPath('page.html'),await page.content().catch(()=>''),{mode:0o600});throw error;}
 finally{await Promise.all(state.pending);await writeFile(info.outputPath('observations.json'),JSON.stringify({screens:state.screens,errors:state.networkErrors},null,2),{mode:0o600});await vkuContext.tracing.stop({path:info.outputPath('trace.zip')});await page.close();}
});
