import os
import __main__

import shiboken6
from PySide6.QtWidgets import *
from PySide6.QtCore import *

from astro import ui
from astro import graphics
from astro import mesh
from astro import post
from astro import marker


class Animation(QWidget):
    def __init__(self, parent=None):
        super(Animation, self).__init__(parent)

        # 패널을 옮길 때 위젯째 옮기므로 레이아웃은 패널 프레임이 아니라 위젯 자신에 둔다
        vbox = QVBoxLayout(self)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        for text, slot in (("Start", self.onStart), ("Stop", self.onStop), ("Reset", self.onReset)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            hbox.addWidget(button)
        hbox.addStretch(1)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QLabel('Time Step: '))
        self.spinBox = QSpinBox(self)
        self.spinBox.setFixedWidth(60)
        self.spinBox.valueChanged.connect(self.onTimeStepChanged)
        hbox.addWidget(self.spinBox)
        hbox.addSpacing(10)
        hbox.addWidget(QLabel('Delay : '))
        self.delaySpinBox = QSpinBox(self)
        self.delaySpinBox.setSuffix(" ms")
        self.delaySpinBox.setRange(0, 100000)
        self.delaySpinBox.setValue(30)
        self.delaySpinBox.setFixedWidth(80)
        self.delaySpinBox.valueChanged.connect(self.onDelayChanged)
        hbox.addWidget(self.delaySpinBox)
        hbox.addStretch(1)

        vbox.addStretch(1)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch(1)
        button = QPushButton("Close")
        button.clicked.connect(self.onClose)
        hbox.addWidget(button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.onTimer)

    def onDelayChanged(self):
        if self.timer.isActive():
            self.timer.setInterval(self.delaySpinBox.value())

    def onTimer(self):
        try:
            next_time_step = self.spinBox.value() + 1
            self.spinBox.setValue(next_time_step if next_time_step < len(post.get_times()) else 0)
        except Exception as e:
            self.timer.stop()
            print(e)
            QMessageBox.critical(self, "Error", str(e))

    def onTimeStepChanged(self):
        try:
            time_step = self.spinBox.value()
            if time_step < len(post.get_times()):
                post.set_current_time_step(time_step)
        except Exception as e:
            print(e)
            QMessageBox.critical(self, "Error", str(e))

    def onStart(self):
        self.timer.start(self.delaySpinBox.value())

    def onStop(self):
        self.timer.stop()

    def onReset(self):
        self.spinBox.setValue(0)
        self.delaySpinBox.setValue(30)

    def onClose(self):
        self.timer.stop()
        restore_dock_height()
        unregister_panel_events()
        ui.remove_panel('animation')


# ---------------------------------------------------------------
# 패널 배치
# AstroWorks 는 Qt Advanced Docking System(ADS)이라 패널이 QDockWidget 이 아닌 QSplitter 안의
# ads::CDockAreaWidget / ads::CDockWidget 에 들어 있다. Python 바인딩이 없어 클래스 이름으로 찾는다

# 기본 콘솔은 도킹 창 제목과 패널 이름이 다르다 (astromesh.exe). 도움말의 'TclConsole' 은 위젯 이름이라 안 된다
BUILTIN_PANELS = {
    'Tcl Console': '#tcl_console',
    'Python Console': '#python_console',
    'Embed Python Console': '#embed_python_console',
}

def ads_ancestor(widget, class_name):
    while widget is not None and widget.metaObject().className() != class_name:
        widget = widget.parentWidget()
    return widget

def dock_widgets_in(area):
    return [c for c in area.findChildren(QWidget) if c.metaObject().className() == 'ads::CDockWidget']

# 붙일 수 있는 패널 이름 후보. 기본 콘솔은 위 표로, 스크립트 패널은 exists_panel 로 확인되는 이름으로 찾는다
def panel_names(dock):
    names = []
    if dock.objectName() in BUILTIN_PANELS:
        names.append(BUILTIN_PANELS[dock.objectName()])
    for child in [dock] + dock.findChildren(QWidget):
        name = child.objectName()
        if name and name not in names and ui.exists_panel(name):
            names.append(name)
    return names

