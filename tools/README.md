# Scientific tools

Tools operate on your licensed local files. No VASP calculation is launched by a Python analysis/preparation tool. Outputs must be new; the example shell launcher also refuses a used calculation directory. Dependencies: `numpy`; `pymatgen` is optional for POSCAR checkpoint export.

| Tool | Input -> output |
| --- | --- |
| `analyze_tddft_nto.py` | Gamma BSEFATBAND -> per-root/per-spin SVD weights, hole/particle coefficients (JSON; complete matrices in optional NPZ). Negative roots retained. Optional matching WAVECAR energy/occupation check. |
| `prepare_nto_seed.py` | Matched GS WAVECAR+BSEFATBAND, or existing reference -> canonical WAVECAR, unchanged reference, occupations, indices, optional configured NTO_SADDLE. Optional contemporaneous source SHA256 check. |
| `analyze_paw_nto.py` | Native PAW WSWQ + current occupations -> complex2×2 M, eigenvalues/invariants, valence/virtual leakage, occupied-subspace loss and individual band weights (JSON/CSV). Seed/branch gates are separate from stationarity. |
| `summarize_saddle.py` | Run directory -> joined SCF/PAW/step/timing data, raw residual streak and completion checks (JSON/CSV). Handles ionic counters, stage-local minima and empty OSZICAR via stdout. |
| `export_ionic_checkpoints.py` | Checkpoint CSV + completed force XML elements -> matching physical/reference paths, geometry, forces, optional hashes/POSCAR. Handles an incomplete live XML tail. |
| `merge_incar.py` | Base INCAR + explicit overlays/KEY=VALUE overrides -> new unique-key INCAR and change/provenance report. Keeps unspecified functional settings. |
| `check_nto_controls.py` | NTO_SADDLE -> mode/eta/stopping/finite-control checks; `--write-defaults` explicitly adds missing mode defaults. |
| `run_single_rank.sh` | Fresh prepared directory + explicit compatible VASP_GAM -> one-rank launch, input hashes, stdout and exit code. |

Use `python3 tools/<name>.py --help`. Complete input fragments and commands: [workflow examples](../examples/workflows/README.md).

NTO SVD/coefficient rotations are algebra in the supplied KS orbital basis. They are **not pseudo-wave overlap estimates**. All reported physical overlap metrics come from native PAW WSWQ or saved native traces. Cross-overlap files alone cannot establish reference/current orthonormality; supply matching natively validated files. The PAW tool keeps tiny negative raw leakage/variance values caused by printed precision and reports unavailable ratios as MISSING instead of silently clipping them.

`analyze_paw_nto.py` defaults to beta, first n_occ reference valence bands excluding the pair, and a dynamic gap window n_occ−6..n_occ+9 plus significant-weight bands. Specify reference indices/valence list when using another layout. Edges are computed from occupations and stored band energies, never inferred from band number; LDIAG F band energies need not be canonical eigenvalues.

`--require-target` is an identity gate only. `--require-residual` additionally requires a completed exit0 run and the configured consecutive raw SECANT criteria; it does not establish the missing full-space residual or final PAW identity by itself. PROJECT and OFF cannot be accepted as a stationary excited result by this tool.

Checkpoint export never rewrites the original reference, starts a restart or restores velocity/optimizer/curvature state. Checkpoint geometry and a completed force record must correspond to the saved pair. Unknown fields stay MISSING.
