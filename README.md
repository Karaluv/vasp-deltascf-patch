# vasp-deltascf-patch

**NTO-guided excited-state ΔSCF saddle-point optimization for VASP 6.6.0.**

A source patcher for one-mode orbital optimization in the full PAW overlap metric. One executable provides runtime **OFF, PROJECT, REFLECT and SECANT** modes through `NTO_SADDLE`. The Hamiltonian, occupations and energy functional are unchanged.

Research software for fixed-occupation excited-state DFT. Relevant to ΔSCF / delta-SCF, natural transition orbitals (NTO), constrained occupations, and MOM / IMOM workflows. MOM/IMOM occupation selectors and charge-constrained DFT are **not implemented** by this patch.

## Supported configuration

- Exact **VASP 6.6.0, release date 06Mar2026** source snapshot; input-file SHA256 checks reject different snapshots.
- Tested implementation: Gamma-real, **one MPI rank**, collinear two-spin PAW hybrid calculation, **224 bands**, **191 occupied beta orbitals**; alpha occupations `192*1 32*0`.
- `ALGO=Damped`, `LDIAG=.FALSE.`, `LSUBROT=.FALSE.`, fixed binary occupations, beta `FERDO=191*1 33*0`.
- Beta band 192 is the empty hole-like orbital. The occupied particle direction is collective, not tied to a single occupied band.
- Public status: experimental. GPU targets compiled locally: Ada, A100, H200 and TITAN X. This is not general MPI, k-point, SOC, arbitrary-band or complex-wavefunction support.

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
| SECANT | -1 | Damped one-mode secant correction with guarded REFLECT fallback |

Change thresholds in `NTO_SADDLE` before starting a run. **No recompilation is required for threshold changes.** The file is read once at startup and effective values are written to OUTCAR. Defaults without explicit STOP_* keys are conservative; the example contains the current exploratory policy.

## Acceptance and outputs

`NTO_SADDLE_TRACE.csv` reports PAW h/p/c, the **raw** mode gradient and available residual estimates. `NTO_SADDLE_STEP.csv` reports requested/measured updates, PAW orthogonality and retraction retries. `full_residual=MISSING` means the full-space stationary residual has not been established; a small energy change or PROJECT plateau is not stationary-state proof.

SECANT stops after three qualifying steps, with a minimum step index of 20 in the example: raw `|g_mode| <= 6.5e-5 eV`, normalized estimated transverse residual `<=1e-4`, transverse subspace residual `<=3e-4 eV`, `|dE|<=5e-8 eV`, `h<0.08`, `p>0.90`, `|c|<0.02`. Both transverse conditions apply. These are diagnostic tolerances, not a universal error bound on energies or forces.

## Documentation

- [Theory](docs/theory.md): mode, PAW metric, projected/reflected steps and stopping.
- [Implementation](docs/implementation.md): integration points, patch format, safeguards.
- [Forces and ionic optimization](docs/forces.md): experimental development and validation gates.
- [Credits](CREDITS.md).

## Development

```sh
python3 -m unittest discover -s tests -v
```

No VASP source is needed for the public tooling tests. Private apply/byte-comparison/revert checks were run against the supported licensed source snapshot. Compilation is separate from physical validation.

MIT applies only to the original additions in this repository. VASP retains its own license and attribution. This is an independent project, not an official VASP release.
