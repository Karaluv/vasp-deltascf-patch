#!/usr/bin/env python3
"""Prepare a Gamma-real canonical beta NTO WAVECAR without an SCF calculation.

No wavefunction-overlap approximation is used: PAW identity requires a separate
native WSWQ preflight. Source files are read-only and outputs must be new.
"""
import argparse
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path

import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class Wavecar:
    """Validated direct-access WAVECAR layout; one k-point, two spins."""
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('rb') as handle:
            first = handle.read(24)
            if len(first) != 24:
                raise ValueError('Truncated WAVECAR header')
            for endian in ['<', '>']:
                recl, spin, tag = struct.unpack(endian + '3d', first)
                if recl.is_integer() and spin == 2 and tag in [45200, 45210, 53300, 53310]:
                    self.endian = endian
                    self.recl, self.tag = int(recl), int(tag)
                    break
            else:
                raise ValueError('Requires a supported Gamma-real WAVECAR (RTAG 45200/45210/53300/53310, ISPIN=2)')
            if self.recl < 32 or self.recl % 8:
                raise ValueError('Invalid record length')
            handle.seek(self.recl)
            second = handle.read(16)
            if len(second) != 16:
                raise ValueError('Truncated global header')
            nk, nb = struct.unpack(self.endian + '2d', second)
            if nk != 1 or not nb.is_integer() or nb < 2:
                raise ValueError('Requires one Gamma k-point and at least two bands')
            self.nbands = int(nb)
        self.dtype = np.dtype(self.endian + ('c8' if self.tag in [45200, 53300] else 'c16'))
        self.float_dtype = np.dtype(self.endian + 'f8')
        self.beta_record = 2 + self.nbands + 1
        if (4 + 3 * self.nbands) * 8 > self.recl:
            raise ValueError('Band metadata does not fit its record')
        if self.path.stat().st_size < (2 + 2 * (self.nbands + 1)) * self.recl:
            raise ValueError('Truncated orbital records')
        self.alpha = self.header(0)
        self.beta = self.header(1)
        for header in [self.alpha, self.beta]:
            if np.max(abs(np.frombuffer(header, dtype=self.float_dtype, count=3, offset=8))) > 1e-12:
                raise ValueError('The k-point must be Gamma')
            nplane = int(np.frombuffer(header[:8], dtype=self.float_dtype)[0])
            if nplane <= 0 or nplane * self.dtype.itemsize > self.recl:
                raise ValueError('Invalid plane-wave count')

    def header(self, spin):
        with self.path.open('rb') as handle:
            handle.seek((2 + spin * (self.nbands + 1)) * self.recl)
            return handle.read(self.recl)

    def metadata(self, spin):
        return np.frombuffer(self.header(spin), dtype=self.float_dtype, count=3 * self.nbands, offset=32).copy().reshape(self.nbands, 3)

    def beta_record_bytes(self, band):
        with self.path.open('rb') as handle:
            handle.seek((self.beta_record + band) * self.recl)
            return handle.read(self.recl)


def binary_count(occupations):
    if not np.all(np.isfinite(occupations)) or np.max(abs(occupations - np.rint(occupations))) > 1e-6:
        raise ValueError('Fractional occupations are unsupported')
    if np.any(occupations < -1e-6) or np.any(occupations > 1 + 1e-6):
        raise ValueError('Expected occupations in [0,1]')
    return int(np.rint(occupations).sum())


