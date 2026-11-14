import csv,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
TOOLS=Path(__file__).resolve().parents[1]/'tools';sys.path.insert(0,str(TOOLS))
from analyze_paw_nto import metrics,read_wswq
from analyze_tddft_nto import analyze
from summarize_saddle import summarize
from export_ionic_checkpoints import export
from merge_incar import parse

class ScientificTools(unittest.TestCase):
 def test_complex_paw_density_matrix_and_all_leakage_channels(self):
  rng=np.random.default_rng(7);U=np.linalg.qr(rng.normal(size=(5,5))+1j*rng.normal(size=(5,5)))[0];f=np.array([1,1,0,0,0]);P=(U*f)@U.conj().T
  m,q,rows=metrics(U.conj().T,f,np.arange(5.),2,3)
  self.assertAlmostEqual(m['h'],P[1,1].real);self.assertAlmostEqual(m['p'],P[2,2].real);self.assertAlmostEqual(m['c_re'],P[1,2].real);self.assertAlmostEqual(m['c_im'],P[1,2].imag)
  self.assertAlmostEqual(m['ell_h_val'],abs(P[0,1])**2);self.assertAlmostEqual(m['ell_h_virt'],sum(abs(P[k,1])**2 for k in [3,4]));self.assertAlmostEqual(m['ell_p_val'],abs(P[0,2])**2);self.assertAlmostEqual(m['ell_p_virt'],sum(abs(P[k,2])**2 for k in [3,4]));self.assertAlmostEqual(m['N_reference_subspace'],np.trace(P[:3,:3]).real);self.assertTrue(q['projector_bounds_within_1e_minus5'])
 def test_wswq_requires_complete_native_selected_spin_block(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'WSWQ';p.write_text('spin=2, kpoint=1\ni=1, j=1 : 1 0\ni=2, j=1 : 0 0\ni=1, j=2 : 0 0\n')
   with self.assertRaises(ValueError):read_wswq(p)
   p.write_text(p.read_text()+'i=2, j=2 : 1 0\n');np.testing.assert_array_equal(read_wswq(p),np.eye(2))
 def test_complex_nto_svd_reconstructs_negative_response_root(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'BSEFATBAND';T=np.array([[.6,.8j],[0,0]],complex);text='8 1\n1BSE eigenvalue -0.2 IP-eigenvalue: 1\n'
   for matrix in [np.zeros((2,2)),T]:
    for i,h in enumerate([1,2]):
     for j,v in enumerate([3,4]):
      z=matrix[i,j];text+=f'0 0 0 {h} {v} 0 {h} {v} {z.real} +i* {z.imag}\n'
   p.write_text(text);out,a=analyze(p,[1],pairs=2);self.assertEqual(out['roots'][0]['energy_ev'],-.2);np.testing.assert_allclose((a['r1_beta_hole_coefficients']*a['r1_beta_singular_values'])@a['r1_beta_particle_coefficients'].conj().T,T,atol=1e-14);self.assertAlmostEqual(out['roots'][0]['spins']['beta']['leading_pair_fraction'],1)
 def test_raw_streak_uses_ionic_stage_index_and_stdout_fallback(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);(d/'NTO_SADDLE').write_text('MODE SECANT\nIONIC_FOLLOW T\n');(d/'OSZICAR').write_text('');(d/'vasp.stdout').write_text('DMP: 1 -799 1e-5\nDMP: 2 -800 1e-6\n'+''.join(f'DMP: {n} -800 1e-10\n' for n in range(1,20)));(d/'OUTCAR').write_text('General timing and accounting informations for this job\n');(d/'vasp.exit').write_text('0\n')
   cols=['ionic_step','step','mode','h','p','c_abs','g_mode_re','R_perp_subspace','R_perp_est_normalized','stop_rule']
   with (d/'NTO_SADDLE_TRACE.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,cols);w.writeheader()
    for n in [17,18,19]:w.writerow(dict(ionic_step=2,step=n,mode='SECANT',h=.001,p=.999,c_abs=.001,g_mode_re=2e-5,R_perp_subspace=3e-5,R_perp_est_normalized='MISSING',stop_rule='FAST_SUBSPACE'))
   out,rows=summarize(d);self.assertTrue(out['completed_residual_candidate']);self.assertFalse(out['full_stationarity_confirmed']);self.assertEqual(out['computed_last_secant_stage_step'],6);self.assertEqual(rows[-1]['energy_source'],'vasp.stdout');(d/'vasp.exit').write_text('1\n');self.assertFalse(summarize(d)[0]['completed_residual_candidate'])
 def test_live_checkpoint_export_ignores_unfinished_force_point(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);(d/'NTO_SADDLE_IONIC_CHECKPOINT.csv').write_text('1,-.7,T,I01,R01\n2,0,F,I02,R02\n');(d/'WAVECAR.I01').write_bytes(b'physical');(d/'WAVECAR.R01').write_bytes(b'reference');(d/'vasprun.xml').write_text('<modeling><calculation><structure><crystal><varray name="basis"><v>1 0 0</v><v>0 1 0</v><v>0 0 1</v></varray></crystal><varray name="positions"><v>0 0 0</v></varray></structure><varray name="forces"><v>3 4 0</v></varray></calculation><calculation>')
   v=export(d,'last',True);self.assertTrue(v['incomplete_xml_tail_ignored']);self.assertEqual(v['exported_points'],1);self.assertEqual(v['checkpoints'][0]['Fmax_eV_angstrom'],5);self.assertEqual(Path(v['checkpoints'][0]['physical_wavecar']).name,'WAVECAR.I01')
 def test_incar_merge_parser_preserves_hybrid_and_rejects_duplicates(self):
  a=parse('AEXX=.4; HFSCREEN=0 # comment\nFERDO=191*1 33*0\n');self.assertEqual(a['AEXX'],'.4');self.assertEqual(a['FERDO'],'191*1 33*0')
  with self.assertRaises(ValueError):parse('AEXX=.4\nAEXX=.25\n')
 def test_launcher_records_nonzero_exit_and_refuses_reusing_outputs(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);fake=d/'fake';fake.write_text('#!/bin/sh\necho synthetic\nexit 7\n');fake.chmod(0o755)
   for name in ['INCAR','POSCAR','POTCAR','KPOINTS','WAVECAR']:(d/name).write_text('synthetic input')
   env=dict(os.environ,VASP_GAM=str(fake),VASP_LAUNCHER='direct',SLURM_NTASKS='1');cmd=['bash',str(TOOLS/'run_single_rank.sh')];a=subprocess.run(cmd,cwd=d,env=env,capture_output=True);self.assertEqual(a.returncode,7);self.assertEqual((d/'vasp.exit').read_text().strip(),'7');self.assertIn('synthetic',(d/'vasp.stdout').read_text());self.assertEqual(subprocess.run(cmd,cwd=d,env=env,capture_output=True).returncode,2)
if __name__=='__main__':unittest.main()
