# Changes from the original single-file project

- Retained the original acceleration expressions and Euler, Heun RK2 and classical RK4 updates.
- Split physics/history management from the optional desktop UI so diagnostics run without Qt.
- Added installable package and console scripts, with a `main.py` compatibility launcher.
- Corrected advanced-sample timestamps: first recorded GUI sample is at dt, not zero.
- Reset now clears both stored and rendered traces and displays initial positions.
- Added finite/positive parameter and dt validation; GUI bounds dt away from zero.
- Corrected the Qt parameter-change slot signature and renamed the timer callback to avoid shadowing QWidget.update.
- UI catches non-finite numerical instability and asks for a smaller step/reset.
- Corrected vertical velocity signs to match the coordinate derivative. Both signs were reversed together upstream, so the old kinetic-energy total was unchanged; this is a consistency correction, not a claimed energy-formula fix.
- Added deterministic numerical tests, optional real-Qt integration tests, CSV outputs, a diagnostic plot, provenance and explanatory documentation.
- Retained exact original source. No unsupported 3D, real-time, long-term-accuracy or novelty claims.