def parse_beta_root(path, root, wavecar, tolerance):
    """VASP BSEFATBAND: equal ordered alpha/beta blocks at one Gamma point."""
    with Path(path).open() as handle:
        ntrans, nroots = map(int, next(handle).split())
        if ntrans <= 0 or ntrans % 2 or not 1 <= root <= nroots:
            raise ValueError('Invalid root or unequal spin-block layout')
        selected = None
        for index in range(1, root + 1):
            header = next(handle).split()
            if not re.match(r'^' + str(index) + r'BSE$', header[0]):
                raise ValueError('Unsupported BSEFATBAND root header')
            energy = float(header[2])
            rows = [next(handle) for _ in range(ntrans)]
            if index == root:
                selected = rows[ntrans // 2:]
    occupied, virtual, entries = set(), set(), []
    metadata = wavecar.metadata(1)
    max_error = 0.0
    for line in selected:
        fields = line.replace('+i*', ' ').replace('-i*', ' -').split()
        if len(fields) != 10 or max(abs(float(x)) for x in fields[:3]) > 1e-12:
            raise ValueError('Requires the supported single-Gamma BSEFATBAND layout')
        hole, particle = int(fields[6]), int(fields[7])
        if not 1 <= hole <= wavecar.nbands or not 1 <= particle <= wavecar.nbands:
            raise ValueError('Response band outside WAVECAR')
        max_error = max(max_error, abs(float(fields[3]) - metadata[hole - 1, 0]), abs(float(fields[4]) - metadata[particle - 1, 0]))
        entries.append((hole, particle, complex(float(fields[8]), float(fields[9]))))
        occupied.add(hole)
        virtual.add(particle)
    if max_error > tolerance:
        raise ValueError('Response/WAVECAR eigenvalue mismatch: ' + str(max_error) + ' eV')
    occupied, virtual = sorted(occupied), sorted(virtual)
    if set(occupied) & set(virtual):
        raise ValueError('Overlapping response hole/particle subspaces')
    if np.max(abs(metadata[np.array(occupied) - 1, 2] - 1)) > 1e-6 or np.max(abs(metadata[np.array(virtual) - 1, 2])) > 1e-6:
        raise ValueError('Response subspaces disagree with beta occupations')
    oi, vi = {b: i for i, b in enumerate(occupied)}, {b: i for i, b in enumerate(virtual)}
    matrix = np.zeros((len(occupied), len(virtual)), complex)
    seen = set()
    for h, p, value in entries:
        if (h, p) in seen:
            raise ValueError('Duplicate beta transition')
        seen.add((h, p))
        matrix[oi[h], vi[p]] = value
    return energy, occupied, virtual, matrix, max_error


def real_direction(vector):
    vector = np.asarray(vector, complex)
    vector = vector * np.exp(-1j * np.angle(vector[np.argmax(abs(vector))]))
    if np.max(abs(vector.imag)) > 1e-10:
        raise ValueError('Complex NTO direction is unsupported by the Gamma-real patch')
    vector = vector.real
    return vector / np.linalg.norm(vector)


def rotate_subspace(path, bands, target, vector, chunk_size):
    """Real Householder rotation, streamed over plane waves; no pseudo-overlaps."""
    if target not in bands:
        raise ValueError('Reference target is outside the response subspace')
    wave = Wavecar(path)
    vector = real_direction(vector)
    w = vector.copy()
    w[bands.index(target)] -= 1
    denominator = float(w @ w)
    if denominator < 1e-24:
        return
    nplane = int(np.frombuffer(wave.beta[:8], dtype=wave.float_dtype)[0])
    with Path(path).open('r+b') as handle:
        for start in range(0, nplane, chunk_size):
            count = min(chunk_size, nplane - start)
            block = np.empty((len(bands), count), wave.dtype)
            for i, band in enumerate(bands):
                handle.seek((wave.beta_record + band) * wave.recl + start * wave.dtype.itemsize)
                block[i] = np.frombuffer(handle.read(count * wave.dtype.itemsize), wave.dtype)
            transformed = (block - (2 / denominator) * w[:, None] * (w @ block)[None, :]).astype(wave.dtype)
            for i, band in enumerate(bands):
                handle.seek((wave.beta_record + band) * wave.recl + start * wave.dtype.itemsize)
                handle.write(transformed[i].tobytes())
        metadata = wave.metadata(1)
        indices = np.array(bands) - 1
        energies = metadata[indices, :2].copy()
        weighted = (w * w) @ energies
        metadata[indices, :2] = energies + (4 * w[:, None] ** 2 / denominator) * (weighted[None, :] / denominator - energies)
        header = bytearray(wave.beta)
        header[32:32 + 24 * wave.nbands] = metadata.astype(wave.float_dtype).tobytes()
        handle.seek(wave.beta_record * wave.recl)
        handle.write(header)


def canonicalize(reference, output, nocc, ref_hole, ref_part, hole_band):
    wave = Wavecar(reference)
    if not (1 <= ref_hole <= nocc < ref_part <= wave.nbands and nocc < hole_band <= wave.nbands):
        raise ValueError('Need a valence reference hole, virtual reference particle and empty current hole slot')
    occupied_sources = [b for b in range(1, nocc + 1) if b != ref_hole] + [ref_part]
    remaining = iter(b for b in range(1, wave.nbands + 1) if b not in set(occupied_sources) and b != ref_hole)
    permutation = occupied_sources + [ref_hole if b == hole_band else next(remaining) for b in range(nocc + 1, wave.nbands + 1)]
    shutil.copyfile(reference, output)
    metadata = wave.metadata(1)[np.array(permutation) - 1].copy()
    metadata[:, 2] = np.arange(wave.nbands) < nocc
    with Path(output).open('r+b') as handle:
        for dest, source in enumerate(permutation, 1):
            handle.seek((wave.beta_record + dest) * wave.recl)
            handle.write(wave.beta_record_bytes(source))
        header = bytearray(wave.beta)
        header[32:32 + 24 * wave.nbands] = metadata.astype(wave.float_dtype).tobytes()
        handle.seek(wave.beta_record * wave.recl)
        handle.write(header)
    result = Wavecar(output)
    for dest, source in enumerate(permutation, 1):
        if result.beta_record_bytes(dest) != wave.beta_record_bytes(source):
            raise ValueError('Orbital-record permutation failed byte verification')
    with Path(reference).open('rb') as a, Path(output).open('rb') as b:
        left = wave.beta_record * wave.recl
        while left:
            size = min(left, 1024 * 1024)
            if a.read(size) != b.read(size):
                raise ValueError('Alpha/global records changed')
            left -= size
    return permutation


def prepare(args):
    source = Path(args.reference or args.ground).resolve()
    before = sha256(source)
    wave = Wavecar(source)
    if wave.tag in [45200, 45210] and not args.gamma_real:
        raise ValueError('Legacy RTAG does not identify Gamma-real packing: assert known vasp_gam provenance with --gamma-real')
    nocc = args.n_occ_beta or binary_count(wave.metadata(1)[:, 2])
    rh, rp, q = args.ref_hole_band or nocc, args.ref_part_band or nocc + 1, args.hole_band or nocc + 1
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    names = ['WAVECAR', 'WAVECAR.qqq', 'nto_seed.json', 'INCAR.occupations', 'NTO_SADDLE.indices']
    if any((output / name).exists() for name in names):
        raise ValueError('Refusing to overwrite an existing output')
    report = {'source_sha256': before, 'nbands': wave.nbands, 'n_occ_beta': nocc, 'ref_hole_band': rh, 'ref_part_band': rp, 'hole_band': q, 'full_paw_identity': 'MISSING', 'status': 'PAW_PREFLIGHT_REQUIRED'}
    temporary = output / '.WAVECAR.reference.tmp'
    with temporary.open('xb'):
        pass
    try:
        shutil.copyfile(source, temporary)
        if args.ground:
            if not args.bsefatband:
                raise ValueError('--ground requires --bsefatband')
            energy, occupied, virtual, matrix, mismatch = parse_beta_root(args.bsefatband, args.root, wave, args.eigenvalue_tolerance)
            u, singular, vh = np.linalg.svd(matrix, full_matrices=False)
            norm = float(np.sum(abs(matrix) ** 2))
            fraction = float(singular[0] ** 2 / norm) if norm else 0
            if norm < args.min_beta_weight or fraction < args.min_pair_fraction:
                raise ValueError('Selected beta root is not dominated by the requested single NTO pair')
            rotate_subspace(temporary, occupied, rh, u[:, 0], args.chunk_coefficients)
            rotate_subspace(temporary, virtual, rp, vh[0].conj(), args.chunk_coefficients)
            report.update(response_sha256=sha256(args.bsefatband),root=args.root,root_energy_ev=energy,beta_weight=norm,pair_fraction=fraction,response_eigenvalue_max_error_ev=mismatch)
        permutation = canonicalize(temporary, output / 'WAVECAR', nocc, rh, rp, q)
        shutil.copyfile(temporary, output / 'WAVECAR.qqq')
        if args.reference and sha256(output / 'WAVECAR.qqq') != before:
            raise ValueError('Provided reference was not preserved')
        if sha256(source) != before:
            raise ValueError('Source file changed during preparation')
        report.update(wavecar_sha256=sha256(output / 'WAVECAR'),reference_sha256=sha256(output / 'WAVECAR.qqq'),destination_to_reference_band=permutation,occupied_reference_bands=permutation[:nocc],records_and_alpha_verified=True)
        alpha = Wavecar(output / 'WAVECAR').metadata(0)[:, 2]
        nalpha = binary_count(alpha)
        if np.max(abs(alpha - (np.arange(wave.nbands) < nalpha))) > 1e-6:
            raise ValueError('Noncanonical alpha occupations need explicit handling')
        (output / 'INCAR.occupations').write_text(f'FERWE = {nalpha}*1 {wave.nbands-nalpha}*0\nFERDO = {nocc}*1 {wave.nbands-nocc}*0\n')
        (output / 'NTO_SADDLE.indices').write_text(f'N_OCC_BETA {nocc}\nHOLE_BAND {q}\nREF_HOLE_BAND {rh}\nREF_PART_BAND {rp}\n')
        (output / 'nto_seed.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    except BaseException:
        for name in names:
            (output / name).unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--reference', type=Path, help='Existing NTO reference; copied unchanged')
    source.add_argument('--ground', type=Path, help='Matching ground-state Gamma-real WAVECAR')
    parser.add_argument('--bsefatband', type=Path)
    parser.add_argument('--gamma-real', action='store_true', help='Assert vasp_gam provenance when legacy RTAG cannot distinguish packing')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--root', type=int, default=1)
    parser.add_argument('--n-occ-beta', type=int)
    parser.add_argument('--hole-band', type=int)
    parser.add_argument('--ref-hole-band', type=int)
    parser.add_argument('--ref-part-band', type=int)
    parser.add_argument('--eigenvalue-tolerance', type=float, default=0.002)
    parser.add_argument('--min-beta-weight', type=float, default=0.9)
    parser.add_argument('--min-pair-fraction', type=float, default=0.9)
    parser.add_argument('--chunk-coefficients', type=int, default=4096)
    args = parser.parse_args()
    if args.chunk_coefficients < 1:
        parser.error('--chunk-coefficients must be positive')
    try:
        print(json.dumps(prepare(args), indent=2, allow_nan=False))
    except (OSError,ValueError,StopIteration) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
