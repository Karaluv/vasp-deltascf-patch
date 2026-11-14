#!/usr/bin/env python3
"""Extract spin-resolved NTO coefficients/weights from Gamma BSEFATBAND.

SVD in the response orbital basis is not a physical PAW overlap calculation.
Use the matching WAVECAR when generating a seed, then validate it natively.
"""
import argparse,json,re,sys
from pathlib import Path
import numpy as np
from nto_io import sha256,write_json
from prepare_nto_seed import Wavecar

def selected_roots(path,requested):
 with Path(path).open() as f:
  try:nt,nr=map(int,next(f).split())
  except (StopIteration,ValueError) as e:raise ValueError('Invalid BSEFATBAND header') from e
  if nt<=0 or nt%2:raise ValueError('Requires equal ordered alpha/beta transition blocks')
  wanted=set(range(1,nr+1)) if requested is None else set(requested)
  if not wanted or min(wanted)<1 or max(wanted)>nr:raise ValueError('Requested root outside file')
  for index in range(1,max(wanted)+1):
   line=next(f);m=re.match(r'\s*(\d+)BSE\s+eigenvalue\s+([-+\d.EeDd]+)',line)
   if not m or int(m[1])!=index:raise ValueError('Unsupported root-header layout')
   energy=float(m[2].replace('D','E').replace('d','e'));blocks=[[],[]]
   for t in range(nt):
    line=next(f)
    if index not in wanted:continue
    q=line.replace('+i*',' ').replace('-i*',' -').split()
    if len(q)!=10 or max(abs(float(x)) for x in q[:3])>1e-12:raise ValueError('Requires single-Gamma BSEFATBAND layout')
    blocks[t//(nt//2)].append((int(q[6]),int(q[7]),float(q[3]),float(q[4]),complex(float(q[8]),float(q[9]))))
   if index in wanted:yield index,energy,blocks

def analyze(path,roots,pairs=3,wavecar=None,tolerance=.002):
 wave=Wavecar(wavecar) if wavecar else None;result=[];arrays={}
 for index,energy,blocks in selected_roots(path,roots):
  item=dict(root=index,energy_ev=energy,spins={});total=0.
  if not np.isfinite(energy):raise ValueError('Nonfinite root energy')
  for spin,entries in enumerate(blocks):
   occupied=sorted({e[0] for e in entries});virtual=sorted({e[1] for e in entries})
   if set(occupied)&set(virtual) or not occupied or min(occupied+virtual)<1:raise ValueError('Invalid occupied/virtual labels')
   oi={b:i for i,b in enumerate(occupied)};vi={b:i for i,b in enumerate(virtual)};T=np.zeros((len(occupied),len(virtual)),complex);seen=set();error=0.
   metadata=wave.metadata(spin) if wave else None
   for h,p,eh,ep,value in entries:
    if (h,p) in seen:raise ValueError('Duplicate transition')
    seen.add((h,p));T[oi[h],vi[p]]=value
    if wave:
     if max(h,p)>wave.nbands:raise ValueError('Response band outside WAVECAR')
     if abs(metadata[h-1,2]-1)>1e-6 or abs(metadata[p-1,2])>1e-6:raise ValueError('Response occupations disagree with WAVECAR')
     error=max(error,abs(eh-metadata[h-1,0]),abs(ep-metadata[p-1,0]))
   if not np.isfinite(T).all():raise ValueError('Nonfinite transition amplitudes')
   if wave and error>tolerance:raise ValueError(f'Response/WAVECAR band-energy mismatch: {error:.17g} eV')
   U,s,Vh=np.linalg.svd(T,full_matrices=False);weights=s*s;norm=float(weights.sum());total+=norm;label=['alpha','beta'][spin];prefix=f'r{index}_{label}'
   arrays.update({prefix+'_hole_bands':np.array(occupied),prefix+'_particle_bands':np.array(virtual),prefix+'_hole_coefficients':U,prefix+'_particle_coefficients':Vh.conj().T,prefix+'_singular_values':s,prefix+'_transition_matrix':T})
   def vector(v):return [dict(band=b,re=float(x.real),im=float(x.imag)) for b,x in v]
   top=[]
   for k in range(min(pairs,len(s))):
    top.append(dict(pair=k+1,weight=float(weights[k]),fraction_of_spin= float(weights[k]/norm) if norm else 0.,hole=vector(zip(occupied,U[:,k])),particle=vector(zip(virtual,Vh[k].conj()))))
   item['spins'][label]=dict(transition_count=len(entries),spin_weight=norm,all_pair_weights=weights.tolist(),leading_pair_fraction=float(weights[0]/norm) if norm else 0.,effective_pair_count=float(norm*norm/(weights@weights)) if norm else 0.,band_energy_max_error_ev=error if wave else 'MISSING',pairs=top)
  item['total_amplitude_norm2']=total;result.append(item)
 return dict(source=str(Path(path).resolve()),source_sha256=sha256(path),matching_wavecar_sha256=sha256(wavecar) if wavecar else 'MISSING',layout='single Gamma; equal ordered alpha/beta blocks',coefficient_convention='T=U diag(s) V^H; hole=U, particle=V',metric_scope='Response coefficient algebra only; no wavefunction overlaps computed',roots=result),arrays

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('bsefatband',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--roots',default='1',help='Comma-separated root indices');g.add_argument('--all-roots',action='store_true');p.add_argument('--pairs',type=int,default=3);p.add_argument('--wavecar',type=Path,help='Optional matching orbital/energy provenance check');p.add_argument('--eigenvalue-tolerance',type=float,default=.002);p.add_argument('--json',type=Path,required=True);p.add_argument('--npz',type=Path,help='All matrices/vectors; new file only');a=p.parse_args()
 try:
  if a.pairs<1 or a.eigenvalue_tolerance<0:raise ValueError('Invalid pair count/tolerance')
  for dest in [a.json,a.npz]:
   if dest and dest.exists():raise ValueError('Refusing existing output: '+str(dest))
  out,arrays=analyze(a.bsefatband,None if a.all_roots else [int(x) for x in a.roots.split(',')],a.pairs,a.wavecar,a.eigenvalue_tolerance)
  if a.npz:
   a.npz.parent.mkdir(parents=True,exist_ok=True)
   with a.npz.open('xb') as f:np.savez_compressed(f,**arrays)
  write_json(a.json,out);print(json.dumps(dict(json=str(a.json),roots=len(out['roots']),npz=str(a.npz) if a.npz else None)))
 except (OSError,ValueError,StopIteration) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
