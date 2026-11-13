# Implementation map

| File | Addition |
| --- | --- |
| src/rot.F | Runtime parser, full-PAW diagnostics, Damped direction filtering, secant history and measured-retraction correction |
| src/electron_all.F | Electronic-step index passed to EDWAV and raw-residual stopping gate |

The unified patch changes rot.F, electron_all.F and main.F (opt-in ionic hooks). Narrow PAW overlaps use native W1_DOT with CQIJ; full diagnostic shadows use CALC_PAW_OVERLAP. no alternative pseudo-overlap implementation is shipped. Exact exchange follows the active VASP EDWAV branch; the trace distinguishes active action from the availability of ACE.

One binary contains all modes. The NTO_SADDLE parser validates the supported dimensions, spin, selected hole and mode/eta combination. Unsupported rotation paths fail rather than silently bypassing the filter. Parameter changes do not alter FERDO, the functional or the Hamiltonian.

The update is filtered before retraction, including its Damped velocity component. FAST_PATH calls native ORTHCH once, then measures the selected two-plane using scalar native PAW overlaps. The finite correction solves b cos(delta)+c sin(delta)=target, choosing the nearest angle, rather than approximating the angle linearly. CW and augmentation projectors are rotated together, with consistent velocity transport. Invalid identities, unreachable targets or nonfinite steps save diagnostic state and fail. Full Gram checks are optional; absence is printed MISSING.

The static trust corridor redirects only a proposed increase of |c| above TRUST_C_MAX. It acts on the exact chosen-plane coherence model; environmental relaxation may change actual c. It is not an extra Hamiltonian or stationary proof. Raw gradients remain unfiltered for acceptance.

## Context-free patch format

Each manifest records original and patched file SHA256, zero-based line ranges, hashes of removed material and hashes of addition payloads. Removed VASP text is not distributed. The user supplies the exact original files. A private source snapshot test checks patched bytes against the compiled implementation and checks exact restoration.

The patch supports one specified VASP 6.6.0 snapshot. Hash mismatch can indicate a different vendor revision or local customization; manual review and regeneration are required. Do not use fuzzy patching for an unreviewed release.

## Scope

Runtime occupied/hole/reference indices replace fixed dimensions. The supported implementation remains single-rank Gamma-real beta-spin with contiguous binary occupations. Public search topics MOM, IMOM and constrained DFT describe related excited-state workflows, not additional implemented algorithms. No penalty, guide potential, level shift or occupation selector is included.

Version0.2.1 changes only the SECANT direction safeguard and adds the opt-in SECANT_ROOT_STEP flag. NTO_FAST_TIMING.csv also records target_kind and secant_root_step. The default ascent test uses unmodified g_raw; relativecap2.5 and damping0.35 remain. Source-only apply/byte-equality/revert/idempotency checks match all four compiled targets; the live direction regression is distinct from stationary-state acceptance.