# 메인 창 하단에 보이는 도킹 위젯들. 닫힌 패널은 보이지 않으므로 빠진다
# 하단 패널은 도킹 영역이 가로로 넓고 영역의 세로 중심이 아래쪽 절반에 있는 것으로 본다
# (하단 패널이 여럿 쌓이면 윗변이 위쪽 절반으로 올라갈 수 있다. 좌우 패널은 세로로 길쭉해서 빠진다)
def bottom_docks():
    mains = [m for m in QApplication.topLevelWidgets() if isinstance(m, QMainWindow) and m.isVisible()]
    if not mains:
        return []
    main = mains[0]
    docks = []
    for dock in QApplication.allWidgets():
        if dock.metaObject().className() != 'ads::CDockWidget' or not dock.isVisible() or dock.window() is not main:
            continue
        area = ads_ancestor(dock, 'ads::CDockAreaWidget') or dock
        center_y = area.mapTo(main, QPoint(0, 0)).y() + area.height() / 2
        if area.width() > area.height() and center_y > main.height() / 2:
            docks.append(dock)
    return docks

# dock 옆에 animation 패널을 탭으로 만든다. 붙일 수 있는 이름이 없으면 False
def attach_to(dock):
    for name in panel_names(dock):
        try:
            ui.add_panel_tab(name, 'animation', 'Animation')
            return True
        except SystemError:
            pass
    return False

# 하단에 열려 있는 패널 옆에 탭으로 붙이고, 없으면 하단에 따로 띄운다
def add_animation_panel(docks):
    if not any(attach_to(dock) for dock in docks):
        ui.add_panel('animation', 'Animation', ui.DOCK_BOTTOM, [300, 300])
    ui.select_panel('animation')

# 패널 프레임에 위젯을 꽉 채워 넣는다
def put_into_frame(widget):
    frame = ui.find_panel_frame('animation')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(widget)
    widget.show()
    return frame


# ---------------------------------------------------------------
# 패널 높이
# 패널이 들어 있는 세로 splitter 의 칸을 내용물 최소 높이로 줄이고, Close 때 되돌린다

def find_splitter():
    item = frame
    while item.parentWidget() is not None:
        parent = item.parentWidget()
        if isinstance(parent, QSplitter) and parent.orientation() == Qt.Vertical:
            return parent, item
        item = parent
    return None, None

# 남는 높이는 옆 칸(3D 창)에 준다. 원래 크기는 처음 한 번만 기억해 둔다
def fit_dock_height():
    splitter, item = find_splitter()
    if splitter is None:
        return
    sizes = splitter.sizes()
    i = splitter.indexOf(item)
    j = i - 1 if i > 0 else i + 1
    if j >= len(sizes):
        return
    if splitter.property('anim_restore_sizes') is None:
        splitter.setProperty('anim_restore_sizes', list(sizes))
    height = item.height() - frame.height() + frame.minimumSizeHint().height()
    sizes[j] += sizes[i] - height
    sizes[i] = height
    splitter.setSizes(sizes)

def restore_dock_height():
    splitter, item = find_splitter()
    if splitter is None or splitter.property('anim_restore_sizes') is None:
        return
    splitter.setSizes(splitter.property('anim_restore_sizes'))
    splitter.setProperty('anim_restore_sizes', None)


# ---------------------------------------------------------------
# 하단 패널 따라가기
# Animation 만 하단에 있을 때 다른 패널이 하단에 뜨면 Animation 을 그 패널 옆 탭으로 옮긴다
# 이미 열린 패널을 옮기는 명령이 없어서 Animation 쪽이 옮겨 간다. 위젯은 그대로 옮기므로 상태가 유지된다

