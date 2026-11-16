#!/usr/bin/env python3
"""Create a read-only-source VKU Playwright workspace; author cases separately."""
import argparse,hashlib,json,shutil
from pathlib import Path
from urllib.parse import urlsplit

def prepare(url,settings_path,output):
    parsed=urlsplit(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('URL must be http(s) without embedded credentials')
    source=Path(settings_path).expanduser().resolve(strict=True)
    raw=source.read_bytes();model=json.loads(raw)
    if not isinstance(model,dict) or not isinstance(model.get('screens'),list) or not model['screens']:
        raise ValueError('Expected VKU settings with a nonempty screens array')
    out=Path(output).expanduser().resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Output is not empty; inspect/reuse the existing test project')
    ids=[s['id']for s in model['screens']]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate screen IDs')
    digest=hashlib.sha256(raw).hexdigest()
    inventory={'source':str(source),'sha256':digest,'init':model.get('init'),'initScreens':model.get('initScreens'),'screens':model['screens'],'fields':model.get('applicationFields',[]),'screenRules':model.get('screenRules',{}),'cycledScreenRules':model.get('cycledScreenRules',{}),'externalScreenIds':model.get('externalScreenIds',[])}
    config={'url':url,'settingsPath':str(source),'settingsSHA256':digest,'channel':'chrome','headless':False,'profileDirectory':'.profile','mutationOrigins':[f'{parsed.scheme}://{parsed.netloc}'],'mutations':{'sign':False,'send':False},'generatedNames':[],'xsdPath':None}
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    shutil.copytree(Path(__file__).resolve().parents[1]/'assets/project',out,dirs_exist_ok=True)
    for name,value in [('inventory.json',inventory),('vku.config.json',config)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise RuntimeError('Source changed during inventory')
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--settings',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try:out=prepare(a.url,a.settings,a.output)
    except (ValueError,OSError,KeyError)as e:p.exit(2,str(e)+'\n')
    print(f'Created {out}; author cases.mjs and service adapters before running tests. Source unchanged.')
if __name__=='__main__':main()
