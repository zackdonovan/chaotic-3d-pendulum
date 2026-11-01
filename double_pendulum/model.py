"""Planar point-mass double pendulum and fixed-step integrators."""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Type

@dataclass
class PendulumConfig:
    """Configuration class for a double pendulum simulation.
    
    Attributes:
        name: Identifier for the pendulum
        color: Color for visualization
        integrator_type: Numerical integration method class
        theta1: Initial angle of first arm in degrees
        theta2: Initial angle of second arm in degrees
        m1: Mass of first bob in kg
        m2: Mass of second bob in kg
        l1: Length of first arm in meters
        l2: Length of second arm in meters
        g: Gravitational acceleration in m/s²
    """
    name: str
    color: str
    integrator_type: Type['DoublePendulumBase']
    theta1: float = 120.0
    theta2: float = 90.0
    m1: float = 1.0
    m2: float = 1.0
    l1: float = 1.0
    l2: float = 1.0
    g: float = 9.81

# ── Pendulum dynamics ─────────────────────────────────────────────────────────

class DoublePendulumBase:
    """Base class implementing the physics of a double pendulum.
    
    This class handles the core physics calculations including:
    - State derivatives for numerical integration
    - Position calculations for visualization
    - Energy calculations for analysis
    """
    def __init__(self, config: PendulumConfig):
        for key in ("m1", "m2", "l1", "l2", "g"):
            value = getattr(config, key)
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{key} must be finite and positive")
        if not np.all(np.isfinite([config.theta1, config.theta2])):
            raise ValueError("Initial angles must be finite")
        self.config = config
        self.state = np.array([
            np.deg2rad(config.theta1),
            np.deg2rad(config.theta2),
            0.0, 0.0
        ], dtype=float)
        self.m1, self.m2 = config.m1, config.m2
        self.l1, self.l2 = config.l1, config.l2
        self.g = config.g

    def deriv(self, s):
        """Calculate derivatives of the state vector.
        
        Args:
            s: State vector [θ1, θ2, ω1, ω2] where θ are angles and ω are angular velocities
            
        Returns:
            Array of derivatives [ω1, ω2, α1, α2] where α are angular accelerations
        """
        s = np.asarray(s, dtype=float)
        if s.shape != (4,) or not np.all(np.isfinite(s)):
            raise ValueError("state must contain four finite numbers")
        th1, th2, w1, w2 = s
        m1, m2, l1, l2, g = self.m1, self.m2, self.l1, self.l2, self.g
        delta = th2 - th1
        denom1 = (m1 + m2)*l1 - m2*l1*np.cos(delta)**2
        a1 = (
            m2*l1*w1**2*np.sin(delta)*np.cos(delta)
            + m2*g*np.sin(th2)*np.cos(delta)
            + m2*l2*w2**2*np.sin(delta)
            - (m1 + m2)*g*np.sin(th1)
        ) / denom1
        denom2 = (l2/l1)*denom1
        a2 = (
            -m2*l2*w2**2*np.sin(delta)*np.cos(delta)
            + (m1+m2)*g*np.sin(th1)*np.cos(delta)
            - (m1+m2)*l1*w1**2*np.sin(delta)
            - (m1+m2)*g*np.sin(th2)
        ) / denom2
        return np.array([w1, w2, a1, a2], dtype=float)

    def position(self):
        """Calculate the positions of both pendulum bobs.
        
        Returns:
            Tuple of (x1, y1, x2, y2) coordinates for both bobs
        """
        th1, th2, _, _ = self.state
        x1 = self.l1 * np.sin(th1)
        y1 = -self.l1 * np.cos(th1)
        x2 = x1 + self.l2 * np.sin(th2)
        y2 = y1 - self.l2 * np.cos(th2)
        return x1, y1, x2, y2

    def energy(self):
        """Calculate the total energy of the pendulum system.
        
        Returns:
            Total energy (kinetic + potential) in joules
        """
        th1, th2, w1, w2 = self.state
        m1, m2, l1, l2, g = self.m1, self.m2, self.l1, self.l2, self.g
        v1x = l1*w1*np.cos(th1); v1y = l1*w1*np.sin(th1)
        v2x = v1x + l2*w2*np.cos(th2); v2y = v1y + l2*w2*np.sin(th2)
        KE = 0.5*m1*(v1x**2+v1y**2) + 0.5*m2*(v2x**2+v2y**2)
        y1 = -l1*np.cos(th1); y2 = y1 - l2*np.cos(th2)
        PE = m1*g*y1 + m2*g*y2
        return KE + PE

class EulerPendulum(DoublePendulumBase):
    """First-order explicit Euler integration method."""
    def step(self, dt):
        _validate_dt(dt)
        self.state += dt * self.deriv(self.state)
        return self.position()

