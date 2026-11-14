#!/usr/bin/env python3
"""NTO occupation matrix, leakage channels and orbital weights from native PAW WSWQ.

WSWQ rows are current orbitals, columns reference orbitals. A pseudo-wave
coefficient dot product is deliberately not an input supported by this tool.
"""
import argparse,json,re
from pathlib import Path
import numpy as np
from nto_io import MISSING,number,sha256,write_json,write_csv
from prepare_nto_seed import Wavecar

def read_wswq(path,spin=2):
 active=False;entries={};max_i=max_j=0;pattern=re.compile(r'i=\s*(\d+),\s*j=\s*(\d+)\s*:\s*(\S+)\s+(\S+)')
 with Path(path).open() as f:
  for line in f:
   if 'spin=' in line:
    s=re.search(r'spin=\s*(\d+)',line);k=re.search(r'kpoint=\s*(\d+)',line);active=bool(s and int(s[1])==spin)
    if active and (not k or int(k[1])!=1):raise ValueError('Only a single Gamma k-point is supported')
    continue
   m=pattern.match(line.strip())
   if active and m:
    i,j=int(m[1]),int(m[2]);a,b=number(m[3]),number(m[4])
    if i<1 or j<1 or a is None or b is None:raise ValueError('Invalid/nonfinite overlap entry')
    if (i,j) in entries:raise ValueError('Repeated WSWQ block/entry; do not mix k-points or runs')
    entries[i,j]=complex(a,b);max_i=max(max_i,i);max_j=max(max_j,j)
 if not entries or len(entries)!=max_i*max_j:raise ValueError('Incomplete selected-spin WSWQ matrix')
 C=np.empty((max_i,max_j),complex)
 for (i,j),v in entries.items():C[i-1,j-1]=v
 return C

def eigenval(path,spin=2):
 found=[]
 for line in Path(path).read_text().splitlines()[6:]:
  q=line.split()
  if len(q)==5 and q[0].isdigit():found.append((int(q[0]),float(q[spin]),float(q[spin+2])))
 if not found or [x[0] for x in found]!=list(range(1,len(found)+1)):raise ValueError('Requires a complete one-k-point spin-polarized EIGENVAL')
 return np.array([x[1] for x in found]),np.array([x[2] for x in found])

