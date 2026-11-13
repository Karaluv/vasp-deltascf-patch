# Changelog

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
