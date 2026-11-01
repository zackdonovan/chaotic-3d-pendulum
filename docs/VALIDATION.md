# Validation record — 2026-11-01

## Executed checks

- Base scientific Python environment: `python -m unittest discover -s tests -v` — 25 discovered; 21 passed, 4 Qt tests explicitly skipped.
- GUI-enabled environment: `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v` — all 25 passed.
- Installed package using `pip install --no-deps --no-build-isolation .` in a writable virtual environment with the documented scientific packages and optional Qt dependencies. Executed the installed `pendulum-demo` entry point from outside the source directory; all six expected outputs were produced.
- Ran the actual Qt application for 200 simulation frames using Linux offscreen rendering and visually inspected its rendered parameter panel, pendulum, traces and three energy plots. This is not native macOS or Windows QA.
- Inspected the generated three-panel `examples/comparison.png` at full resolution. The checked-in CSV/JSON/PNG are real generated outputs, not illustrative placeholders.
- Verified the original `main` file against the original Git blob SHA in `PROVENANCE.md` (21641 bytes).
- Compiled all Python source and tests with `compileall`. A scoped source/document scan found no embedded credential assignments; the archive excludes environments, caches, build output and local metadata.

## Interpretation

The tested scope is a numerical-methods educational demo, not a validated engineering model or a chaos research result. Unit tests include an independently assembled mass-matrix formulation, directional energy derivative, normal-mode check, constrained rod geometry, time-reversal check, convergence, invalid inputs, no-clobber output handling, and actual Qt controls. Consult `MODEL.md` for assumptions and limits.

This record documents the tested revision and its execution environment.

## Independent release check

A separate reviewer copied the candidate into a separate directory, created a fresh virtual environment (not system-site-packages), and installed `.[gui]` using normal pip on 2026-11-01. Installation succeeded with NumPy 2.5.4, Matplotlib 3.11.2, PySide6 6.8.3 and pyqtgraph 0.13.7. All 25 tests passed, including all four actual Qt integration tests. The installed `pendulum-demo` ran from outside the checkout and reproduced the expected energy/convergence results. The generated plot and offscreen GUI render were independently inspected for readability. No release-blocking code findings; only benign cache/fontconfig/Qt platform warnings. Native macOS/Windows integration remains untested.
