# Model and validation

## Assumptions and coordinates

Two point masses m1 and m2 hang from massless rigid rods of lengths l1 and l2. The pivot is fixed. Gravity is uniform and vertical; there is no friction, damping, collision, forcing or out-of-plane motion. Both angles are absolute angles measured from vertically downward, in radians internally. The GUI accepts initial degrees. Initial angular velocities are zero.

The state order is `[theta1, theta2, omega1, omega2]`.

```
x1 = l1 sin(theta1)              y1 = -l1 cos(theta1)
x2 = x1 + l2 sin(theta2)         y2 = y1 - l2 cos(theta2)
```

With d = theta1 − theta2, the equations follow from the Euler–Lagrange equations and can independently be expressed as:

```
[ (m1+m2) l1²        m2 l1 l2 cos(d) ] [alpha1]   [ -m2 l1 l2 sin(d) omega2² - (m1+m2) g l1 sin(theta1) ]
[ m2 l1 l2 cos(d)    m2 l2²         ] [alpha2] = [ +m2 l1 l2 sin(d) omega1² - m2 g l2 sin(theta2)      ]
```

The implementation retains the original algebraically solved acceleration formulas; tests compare them against a separately assembled matrix solve at 50 seeded states with unequal masses and lengths. Positive masses and lengths keep this matrix nonsingular.

```
T = 1/2 (m1+m2) l1² omega1² + 1/2 m2 l2² omega2²
    + m2 l1 l2 omega1 omega2 cos(d)
V = -(m1+m2) g l1 cos(theta1) - m2 g l2 cos(theta2)
E = T + V
```

For equal masses and lengths at small angles, squared normal frequencies are `(g/l)(2 ± sqrt(2))`. A numerical Jacobian test checks this limiting behavior. The energy directional-derivative test checks that `grad(E) · f(state)` vanishes within finite-difference precision.

## Integrators

- Euler: one derivative evaluation per step, first-order global accuracy.
- RK2: Heun's explicit trapezoidal method, two evaluations per step, second-order global accuracy. It is not midpoint RK2.
- RK4: classical four-stage Runge–Kutta, fourth-order global accuracy on smooth solutions over finite intervals.

None is symplectic or adaptive. Equal step count is not equal computational cost. RK4's favorable result here is not a universal performance guarantee.

## Reproducible diagnostics

`pendulum-demo` runs two deliberately separate diagnostics:

1. A 10-second nonlinear trajectory at 120° / 90°, dt = 0.01 s, illustrating energy drift and trajectory differences.
2. A two-second low-amplitude trajectory at 10° / 5°, with dt = 0.01, 0.005 and 0.0025 s, compared to RK4 dt = 0.00015625 s. Estimated order is `log2(error(h)/error(h/2))`.

The first experiment is illustrative; trajectory divergence alone cannot distinguish chaos from integrator error. The second uses a short horizon to reduce amplification of numerical errors. Its endpoint norm is an unweighted diagnostic of the four state components, not a dimensional physical error metric. Tests check expected orders only for this smooth, specified case.

## Verification boundaries

Verified on Linux/Python 3.12: core and optional Qt integration tests, installed console commands, generated plots, no-clobber outputs and clean-extraction testing. Offscreen GUI tests exercise real Qt objects and signal handling, but do not prove native OS window-manager behavior. No hardware experiment, physical parameter fit, chaos exponent, adaptive solver or full long-time error bound is claimed.
