#!/usr/bin/env python3
"""Apply authored insertions to an exact, locally licensed VASP source tree."""
import argparse,hashlib,json,os
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def transform(data,entry,folder):
 if digest(data)!=entry['before_sha256']:raise ValueError('Unrecognized original source: '+entry['path'])
 lines=data.splitlines(keepends=True)
 for op in reversed(entry['edits']):
  lo,hi=op['start_line'],op['end_line'];old=b''.join(lines[lo:hi])
  if digest(old)!=op['removed_sha256']:raise ValueError('Edit preimage mismatch')
  addition=(folder/op['payload']).read_bytes()
  if digest(addition)!=op['payload_sha256']:raise ValueError('Payload checksum mismatch')
  lines[lo:hi]=addition.splitlines(keepends=True)
 result=b''.join(lines)
 if digest(result)!=entry['after_sha256']:raise ValueError('Patched source checksum mismatch')
 return result

def patch(root,manifest,action):
 root=Path(root).resolve();manifest=Path(manifest).resolve();m=json.loads(manifest.read_text());folder=manifest.parent
 version=root/'src/version.F'
 if not version.is_file() or digest(version.read_bytes())!=m['version_sha256']:raise ValueError('Requires the documented VASP 6.6.0 source snapshot; version.F differs')
 prepared=[];backup=root/'.nto-dscf-backup'/m['variant']
 for e in m['files']:
  p=root/e['path'];data=p.read_bytes();h=digest(data);b=backup/e['path']
  if action=='revert':
   if h==e['before_sha256']:continue
   if h!=e['after_sha256'] or not b.is_file() or digest(b.read_bytes())!=e['before_sha256']:raise ValueError('Cannot safely revert '+e['path'])
   prepared.append((p,b.read_bytes(),None))
  else:
   if h==e['after_sha256']:continue
   prepared.append((p,transform(data,e,folder),data))
 if action=='check':return {'variant':m['variant'],'files_to_change':len(prepared),'action':action}
 # Validate every input and payload before writing any source.
 for p,new,old in prepared:
  if old is not None:
   b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True)
   if b.exists() and b.read_bytes()!=old:raise ValueError('Backup collision '+str(b))
   if not b.exists():b.write_bytes(old)
 for p,new,_ in prepared:
  tmp=p.with_name(p.name+'.nto-tmp');tmp.write_bytes(new);os.replace(tmp,p)
 return {'variant':m['variant'],'files_changed':len(prepared),'action':action}

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('vasp_root',type=Path);a.add_argument('--variant',choices=['static','ionic-experimental'],default='static');g=a.add_mutually_exclusive_group();g.add_argument('--apply',action='store_true');g.add_argument('--revert',action='store_true');v=a.parse_args();manifest=Path(__file__).resolve().parents[1]/'patches'/('vasp-6.6.0-'+v.variant)/'manifest.json'
 try:print(json.dumps(patch(v.vasp_root,manifest,'apply' if v.apply else 'revert' if v.revert else 'check'),indent=2))
 except (OSError,ValueError,KeyError) as e:a.exit(1,str(e)+'\n')
if __name__=='__main__':main()
