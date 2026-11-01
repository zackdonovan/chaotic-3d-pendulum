"""Optional offscreen integration tests; install the gui extra to execute."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import importlib.util
import unittest
HAS_GUI = importlib.util.find_spec('PySide6') and importlib.util.find_spec('pyqtgraph')

@unittest.skipUnless(HAS_GUI, 'Install .[gui] to run Qt integration tests')
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyqtgraph.Qt import QtWidgets
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    def setUp(self):
        from double_pendulum.gui import MainWindow
        self.window=MainWindow(); self.window.show(); self.app.processEvents(); self.ui=self.window.simulator
    def tearDown(self):
        self.ui.timer.stop(); self.window.close(); self.app.processEvents()
    def test_initial_positions_and_reset(self):
        self.assertEqual(len(self.ui.anim_items[0][0].xData),2)
        for _ in range(10): self.ui.advance_frame()
        self.assertTrue(self.ui.trace_items[0].xData.size)
        self.ui.reset_btn.click()
        self.assertEqual(self.ui.simulation.times,[])
        self.assertTrue(self.ui.trace_items[0].xData is None or not self.ui.trace_items[0].xData.size)
        self.assertEqual(self.ui.start_btn.text(),'Start')
    def test_dt_signal(self):
        self.ui.global_params.child('dt (s)').setValue(.002)
        self.assertEqual(self.ui.dt,.002)
        self.ui.advance_frame(); self.assertEqual(self.ui.simulation.times,[.002])
    def test_start_pause_reset(self):
        self.ui.start_btn.click(); self.assertTrue(self.ui.running); self.assertTrue(self.ui.timer.isActive())
        self.ui.start_btn.click(); self.assertFalse(self.ui.running); self.assertFalse(self.ui.timer.isActive())
        self.ui.start_btn.click(); self.ui.reset_btn.click(); self.assertFalse(self.ui.running)
    def test_apply_parameters_and_method(self):
        self.ui.pendulum_params[0].child('theta1 (°)').setValue(42)
        self.ui.pendulum_params[0].child('l1 (m)').setValue(2)
        self.ui.global_params.child('g (m/s²)').setValue(3.7)
        self.ui.integrator_buttons[0].buttons()[2].setChecked(True)
        self.ui.reset_btn.click()
        p=self.ui.simulation.pendulums[0]
        self.assertEqual(p.config.theta1,42); self.assertEqual(p.l1,2); self.assertEqual(p.g,3.7)
        self.assertEqual(type(p).__name__,'RK4Pendulum')
