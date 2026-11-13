# Implementation map

| File | Addition |
| --- | --- |
| src/rot.F | Runtime parser, full-PAW diagnostics, Damped direction filtering, secant history and measured-retraction correction |
| src/electron_all.F | Electronic-step index passed to EDWAV and raw-residual stopping gate |

The static patch changes these two files only. PAW overlaps use VASP's existing CALC_PAW_OVERLAP routine; no alternative pseudo-overlap implementation is shipped. Exact exchange follows the active VASP EDWAV branch; the trace distinguishes active action from the availability of ACE.

One binary contains all modes. The NTO_SADDLE parser validates the supported dimensions, spin, selected hole and mode/eta combination. Unsupported rotation paths fail rather than silently bypassing the filter. Parameter changes do not alter FERDO, the functional or the Hamiltonian.

The update is filtered before retraction. The retracted finite step is measured in the PAW metric. Up to eight algebraic retries restore both wavefunctions and incoming velocity. Small bounded mismatch can accept the best attempt and is logged. Nonfinite steps, invalid orthogonality or major identity loss remain hard failures with saved diagnostic states.

## Context-free patch format

Each manifest records original and patched file SHA256, zero-based line ranges, hashes of removed material and hashes of addition payloads. Removed VASP text is not distributed. The user supplies the exact original files. A private source snapshot test checks patched bytes against the compiled implementation and checks exact restoration.

The patch supports one specified VASP 6.6.0 snapshot. Hash mismatch can indicate a different vendor revision or local customization; manual review and regeneration are required. Do not use fuzzy patching for an unreviewed release.

## Scope

Current fixed dimensions are a deliberate experimental limitation. Public search topics MOM, IMOM and constrained DFT describe related excited-state workflows, not additional implemented algorithms. No penalty, guide potential, level shift or occupation selector is included.
