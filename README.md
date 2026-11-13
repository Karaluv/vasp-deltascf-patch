# vasp-deltascf-patch

**NTO-guided excited-state ΔSCF saddle-point optimization for VASP 6.6.0.**

A source patcher for one-mode orbital optimization in the full PAW overlap metric. One executable provides runtime **OFF, PROJECT, REFLECT, SECANT and AUTO** modes through `NTO_SADDLE`. The Hamiltonian, occupations and energy functional are unchanged.

Research software for fixed-occupation excited-state DFT. Relevant to ΔSCF / delta-SCF, natural transition orbitals (NTO), constrained occupations, and MOM / IMOM workflows. MOM/IMOM occupation selectors and charge-constrained DFT are **not implemented** by this patch.

## Supported configuration

- Exact **VASP 6.6.0, release date 06Mar2026** source snapshot; input-file SHA256 checks reject different snapshots.
- Tested implementation: Gamma-real, **one MPI rank**, collinear two-spin PAW hybrid calculation, reference tests use **224 bands**, **191 occupied beta orbitals**; alpha occupations `192*1 32*0`. Band indices and occupied count are runtime parameters, NBANDS comes from WDES.
- `ALGO=Damped`, `LDIAG=.FALSE.`, `LSUBROT=.FALSE.`, fixed binary occupations, beta `FERDO=191*1 33*0`.
- In the example, beta band 192 is the empty hole-like orbital. The occupied particle direction is collective, not tied to a single occupied band.
- Public status: experimental. GPU targets compiled locally: Ada, A100, H200 and TITAN X. This is not general MPI, k-point, SOC, complex-wavefunction support; other system sizes still require scientific validation.

This repository contains authored modifications and tooling. Obtain VASP separately under your own license. No VASP source distribution, executable, POTCAR or wavefunction data is included.

## Apply to your licensed source copy

```sh
python3 tools/patch_vasp.py /path/to/vasp.6.6.0          # dry-run, SHA256 checks
python3 tools/patch_vasp.py /path/to/vasp.6.6.0 --apply
# Rebuild vasp_gam using your existing supported VASP build configuration.
python3 tools/patch_vasp.py /path/to/vasp.6.6.0 --revert # restore local backups
```

All inputs are checked before source writes. Applying twice is idempotent. Original files are backed up locally under `.nto-dscf-backup/`; they must never be uploaded. The patcher distributes context-free edit payloads and hashes, rather than a VASP source archive. Other releases require a reviewed port; do not disable the hash checks.

## Runtime input

Copy [examples/NTO_SADDLE](examples/NTO_SADDLE) and merge [examples/INCAR.fragment](examples/INCAR.fragment) with the original functional/PAW settings. Supply a matching canonical excited-state `WAVECAR` and an unchanged initial reference as `WAVECAR.qqq`. The reference stores hole in beta column 191 and particle in beta column 192. The running canonical seed stores occupied particle in 191 and empty hole in 192. Swapping occupations alone does not prepare that seed.

| MODE | ETA | Purpose |
| --- | ---: | --- |
| OFF | 1 | Diagnostics with the original update; omit NTO_SADDLE for ordinary operation |
| PROJECT | 0 | Remove one mode from the actual update; preparation only |
| REFLECT | -1 | Reverse the selected update component |
| SECANT | -1 | Damped one-mode secant correction with raw-gradient ascent safeguard |
| AUTO | staged | PROJECT -> REFLECT -> SECANT in one process; N_PROJECT/N_REFLECT control durations (experimental) |

Change thresholds in `NTO_SADDLE` before starting a run. **No recompilation is required for threshold changes.** The file is read once at startup and effective values are written to OUTCAR. Defaults without explicit STOP_* keys are conservative; the example contains the current exploratory policy.

## Seed preparation and dimensions

`tools/prepare_nto_seed.py` prepares a canonical seed from a matching Gamma-real reference or from a matching ground WAVECAR plus BSEFATBAND. Use `--help` for required provenance assertions and root selection. It copies the unchanged reference and permutes complete orbital records and metadata; occupations alone are insufficient. It checks file layout, matching eigenvalues and coefficient-space transformations. **Native full-PAW preflight remains required:** the tool labels PAW identity `PAW_PREFLIGHT_REQUIRED`, never inferred from plane-wave norms.

