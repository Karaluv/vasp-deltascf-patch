# One-mode orbital root finding

For occupied beta orbitals, let `v_i=<psi_i|S|p0>`, `p=v†v` and `u=P p0/sqrt(p)`. The selected empty direction is `q=psi_192`. S is the complete PAW overlap; pseudo-wavefunction overlaps are insufficient.

For the occupied–q column d of the actual orbital update, define `a=(v†d)/(v†v)` and replace

```
d_new = d + (eta-1) v a
```

The corresponding conjugate block must preserve the anti-Hermitian generator. Gamma-real is the implemented specialization. This is a collective occupied direction; following only the band with the largest particle weight is a different algorithm.

PROJECT (`eta=0`) removes this component while the environment relaxes. REFLECT (`eta=-1`) reverses it. SECANT uses the signed raw `g=<q|F[P]|u>` and a local angular history, with damping 0.35, a ceiling 2.5 times the unmodified mode step, a 0.02-radian angle ceiling and protected fallback. A detected root crossing uses a soft reflected step. The initial SDA iteration is projected and is excluded from secant history.

The actual Damped direction includes orbital velocity and the IROT=3 subspace rotation. Editing a Hamiltonian matrix alone would not filter this total direction. The patch measures the retracted PAW rotation after ORTHCH and applies bounded algebraic retries without rebuilding Fock or the density.

## Density diagnostics

With `u_n=<h0|S|psi_n>` and `v_n=<p0|S|psi_n>`, occupations f give

```
h = sum(f |u|²), p = sum(f |v|²), c = sum(f u conj(v))
cmax² = min(h(1-h), p(1-p))
ell_h = h(1-h)-|c|², ell_p = p(1-p)-|c|²
```

A small c diagnoses control of the coherent pair rotation. h alone also contains relaxation into the surrounding occupied space; it is not a standalone coherence measure.

## Stationarity

The target is the original occupied–virtual residual `Q F[P] P=0`, not a modified Hamiltonian or vanishing filtered gradient. The implementation exposes a subspace residual and an estimate from the available real orbital gradient. It does not claim an independently verified full-space residual. PROJECT is a preparation state even when its filtered update vanishes.

The rough scaling `delta E ~ g²/curvature` requires a curvature estimate; a gradient tolerance alone does not guarantee a universal energy error.

For fixed occupations at a true electronic stationary point, electronic-response terms vanish in the derivative of the stationary branch energy, including at a saddle. Residual electronic error, branch changes and predictor/PAW transport errors still require force checks. See the [VASP force discussion](https://vasp.at/wiki/Hellmann-Feynman_forces).
