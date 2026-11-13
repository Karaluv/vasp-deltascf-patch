# Forces and continuous geometry optimization

Status: opt-in prototype implemented and compiled for the Ada GPU target. A two-ionic-step O38 test is running. Force accuracy, restart continuity and near-native speed are not yet validated.

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
W used for forces is untouched. The copied reference stores h191/p192 and is
reprojected and PAW-orthonormalized on the next geometry. The original on-disk NTO
reference is never rewritten.

The main-loop hooks surround ELECTRONIC_OPTIMIZATION. Native FORCE_AND_STRESS and
the ionic optimizer are unchanged. Secant history resets at a geometry change.
The electronic CSVs add `ionic_step`; NTO_SADDLE_IONIC.csv records accepted steps
and reference orthogonality. From step 2, h/p/c refer to the transported local
reference, **not** to an unchanged initial-geometry NTO. Long-trajectory branch
identity requires additional diagnostics. A process restart with this rolling
reference has not yet been implemented/validated; the current test is continuous
inside one process.