Set `N_OCC_BETA`, `HOLE_BAND`, `REF_HOLE_BAND`, `REF_PART_BAND`. If occupied count is omitted/AUTO it is inferred from contiguous binary beta occupations. The example indices are 191,192,191,192. General k points, multi-rank and complex orbitals remain unsupported.

## FAST_PATH and trust corridor

The default fast path uses two beta reference columns with VASP's native PAW `W1_DOT(...,CQIJ)`. It calls native ORTHCH once, then solves a finite-angle two-plane Givens correction and transports Damped velocity consistently. Full overlap matrices and repeated ORTHCH retries are absent from the fast electronic loop. Set `TRACE_FULL_DIAG T` for narrow/full PAW comparisons and global Gram checks.

Static SECANT uses `TRUST_C T`, `TRUST_C_MAX 0.015`: above the threshold a proposal that increases coherence in the selected two-plane is redirected toward lower coherence. Other relaxation modes can still change the actual measured coherence. This safeguard never changes raw g_mode or establishes stationarity by itself. Ionic-follow calculations use their own moving-reference controls; see forces documentation.

## Ascent guard and current limitation

The default SECANT safeguard tests the original gradient, not the total native search direction: with `delta_theta=-TARGET*TIME*sqrt(p)`, first-order selected-mode work is `2*g_raw*delta_theta`. The native direction includes momentum and preconditioning, so `TARGET*A<0` alone does not establish ascent. Version0.2.1 corrects that test. A private same-seed O68 regression removed the observed wrong-sign mode steps; it has **not** established SCF convergence.

The relative ceiling remains `2.5*abs(A)`. It can strongly limit the secant angle when the inertial direction nearly cancels despite a nonzero gradient. No runtime key disables that ceiling in this release. `SECANT_ROOT_STEP T` is a separate experimental signed-root policy that bypasses the ascent veto; it retains damping, both angle/relative limits and raw-residual acceptance. Its default is F and AUTO does not enable it.

## Acceptance and outputs

`NTO_SADDLE_TRACE.csv` reports PAW h/p/c, the **raw** mode gradient and available residual estimates. `NTO_SADDLE_STEP.csv` reports requested/measured updates and the exact Givens correction. `NTO_FAST_TIMING.csv` records timing and invariants. Full orthogonality diagnostics are MISSING when disabled. `full_residual=MISSING` means the full-space stationary residual has not been established; a small energy change or PROJECT plateau is not stationary-state proof.

SECANT stops after three qualifying steps, with a minimum step index of 20 in the example: raw `|g_mode| <= 6.5e-5 eV`, normalized estimated transverse residual `<=1e-4`, transverse subspace residual `<=3e-4 eV`, `|dE|<=5e-8 eV`, `h<0.08`, `p>0.90`, `|c|<0.02`. With `FAST_PATH T` (default), the subspace condition applies and the external/normalized full-PAW estimate is MISSING. `TRACE_FULL_DIAG T` enables the expensive diagnostic estimate and both transverse conditions apply. These are diagnostic tolerances, not a universal error bound on energies or forces.

## Documentation

- [Theory](docs/theory.md): mode, PAW metric, projected/reflected steps and stopping.
- [Implementation](docs/implementation.md): integration points, patch format, safeguards.
- [Forces and ionic optimization](docs/forces.md): opt-in compiled prototype, native-loop hooks and validation gates.
- [Performance evidence](docs/performance.md): matched native LOOP timings and PAW checks.
- [Credits](CREDITS.md).

## Development

```sh
python3 -m pip install numpy
python3 -m unittest discover -s tests -v
```

No VASP source is needed for the public tooling tests. Private apply/byte-comparison/revert checks were run against the supported licensed source snapshot. Compilation is separate from physical validation.

MIT applies only to the original additions in this repository. VASP retains its own license and attribution. This is an independent project, not an official VASP release.

Upgrading from v0.1.0 or v0.2.0: revert with that tagged patcher first, then apply this version to the pristine source. Both compatibility variants now contain the same unified three-file code; IONIC_FOLLOW remains opt-in and experimental.
