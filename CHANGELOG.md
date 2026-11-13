# Changelog

## 0.1.0 — 2026-11-13

- Exact-snapshot, context-free patcher for VASP 6.6.0.
- One executable with OFF / PROJECT / REFLECT / SECANT runtime modes.
- Full PAW mode measurements, Damped velocity/retraction handling and raw residual diagnostics.
- Runtime stopping thresholds, eight bounded algebraic retries and damped secant safeguards.
- Static implementation compiled for Ada, A100, H200 and TITAN X locally.
- Opt-in ionic-experimental variant: in-memory local PAW reference transport and native force gate, compiled for Ada; two-step test in progress, force accuracy unvalidated.
