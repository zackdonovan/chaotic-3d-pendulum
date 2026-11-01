"""Reproducible, display-free numerical diagnostics (no Qt required)."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .model import PendulumConfig, METHODS


def simulate(method, duration=10.0, dt=0.01, angles=(120., 90.)):
    if not np.isfinite(duration) or not np.isfinite(dt) or duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be finite and positive")
    count = round(duration / dt)
    if count < 1 or count > 1_000_000 or not np.isclose(count * dt, duration, rtol=0, atol=1e-10):
        raise ValueError("duration/dt must be an integer from 1 to 1,000,000")
    pend = METHODS[method](PendulumConfig(method, 'blue', METHODS[method], theta1=angles[0], theta2=angles[1]))
    rows = [[0., *pend.state, pend.energy(), *pend.position()]]
    for i in range(count):
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            pend.step(dt)
            row = [(i+1)*dt, *pend.state, pend.energy(), *pend.position()]
            if not np.all(np.isfinite(row)):
                raise FloatingPointError(f"{method} diverged; reduce dt")
        rows.append(row)
    return np.array(rows)


def convergence():
    """Short, small-angle trajectory; fine RK4 is a numerical reference, not truth."""
    steps = [.01, .005, .0025]
    reference = simulate('rk4', 2., .00015625, (10., 5.))[-1, 1:5]
    result = {}
    for method in METHODS:
        errors = [float(np.linalg.norm(simulate(method, 2., dt, (10., 5.))[-1,1:5] - reference)) for dt in steps]
        result[method] = {'dt_s': steps, 'endpoint_state_l2_error': errors,
                          'observed_order': [float(np.log2(errors[i]/errors[i+1])) for i in range(2)]}
    return result


def demo(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory is not empty; choose a new directory")
    output.mkdir(parents=True, exist_ok=True)
    colors = {'euler': '#e66b50', 'rk2': '#4b93cd', 'rk4': '#41ad93'}
    summary = {'model': 'planar, point masses, massless rigid rods, no damping',
               'duration_s': 10, 'dt_s': .01, 'initial_angles_degrees': [120, 90],
               'energy_scale_J': 29.43, 'methods': {}, 'convergence': convergence()}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7), constrained_layout=True)
    fig.suptitle('Double pendulum: numerical method matters', fontsize=18, fontweight='bold')
    for method, color in colors.items():
        data = simulate(method)
        with (output / f'{method}.csv').open('w', newline='') as f:
            writer = csv.writer(f); writer.writerow(['t_s','theta1_rad','theta2_rad','omega1_rad_s','omega2_rad_s','energy_J','x1_m','y1_m','x2_m','y2_m']); writer.writerows(data)
        error = (data[:,5]-data[0,5])/summary['energy_scale_J']
        summary['methods'][method] = {'max_abs_energy_drift_over_scale': float(np.max(np.abs(error))),
                                     'final_energy_J': float(data[-1,5])}
        axes[0].plot(data[:,0], error, color=color, label=method.upper(), lw=1.7)
        axes[1].plot(data[:,8], data[:,9], color=color, alpha=.75, lw=.9)
        c = summary['convergence'][method]
        axes[2].loglog(c['dt_s'], c['endpoint_state_l2_error'], 'o-', color=color, label=method.upper())
    axes[0].set(xlabel='Simulated time (s)', ylabel='(E − E₀) / energy scale', title='Energy drift · 120° / 90°'); axes[0].legend(frameon=False)
    axes[1].set(xlabel='x₂ (m)', ylabel='y₂ (m)', title='Second-bob trajectories'); axes[1].set_aspect('equal')
    axes[2].set(xlabel='Step size (s)', ylabel='State error vs fine RK4', title='Short-horizon convergence · 10° / 5°')
    for ax in axes:
        ax.grid(alpha=.18); ax.spines[['top','right']].set_visible(False)
    fig.savefig(output/'comparison.png', dpi=160); plt.close(fig)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='results', help='New or empty output directory')
    args = parser.parse_args()
    try:
        result = demo(args.output)
    except (ValueError, FloatingPointError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
