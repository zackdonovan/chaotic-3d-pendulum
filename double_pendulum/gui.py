"""Interactive Qt frontend; changes to initial conditions apply on Reset."""
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from pyqtgraph.parametertree import Parameter, ParameterTree
from .model import PendulumConfig, PendulumSimulation, EulerPendulum, RK2Pendulum, RK4Pendulum

class PendulumSimulator(QtWidgets.QWidget):
    """Main GUI widget for the double pendulum simulator.
    
    This class implements the complete user interface including:
    - Parameter controls for each pendulum
    - Real-time visualization
    - Energy plots
    - Simulation controls
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.initSimulation()

    def initUI(self):
        """Initialize the user interface components."""
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Left panel setup
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Global parameters
        global_params = [
            {'name': 'dt (s)', 'type': 'float', 'value': 0.01, 'step': 0.001, 'limits': [0.0001, 0.05]},
            {'name': 'g (m/s²)', 'type': 'float', 'value': 9.81, 'step': 0.1, 'limits': [0.01, 100]}
        ]
        self.global_params = Parameter.create(name='Global Parameters', type='group', children=global_params)
        self.global_tree = ParameterTree()
        self.global_tree.setParameters(self.global_params, showTop=False)
        self.global_params.child('dt (s)').sigValueChanged.connect(self.update_dt)
        left_layout.addWidget(self.global_tree)
        
        # Pendulum parameter tabs
        self.pendulum_tabs = QtWidgets.QTabWidget()
        self.pendulum_params = []
        self.integrator_buttons = []
        
        for i in range(3):
            tab = QtWidgets.QWidget()
            tab_layout = QtWidgets.QVBoxLayout(tab)
            
            # Integration method selection
            integrator_group = QtWidgets.QButtonGroup()
            euler_btn = QtWidgets.QRadioButton("Euler")
            rk2_btn = QtWidgets.QRadioButton("RK2")
            rk4_btn = QtWidgets.QRadioButton("RK4")
            
            if i == 0:
                euler_btn.setChecked(True)
            elif i == 1:
                rk2_btn.setChecked(True)
            else:
                rk4_btn.setChecked(True)
                
            integrator_group.addButton(euler_btn)
            integrator_group.addButton(rk2_btn)
            integrator_group.addButton(rk4_btn)
            self.integrator_buttons.append(integrator_group)
            
            integrator_layout = QtWidgets.QHBoxLayout()
            integrator_layout.addWidget(QtWidgets.QLabel("Integration Type:"))
            integrator_layout.addWidget(euler_btn)
            integrator_layout.addWidget(rk2_btn)
            integrator_layout.addWidget(rk4_btn)
            integrator_layout.addStretch()
            
            tab_layout.addLayout(integrator_layout)
            
            # Pendulum parameters
            params = [
                {'name': 'theta1 (°)', 'type': 'float', 'value': 120, 'step': 1, 'limits': [0, 360]},
                {'name': 'theta2 (°)', 'type': 'float', 'value': 90, 'step': 1, 'limits': [0, 360]},
                {'name': 'm1 (kg)', 'type': 'float', 'value': 1.0, 'step': 0.1, 'limits': [0.1, 10]},
                {'name': 'm2 (kg)', 'type': 'float', 'value': 1.0, 'step': 0.1, 'limits': [0.1, 10]},
                {'name': 'l1 (m)', 'type': 'float', 'value': 1.0, 'step': 0.1, 'limits': [0.1, 5]},
                {'name': 'l2 (m)', 'type': 'float', 'value': 1.0, 'step': 0.1, 'limits': [0.1, 5]}
            ]
            p = Parameter.create(name=f'Pendulum {i+1}', type='group', children=params)
            self.pendulum_params.append(p)
            
            tree = ParameterTree()
            tree.setParameters(p, showTop=False)
            tab_layout.addWidget(tree)
            
            self.pendulum_tabs.addTab(tab, f"Pendulum {i+1}")
        
        left_layout.addWidget(self.pendulum_tabs)

        # Instructions text
        instructions = QtWidgets.QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(200)
        instructions.setHtml("""
        <h3>Instructions:</h3>
        <p><b>Global Parameters:</b><br>
        - dt: Time step for simulation (smaller = more accurate but slower)<br>
        - g: Gravitational acceleration</p>
        
        <p><b>Pendulum Parameters:</b><br>
        - theta1, theta2: Initial angles in degrees (0-360)<br>
        - m1, m2: Masses of the bobs in kg<br>
        - l1, l2: Lengths of the arms in meters</p>
        
        <p><b>Integration Methods:</b><br>
        - Euler: Fast but less accurate<br>
        - RK2: Better accuracy, moderate speed<br>
        - RK4: Most accurate but slowest</p>
        
        <p><b>Controls:</b><br>
        - Start/Pause: Toggle simulation<br>
        - Reset: Apply changed parameters and return to initial state<br>
        - One simulation step per display frame; this is not a real-time clock</p>
        """)
        left_layout.addWidget(instructions)

        # Control buttons
        self.start_btn = QtWidgets.QPushButton("Start")
        self.start_btn.clicked.connect(self.toggle)
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.clicked.connect(self.resetSimulation)
        left_layout.addWidget(self.start_btn)
        left_layout.addWidget(self.reset_btn)
        
        left_layout.addStretch()
        
        # Center panel (main simulation)
        center_panel = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_panel)
        
        self.anim_plot = pg.PlotWidget(title="Pendulum")
        self.anim_plot.setAspectLocked(True)
        self.anim_plot.showGrid(x=True, y=True)
        self.anim_plot.setLabel('bottom', 'x', units='m')
        self.anim_plot.setLabel('left', 'y', units='m')
        
        self.legend = pg.LegendItem(offset=(10, 10))
        self.legend.setParentItem(self.anim_plot.graphicsItem())
        
        center_layout.addWidget(self.anim_plot)
        
        # Right panel (energy plots)
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        self.ke_plot = pg.PlotWidget(title="Kinetic Energy")
        self.ke_plot.setLabel('bottom','Time (s)')
        self.ke_plot.setLabel('left','Energy (J)')
        self.ke_plot.showGrid(x=True, y=True)
        right_layout.addWidget(self.ke_plot)
        
        self.pe_plot = pg.PlotWidget(title="Potential Energy")
        self.pe_plot.setLabel('bottom','Time (s)')
        self.pe_plot.setLabel('left','Energy (J)')
        self.pe_plot.showGrid(x=True, y=True)
        right_layout.addWidget(self.pe_plot)
        
        self.te_plot = pg.PlotWidget(title="Total Energy")
        self.te_plot.setLabel('bottom','Time (s)')
        self.te_plot.setLabel('left','Energy (J)')
        self.te_plot.showGrid(x=True, y=True)
        right_layout.addWidget(self.te_plot)
        
        # Add panels to main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        
        # Set initial sizes (15% left, 50% center, 35% right)
        total_width = 1000  # Approximate total width
        main_splitter.setSizes([int(total_width * 0.15), int(total_width * 0.50), int(total_width * 0.35)])
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(main_splitter)

        self.init_plot_items()

    def init_plot_items(self):
        """Initialize plot items for visualization."""
        self.anim_items = []
        self.trace_items = []
        colors = ['red', 'blue', 'green']
        for i, c in enumerate(colors):
            r1 = pg.PlotDataItem(pen=pg.mkPen(c,width=2))
            r2 = pg.PlotDataItem(pen=pg.mkPen(c,width=2))
            b1 = pg.ScatterPlotItem(size=8,brush=pg.mkBrush(c))
            b2 = pg.ScatterPlotItem(size=8,brush=pg.mkBrush(c))
            trace = pg.PlotDataItem(pen=pg.mkPen(c, width=1, style=QtCore.Qt.DotLine))
            for itm in (r1,r2,b1,b2,trace):
                self.anim_plot.addItem(itm)
            self.anim_items.append((r1,r2,b1,b2))
            self.trace_items.append(trace)
            self.legend.addItem(r1, f"Pendulum {i+1}")

        self.energy_plots = {
            'ke': {},
            'pe': {},
            'te': {}
        }

    def update_dt(self, param, value):
        """Update simulation time step."""
        self.dt = self.global_params['dt (s)']

    def initSimulation(self):
        """Initialize simulation parameters and timer."""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.advance_frame)
        self.timer.setInterval(16)  # 60 FPS
        self.running = False
        self.dt = 0.01
        self.resetSimulation()

    def resetSimulation(self):
        """Reset the simulation to initial state."""
        configs = []
        colors = ['red', 'blue', 'green']
        g = self.global_params['g (m/s²)']
        
        for i, params in enumerate(self.pendulum_params):
            selected_type = self.integrator_buttons[i].checkedButton().text()
            if selected_type == "Euler":
                integrator_type = EulerPendulum
            elif selected_type == "RK2":
                integrator_type = RK2Pendulum
            else:
                integrator_type = RK4Pendulum
                
            configs.append(PendulumConfig(
                name=f"Pendulum {i+1}",
                color=colors[i],
                integrator_type=integrator_type,
                theta1=params['theta1 (°)'],
                theta2=params['theta2 (°)'],
                m1=params['m1 (kg)'],
                m2=params['m2 (kg)'],
                l1=params['l1 (m)'],
                l2=params['l2 (m)'],
                g=g
            ))
        
        self.simulation = PendulumSimulation(configs)
        
        for trace in self.trace_items:
            trace.clear()
        for r1,r2,b1,b2 in self.anim_items:
            r1.clear(); r2.clear(); b1.clear(); b2.clear()
        
        for plot in [self.ke_plot, self.pe_plot, self.te_plot]:
            plot.clear()
        
        for config in configs:
            pen = pg.mkPen(config.color, width=2)
            self.energy_plots['ke'][config.name] = self.ke_plot.plot(pen=pen)
            self.energy_plots['pe'][config.name] = self.pe_plot.plot(pen=pen)
            self.energy_plots['te'][config.name] = self.te_plot.plot(pen=pen)

        max_length = max(p['l1 (m)'] + p['l2 (m)'] for p in self.pendulum_params)
        rng = max_length * 1.2
        self.anim_plot.getViewBox().setRange(xRange=(-rng,rng), yRange=(-rng,rng), padding=0)
        
        self.timer.stop()
        self.start_btn.setText("Start")
        self.running = False
        for pend, items in zip(self.simulation.pendulums, self.anim_items):
            x1, y1, x2, y2 = pend.position()
            r1, r2, b1, b2 = items
            r1.setData([0, x1], [0, y1]); r2.setData([x1, x2], [y1, y2])
            b1.setData([x1], [y1]); b2.setData([x2], [y2])

    def toggle(self):
        """Toggle simulation running state."""
        if self.running:
            self.timer.stop()
            self.start_btn.setText("Start")
        else:
            self.timer.start()
            self.start_btn.setText("Pause")
        self.running = not self.running

    def advance_frame(self):
        """Update simulation state and visualization."""
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                positions = self.simulation.step(self.dt)
        except (FloatingPointError, ValueError) as exc:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("Start")
            QtWidgets.QMessageBox.warning(self, "Numerical instability", f"Try a smaller dt and Reset.\n{exc}")
            return
        
        for i, (x1,y1,x2,y2) in enumerate(positions):
            r1,r2,b1,b2 = self.anim_items[i]
            r1.setData([0,x1],[0,y1])
            r2.setData([x1,x2],[y1,y2])
            b1.setData([x1],[y1])
            b2.setData([x2],[y2])
            
            trace = self.trace_items[i]
            trace_data = self.simulation.trace_data[f"Pendulum {i+1}"]
            if trace_data['x']:
                times = np.array(trace_data['times'])
                current_time = times[-1]
                opacities = np.clip((current_time - times) / self.simulation.trace_window, 0, 1)
                color = pg.mkPen(self.simulation.pendulums[i].config.color, width=1, style=QtCore.Qt.DotLine)
                trace.setData(trace_data['x'], trace_data['y'], pen=color)
        
        for name, data in self.simulation.energy_data.items():
            self.energy_plots['ke'][name].setData(self.simulation.times, data['ke'])
            self.energy_plots['pe'][name].setData(self.simulation.times, data['pe'])
            self.energy_plots['te'][name].setData(self.simulation.times, data['te'])

# ── Main application window ─────────────────────────────────────────────────

class MainWindow(QtWidgets.QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.simulator = PendulumSimulator()
        self.setCentralWidget(self.simulator)
        self.setWindowTitle("Planar Double Pendulum | Integrator Comparison")
        self.resize(1400, 850)

def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
