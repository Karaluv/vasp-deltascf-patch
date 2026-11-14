import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('controls',Path(__file__).resolve().parents[1]/'tools/check_nto_controls.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Controls(unittest.TestCase):
 def test_off_defaults_are_energy_only_and_source_is_not_edited_by_default(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'NTO_SADDLE';p.write_text('MODE OFF\n');v=mod.check(p);self.assertEqual(v['explicit_defaults']['STOP_ON_EDIFF_ONLY'],'T');self.assertEqual(p.read_text(),'MODE OFF\n');mod.check(p,True);self.assertIn('STOP_ON_EDIFF_ONLY T',p.read_text())
 def test_off_residual_stop_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'NTO_SADDLE';p.write_text('MODE OFF\nSTOP_ON_EDIFF_ONLY F\n')
   with self.assertRaises(ValueError):mod.check(p)
 def test_nonfinite_controls_and_duplicate_keys_are_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'NTO_SADDLE'
   for text in ['MODE SECANT\nSECANT_DAMPING nan\n','MODE SECANT\nSECANT_CAP_FACTOR inf\n','MODE SECANT\nETA -1\nETA -1\n','MODE SECANT\nSTOP_ON_EDIFF_ONLY T\n']:
    p.write_text(text)
    with self.assertRaises(ValueError):mod.check(p)
if __name__=='__main__':unittest.main()
