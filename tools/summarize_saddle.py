#!/usr/bin/env python3
"""Join raw PAW/residual/update traces and SCF energies without rerunning VASP."""
import argparse,json,re,statistics
from pathlib import Path
from nto_io import MISSING,number,read_csv,controls,write_json,write_csv

def scf_rows(path):
 rows=[];ionic=1;previous=0
 if not path.exists():return rows
 for line in path.read_text(errors='replace').splitlines():
  m=re.match(r'\s*(DAV|DMP|SDA|CG|RMM|RMM-DIIS):\s*(\d+)\s+(\S+)\s+(\S+)',line)
  if not m:continue
  n=int(m[2])
  if n<=previous:ionic+=1
  previous=n;rows.append(dict(ionic_step=ionic,step=n,scf_method=m[1],energy_eV=number(m[3]),dE_eV=number(m[4]),energy_source=path.name))
 return rows

def summarize(directory):
 d=Path(directory);cfg=controls(d/'NTO_SADDLE');trace=read_csv(d/'NTO_SADDLE_TRACE.csv');energy=max([scf_rows(d/'OSZICAR'),scf_rows(d/'vasp.stdout')],key=len);E={(r['ionic_step'],r['step']):r for r in energy}
 updates={tuple(int(r.get(k,1)) for k in ['ionic_step','step']):r for r in read_csv(d/'NTO_SADDLE_STEP.csv')};timing={tuple(int(r.get(k,1)) for k in ['ionic_step','step']):r for r in read_csv(d/'NTO_FAST_TIMING.csv')};joined=[]
 for r in trace:
  key=(int(r.get('ionic_step',1)),int(r['step']));j=dict(r);j.update(E.get(key,{}))
  for prefix,source in [('update_',updates.get(key,{})),('timing_',timing.get(key,{}))]:
   j.update({prefix+k:v for k,v in source.items() if k not in ['ionic_step','step']})
  for k,v in list(j.items()):
   n=number(v)
   if n is not None:j[k]=n
  joined.append(j)
 last=joined[-1] if joined else (energy[-1] if energy else {});ion=int(last.get('ionic_step',1));following=cfg.get('IONIC_FOLLOW','F').upper() in ['T','.TRUE.','TRUE'] and ion>=2
 def threshold(key,default):return float(cfg.get(key,default))
 limits=dict(g_mode_eV=threshold('STOP_G_MODE_MAX',6.5e-5),R_perp_subspace_eV=threshold('STOP_RPERP_SUB_MAX',3e-4),R_perp_est_normalized=threshold('STOP_RPERP_EST_MAX',1e-4),dE_eV=threshold('STOP_DE_MAX',5e-8),h_max=threshold('IONIC_STOP_H_MAX',.05) if following else threshold('STOP_H_MAX',.08),p_min=threshold('IONIC_STOP_P_MIN',.9) if following else threshold('STOP_P_MIN',.9),c_abs_max=threshold('IONIC_STOP_C_MAX',.08) if following else threshold('STOP_C_ABS_MAX',.02))
 count=int(cfg.get('IONIC_STABLE_STEPS',2) if following else cfg.get('STOP_STABLE_STEPS',3));minimum=int(cfg.get('IONIC_MIN_STEP',6) if following else cfg.get('STOP_MIN_STEP',20));tail=joined[-count:];fast=bool(last.get('stop_rule')=='FAST_SUBSPACE')
 def stage_index(row):
  n=int(row['step'])
  if following:return n-int(cfg.get('IONIC_N_PROJECT',8))-int(cfg.get('IONIC_N_REFLECT',5))
  if cfg.get('MODE','').upper()=='AUTO':return n-int(cfg.get('N_PROJECT',80))-int(cfg.get('N_REFLECT',60))
  return n
 def good(row):
  g,rp,rest,de,h,p,c=[number(row.get(k)) for k in ['g_mode_re','R_perp_subspace','R_perp_est_normalized','dE_eV','h','p','c_abs']]
  return bool(row.get('mode')=='SECANT' and int(row.get('ionic_step',1))==ion and None not in [g,rp,de,h,p,c] and abs(g)<=limits['g_mode_eV'] and rp<=limits['R_perp_subspace_eV'] and (fast or rest is not None and rest<=limits['R_perp_est_normalized']) and abs(de)<=limits['dE_eV'] and h<limits['h_max'] and p>limits['p_min'] and c<limits['c_abs_max'])
 numbers=[int(r['step']) for r in tail];consecutive=bool(len(numbers)==count and numbers==list(range(numbers[-1]-count+1,numbers[-1]+1)))
 passed=bool(consecutive and all(good(r) for r in tail) and stage_index(last)>=minimum)
 text=(d/'OUTCAR').read_text(errors='replace') if (d/'OUTCAR').exists() else '';loops=[float(x) for x in re.findall(r'^\s*LOOP:\s+cpu time\s+[\d.]+:\s+real time\s+([\d.]+)',text,re.M)];vpath=d/'validation.json';existing=json.loads(vpath.read_text()) if vpath.exists() else MISSING
 summary=dict(run=str(d.resolve()),trace_rows=len(trace),electronic_rows=len(energy),ionic_steps_in_trace=max((int(r.get('ionic_step',1)) for r in trace),default=0),last=last,configured_thresholds=limits,required_streak=count,minimum_secant_stage_step=minimum,computed_last_secant_stage_step=stage_index(last) if joined else MISSING,estimated_residual_streak_passed=passed,residual_scope=last.get('stop_rule',MISSING),energy_stop_marker='aborting loop because EDIFF is reached' in text,native_estimated_stop_marker='NTO_SADDLE estimated residual criterion reached' in text,terminal_timing='General timing and accounting informations for this job' in text,vasp_exit=(d/'vasp.exit').read_text().strip() if (d/'vasp.exit').exists() else MISSING,median_LOOP_real_seconds=statistics.median(loops[2:] or loops) if loops else MISSING,existing_validation=existing,full_stationarity_confirmed=False,alignment='Raw trace before the update; SCF energy/dE as printed for that iteration. No frozen-state/full-space oracle is implied.',assessment='PROJECT is capture only; OFF is diagnostic only. Streak result uses configured stage-local minimum and does not replace final native PAW identity or force validation.')
 summary['completed_residual_candidate']=bool(passed and summary['vasp_exit']=='0' and summary['terminal_timing'])
 return summary,joined

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--json',type=Path,required=True);p.add_argument('--csv',type=Path);p.add_argument('--require-residual',action='store_true',help='Exit2 unless the configured raw estimated residual streak passes');a=p.parse_args()
 try:
  for q in [a.json,a.csv]:
   if q and q.exists():raise ValueError('Refusing existing output: '+str(q))
  out,rows=summarize(a.run);write_json(a.json,out)
  if a.csv:write_csv(a.csv,rows)
  print(json.dumps({k:out[k] for k in ['trace_rows','estimated_residual_streak_passed','residual_scope','vasp_exit','median_LOOP_real_seconds']}))
  if a.require_residual and not out['completed_residual_candidate']:raise SystemExit(2)
 except (OSError,ValueError,KeyError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
