import hashlib,importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('patcher',Path(__file__).resolve().parents[1]/'tools/patch_vasp.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class PatcherTests(unittest.TestCase):
 def test_context_free_transform_and_tamper_rejection(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);old=b'alpha\nbeta\n';new=b'alpha\ngamma\n';payload=b'gamma\n';(d/'insert.inc').write_bytes(payload);e={'path':'toy','before_sha256':p.digest(old),'after_sha256':p.digest(new),'edits':[dict(start_line=1,end_line=2,removed_sha256=p.digest(b'beta\n'),payload='insert.inc',payload_sha256=p.digest(payload))]}
   self.assertEqual(p.transform(old,e,d),new)
   with self.assertRaises(ValueError):p.transform(b'unrecognized\n',e,d)
   (d/'insert.inc').write_bytes(b'tampered\n')
   with self.assertRaises(ValueError):p.transform(old,e,d)
if __name__=='__main__':unittest.main()