def metrics(C,occupations,energies,ref_hole,ref_part,nocc=None,valence_bands=None):
 C=np.asarray(C,complex)
 if C.ndim!=2 or not np.isfinite(C).all():raise ValueError('Nonfinite/invalid PAW matrix')
 if energies is not None and not np.isfinite(energies).all():raise ValueError('Nonfinite orbital energies')
 raw=np.asarray(occupations,float)
 if len(raw)!=C.shape[0] or not np.isfinite(raw).all() or np.max(abs(raw-np.rint(raw)))>1e-6 or np.any(raw< -1e-6) or np.any(raw>1+1e-6):raise ValueError('Need matching binary current occupations')
 f=np.rint(raw);count=int(f.sum());nocc=count if nocc is None else nocc
 if nocc!=count:raise ValueError('Occupied electron count differs from --n-occ')
 if ref_hole==ref_part or not 1<=min(ref_hole,ref_part)<=max(ref_hole,ref_part)<=C.shape[1]:raise ValueError('Invalid reference pair indices')
 valence=[b for b in range(1,nocc+1) if b not in [ref_hole,ref_part]] if valence_bands is None else list(valence_bands)
 if len(valence)!=len(set(valence)) or any(b in [ref_hole,ref_part] or not 1<=b<=C.shape[1] for b in valence):raise ValueError('Invalid/disjoint reference valence list')
 # u_n=<h0|S|psi_n>=conj(C[n,h]), and likewise for v.
 u=C[:,ref_hole-1].conj();v=C[:,ref_part-1].conj();hu=abs(u)**2;pv=abs(v)**2
 h=float(f@hu);p=float(f@pv);c=complex(np.sum(f*u*v.conj()));c2=float(abs(c)**2);variance=min(h*(1-h),p*(1-p));cmax=float(np.sqrt(variance)) if variance>=0 else MISSING
 eig=np.linalg.eigvalsh(np.array([[h,c],[c.conjugate(),p]]));lh=h*(1-h)-c2;lp=p*(1-p)-c2
 A=C[:,np.array(valence,dtype=int)-1].conj().T;wv=np.sum(abs(A)**2,axis=0);lhv=float(np.sum(abs(A@(f*u.conj()))**2));lpv=float(np.sum(abs(A@(f*v.conj()))**2));nref=float(f@(wv+hu+pv));wvirt=1-hu-pv-wv
 result=dict(h=h,p=p,c_re=c.real,c_im=c.imag,c_abs=abs(c),sqrt_hp=float(np.sqrt(h*p)),c_max=cmax,c_over_cmax=float(abs(c)/cmax) if isinstance(cmax,float) and cmax>0 else MISSING,lambda_max=float(eig[-1]),lambda_min=float(eig[0]),trace=h+p,det=h*p-c2,ell_h=lh,ell_p=lp,ell_h_val=lhv,ell_h_virt=lh-lhv,ell_p_val=lpv,ell_p_virt=lp-lpv,N_reference_subspace=nref,delta_N_virtual=count-nref,reference_subspace_dimension=len(valence)+2,reference_valence_bands=valence,occupied_count=count,occupation_rounding_max_error=float(np.max(abs(raw-f))),reference_hole_band=ref_hole,reference_particle_band=ref_part)
 quality=dict(projector_bounds_within_1e_minus5=bool(-1e-5<=eig[0] and eig[-1]<=1+1e-5 and lh>=-1e-5 and lp>=-1e-5 and lh-lhv>=-1e-5 and lp-lpv>=-1e-5 and np.min(wvirt)>=-1e-5),rounding_policy='Raw derived values are retained; negative tiny leakages/variances are not silently clamped',assumptions='Reference pair/valence and current occupied orbitals are PAW-orthonormal; cross overlaps alone cannot prove this')
 rows=[]
 for i in range(len(f)):
  rows.append(dict(band_n=i+1,occ_f_n=float(f[i]),eigenval_eV=float(energies[i]) if energies is not None else MISSING,h0_weight=float(hu[i]),p0_weight=float(pv[i]),V_weight=float(wv[i]),virtual_weight=float(wvirt[i]),u_re=float(u[i].real),u_im=float(u[i].imag),v_re=float(v[i].real),v_im=float(v[i].imag)))
 empty=np.flatnonzero(f==0);main=int(empty[np.argmax(hu[empty])]) if len(empty) else None
 result['dominant_empty_hole_band']=main+1 if main is not None else MISSING
 if main is not None:
  result['dominant_empty_hole_weight']=float(hu[main]);result['empty_hole_weight_sum_in_saved_bands']=float(hu[empty].sum());result['hole_weight_outside_saved_current_bands']=1-float(hu.sum())
 if energies is not None and np.any(f==1) and np.any(f==0):
  vbm=float(np.max(energies[f==1]));cbm=float(np.min(energies[f==0]));result.update(actual_max_occupied_energy_eV=vbm,actual_min_empty_energy_eV=cbm,occupation_gap_eV=cbm-vbm)
  if main is not None:result.update(dominant_empty_hole_energy_eV=float(energies[main]),dominant_empty_hole_relative_to_occupied_edge_eV=float(energies[main]-vbm),dominant_empty_hole_relative_to_empty_edge_eV=float(energies[main]-cbm))
 return result,quality,rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--wswq',type=Path,required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--eigenval',type=Path);g.add_argument('--wavecar',type=Path,help='Only stored header energies/occupations are read; no pseudo-overlaps');p.add_argument('--spin',type=int,choices=[1,2],default=2);p.add_argument('--n-occ',type=int);p.add_argument('--ref-hole-band',type=int);p.add_argument('--ref-part-band',type=int);p.add_argument('--valence-bands',help='Explicit comma-separated reference indices; default first n_occ excluding pair');p.add_argument('--hole-band',type=int,help='Current empty hole slot, required by --expect-seed');p.add_argument('--particle-band',type=int,help='Current particle slot, default n_occ');p.add_argument('--weight-cutoff',type=float,default=.01);p.add_argument('--json',type=Path,required=True);p.add_argument('--csv',type=Path);p.add_argument('--expect-seed',action='store_true');p.add_argument('--require-target',action='store_true');p.add_argument('--tolerance',type=float,default=1e-5);a=p.parse_args()
 try:
  for path in [a.json,a.csv]:
   if path and path.exists():raise ValueError('Refusing existing output: '+str(path))
  C=read_wswq(a.wswq,a.spin)
  if a.eigenval:energies,f=eigenval(a.eigenval,a.spin)
  else:
   wave=Wavecar(a.wavecar);m=wave.metadata(a.spin-1);energies,f=m[:,0],m[:,2]
  nocc=a.n_occ if a.n_occ is not None else int(np.rint(f).sum());rh=a.ref_hole_band or nocc;rp=a.ref_part_band or nocc+1
  m,q,rows=metrics(C,f,energies,rh,rp,nocc,[int(x) for x in a.valence_bands.split(',')] if a.valence_bands else None);current_hole=a.hole_band or nocc+1;part=a.particle_band or nocc
  seed=False
  if 1<=current_hole<=len(rows) and 1<=part<=len(rows):seed=bool(m['h']<a.tolerance and abs(m['p']-1)<a.tolerance and m['c_abs']<a.tolerance and rows[current_hole-1]['occ_f_n']==0 and rows[part-1]['occ_f_n']==1 and abs(rows[current_hole-1]['h0_weight']-1)<a.tolerance and abs(rows[part-1]['p0_weight']-1)<a.tolerance)
  target=bool(m['h']<.08 and m['p']>.9 and m['c_abs']<.02);selected=[r for r in rows if max(1,nocc-6)<=r['band_n']<=min(len(rows),nocc+9) or r['h0_weight']>a.weight_cutoff or r['p0_weight']>a.weight_cutoff or (1-r['occ_f_n'])*r['V_weight']>a.weight_cutoff]
  out=dict(metric='Native VASP full-PAW WSWQ; no coefficient-space overlap',source_wswq_sha256=sha256(a.wswq),occupation_source_sha256=sha256(a.eigenval or a.wavecar),spin=a.spin,metrics=m,quality=q,full_paw_seed_identity_passed=seed,working_target_identity_passed=target,stationarity='MISSING: this tool measures identity/projector only',bands=rows)
  write_json(a.json,out)
  if a.csv:write_csv(a.csv,selected)
  print(json.dumps(dict(json=str(a.json),h=m['h'],p=m['p'],c_abs=m['c_abs'],seed_identity_passed=seed,target_identity_passed=target)))
  if not q['projector_bounds_within_1e_minus5'] or a.expect_seed and not seed or a.require_target and not target:raise SystemExit(2)
 except (OSError,ValueError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
