# Changelog

## 0.3.2 — 2026-11-14

- Tooling-only preflight validation for boolean flags and an empty hole outside the occupied beta block. Native source/binaries are unchanged from0.3.1; changing settings does not trigger a rebuild.


## 0.3.1 — 2026-11-14

- Respect the native three-character OUTWAV suffix ABI. Accepted physical/local-reference snapshots use distinct base36 Ixy/Rxy names instead of truncating long suffixes.
- All four GPU builds recompiled in separate directories; active v0.3 deltaSCF executables preserved.


## 0.3.0 — 2026-11-14

- Align compiled stopping defaults with the calibrated runtime example (g6.5e-5eV, h0.08, p0.90, |c|0.02); no Hamiltonian changes.
- Runtime SECANT_DAMPING, SECANT_CAP_FACTOR and SECANT_MAX_ANGLE with finite/bounds checks; defaults remain0.35/2.5/0.02.
- Add a pre-submission control checker and correct OFF energy-only stop example.
- Optional accepted ionic WAVECAR/local-reference snapshots; geometry/force/restart validation remains experimental.
- Separate batch completion, estimated residual acceptance and independent OFF measurements in documentation.


## 0.1.0 — 2026-11-13

- Exact-snapshot, context-free patcher for VASP 6.6.0.
- One executable with OFF / PROJECT / REFLECT / SECANT runtime modes.
- Full PAW mode measurements, Damped velocity/retraction handling and raw residual diagnostics.
- Runtime stopping thresholds, eight bounded algebraic retries and damped secant safeguards.
- Static implementation compiled for Ada, A100, H200 and TITAN X locally.
- Opt-in ionic-experimental variant: in-memory local PAW reference transport and native force gate, compiled for Ada; two-step test in progress, force accuracy unvalidated.

## Unified FAST_PATH update — 2026-11-13

- Native rank2 beta PAW projections; optional full shadows, exact finite Givens retraction and Damped velocity transport without ORTHCH retries.
- Runtime occupied/reference indices and experimental AUTO schedule; seed preparation tool, preserving full records/reference and requiring native PAW preflight.
- Static coherence trust corridor; following-ion8/5 recapture, curvature carry, TIME.08 and separate moving-reference tolerances.
- Three-file unified implementation, clean MIT license; matched Ada overhead+0.7463%. Full residual and force accuracy remain unvalidated.

##0.2.1 —2026-11-14

- Correct default SECANT ascent orientation using original g_raw, not the total inertial native A. The previous A-sign test permitted mode-descent steps.
- Keep relativecap2.5, damping0.35 and absoluteangle0.02 unchanged; document the remaining near-cancellation bottleneck.
- Add opt-in experimental SECANT_ROOT_STEP and auditable target-kind fields. Four GPU targets compiled; same-seed direction regression is not a convergence or force proof.