class RK2Pendulum(DoublePendulumBase):
    """Second-order Runge-Kutta integration method."""
    def step(self, dt):
        _validate_dt(dt)
        s = self.state
        k1 = self.deriv(s)
        k2 = self.deriv(s + dt*k1)
        self.state = s + (dt/2)*(k1 + k2)
        return self.position()

class RK4Pendulum(DoublePendulumBase):
    """Fourth-order Runge-Kutta integration method."""
    def step(self, dt):
        _validate_dt(dt)
        s = self.state
        k1 = self.deriv(s)
        k2 = self.deriv(s + 0.5*dt*k1)
        k3 = self.deriv(s + 0.5*dt*k2)
        k4 = self.deriv(s + dt*k3)
        self.state = s + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
        return self.position()

# ── Pendulum Simulation ─────────────────────────────────────────────────────

class PendulumSimulation:
    """Manages multiple pendulum simulations with data collection and visualization.
    
    This class handles:
    - Multiple pendulum instances with different integration methods
    - Energy tracking over time
    - Position history for trace visualization
    - Time window management for data storage
    """
    def __init__(self, configs: List[PendulumConfig]):
        if not configs or len({c.name for c in configs}) != len(configs):
            raise ValueError("Provide nonempty configurations with unique names")
        self.elapsed = 0.0
        self.pendulums = [config.integrator_type(config) for config in configs]
        self.times = []
        self.energy_data = {config.name: {'ke': [], 'pe': [], 'te': []} 
                           for config in configs}
        self.window_size = 10.0  # Time window for energy data
        self.use_window = False
        self.trace_data = {config.name: {'x': [], 'y': [], 'times': []} 
                          for config in configs}
        self.trace_window = 15.0  # Time window for trace visualization

    def reset(self):
        """Reset all pendulums to their initial states and clear stored data."""
        for pend in self.pendulums:
            pend.state = np.array([
                np.deg2rad(pend.config.theta1),
                np.deg2rad(pend.config.theta2),
                0.0, 0.0
            ], dtype=float)
        self.elapsed = 0.0
        self.times = []
        for trace in self.trace_data.values():
            for values in trace.values():
                values.clear()
        for data in self.energy_data.values():
            data['ke'] = []
            data['pe'] = []
            data['te'] = []
        self.use_window = False

    def step(self, dt: float) -> List[Tuple[float, float, float, float]]:
        """Advance the simulation by one time step.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            List of (x1, y1, x2, y2) positions for each pendulum
        """
        _validate_dt(dt)
        self.elapsed += dt
        t = self.elapsed
        self.times.append(t)
        
        if not self.use_window and t >= self.window_size:
            self.use_window = True
        
        if self.use_window:
            cutoff_time = t - self.window_size
            while self.times and self.times[0] < cutoff_time:
                self.times.pop(0)
                for data in self.energy_data.values():
                    data['ke'].pop(0)
                    data['pe'].pop(0)
                    data['te'].pop(0)
        
        positions = []
        for i, pend in enumerate(self.pendulums):
            pos = pend.step(dt)
            positions.append(pos)
            
            # Update trace data
            x1, y1, x2, y2 = pos
            trace_data = self.trace_data[pend.config.name]
            trace_data['x'].append(x2)
            trace_data['y'].append(y2)
            trace_data['times'].append(t)
            
            # Remove old trace points
            cutoff_time = t - self.trace_window
            while trace_data['times'] and trace_data['times'][0] < cutoff_time:
                trace_data['x'].pop(0)
                trace_data['y'].pop(0)
                trace_data['times'].pop(0)
            
            # Calculate and store energies
            th1, th2, w1, w2 = pend.state
            m1, m2, l1, l2, g = pend.m1, pend.m2, pend.l1, pend.l2, pend.g
            
            v1x = l1*w1*np.cos(th1); v1y = l1*w1*np.sin(th1)
            v2x = v1x + l2*w2*np.cos(th2); v2y = v1y + l2*w2*np.sin(th2)
            KE = 0.5*m1*(v1x**2+v1y**2) + 0.5*m2*(v2x**2+v2y**2)
            
            y1 = -l1*np.cos(th1); y2 = y1 - l2*np.cos(th2)
            PE = m1*g*y1 + m2*g*y2
            
            data = self.energy_data[pend.config.name]
            data['ke'].append(KE)
            data['pe'].append(PE)
            data['te'].append(KE + PE)
            
        return positions



def _validate_dt(dt):
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")

METHODS = {"euler": EulerPendulum, "rk2": RK2Pendulum, "rk4": RK4Pendulum}
