# FAST_PATH validation and performance

One local O38 Gamma-real PBE0.40 test, VASP6.6.0, one MPI rank, one RTX4500 Ada, same input WAVECAR and physical GPU:

| Electronic loop | Median LOOP real time, first2 excluded |
| --- | ---: |
| Original stock Damped | 21.8421 s |
| FAST SECANT | 22.0051 s |

FAST/stock ratio1.0074626524006391 (+0.74626524006391%). The short test has3 steady samples per timed branch. This establishes small per-electronic-step overhead for this input; it does not establish a universal speedup, Ground State timing, whole-trajectory convergence speed or GPU scaling. In particular, a5–6x speedup is not supported by this matched test: original stock already costs about22s here.

OFF reproduced the8 printed stock SCF energies exactly on the same GPU/input. Three full-diagnostic PROJECT steps compared native rank2/full PAW overlaps: maximum difference9.4368957093138306e-15; maximum PAW Gram error1.5210055437364645e-14; maximum exact mode error6.1120664833279255e-15. Five default FAST SECANT steps had maximum mode error3.9828484443610226e-15. Diagnostic matrices were disabled for the timed FAST branch; unavailable norms are MISSING.

Ada, A100, H200 and TITAN targets compiled from identical changed Fortran source; this benchmark validates runtime on Ada. Compilation on the other targets does not establish their timing or scientific convergence. Independent force finite differences and continuous ionic convergence remain open checks.
