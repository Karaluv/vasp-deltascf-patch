#!/usr/bin/env python3
"""Pair accepted native wave/reference checkpoints with completed force geometries.

Reads finished calculation elements even when a live vasprun.xml has an
incomplete tail. Does not run VASP, restore optimizer history or overwrite inputs.
"""
import argparse,csv,json,math,re,xml.etree.ElementTree as ET
from pathlib import Path
from nto_io import MISSING,number,read_csv,sha256,write_json

def export(run,point=None,checksums=False):
 run=Path(run).resolve();metadata={}
 with (run/'NTO_SADDLE_IONIC_CHECKPOINT.csv').open() as f:
  for row in csv.reader(f):
   if row and row[0].strip()=='ionic_step':continue
   if len(row)!=5:raise ValueError('Incomplete/unsupported native checkpoint metadata')
   index=int(row[0]);suffixes=[x.strip() for x in row[3:]]
   if index in metadata or any(not re.fullmatch('[A-Za-z0-9]{3}',x) for x in suffixes):raise ValueError('Invalid/duplicate checkpoint index or native suffix')
   metadata[index]=row
 paw={int(r['ionic_step']):r for r in read_csv(run/'NTO_SADDLE_IONIC.csv')};result=[];index=0;incomplete=False
 try:
  for event,element in ET.iterparse(run/'vasprun.xml',events=['end']):
   if element.tag!='calculation':continue
   force=element.find("varray[@name='forces']");structure=element.find('structure')
   if force is not None and structure is not None:
    index+=1
    if index in metadata:
     row=metadata[index];physical=run/('WAVECAR.'+row[3].strip());reference=run/('WAVECAR.'+row[4].strip());forces=[[float(v) for v in r.text.split()] for r in force];basis=[[float(v) for v in r.text.split()] for r in structure.find("crystal/varray[@name='basis']")];positions=[[float(v) for v in r.text.split()] for r in structure.find("varray[@name='positions']")]
     if not forces or len(forces)!=len(positions) or any(len(v)!=3 for v in forces+positions+basis) or len(basis)!=3 or not all(math.isfinite(v) for row2 in forces+positions+basis for v in row2):raise ValueError('Malformed/nonfinite accepted geometry or forces')
     if not physical.is_file() or not reference.is_file():raise ValueError('MISSING physical/reference snapshot for completed force point '+str(index))
     result.append(dict(ionic_step=index,physical_wavecar=str(physical),local_reference=str(reference),physical_wavecar_sha256=sha256(physical) if checksums else MISSING,local_reference_sha256=sha256(reference) if checksums else MISSING,lattice_angstrom=basis,fractional_positions=positions,forces_eV_angstrom=forces,Fmax_eV_angstrom=max(math.sqrt(sum(v*v for v in row2)) for row2 in forces),kappa=number(row[1]),kappa_valid=row[2].strip(),native_reference_ortho_error=number(paw.get(index,{}).get('reference_ortho_error')),native_PAW_measurement=paw.get(index,MISSING)))
   element.clear()
 except ET.ParseError:incomplete=True
 if point=='last':result=result[-1:]
 elif point is not None:result=[r for r in result if r['ionic_step']==int(point)]
 if point is not None and not result:raise ValueError('Requested completed checkpoint is not available')
 return dict(run=str(run),completed_force_points=index,exported_points=len(result),incomplete_xml_tail_ignored=incomplete,checkpoints=result,scope='Completed native force point and matching saved physical/local reference; no new overlaps computed',original_reference_preserved=True,automatic_optimizer_or_curvature_restore=False,finite_difference_force_accuracy=MISSING)

def write_poscars(run,output,points):
 try:from pymatgen.core import Structure,Lattice
 except ImportError as e:raise ValueError('--write-poscar requires pymatgen; JSON-only export does not') from e
 original=Structure.from_file(Path(run)/'POSCAR')
 for row in points:
  path=Path(output)/('POSCAR.accepted'+str(row['ionic_step']).zfill(4))
  if path.exists():raise ValueError('Refusing existing geometry: '+str(path))
  if len(original)!=len(row['fractional_positions']):raise ValueError('Original atom order/accepted geometry differ')
  structure=Structure(Lattice(row['lattice_angstrom']),original.species,row['fractional_positions'],site_properties=original.site_properties);structure.to(filename=str(path),fmt='poscar');row['geometry_file']=str(path.resolve())

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--point',help='Ionic index or last; default all completed points');p.add_argument('--checksums',action='store_true');p.add_argument('--write-poscar',action='store_true',help='Requires optional pymatgen; preserves input atom order/selective flags');a=p.parse_args()
 try:
  destination=a.output_dir/'checkpoints.json'
  if destination.exists():raise ValueError('Refusing existing output: '+str(destination))
  out=export(a.run,a.point,a.checksums);a.output_dir.mkdir(parents=True,exist_ok=True)
  if a.write_poscar:write_poscars(a.run,a.output_dir,out['checkpoints'])
  write_json(destination,out);print(json.dumps(dict(json=str(destination),completed_force_points=out['completed_force_points'],exported_points=out['exported_points'],incomplete_tail_ignored=out['incomplete_xml_tail_ignored'])))
 except (OSError,ValueError,KeyError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
