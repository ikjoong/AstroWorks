import glob
import os
import os.path
import io
import json
import re
from random import randrange

import qtpy 
from qtpy import QtGui, QtWidgets, QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QMessageBox, QFileDialog, QVBoxLayout, QApplication, QToolButton, QMenu
from qtpy.QtCore import QSize, Qt, QStandardPaths

from pyqtribbon import RibbonBar

from astro import ui
from astro import mesh
from astro import geometry as geom
from astro import interpreter as interp
def Restart():
    interp.eval_tcl('*restart')

def Todolist():
    interp.eval_tcl('''
    cd C:/AstroWorks/scripts/_ikjoong
    source C:/AstroWorks/scripts/_ikjoong/todolist.tcl
    ''')


def OnTclCmd():
    interp.eval_tcl('''
    tk_messageBox -message 1
    source C:/AstroWorks/examples/animation.tcl
    ''')

def Restart():
    interp.eval_tcl('*restart')



def GetIcon(name):
    astro_path = os.environ["ASTRO"]

    path = astro_path + "/icons/vs2019/" + name + ".svg"
    if os.path.isfile(path):
        return path

    path = astro_path + "/../icons/vs2019/" + name + ".svg"
    if os.path.isfile(path):
        return path

    path = astro_path + "/scripts/pyqtribbon/icons/" + name + ".svg"
    if os.path.isfile(path):
        return path

    path = astro_path + "/../scripts/pyqtribbon/icons/" + name + ".svg"
    if os.path.isfile(path):
        return path

    path = astro_path + "/scripts/pyqtribbon/icons/" + name + ".png"
    if os.path.isfile(path):
        return path

    path = astro_path + "/../scripts/pyqtribbon/icons/" + name + ".png"
    if os.path.isfile(path):
        return path

# 읽을 수 있는 확장자는 **앱에 물어본다.**
#
# 예전에는 이 파일에 손으로 적어 두었다. 그래서 리더를 더해도 파일 대화상자에는
# 안 보였고(.rad 가 그랬다), vtu/vts/vtp/mfem/vxl/inc/asc/h5 는 진작부터 빠져
# 있었다. 목록의 주인은 GLWindow::importFormats() 하나다.
CAD_EXTS = ['.step', '.stp', '.iges', '.igs', '.brep']


def _mesh_exts():
    try:
        return ['.' + e for e in mesh.get_import_formats()]
    except Exception:
        # 옛 빌드에서도 돌게 둔다. 없으면 예전 목록으로 버틴다
        return ['.key', '.k', '.dyn', '.mesh', '.stl', '.ply', '.obj', '.off', '.vtk', '.unv']


def _is_mesh_file(path):
    # GLWindow::isModelFile 과 같게 본다. d3plot 과 A001 같은 애니메이션
    # 파일은 확장자가 없어 이름으로 가른다
    if os.path.splitext(path)[1].lower() in _mesh_exts():
        return True

    base = os.path.basename(path).split('.')[0]
    if base.lower() == 'd3plot':
        return True

    return re.match(r'^(.*?)(A\d+)$', base) is not None


def _file_filter():
    mesh_pat = ';'.join('*' + e for e in _mesh_exts())
    cad_pat = ';'.join('*' + e for e in CAD_EXTS)

    return ("Mesh Files (%s);;" % mesh_pat) + ("CAD Files (%s);;" % cad_pat) + "All Files(*.*)"


#
# ---- 파일 대화상자
#
# **본창에 매달고, 하나만 띄운다.**
#
# 예전에는 부모를 None 으로 줬다. 그러면 대화상자가 떠 있는 동안에도 본창이
# 살아 있어서 리본을 또 누를 수 있다. 그 클릭은 첫 대화상자의 중첩 이벤트
# 루프 안에서 돌아, 대화상자 안에서 대화상자가 또 뜬다 - Open 을 누르다
# 가끔 ACCESS VIOLATION 으로 죽던 자리다(선택의 중첩 루프가 연타에 죽는
# 것과 같은 꼴).
#
# 본창을 부모로 주면 대화상자가 본창을 막는다. 그래도 단축키·코드에서 다시
# 부를 수 있으니 떠 있는 동안은 두 번째 호출을 그냥 돌려보낸다.
#
_dialog_busy = False


def _dialog_parent():
    try:
        return ui.find_main_window()
    except Exception:
        return None


