import{readFile,mkdir,writeFile}from'node:fs/promises';import{createHash}from'node:crypto';import{resolve}from'node:path';
export async function configuration(){
 const c=JSON.parse(await readFile(new URL('../vku.config.json',import.meta.url),'utf8'));
 const raw=await readFile(c.settingsPath);
 if(createHash('sha256').update(raw).digest('hex')!==c.settingsSHA256)throw new Error('PRECONDITION: settings changed; review cases and refresh inventory/configuration');
 return c;
}
export function decode(answer){const v=answer?.value;if(typeof v!=='string')return v;const t=v.trim();if(!/^[\[{\"]/.test(t)&&!['true','false','null'].includes(t))return v;try{return JSON.parse(v);}catch{return v;}}
export function observe(page){
 const state={submitted:null,dto:null,manifest:null,screens:[],pending:[],networkErrors:[]};
 page.on('request',r=>{if(!/\/scenario\/getNextStep$/.test(new URL(r.url()).pathname))return;try{const d=r.postDataJSON()?.scenarioDto;if(d)state.submitted=d;}catch{}});
 page.on('requestfailed',r=>{const u=new URL(r.url());state.networkErrors.push({host:u.hostname,path:u.pathname,error:r.failure()?.errorText});});
 page.on('response',r=>{const p=new URL(r.url()).pathname;if(!/\/scenario\/(getService|getNextStep)$/.test(p)&&!p.endsWith('/prepareFiles'))return;
  state.pending.push((async()=>{try{const b=await r.json();if(b.scenarioDto){state.dto=b.scenarioDto;for(const id of[b.scenarioDto.display?.id,...(b.scenarioDto.finishedAndCurrentScreens||[]).map(s=>typeof s==='string'?s:s.id)].filter(Boolean))if(!state.screens.includes(id))state.screens.push(id);}if(p.endsWith('/prepareFiles'))state.manifest=b;}catch(e){state.networkErrors.push({path:p,error:e.message});}})());});
 return state;
}
export async function saveGeneratedPackage(page,state,info,config,locator){
 if(!config.generatedNames?.length)throw new Error('AUTHOR: identify generated document names from this service manifest/contract');
 const all=locator||page.getByRole('link',{name:/^Скачать\s+всё$/i}).filter({visible:true});
 await all.waitFor({state:'visible',timeout:60000});await Promise.all(state.pending);
 const dir=info.outputPath('generated');await mkdir(dir,{recursive:true,mode:0o700});
 const dto=state.submitted||state.dto;if(!dto)throw new Error('ARTIFACT: no observed form DTO');
 const answers={...dto.applicantAnswers,...dto.currentValue};
 await writeFile(resolve(dir,'snapshot.json'),JSON.stringify({orderId:dto.orderId,answers:Object.fromEntries(Object.entries(answers).map(([k,v])=>[k,decode(v)])),manifest:state.manifest,generatedNames:config.generatedNames},null,2),{mode:0o600});
 const event=page.waitForEvent('download',{timeout:60000});await all.click();const file=await event;
 await file.saveAs(resolve(dir,'package.zip'));if(await file.failure())throw new Error('ARTIFACT: download failed');return dir;
}
