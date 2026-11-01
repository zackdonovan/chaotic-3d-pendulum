import unittest
import numpy as np
from double_pendulum.model import PendulumConfig, EulerPendulum, RK2Pendulum, RK4Pendulum, PendulumSimulation, METHODS
from double_pendulum.cli import simulate, convergence


def make(cls=RK4Pendulum, **kwargs):
    return cls(PendulumConfig('test', 'blue', cls, **kwargs))


class ModelTests(unittest.TestCase):
    def test_equilibrium(self):
        for cls in METHODS.values():
            p=make(cls,theta1=0,theta2=0)
            p.step(.01)
            np.testing.assert_array_equal(p.state,0)
    def test_positions_preserve_lengths(self):
        p=make(l1=1.3,l2=.8)
        x1,y1,x2,y2=p.position()
        self.assertAlmostEqual(np.hypot(x1,y1),1.3)
        self.assertAlmostEqual(np.hypot(x2-x1,y2-y1),.8)
    def test_energy_at_rest(self):
        self.assertAlmostEqual(make(theta1=0,theta2=0).energy(),-29.43)
    def test_mass_matrix_equations_independently(self):
        rng=np.random.default_rng(71)
        for _ in range(50):
            p=make(m1=.8,m2=1.2,l1=.7,l2=1.1)
            t1,t2,w1,w2=s=rng.uniform(-2,2,4)
            d=t1-t2; m1,m2,l1,l2,g=p.m1,p.m2,p.l1,p.l2,p.g
            mass=np.array([[(m1+m2)*l1*l1,m2*l1*l2*np.cos(d)],[m2*l1*l2*np.cos(d),m2*l2*l2]])
            force=np.array([-m2*l1*l2*np.sin(d)*w2*w2-(m1+m2)*g*l1*np.sin(t1), m2*l1*l2*np.sin(d)*w1*w1-m2*g*l2*np.sin(t2)])
            np.testing.assert_allclose(p.deriv(s)[2:],np.linalg.solve(mass,force),atol=1e-12)
    def test_energy_directional_derivative(self):
        p=make(); s=np.array([.5,-.3,.7,-.2]); eps=1e-6
        v=p.deriv(s); p.state=s+eps*v; plus=p.energy(); p.state=s-eps*v; minus=p.energy()
        self.assertLess(abs((plus-minus)/(2*eps)),1e-7)
    def test_small_angle_normal_frequencies(self):
        p=make(); eps=1e-6
        a=np.column_stack([p.deriv(np.array([eps,0,0,0]))[2:]/eps,p.deriv(np.array([0,eps,0,0]))[2:]/eps])
        actual=np.sort(np.linalg.eigvals(-a))
        np.testing.assert_allclose(actual,9.81*np.array([2-np.sqrt(2),2+np.sqrt(2)]),rtol=1e-10)
    def test_velocity_reversal(self):
        p=make(); p.state=np.array([.4,-.7,.2,-.3]); initial=p.state.copy()
        for _ in range(100): p.step(.001)
        p.state[2:] *= -1
        for _ in range(100): p.step(.001)
        expected=initial.copy(); expected[2:]*=-1
        np.testing.assert_allclose(p.state,expected,atol=1e-10)
    def test_invalid_parameters(self):
        for k in ['m1','m2','l1','l2','g']:
            for v in [0,-1,np.nan,np.inf]:
                with self.subTest(k=k,v=v), self.assertRaises(ValueError): make(**{k:v})
    def test_invalid_angles(self):
        with self.assertRaises(ValueError): make(theta1=np.nan)
    def test_invalid_state(self):
        for s in [[1,2],[0,0,0,np.nan]]:
            with self.assertRaises(ValueError): make().deriv(s)
    def test_invalid_steps(self):
        for cls in METHODS.values():
            for dt in [0,-1,np.inf,np.nan]:
                with self.assertRaises(ValueError): make(cls).step(dt)
    def test_no_derivative_mutation(self):
        s=np.array([.2,.4,.7,.1]); expected=s.copy(); make().deriv(s)
        np.testing.assert_array_equal(s,expected)
    def test_simulation_time_and_reset(self):
        sim=PendulumSimulation([PendulumConfig('a','red',RK4Pendulum)])
        sim.step(.01); self.assertEqual(sim.times,[.01]); self.assertEqual(sim.trace_data['a']['times'],[.01])
        sim.reset(); self.assertEqual(sim.times,[]); self.assertEqual(sim.elapsed,0); self.assertEqual(sim.trace_data['a']['x'],[])
        sim.step(.02); self.assertEqual(sim.times,[.02])
    def test_window_alignment(self):
        sim=PendulumSimulation([PendulumConfig('a','red',RK4Pendulum,theta1=1,theta2=1)])
        sim.window_size=.03; sim.trace_window=.02
        for _ in range(10): sim.step(.01)
        self.assertEqual(len(sim.times),len(sim.energy_data['a']['te']))
        self.assertGreaterEqual(sim.times[0],sim.elapsed-.03-1e-12)
        self.assertGreaterEqual(sim.trace_data['a']['times'][0],sim.elapsed-.02-1e-12)
    def test_duplicate_names(self):
        c=PendulumConfig('a','red',RK4Pendulum)
        for configs in [[],[c,c]]:
            with self.assertRaises(ValueError): PendulumSimulation(configs)
    def test_rk4_energy_drift(self):
        data=simulate('rk4',2.,.005)
        self.assertLess(np.max(np.abs(data[:,5]-data[0,5])),1e-5)
    def test_observed_convergence_order(self):
        result=convergence()
        for method,order in [('euler',1),('rk2',2),('rk4',4)]:
            for value in result[method]['observed_order']:
                self.assertGreater(value,order-.25); self.assertLess(value,order+.25)
    def test_initial_row_and_endpoint(self):
        data=simulate('rk4',.1,.01)
        self.assertEqual(data.shape,(11,10)); self.assertEqual(data[0,0],0); self.assertEqual(data[-1,0],.1)
    def test_invalid_duration(self):
        for duration,dt in [(0,.1),(.1,0),(.1,.03),(np.inf,.1),(1,1e-8)]:
            with self.assertRaises(ValueError): simulate('rk4',duration,dt)

if __name__=='__main__': unittest.main()