def _one_dialog(func):
    #
    # **인자는 버린다.** 버튼의 clicked 는 checked 를 넘기는데 감싼 함수는
    # 인자를 안 받는다. 그대로 넘기면 TypeError 다 - 원래 함수를 바로
    # 이을 때는 PySide 가 시그니처를 보고 알아서 뺐다.
    #
    def wrapper(*args, **kwargs):
        global _dialog_busy

        if _dialog_busy:
            return None

        _dialog_busy = True
        try:
            return func()
        finally:
            _dialog_busy = False

    wrapper.__name__ = func.__name__
    return wrapper


@_one_dialog
def OnOpenFile():
    fileName = QFileDialog.getOpenFileName(_dialog_parent(), "Open", None, _file_filter())
    if fileName[0] == '': return

    name, ext = os.path.splitext(fileName[0])

    if( ext.lower() in CAD_EXTS ):
        geom.load_model(fileName[0])
    elif( _is_mesh_file(fileName[0]) ):
        mesh.load_model(fileName[0])
    else:
        QMessageBox.warning(None, "AstroMesh", 'The file selected is an unsupported format.')

def _model_is_empty():
    try:
        return len(mesh.get_component_list()) == 0
    except Exception:
        return False


@_one_dialog
def OnImportFile():
    """지금 모델에 파일을 얹는다.

    **빈 화면이면 Open 과 같게 연다.** import 는 그래픽을 초기화하지 않고
    (GLWindow::import 는 initGraphics 를 안 부른다) 화면도 맞추지 않는다.
    처음 여는 모델을 import 로 넣으면 안 보이거나 엉뚱한 자리에 선다.

    이미 모델이 있으면 보기는 그대로 둔다. 얹은 것이 어디 있든 보던
    것을 지킨다 - 필요하면 사용자가 맞춘다.
    """
    parent = _dialog_parent()

    fileName = QFileDialog.getOpenFileName(parent, "Import", None, _file_filter())
    if fileName[0] == '': return

    path = fileName[0]
    name, ext = os.path.splitext(path)
    ext = ext.lower()

    empty = _model_is_empty()

    try:
        if ext not in CAD_EXTS and _is_mesh_file(path):
            if empty:
                mesh.load_model(path)
            else:
                mesh.import_model(path)

        elif ext in CAD_EXTS:
            if empty:
                geom.load_model(path)
            else:
                geom.import_model(path)

        else:
            QMessageBox.warning(parent, "AstroMesh",
                    'The file selected is an unsupported format.')

    except Exception as e:
        QMessageBox.critical(parent, "AstroMesh", str(e))

@_one_dialog
def OnSaveFile():
    extensions = "AstroMesh Files (*.h5);;"
    extensions += "All Files(*.*)"

    fileName = QFileDialog.getSaveFileName(_dialog_parent(), "Save", None, extensions)
    if fileName[0] == '': return

    name, ext = os.path.splitext(fileName[0])

    if ext.lower() == '.h5':
        mesh.save_model(fileName[0])
    else:
        QMessageBox.warning(None, "AstroMesh", 'File extension not supported.')

#
# ---- 내보내기
#
# 형식 이름은 앱이 준다(mesh.get_export_formats() -> GLWindow::exportFormats()).
# 이름이 곧 확장자인데 **exodus 만 아니다** - 그래서 대화상자에서 고른 형식을
# export_model 에 **직접 넘긴다.** 확장자로만 가르게 두면 a.exo 가 "모르는
# 형식" 으로 떨어진다.
#
_EXPORT_LABELS = {
    'key':    ('LS-DYNA',       ['.k', '.key', '.dyn']),
    'rad':    ('Radioss',       ['.rad']),
    'vtk':    ('VTK',           ['.vtk']),
    'stl':    ('STL',           ['.stl']),
    'obj':    ('Wavefront OBJ', ['.obj']),
    'off':    ('OFF',           ['.off']),
    'mesh':   ('Medit',         ['.mesh']),
    'exodus': ('Exodus II',     ['.exo', '.e']),
}

# 덱을 읽어 온 모델이면 같은 솔버로 권한다. 리더가 SetModelSolver 로 적는다
_SOLVER_FORMAT = {'radioss': 'rad', 'lsdyna': 'key'}


