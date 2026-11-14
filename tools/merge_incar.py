#!/usr/bin/env python3
"""Merge explicit INCAR overlays into a new file, retaining the base Hamiltonian."""
import argparse,json,re
from pathlib import Path
from nto_io import sha256

def parse(text):
 result={}
 for n,line in enumerate(text.splitlines(),1):
  active=re.split('[#!]',line,1)[0].strip()
  if not active:continue
  for part in active.split(';'):
   if not part.strip():continue
   m=re.fullmatch(r'\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*',part)
   if not m or not m[2] or m[2].endswith('\\'):raise ValueError(f'Unsupported assignment on line {n}; use complete KEY=VALUE lines')
   key=m[1].upper()
   if key in result:raise ValueError('Duplicate active key within an input: '+key)
   result[key]=m[2]
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);p.add_argument('--overlay',type=Path,action='append',default=[]);p.add_argument('--set',dest='assignments',action='append',default=[],help='Explicit KEY=VALUE override; may repeat');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  if a.output.exists():raise ValueError('Refusing existing output: '+str(a.output))
  base=parse(a.base.read_text());merged=dict(base)
  for overlay in a.overlay:merged.update(parse(overlay.read_text()))
  for assignment in a.assignments:merged.update(parse(assignment))
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with a.output.open('x') as f:
   f.write('# Generated from an explicit base; unchanged keys retain their original values.\n')
   for key,value in merged.items():f.write(key+' = '+value+'\n')
  changed={k:dict(before=base.get(k,'MISSING'),after=v) for k,v in merged.items() if base.get(k)!=v};print(json.dumps(dict(output=str(a.output),base_sha256=sha256(a.base),overlay_sha256={str(q):sha256(q) for q in a.overlay},output_sha256=sha256(a.output),changes=changed),indent=2))
 except (OSError,ValueError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
