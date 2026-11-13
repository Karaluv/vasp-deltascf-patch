import argparse
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location('seed', Path(__file__).resolve().parents[1] / 'tools/prepare_nto_seed.py')
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


def fixture(path):
    recl, nb, nplane = 256, 4, 3
    data = bytearray((2 + 2 * (nb + 1)) * recl)
    struct.pack_into('<3d', data, 0, recl, 2, 45200)
    struct.pack_into('<2d', data, recl, 1, nb)
    for spin in [0, 1]:
        start = 2 + spin * (nb + 1)
        struct.pack_into('<4d', data, start * recl, nplane, 0, 0, 0)
        for band in range(1, nb + 1):
            struct.pack_into('<3d', data, start * recl + 32 + (band - 1) * 24, band, 0, float(band <= 2))
            record = (start + band) * recl
            coeff = np.array([band, spin + .2j, band * .01], dtype='<c8')
            data[record:record + coeff.nbytes] = coeff.tobytes()
            data[record + coeff.nbytes:record + recl] = bytes([band + spin * 5]) * (recl - coeff.nbytes)
    path.write_bytes(data)


class SeedTests(unittest.TestCase):
    def test_record_and_metadata_swap_preserves_alpha_and_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / 'reference.nto'
            fixture(src)
            original = src.read_bytes()
            args = argparse.Namespace(reference=src, ground=None, output_dir=root / 'seed', n_occ_beta=None, ref_hole_band=None, ref_part_band=None, hole_band=None, gamma_real=True)
            report = seed.prepare(args)
            self.assertEqual(src.read_bytes(), original)
            self.assertEqual((root / 'seed/WAVECAR.qqq').read_bytes(), original)
            self.assertEqual(report['destination_to_reference_band'], [1, 3, 2, 4])
            before, after = seed.Wavecar(src), seed.Wavecar(root / 'seed/WAVECAR')
            np.testing.assert_array_equal(after.metadata(1)[:, 0], [1, 3, 2, 4])
            np.testing.assert_array_equal(after.metadata(1)[:, 2], [1, 1, 0, 0])
            self.assertEqual(before.header(0), after.header(0))
            self.assertEqual(report['full_paw_identity'], 'MISSING')
            with self.assertRaises(ValueError):
                seed.prepare(args)

    def test_nonadjacent_hole_slot_and_record_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dest = root / 'reference', root / 'canonical'
            fixture(src)
            order = seed.canonicalize(src, dest, 2, 2, 3, 4)
            self.assertEqual(order, [1, 3, 4, 2])
            a, b = seed.Wavecar(src), seed.Wavecar(dest)
            self.assertEqual(a.beta_record_bytes(2), b.beta_record_bytes(4))

    def test_householder_matches_requested_nto_linear_combination(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'WAVECAR'
            fixture(path)
            before = seed.Wavecar(path)
            coefficients = np.array([np.frombuffer(before.beta_record_bytes(i), dtype='<c8', count=3) for i in [1, 2]])
            direction = np.array([.6, .8])
            seed.rotate_subspace(path, [1, 2], 2, direction, 2)
            actual = np.frombuffer(seed.Wavecar(path).beta_record_bytes(2), dtype='<c8', count=3)
            np.testing.assert_allclose(actual, direction @ coefficients, rtol=1e-6, atol=1e-7)
            # Byte/linear-algebra test only: no physical wavefunction overlap is asserted.


if __name__ == '__main__':
    unittest.main()