def _export_rows():
    """[(형식, 거르개 글, 확장자들), ...]"""
    try:
        names = [str(n) for n in mesh.get_export_formats()]
    except Exception:
        # 옛 빌드. 앱이 아는 것과 같게
        names = ['key', 'rad', 'vtk', 'stl', 'obj', 'off', 'mesh', 'exodus']

    rows = []

    for n in names:
        label, exts = _EXPORT_LABELS.get(n, (n.upper(), ['.' + n]))
        rows.append((n, '%s (%s)' % (label, ' '.join('*' + e for e in exts)), exts))

    return rows


@_one_dialog
def OnExportFile():
    parent = _dialog_parent()

    if _model_is_empty():
        QMessageBox.information(parent, "AstroMesh", 'There is no model to export.')
        return

    rows = _export_rows()
    if len(rows) == 0:
        return

    try:
        solver = mesh.get_meta_value('astro.solver', '')
    except Exception:
        solver = ''

    want = _SOLVER_FORMAT.get(solver)
    first = next((r[1] for r in rows if r[0] == want), rows[0][1])

    path, chosen = QFileDialog.getSaveFileName(parent, "Export", None,
            ';;'.join(r[1] for r in rows), first)
    if path == '': return

    #
    # **형식 가르기.** 적은 확장자가 아는 것이면 그것이 먼저다 - 거르개를
    # LS-DYNA 에 둔 채 a.rad 라고 적었으면 Radioss 를 원한 것이다. 확장자가
    # 없으면 고른 거르개를 따르고 그 확장자를 붙인다.
    #
    ext = os.path.splitext(path)[1].lower()

    fmt = next((r[0] for r in rows if ext in r[2]), None)

    if fmt is None:
        picked = next((r for r in rows if r[1] == chosen), rows[0])
        fmt = picked[0]

        if ext == '':
            path += picked[2][0]

    try:
        report = mesh.export_model(path, fmt)
    except Exception as e:
        QMessageBox.critical(parent, "AstroMesh", str(e))
        return

    # 무엇을 썼는지. 건너뛴 것이 있으면 여기 나온다
    lines = [str(l) for l in (report or [])]

    msg = 'Exported to\n%s' % path
    if len(lines) > 0:
        msg += '\n\n' + '\n'.join(lines[:20])
        if len(lines) > 20:
            msg += '\n... (%d more)' % (len(lines) - 20)

    QMessageBox.information(parent, "AstroMesh", msg)


def OnCloseFile():
    mesh.free()

def OnToggleTclConsole():
    ui.toggle_tcl_console_visible()

def OnTogglePythonConsole():
    ui.toggle_python_console_visible()

def OnToggleEmbedPythonConsole():
    ui.toggle_embed_python_console_visible()

def OnToggleCopilot():
    ui.toggle_copilot_visible()

def OnToggleLoadSymbol(checked):
    """하중 심볼 화살표를 켜고 끈다.

    **화살표는 절점마다 하나씩 선다**(reader/radioss_reader.cpp BuildLoads).
    /GRAV 처럼 파트 전체에 걸리는 하중이면 한 장에 천 개가 넘어 형상을
    덮는다. HyperMesh 는 카드 한 장에 하중 하나를 두고 절점으로 안 편다.

    크기는 `*set_arrow_scaling` 으로 줄인다. 기본값은 0.1 이다
    (glwindow.cpp DEFAULT_ARROW_SCALING). 그래도 거슬리면 이걸로 끈다.

    **화살표를 통째로 끈다.** `*create_arrow` 로 스크립트가 세운 것도 같이
    숨는다. 후처리 벡터는 딴 깃발이라 안 건드린다(drawPostVectors).
    """
    try:
        interp.eval_tcl('*set_arrow_visible ' + ('true' if checked else 'false'))
    except Exception as e:
        # 모델을 안 열었으면 GL 창이 없다. 조용히 지나가면 왜 안 되는지 모른다
        print('load symbol toggle: %s' % e)

def addSubMenu(menu, text):
    #subMenu.setFont(":/fonts/Consolas.ttf")
    return subMenu

