"""Validate only explicitly identified generated XML/PDF; never modify the ZIP."""
import argparse,json,zipfile,stat,shutil,subprocess
from pathlib import Path,PurePosixPath

def validate(package,names,output,xsd=None,render=False,pdftoppm=None,max_bytes=512*1024*1024):
 out=Path(output);out.mkdir(parents=True,exist_ok=True,mode=0o700)
 result={'ok':False,'checks':[],'errors':[],'unverified':[],'files':[],'businessSemantics':'not checked by generic helper','visualReview':'not performed'}
 if not names or any(Path(n).name!=n or n in ('.','..') for n in names):raise ValueError('Supply generated basenames, not arbitrary archive paths')
 with zipfile.ZipFile(package)as z:
  selected={}
  for info in z.infolist():
   path=PurePosixPath(info.filename.replace('\\','/'))
   if path.is_absolute()or'..'in path.parts:raise ValueError('Unsafe archive path')
   if path.name not in names or info.is_dir():continue
   if stat.S_ISLNK(info.external_attr>>16):raise ValueError('Archive symlink')
   if path.name in selected:raise ValueError('Ambiguous generated basename: '+path.name)
   selected[path.name]=info
  if set(selected)!=set(names):raise ValueError('Missing generated files: '+','.join(sorted(set(names)-set(selected))))
  if sum(i.file_size for i in selected.values())>max_bytes:raise ValueError('Local analysis size budget exceeded; adjust --max-bytes deliberately')
  for name,info in selected.items():
   path=out/name;path.write_bytes(z.read(info));result['files'].append(name)
   if name.lower().endswith('.xml'):
    try:
     from lxml import etree as E
     tree=E.parse(str(path),E.XMLParser(resolve_entities=False,no_network=True));result['checks'].append(name+': XML syntax')
     if xsd:
      schema=E.XMLSchema(E.parse(str(xsd),E.XMLParser(resolve_entities=False,no_network=True)));schema.assertValid(tree);result['checks'].append(name+': XSD')
     else:result['unverified'].append(name+': XSD not supplied')
    except ImportError:result['errors'].append(name+': dependency lxml missing')
    except Exception as e:result['errors'].append(name+': '+str(e))
   elif name.lower().endswith('.pdf'):
    try:
     from pypdf import PdfReader
     reader=PdfReader(path);texts=[page.extract_text()or''for page in reader.pages]
     if not texts:raise ValueError('PDF has no pages')
     (out/(name+'.txt')).write_text('\n'.join(texts));result['checks'].append(name+': PDF parsed, '+str(len(texts))+' pages')
     if render:
      binary=pdftoppm or shutil.which('pdftoppm')
      if not binary:raise RuntimeError('pdftoppm missing for requested render')
      pages=out/(name+'-pages');pages.mkdir(exist_ok=True)
      subprocess.run([binary,'-png','-r','70',str(path),str(pages/'page')],check=True,capture_output=True);result['checks'].append(name+': rendered')
    except ImportError:result['errors'].append(name+': dependency pypdf missing')
    except Exception as e:result['errors'].append(name+': '+str(e))
   else:result['errors'].append(name+': unsupported generated document type')
 result['ok']=not result['errors'];(out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--zip',required=True);p.add_argument('--name',action='append',required=True);p.add_argument('--output',required=True);p.add_argument('--xsd');p.add_argument('--render',action='store_true');p.add_argument('--pdftoppm');p.add_argument('--max-bytes',type=int,default=512*1024*1024);a=p.parse_args()
 try:r=validate(a.zip,a.name,a.output,a.xsd,a.render,a.pdftoppm,a.max_bytes)
 except (ValueError,OSError,zipfile.BadZipFile)as e:p.exit(2,str(e)+'\n')
 print(json.dumps({'ok':r['ok'],'checks':len(r['checks']),'errors':r['errors'],'unverified':r['unverified']},ensure_ascii=False));raise SystemExit(0 if r['ok']else 1)
if __name__=='__main__':main()
