import{appendFileSync,writeFileSync,readFileSync,existsSync,mkdirSync}from'node:fs';import{resolve}from'node:path';
export default class Reporter{
 onTestEnd(test,result){
  const id=test.annotations.find(a=>a.type==='case')?.description||test.title;
  const outcome=test.annotations.find(a=>a.type==='outcome')?.description;
  const error=result.errors.map(e=>e.message||'').join('\n').replace(/\u001b\[[0-9;]*m/g,'');
  let status=result.status;
  if(status==='passed')status=['sent','refused'].includes(outcome)?'passed':outcome==='probe'?'probe-passed':'partial';
  if(error.includes('PRECONDITION:')||error.includes('BLOCKED_MUTATION:'))status='blocked';
  const row={id,title:test.title,status,outcome,run:process.env.VKU_RUN_DIR,at:new Date().toISOString(),settingsHash:test.annotations.find(a=>a.type==='settings-sha256')?.description,error};
  mkdirSync('artifacts',{recursive:true,mode:0o700});appendFileSync('artifacts/attempts.jsonl',JSON.stringify(row)+'\n',{mode:0o600});
  const all=readFileSync('artifacts/attempts.jsonl','utf8').trim().split('\n').filter(Boolean).map(s=>JSON.parse(s)),latest=new Map();for(const r of all)latest.set(r.id,r);
  const table=rows=>'| Кейс | Статус | Время UTC | Прогон |\n|---|---|---|---|\n'+rows.map(r=>`| ${r.title.replaceAll('|','/')} | ${r.status} | ${r.at} | [Артефакты](${resolve(r.run)}) |`).join('\n')+'\n';
  writeFileSync('RESULTS.md','# Последние результаты\n\npassed = подтверждённая отправка/финал либо ожидаемый отказ; probe-passed/partial не считаются полным прохождением.\n\n'+table([...latest.values()]));
  writeFileSync('RUN_HISTORY.md','# История всех попыток\n\n'+table(all));
 }
}