def move_to_new_bottom_panel():
    global frame
    # 탭의 x 로 닫으면 Close 버튼을 거치지 않아 감시가 남는다. 패널이나 위젯이 지워졌으면 감시를 끈다
    current = ui.find_panel_frame('animation')
    if current is None or not shiboken6.isValid(w) or not shiboken6.isValid(current) or w.parentWidget() is not current:
        unregister_panel_events()
        return
    frame = current
    watch_docks()
    anim_dock = ads_ancestor(frame, 'ads::CDockWidget')
    anim_area = ads_ancestor(frame, 'ads::CDockAreaWidget')
    # 닫혀서 숨겨졌거나, Animation 혼자 있는 영역이 아니면 그대로 둔다
    if anim_dock is None or anim_area is None or not anim_dock.isVisible():
        return
    if dock_widgets_in(anim_area) != [anim_dock]:
        return
    for dock in bottom_docks():
        if ads_ancestor(dock, 'ads::CDockAreaWidget') is anim_area or not panel_names(dock):
            continue
        # 위젯을 떼어 놓고 패널을 다시 만든 뒤 새 프레임에 넣는다
        restore_dock_height()
        w.setParent(None)
        ui.remove_panel('animation')
        add_animation_panel([dock])
        frame = put_into_frame(w)
        QTimer.singleShot(0, fit_dock_height)
        return

# 패널이 열리고 닫히는 것은 ADS 시그널로 안다 (PanelShown 같은 Tcl 콜백은 오지 않았다)
# 시그널 이름 문자열로 도킹 위젯마다 한 번만 연결하고, 연결은 늘 schedule_move 로 간다
# 실제로 할 일은 __main__.__animation_watcher__ 가 정한다. 버튼을 다시 눌러도 연결이 쌓이지 않는다
def schedule_move(*args):
    watcher = getattr(__main__, '__animation_watcher__', None)
    if watcher is None:
        return
    try:
        watcher()
    except RuntimeError:
        # Animation 위젯이 이미 지워졌다
        __main__.__animation_watcher__ = None

def watch_docks():
    for widget in QApplication.allWidgets():
        if widget.property('anim_watched'):
            continue
        class_name = widget.metaObject().className()
        if class_name == 'ads::CDockWidget':
            QObject.connect(widget, SIGNAL('visibilityChanged(bool)'), schedule_move)
            widget.setProperty('anim_watched', True)
        elif class_name == 'ads::CDockManager':
            # 새 패널이 생기면 새 도킹 영역이 생긴다
            QObject.connect(widget, SIGNAL('dockAreasAdded()'), schedule_move)
            widget.setProperty('anim_watched', True)

# 시그널이 한꺼번에 여러 번 와도 배치가 끝난 뒤 한 번만 보도록 타이머로 모은다
def register_panel_events():
    move_timer = QTimer(w)
    move_timer.setSingleShot(True)
    move_timer.setInterval(0)
    move_timer.timeout.connect(move_to_new_bottom_panel)
    __main__.__animation_watcher__ = move_timer.start
    watch_docks()

def unregister_panel_events():
    __main__.__animation_watcher__ = None


# ---------------------------------------------------------------
# 실행

ui.set_window_layout(0)
if ui.get_window_type(0) != ui.WINDOW_TYPE_OPENGL:
    ui.set_window_type(0, ui.WINDOW_TYPE_OPENGL)
ui.set_current_window(0)

graphics.set_edge_thickness(1)
graphics.set_edge_visible(True)

if ui.exists_panel('animation'):
    ui.remove_panel('animation')
add_animation_panel(bottom_docks())

w = Animation()
frame = put_into_frame(w)
# 레이아웃이 잡힌 뒤에 높이를 계산해야 하므로 이벤트 루프로 미룬다
QTimer.singleShot(0, fit_dock_height)
register_panel_events()

model_name = os.path.join(os.environ["ASTRO"], "examples", "samples", "truck", "d3plot")
mesh.load_model(model_name)
post.load_result(model_name)
w.spinBox.setMaximum(len(post.get_times()) - 1)

post.load_contour('displacement', 'mag')
marker.create_mark('elems', 1, 'all')
elems = marker.get_mark('elems', 1)
marker.clear_mark_all()
post.set_contour_element(elems, True)
post.set_contour_visible(True)
post.set_legend_visible(True)
