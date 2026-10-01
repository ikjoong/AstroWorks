from astro import ui
from astro import graphics 
from astro import mesh
from astro import post
from astro import marker

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import *
from PySide6.QtCore import *

ui.set_window_layout(0)
if ui.get_window_type(0) != ui.WINDOW_TYPE_OPENGL:
    ui.set_window_type(0, ui.WINDOW_TYPE_OPENGL)
ui.set_current_window(0)

graphics.set_edge_thickness(1)
graphics.set_edge_visible(True)

if ui.exists_panel('animation') == True:
    ui.remove_panel('animation')

ui.add_panel_tab('#python_console', 'animation', 'Animation')
ui.select_panel('animation')

class Animation(QWidget):
    def __init__(self, parent=None):
        super(Animation, self).__init__(parent)

        #print(parent)

        #parent.setStyleSheet("background-color:red;");

        #self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.vbox = QVBoxLayout(parent)
        #self.vbox.setSpacing(2)
        #self.vbox.setAlignment(Qt.AlignTop)
        #self.vbox.setContentsMargins(0, 0, 0, 0)
        #self.setLayout(self.vbox)

        # ----------
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox)

        button = QPushButton("Start")
        button.clicked.connect(self.onStart)
        self.hbox.addWidget(button)

        button = QPushButton("Stop")
        button.clicked.connect(self.onStop)
        self.hbox.addWidget(button)

        button = QPushButton("Reset")
        button.clicked.connect(self.onReset)
        self.hbox.addWidget(button)
        
        self.hbox.addStretch()
        
        # ----------
        self.hbox = QHBoxLayout()
        #self.hbox.setSpacing(20)
        self.vbox.addLayout(self.hbox)

        label = QLabel('Time Step: ')
        self.hbox.addWidget(label);

        self.spinBox = QSpinBox(self)
        self.spinBox.setFixedWidth(60)
        self.spinBox.valueChanged.connect(self.onTimeStepChanged)
        self.hbox.addWidget(self.spinBox)
        
        spacer = QLabel();
        spacer.setFixedWidth(10);
        self.hbox.addWidget(spacer)

        label = QLabel('Delay : ')
        self.hbox.addWidget(label);

        self.delaySpinBox = QSpinBox(self)
        self.delaySpinBox.setSuffix(" ms")
        self.delaySpinBox.setMinimum(0)
        self.delaySpinBox.setMaximum(100000)
        self.delaySpinBox.setValue(30)
        self.delaySpinBox.setFixedWidth(80)
        self.delaySpinBox.valueChanged.connect(self.onDelayChanged)
        self.hbox.addWidget(self.delaySpinBox)

        self.hbox.addStretch(1)

        # ----------
        self.vbox.addStretch(1)

        # ----------
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox)

        self.hbox.addStretch(1)
        #self.hbox.addSpacing(100)
        button = QPushButton("Close")
        button.clicked.connect(self.onClose)
        self.hbox.addWidget(button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.onTimer)

    def onDelayChanged(self):
        ms = self.delaySpinBox.value()

        if self.timer.isActive():
            self.timer.setInterval(ms)

    def onTimer(self):
        time_step = self.spinBox.value()
        next_time_step = time_step + 1

        try:
            times = post.get_times()
            if len(times) > next_time_step:
                self.spinBox.setValue(next_time_step)
            else:
                self.spinBox.setValue(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print(e)
            self.timer.stop()

    def onTimeStepChanged(self):
        time_step = self.spinBox.value()
        try:
            times = post.get_times()
            if len(times) > time_step:
                post.set_current_time_step(time_step)
                self.spinBox.setValue(time_step)
            #print(times)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print(e)
        
    def onStart(self):
        ms = self.delaySpinBox.value()
        self.timer.start(ms)

    def onStop(self):
        self.timer.stop()

    def onReset(self):
        self.spinBox.setValue(0)
        self.delaySpinBox.setValue(30)

    def onClose(self):
        self.timer.stop()
        ui.remove_panel('animation')
        #QMessageBox.about(self, "Close", "This is about application")

frame = ui.find_panel_frame('animation')
w = Animation(frame)
w.show()
 
astro_path = os.environ["ASTRO"]
model_name = astro_path + "examples/samples/truck/d3plot"
mesh.load_model(model_name)
#mesh.load_model('./samples/d3plot/truck/d3plot')
#mesh.load_model('C:/WORKSPACE/MOBIS/y2014-lij-cockpit/src/test/HEAD_IMPACT_EU/PT01/run00/d3plot')
#mesh.load_model('./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot')
#mesh.load_model('./samples/d3plot/wheel/d3plot')
#post.load_result('./samples/d3plot/truck/d3plot')
post.load_result(model_namE)

times = post.get_times()
print(times)

#mesh.load_model('./samples/d3plot/truck/d3plot', 'contour=displacement,mag')
#mesh.load_model('./samples/d3plot/truck/d3plot', 'contour=stress,von_mises')
#mesh.load_model('./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot', 'contour=displacement,mag')

times = post.get_times()
w.spinBox.setMinimum(0)
w.spinBox.setMaximum(len(times)-1)
    
if 1:
    # ------------------------
    '''
    marker.create_mark('comps', 1, 'all')
    comps = marker.get_mark('comps', 1)
    marker.clear_mark_all();
    post.set_contour_component(comps, True)
    '''

    post.load_contour('displacement', 'mag')
    #post.load_contour('effective_plastic_strain')
    #post.load_contour('stress', 'von_mises')

    marker.create_mark('elems', 1, 'all')
    elems = marker.get_mark('elems', 1)
    marker.clear_mark_all();
    post.set_contour_element(elems, True)

    # ------------------------
    post.set_contour_visible(True)
    post.set_legend_visible(True)

    '''
    # contour 값 로딩후 진행
    #*load ./samples/d3plot/truck/d3plot "contour=Velocity,X"
    #*load ./samples/d3plot/truck/d3plot "contour=Stress,VonMises"
    #*load ./samples/d3plot/truck/d3plot "contour=Velocity,Mag"
    *load ./samples/d3plot/truck/d3plot "contour=Displacement,Mag"

    #*load ./samples/d3plot/samsung/d3plot/d3plot "contour=Displacement,Mag"
    #*load ./samples/d3plot/samsung/d3plot/d3plot "contour=Velocity,Mag"

    #*load ./samples/d3plot/bumper/d3plot "contour=Displacement,Mag"

    #*load ./samples/d3plot/wheel/d3plot "contour=Displacement,Mag"
    #*load ./samples/d3plot/wheel/d3plot "contour=Stress,VonMises"

    #*load ./samples/d3plot/_TEST/d3plot "contour=Displacement,Mag"

    #*load ./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot "contour=Velocity,X"
    #*load ./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot "contour=Velocity,Mag"
    #*load ./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot "contour=Displacement,Mag"
    #*load ./samples/d3plot/PZ01_Top_90cm_30d_140703/d3plot "contour=Stress,VonMises"
    '''
