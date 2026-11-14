# Forces and continuous geometry optimization

Status: opt-in unified prototype compiled for four GPU targets. The previous O38 test accepted the first geometry and evaluated native forces; the second did not pass the electronic gate within its budget. An updated FAST ionic test is separate. Force accuracy, restart continuity and near-native ionic speed remain unvalidated.

The implementation uses one native VASP process: SECANT electronic solve, stationary-state acceptance gate, VASP native force/stress evaluation, native ionic optimizer, and an in-memory electronic restart on the next geometry. No external restart per ionic step is intended.

A geometry update invalidates old atom-centered PAW projection coefficients. Recompute projections and PAW orthonormality on the new geometry. Carry the accepted occupied subspace, collective particle direction and empty hole direction; reset the secant angular/gradient history, since the energy surface and local gauge changed. Keep the immutable input NTO reference on disk, and distinguish transported local references from the original NTO diagnostics.

The first prototype uses fixed cell and IWAVPR=0 to isolate transport. VASP's [IWAVPR documentation](https://vasp.at/wiki/IWAVPR) describes 0 as disabling prediction and 11 as the charge-density predictor commonly used for relaxation. IWAVPR=11 is a subsequent comparison, not a demonstrated equivalent.

## Acceptance before use

1. Reject ionic advancement if SECANT reaches NELM without the specified raw-residual/identity gate.
2. Two or more ionic steps in one process, with unambiguous ionic/electronic indices and preserved branch identity.
3. Compare native forces with central finite differences on the same excited branch, tightening electronic tolerances as needed.
4. Test reload continuity, small displacements, reference normalization and PAW projector refresh.
5. Compare elapsed time per accepted electronic/ionic step with stock on the same hardware. Near-native speed is a design goal, not yet a measured result.

The [official ΔSCF instructions](https://vasp.at/wiki/Delta_Self-Consistent_Field) explain fixed occupations and LDIAG. [LDIAG](https://vasp.at/wiki/LDIAG) also affects the final subspace diagonalization and forces; a Gamma NTO saddle patch needs its own force validation with the chosen setting.

## Try the opt-in prototype

Start from a clean supported licensed source tree (or revert the static variant first):

```sh
python3 tools/patch_vasp.py /path/to/vasp.6.6.0 --variant ionic-experimental --apply
# Rebuild vasp_gam with your existing toolchain.
```

This variant includes all static modes in the same binary. Add `IONIC_FOLLOW T`
to `NTO_SADDLE` in SECANT mode and use
[INCAR.ionic.fragment](../examples/INCAR.ionic.fragment). The first supported
prototype requires fixed cell `ISIF<=2`, `IWAVPR=0` and the static one-rank/Gamma
restrictions. It refuses forces/ionic advancement after an unaccepted electronic
solve, and rechecks the final PAW identity before handing control to native forces.

The accepted occupied orbitals are only gauge-rotated in an internal copy, using
a Householder transform to isolate the collective particle direction. The physical
W used for forces is untouched. The copied reference stores h/p in the configured reference slots and is
reprojected and PAW-orthonormalized on the next geometry. The original on-disk NTO
reference is never rewritten.

The main-loop hooks surround ELECTRONIC_OPTIMIZATION. Native FORCE_AND_STRESS and
the ionic optimizer are unchanged. Angular/gradient history resets at a geometry change. A reliable signed curvature estimate is carried from the accepted point as an initial scale; it is not used as a stale gradient.
The electronic CSVs add `ionic_step`; NTO_SADDLE_IONIC.csv records accepted steps
and reference orthogonality. From step 2, h/p/c refer to the transported local
reference, **not** to an unchanged initial-geometry NTO. Long-trajectory branch
identity requires additional diagnostics. A process restart with this rolling
reference has not yet been implemented/validated; the current test is continuous
inside one process.

The MPI source normalizes input `IWAVPR=0` to internal value 10. The prototype
checks the effective predictor mode modulo 10, accepting both disabled forms.
An initial prototype stopped at this guard before forces; the corrected build
is used in the current two-step test.

## Following-ion fast controls

For IONIC_FOLLOW T and ionic_step>=2, the default recapture is 8 PROJECT steps, 5 REFLECT steps, then SECANT, with electronic TIME0.08. Keys: IONIC_N_PROJECT, IONIC_N_REFLECT, IONIC_TIME. Following SECANT requires at least6 stage steps and2 qualifying frames (IONIC_MIN_STEP/IONIC_STABLE_STEPS). Identity controls are IONIC_STOP_H_MAX0.05, IONIC_STOP_P_MIN0.90, IONIC_STOP_C_MAX0.08. Initial-ion controls remain STOP_*. Larger allowed local coherence is a working branch-following tolerance, not proof of a particular atomic-orbital rotation. FAST uses the raw subspace stopping scope described in the README; finite-difference force validation is still required.


## Accepted-point snapshots (v0.3)

`SAVE_IONIC_REFERENCE T` writes `WAVECAR.ionNNNN` for the physical accepted orbitals and `WAVECAR.refNNNN` for the transported local reference before native force evaluation. NTO_SADDLE_IONIC_CHECKPOINT.csv records the ionic index, saved curvature and suffixes. The original reference file is never rewritten. Pair snapshots with the corresponding accepted geometry/force record from vasprun.xml; a wave file alone does not prove that the following force calculation finished. Curvature serialization is diagnostic; automatic cross-process curvature/ionic-optimizer restoration is not yet implemented.

The continuous O38 pilot completed two accepted native-force points in one process (20 and155 SCF iterations). Maximum forces were4.099030683053784 and3.5087842071791364eV/angstrom. Per-electronic-step timing stayed near the matched stock benchmark;155 iterations on the second point means near-GS ionic speed has not been established. Finite-difference force accuracy remains unvalidated.
