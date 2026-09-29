#===========================================================================================
# todolist.tcl 을 Python(qtpy) 으로 옮긴 것. 기능과 이름은 tcl 판과 같다.
#
# Qt 위젯이라 따로 색을 주지 않아도 AstroWorks 의 현재 테마를 따른다.
# 할 일 파일은 tcl 판과 같은 _ikjoong/to_do_list.txt 를 쓴다. tcl 판은 이 파일을
# 찾으려고 cd 로 프로그램 작업 폴더를 바꿨지만, 여기서는 절대 경로를 쓴다.
#===========================================================================================
import os

from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QPlainTextEdit,
                            QPushButton, QVBoxLayout, QWidget)

_HERE = os.path.dirname(os.path.abspath(__file__))

# 창을 들고 있어야 가비지 컬렉터가 닫지 않는다 (tcl 의 .texteditor 자리)
w = None


def _read_text(path):
    # tcl 판이 시스템 인코딩(cp949)으로 저장했을 수 있어 utf-8 이 안 되면 cp949 로 읽는다
    for enc in ("utf-8", "cp949"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(), enc
        except UnicodeDecodeError:
            pass
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), "utf-8"


class TextEditor(QWidget):
    def __init__(self, target_file, parent=None):
        super().__init__(parent, Qt.Window)
        self.target_file = target_file
        self.filename = target_file
        self.encoding = "utf-8"
        #---
        todolist = ""
        if not os.path.exists(target_file):
            open(target_file, "w").close()
        else:
            todolist, self.encoding = _read_text(target_file)
        #---
        self.setWindowTitle("To do list")
        self.resize(500, 400)
        self._center_on(parent)
        #-----------------------
        self.edit1 = QPlainTextEdit()
        self.edit1.setFont(QFont("Courier New", 12))
        self.edit1.setPlainText(todolist)
        #
        btn1 = QPushButton("Save")
        btn1.clicked.connect(self.SaveFile)
        #btn2 = QPushButton("Clear")
        #btn2.clicked.connect(self.ClearEdit)
        btn3 = QPushButton("Exit")
        btn3.clicked.connect(self.QuitFile)
        #
        mb = QHBoxLayout()
        mb.addWidget(btn1)
        #mb.addWidget(btn2)
        mb.addWidget(btn3)
        mb.addStretch(1)
        #-- 버튼 줄은 맨 아래
        layout = QVBoxLayout(self)
        layout.addWidget(self.edit1, 1)
        layout.addLayout(mb)

    #--------------------------------------------------------
    def _center_on(self, parent):
        # AstroMesh 본창 가운데에 띄운다. 본창이 없으면 화면 가운데
        if parent is not None:
            center = parent.frameGeometry().center()
        else:
            center = QApplication.primaryScreen().availableGeometry().center()
        rect = self.frameGeometry()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    #--------------------------------------------------------
    def NewFile(self):
        self.edit1.clear()
        self.filename = "New"
        self.setWindowTitle(f"EDIT: {self.filename}")

    #--------------------------------------------------------
    def LoadFile(self):
        fn = self.GetFileName()
        if not fn:
            return
        text, self.encoding = _read_text(fn)
        self.ClearEdit()
        self.edit1.setPlainText(text)
        self.filename = fn
        self.setWindowTitle(f"EDIT : {self.filename}")

    #--------------------------------------------------------
    def _write(self, path):
        # tcl 판은 저장할 때마다 끝에 빈 줄이 하나씩 늘었다. 여기서는 끝 줄바꿈을 하나만 둔다
        text = self.edit1.toPlainText()
        if not text.endswith("\n"):
            text += "\n"
        with open(path, "w", encoding=self.encoding) as f:
            f.write(text)

    def SaveFile(self):
        self._write(self.target_file)

    #--------------------------------------------------------
    def SaveAsFile(self):
        fn = self.GetFileName()
        if not fn:
            return
        self._write(fn)
        self.filename = fn
        self.setWindowTitle(f"EDIT : {self.filename}")

    #--------------------------------------------------------
    def QuitFile(self):
        self.close()

    #--------------------------------------------------------
    def ClearEdit(self):
        self.edit1.clear()

    #--------------------------------------------------------
    def GetFileName(self):
        types = ";;".join([
            "Text Files (*.txt)",
            "TCL Scripts (*.tcl)",
            "C Source Files (*.c)",
            "GIF Files (*.gif)",
            "All Files (*)",
        ])
        fn, _ = QFileDialog.getOpenFileName(self, "", "", types)
        return fn


#===========================================================================================
def cmd_texteditor(tfile=""):
    global w
    #---
    target_file = tfile or os.path.join(_HERE, "to_do_list.txt")
    #--- 이미 떠 있으면 닫고 새로 연다 (tcl 판의 winfo exists / destroy 와 같다)
    # 모듈을 다시 읽으면 전역 w 가 비므로 창 이름으로 찾는다
    for old in QApplication.topLevelWidgets():
        if old.objectName() == "texteditor":
            old.close()
    #---
    parent = None
    try:
        from astro import ui
        parent = ui.find_main_window()
    except Exception:
        pass
    #---
    w = TextEditor(target_file, parent)
    w.setObjectName("texteditor")
    w.setAttribute(Qt.WA_DeleteOnClose)
    w.show()
    return w


#--------------------------------
if __name__ == "__main__":
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    cmd_texteditor()
    sys.exit(app.exec_())
