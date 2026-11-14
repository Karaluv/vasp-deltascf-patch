#!/usr/bin/env python3
"""Check NTO_SADDLE settings before VASP; optionally write explicit mode defaults."""
import argparse,json,math
from pathlib import Path
ETA={'OFF':1.,'PROJECT':0.,'REFLECT':-1.,'SECANT':-1.,'AUTO':0.}
TRUE={'T','TRUE','.TRUE.'};FALSE={'F','FALSE','.FALSE.'}
def check(path,write_defaults=False):
 path=Path(path);lines=path.read_text().splitlines();settings={}
 for number,line in enumerate(lines,1):
  words=line.split('#',1)[0].split()
  if not words:continue
  if len(words)!=2:raise ValueError(f'Line {number}: expected KEY VALUE')
  key,value=words[0].upper(),words[1]
  if key in settings:raise ValueError('Duplicate control: '+key)
  settings[key]=value
 mode=settings.get('MODE','').upper()
 if mode not in ETA:raise ValueError('MODE must be OFF, PROJECT, REFLECT, SECANT or AUTO')
 expected_stop='T' if mode=='OFF' else 'F';defaults={'ETA':str(ETA[mode]),'STOP_ON_EDIFF_ONLY':expected_stop}
 added={k:v for k,v in defaults.items() if k not in settings};effective=dict(settings,**added)
 for key,value in effective.items():
  if key.startswith('STOP_') and key!='STOP_ON_EDIFF_ONLY' or key in ['ETA','TRUST_C_MAX','IONIC_TIME','IONIC_STOP_H_MAX','IONIC_STOP_P_MIN','IONIC_STOP_C_MAX','SECANT_DAMPING','SECANT_CAP_FACTOR','SECANT_MAX_ANGLE']:
   try:finite=math.isfinite(float(value))
   except ValueError:finite=False
   if not finite:raise ValueError(key+' must be finite')
 if abs(float(effective['ETA'])-ETA[mode])>1e-12:raise ValueError('ETA does not match MODE '+mode)
 stop=effective['STOP_ON_EDIFF_ONLY'].upper()
 if stop not in TRUE|FALSE or (stop in TRUE)!=(mode=='OFF'):raise ValueError('OFF requires STOP_ON_EDIFF_ONLY T; active modes require F')
 for key in ['SPIN','N_OCC_BETA','N_OCC','HOLE_BAND','REF_HOLE_BAND','REF_PART_BAND','N_PROJECT','N_REFLECT','PRINT_EVERY','IONIC_MIN_STEP','IONIC_STABLE_STEPS','STOP_MIN_STEP','STOP_STABLE_STEPS']:
  if key in effective and (int(effective[key])<1 or str(int(effective[key]))!=effective[key]):raise ValueError(key+' must be a positive integer')
 if 'SPIN' in effective and int(effective['SPIN'])!=2:raise ValueError('This release supports beta SPIN2 only')
 if 'N_OCC' in effective and 'N_OCC_BETA' in effective and effective['N_OCC']!=effective['N_OCC_BETA']:raise ValueError('Conflicting N_OCC aliases')
 damp=float(effective.get('SECANT_DAMPING',.35));cap=float(effective.get('SECANT_CAP_FACTOR',2.5));angle=float(effective.get('SECANT_MAX_ANGLE',.02))
 if not 0<damp<=1 or not 0<=cap<=100 or not 0<angle<=.1:raise ValueError('Invalid SECANT damping/cap/angle bounds')
 if write_defaults and added:path.write_text('\n'.join(lines+[k+' '+v for k,v in added.items()])+'\n')
 return dict(valid=True,mode=mode,explicit_defaults=added,written=bool(write_defaults and added),secant_damping=damp,secant_cap_factor=cap,secant_max_angle=angle,full_stationarity_claim=False)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path);p.add_argument('--write-defaults',action='store_true');args=p.parse_args()
 try:print(json.dumps(check(args.path,args.write_defaults),indent=2))
 except (OSError,ValueError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
