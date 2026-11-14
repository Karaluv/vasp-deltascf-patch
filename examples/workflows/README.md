# Executable workflow examples

These are **72-atom,383-electron Gamma beta-excitation examples**: NBANDS224, alpha192 occupied, beta191 occupied. Adjust all band windows, masks and NTO indices together for another system. Preserve the intended base functional/POTCAR/basis/cell; fragments are explicit overlays, not complete replacement INCARs. Commands use new output directories and refuse to overwrite old calculations.

Install `numpy`; POSCAR checkpoint export optionally needs `pymatgen`. Set `REPO` to the absolute repository path. Load your site's matching compiler/CUDA/MPI environment and select the executable explicitly. The examples do not guess which GPU/binary to use. `run_single_rank.sh` supports `VASP_LAUNCHER=mpirun` (default), `srun` or `direct` and writes input hashes, stdout and exit status. A site-neutral Slurm skeleton is included; a local dispatcher should use its qualified profiles instead.

## 1. TDDFT/BSE -> NTO -> canonical seed

Set `GS` to the original matching ground directory and `TDDFT` to its completed response directory. Set `SOURCE_SHA256` to the GS WAVECAR hash **recorded for that response**, not a hash of an arbitrary replacement. Run `01_tddft_to_nto/commands.sh` in a fresh work area. It exports NTO weights/vectors (JSON/NPZ), creates the reference/canonical seed, writes occupations and generates an AUTO NTO_SADDLE with matching indices.

An energy match is a consistency check, not proof of orbital gauge. Do not substitute a nearby geometry or another ground WAVECAR. Legacy RTAG needs the explicit, known `vasp_gam` provenance assertion `--gamma-real`.

An existing reference can also be used:

```sh
python3 "$REPO/tools/prepare_nto_seed.py" --reference /path/reference.nto \
  --gamma-real --output-dir seed \
  --saddle-template "$REPO/examples/workflows/03_auto/NTO_SADDLE"
```

## 2. Full-PAW seed preflight

Set `SEED` to the absolute generated directory, `VASP_STOCK_GAM` to an original compatible executable, and `GEOMETRY` to the exact geometry matching the response WAVECAR. Typically this is TDDFT/POSCAR or the final GS/CONTCAR. **The original GS/POSCAR may be the unrelaxed starting geometry.** Run `02_paw_preflight/commands.sh`. It requests native WSWQ and checks h≈0,p≈1,c≈0 and the canonical particle/hole slots. Preparation alone never claims PAW identity.

## 3. AUTO in one process

Set `PREFLIGHT` to the absolute accepted preflight directory and `VASP_SADDLE_GAM` to the patched executable. Run `03_auto/commands.sh`. It uses PROJECT80 -> REFLECT60 -> SECANT≤200, TIME0.05, NELM340. The summary and final native PAW identity gate must both pass before downstream use.

## 4. Separate PROJECT/REFLECT/SECANT directories

`04_staged/commands.sh` preserves each final WAVECAR and the initial reference. PROJECT is capture only. Repeated process starts lose Damped velocity/secant history; AUTO avoids that difference. The sample index files are for191/192; for another system, replace them with the emitted NTO_SADDLE.indices values rather than appending duplicate keys.

## 5. Continuous excited-state geometry optimization

Set `S4` to an accepted excited directory. `05_ionic/commands.sh` starts a bounded8-point native IBRION2 pilot with IWAVPR0 and accepted physical/local-reference snapshots. Following ions use8PROJECT/5REFLECT/SECANT, TIME0.08. Original reference data stays unchanged. The exporter pairs completed forces with Ixy/Rxy checkpoints and matching geometries, including a live XML with an unfinished tail. Neither snapshot creation nor this example establishes finite-difference force accuracy or restores optimizer history.

## 6. Hybrid TDDFT about an excited projector

`06_excited_tddft/commands.sh` uses the original compatible response binary, fixed excited occupations and ICHARG0. It intentionally does not copy a GS CHGCAR or stale WAVEDER. The O180/V16 kernel/window matches the example GS response. IDIOT0 gives energies/eigenvectors, **not optical strengths**. Negative roots are kept. TDHF-only VASP can omit normal EIGENVAL/final WSWQ; do not invent a final projector check. Occupied-block canonicality and interpretation of excited-reference spectra require separate validation.

## 7. OFF/raw diagnostic

`07_off_diagnostic/commands.sh` uses MODE OFF, ETA1, STOP_ON_EDIFF_ONLY T, one electronic step and full diagnostics. The first trace measures the input before an ordinary update. It is not an update-free oracle; never overwrite the accepted S4 with this probe output.
