# Forces and continuous geometry optimization

Status: experimental ionic transport is under development. Static electronic tests and successful compilation do not validate excited-state forces or production geometry relaxation.

The intended path is one native VASP process: SECANT electronic solve, stationary-state acceptance gate, VASP native force/stress evaluation, native ionic optimizer, and an in-memory electronic restart on the next geometry. No external restart per ionic step is intended.

A geometry update invalidates old atom-centered PAW projection coefficients. Recompute projections and PAW orthonormality on the new geometry. Carry the accepted occupied subspace, collective particle direction and empty hole direction; reset the secant angular/gradient history, since the energy surface and local gauge changed. Keep the immutable input NTO reference on disk, and distinguish transported local references from the original NTO diagnostics.

The first prototype uses fixed cell and IWAVPR=0 to isolate transport. VASP's [IWAVPR documentation](https://vasp.at/wiki/IWAVPR) describes 0 as disabling prediction and 11 as the charge-density predictor commonly used for relaxation. IWAVPR=11 is a subsequent comparison, not a demonstrated equivalent.

## Acceptance before use

1. Reject ionic advancement if SECANT reaches NELM without the specified raw-residual/identity gate.
2. Two or more ionic steps in one process, with unambiguous ionic/electronic indices and preserved branch identity.
3. Compare native forces with central finite differences on the same excited branch, tightening electronic tolerances as needed.
4. Test reload continuity, small displacements, reference normalization and PAW projector refresh.
5. Compare elapsed time per accepted electronic/ionic step with stock on the same hardware. Near-native speed is a design goal, not yet a measured result.

The [official ΔSCF instructions](https://vasp.at/wiki/Delta_Self-Consistent_Field) explain fixed occupations and LDIAG. [LDIAG](https://vasp.at/wiki/LDIAG) also affects the final subspace diagonalization and forces; a Gamma NTO saddle patch needs its own force validation with the chosen setting.