def GetGrayed(src):
    if isinstance(src, QtGui.QPixmap):
        src = src.toImage()
    dest = QtGui.QImage(src.size(), QtGui.QImage.Format_ARGB32)
    widthRange = range(src.width())
    for y in range(src.height()):
        for x in widthRange:
            pixel = src.pixelColor(x, y)
            alpha = pixel.alpha()
            if alpha < 255:
                alpha //= 3
            gray = QtGui.qGray(src.pixel(x, y))
            pixel.setRgb(gray, gray, gray, alpha)
            dest.setPixelColor(x, y, pixel)
    return QtGui.QPixmap.fromImage(dest)

global ribbonBar

# **메뉴 포인터를 들고 있지 않는다.**
#
# QMenu 는 부모가 지우면 파이썬 쪽 껍데기만 남는다. 나중에 그걸 만지면
# "Internal C++ object already deleted" 로 죽는다. 대신 메뉴가 열릴 때
# 채운다 - 그 시점에는 살아 있는 것이 보장된다.

# ---------------------------------------------------------------------------
# 최근 연 모델
#
# **경로는 ModelLoaded 콜백에서 모은다.** OnOpenFile 에서만 모으면 Tcl 의
# *load 로 연 것이 빠진다. 콜백은 인자를 안 주므로 경로는 *get_file_name 으로
# 따로 물어본다.
# ---------------------------------------------------------------------------

RECENT_MAX = 10
RECENT_TITLE = "Recent Models"

def _recent_file_path():
    """목록을 담아 둘 파일. 배치 파일과 같은 자리다."""
    dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if dir == '':
        return ''

    return os.path.join(dir, 'recent.json')

def _recent_load():
    path = _recent_file_path()
    if path == '' or not os.path.exists(path):
        return []

    try:
        with io.open(path, encoding='utf-8') as f:
            items = json.load(f)
    except Exception:
        # 깨졌으면 없는 셈 친다. 목록 하나 때문에 시작이 막히면 안 된다
        return []

    return [p for p in items if isinstance(p, str)]

