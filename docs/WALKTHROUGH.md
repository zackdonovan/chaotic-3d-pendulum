# Five-minute walkthrough

1. Open `examples/comparison.png`. Explain that all three methods solve the same equations, but Euler adds substantial artificial energy at the chosen step size.
2. Run `pendulum-demo --output my-run` and inspect `summary.json`. Explain the distinction between the nonlinear energy example and the low-amplitude convergence experiment.
3. Launch `pendulum-gui`. Start, pause and reset. Choose RK4 for all three pendulums; change one initial angle slightly, then reset. Describe this as a visual exploration, not a quantitative proof of chaos.
4. Open `model.py`: show the state, acceleration equations and four stages of RK4. Explain why the state includes angular velocities and why the two angles are absolute, not relative joint angles.
5. Open `tests/test_model.py`: show the independent mass-matrix test and the normal-mode limit. These test physics rather than simply confirming that the program runs.

## Questions to be ready to answer

- Why can two trajectories differ even if both programs implement the same equations?
- Why use energy conservation as a diagnostic, and why does it not prove trajectory accuracy?
- How do costs differ between Euler, Heun and RK4 at the same dt?
- Why isn't a finite-step RK4 trajectory exact ground truth?
- What was present in the original project, and what was added in the November 2026 revision?

Scope: a planar numerical simulation using standard integrators; no experimental validation is included.