def _recent_save(items):
    path = _recent_file_path()
    if path == '':
        return

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with io.open(path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print('could not save the recent file list:', e)

def _recent_add(path):
    if path is None or path == '':
        return

    path = os.path.normpath(path)

    items = _recent_load()

    # 같은 파일은 위로 올린다. 대소문자는 Windows 기준으로 무시한다
    items = [p for p in items if os.path.normcase(p) != os.path.normcase(path)]
    items.insert(0, path)

    _recent_save(items[:RECENT_MAX])

    RebuildRecentMenu()

def _recent_open(path):
    if not os.path.exists(path):
        QMessageBox.warning(None, "AstroMesh", "File not found:\n" + path)

        # 없는 파일은 목록에서 뺀다
        items = [p for p in _recent_load()
                 if os.path.normcase(p) != os.path.normcase(path)]
        _recent_save(items)
        RebuildRecentMenu()
        return

    # 예전에는 확장자를 여기 따로 적어 두어 .rad 가 빠져 있었다. Open 과
    # 같은 판정을 쓴다
    name, ext = os.path.splitext(path)

    if ext.lower() in CAD_EXTS:
        geom.load_model(path)
    elif _is_mesh_file(path):
        mesh.load_model(path)
    else:
        QMessageBox.warning(None, "AstroMesh", 'The file selected is an unsupported format.')

def OnModelLoaded():
    """모델이 열릴 때마다 불린다. GUI 든 *load 든 여기로 온다."""
    _recent_add(interp.eval_tcl('*get_file_name'))

def _find_recent_menu():
    """최근 목록 메뉴를 리본에서 찾아 내려간다.

    **포인터를 캐시하면 안 된다.** QMenu 는 C++ 쪽에서 지워질 수 있고,
    그러면 파이썬 껍데기만 남아 만지는 순간 죽는다
    (Internal C++ object already deleted). 리본 바는 창이 들고 있어 안정적이니
    거기서 매번 내려간다.
    """
    global ribbonBar

    try:
        menu = ribbonBar.applicationOptionButton().menu()
    except Exception:
        return None

    if menu is None:
        return None

    for act in menu.actions():
        if act.text() == RECENT_TITLE:
            return act.menu()

    return None

def RebuildRecentMenu():
    """메뉴를 지금 목록으로 다시 채운다."""
    recentMenu = _find_recent_menu()
    if recentMenu is None:
        return

    recentMenu.clear()

    items = _recent_load()

    if len(items) == 0:
        action = recentMenu.addAction("(empty)")
        action.setEnabled(False)
        return

    for i, path in enumerate(items):
        # 앞에 번호를 붙여 키보드로도 고를 수 있게 한다
        action = recentMenu.addAction('&%d  %s' % (i + 1, os.path.basename(path)))
        action.setToolTip(path)

        # 기본 인자로 지금 값을 묶는다. 안 그러면 마지막 path 만 잡힌다
        action.triggered.connect(lambda checked=False, p=path: _recent_open(p))

    recentMenu.addSeparator()

    action = recentMenu.addAction("Clear List")
    action.triggered.connect(
            lambda checked=False: (_recent_save([]), RebuildRecentMenu()))

def CreateRibbon():
    global ribbonBar

    #print(QtCore.__version__)

    window = ui.find_main_window()

    ribbonBar = RibbonBar()
    ribbonBar.setRibbonHeight(100)
    window.setMenuBar(ribbonBar)

    ribbonBar.setObjectName("RibbonBar")

    ribbonBar.setApplicationIcon(QIcon(GetIcon("app")))
    ribbonBar.applicationOptionButton().setToolTip("AstroMesh")

    fileMenu = ribbonBar.applicationOptionButton().addFileMenu()

    # 예제로 들어 있던 Menu #1~#3 자리표시를 최근 목록으로 바꿨다
    fileMenu.addMenu(RECENT_TITLE)

    # 반환값을 안 들고 있는다. 필요할 때 _find_recent_menu() 로 찾는다
    RebuildRecentMenu()

    # 콜백은 여기서 못 건다. 리본은 GL 창보다 먼저 만들어지는데
    # *set_callback 은 GL 창이 있어야 한다. init.tcl 의 program_started 가 건다

    path = os.environ["ASTRO"]

    # HERE start
    # Right toolbar ----------------------------
    # Restart
    rbutton01 = QToolButton()
    rbutton01.setText("Restart")
    ribbonBar.addRightToolButton(rbutton01)
    rbutton01.setToolTip("종료후 재시작")  
    rbutton01.clicked.connect(Restart)  

    # Todolist
    rbutton02 = QToolButton()
    rbutton02.setText("Todolist")
    ribbonBar.addRightToolButton(rbutton02)
    rbutton02.setToolTip("해야할일 목록")  
    rbutton02.clicked.connect(Todolist)  


    # Quick Button File
    qbtn_file = QToolButton()
    qbtn_file.setText("File")
    qbtn_file.setToolTip("파일 관리")
    qbtn_file.setStyleSheet("QToolButton::menu-indicator { image: none; }")
    ribbonBar.addQuickAccessButton(qbtn_file)
    fileMenu = QMenu(qbtn_file)
    #--
    actionOpen = fileMenu.addAction("Open")
    actionOpen.triggered.connect(OnOpenFile)
    #
    actionClose = fileMenu.addAction("Save")
    #actionClose.triggered.connect(OnTclCmd)
    #
    actionClose = fileMenu.addAction("Import")
    #actionClose.triggered.connect(OnTclCmd)
    #
    actionClose = fileMenu.addAction("Export")
    #actionClose.triggered.connect(OnTclCmd)
    #
    actionClose = fileMenu.addAction("Export")
    #actionClose.triggered.connect(OnTclCmd)
    #--

    qbtn_file.setMenu(fileMenu)
    qbtn_file.setPopupMode(QToolButton.InstantPopup)


    #quick Button
    qbutton = QToolButton()
    qbutton.setText("Quick Button")
    ribbonBar.addQuickAccessButton(qbutton)
    qbutton.setToolTip("Button 시험")  
    qbutton.clicked.connect(OnTclCmd)  



    #quick Button
    qbutton = QToolButton()
    qbutton.setText("Quick Button")
    ribbonBar.addQuickAccessButton(qbutton)
    qbutton.setToolTip("Button 시험")  
    qbutton.clicked.connect(OnTclCmd)  

    # HERE end

    homeCategory = ribbonBar.addCategory("File1")

    modelPanel = homeCategory.addPanel("Model", showPanelOptionButton=False)
    b=modelPanel.addSmallButton("Open", icon=QIcon(GetIcon("Open_16x")))
    b.setMaximumIconSize(16)
    b.clicked.connect(OnOpenFile)  # type: ignore

    b=modelPanel.addSmallButton("Save", icon=QIcon(GetIcon("SaveStatusBar8_16x")))
    b.setMaximumIconSize(16)
    b.clicked.connect(OnSaveFile)  # type: ignore

    b=modelPanel.addSmallButton("Import", icon=QIcon(GetIcon("Import_16x")))
    b.setMaximumIconSize(16)
    b.clicked.connect(OnImportFile)  # type: ignore

    b=modelPanel.addSmallButton("Close", icon=QIcon(GetIcon("Close_12x_16x")))
    b.setMaximumIconSize(16)
    b.clicked.connect(OnCloseFile)  # type: ignore

    b=modelPanel.addSmallButton("Export", icon=QIcon(GetIcon("Export_16x")))
    b.setMaximumIconSize(16)
    b.clicked.connect(OnExportFile)  # type: ignore
    #modelPanel.addSeparator().setTopBottomMargins(0,0);
    
    '''
    astro_path = os.environ["ASTRO"]
    pattern = astro_path + "/icons/vs2012/**/*.png"
    files = glob.glob(pattern, recursive=True)
    if len(files) == 0:
        pattern = astro_path + "/../icons/vs2012/**/*.png"
        files = glob.glob(pattern, recursive=True)

    for i in range(0, 5):
        modelPanel = homeCategory.addPanel("Panel #{0}".format(i), showPanelOptionButton=False)

        for j in range(0, 12):
            file = files[randrange(len(files))]
            original = QtGui.QPixmap(file)
            icon = QtGui.QIcon(GetGrayed(original))
            icon.addPixmap(original, QtGui.QIcon.Normal, QtGui.QIcon.On)

            b=modelPanel.addSmallButton("name", icon)
            b.setMaximumIconSize(16)
            b.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
    '''

    viewCategory = ribbonBar.addCategory("View")

    consolePanel = viewCategory.addPanel("Console", showPanelOptionButton=False)
    b=consolePanel.addLargeButton("Tcl", icon=QIcon(GetIcon("Tcl")))
    b.clicked.connect(OnToggleTclConsole)  # type: ignore
    b.setIconSize(QSize(16, 16))
    b.setMaximumIconSize(32)

    #b.setToolButtonStyle(Qt.ToolButtonIconOnly)
    b=consolePanel.addLargeButton("Python", icon=QIcon(GetIcon("python")))
    b.clicked.connect(OnTogglePythonConsole)  # type: ignore
    b.setIconSize(QSize(16, 16))
    b.setMaximumIconSize(32)
    #b.setFixedWidth(80)
    #b.setToolButtonStyle(Qt.ToolButtonIconOnly)
    
    #b.setToolButtonStyle(Qt.ToolButtonIconOnly)
    b=consolePanel.addLargeButton("Embed\nPython", icon=QIcon(GetIcon("embedpython")))
    b.clicked.connect(OnToggleEmbedPythonConsole)  # type: ignore
    b.setIconSize(QSize(16, 16))
    b.setMaximumIconSize(16)
    #b.setFixedWidth(80)
    #b.setToolButtonStyle(Qt.ToolButtonIconOnly)
    
    displayPanel = viewCategory.addPanel("Display", showPanelOptionButton=False)

    # 아이콘은 모델 브라우저의 Loads 갈래와 같은 것을 쓴다. 같은 것을 켜고
    # 끄는 자리라 그림도 같아야 한다 (keyword/radioss/browser.txt 의 GROUP Loads)
    b=displayPanel.addSmallButton("Load Symbols",
            icon=QIcon(":/res/browser/browserForce-16.png"),
            checkable=True, tooltip="Show or hide load symbols")
    b.setChecked(True)
    b.clicked.connect(OnToggleLoadSymbol)  # type: ignore
    b.setMaximumIconSize(16)

    panel = viewCategory.addPanel("Assistant", showPanelOptionButton=False)
    b=panel.addLargeButton("Copilot", icon=QIcon(GetIcon("chatbot")))
    b.clicked.connect(OnToggleCopilot)  # type: ignore
    b.setIconSize(QSize(16, 16))
    b.setMaximumIconSize(32)

    #-- seletct current category
    ribbonBar.setCurrentCategory(viewCategory)


'''
try:
    ...
except Exception as e:
    print(str("Error: ") + str(e) + "\n")
    QMessageBox.critical(None, "Error", str(e))
'''
