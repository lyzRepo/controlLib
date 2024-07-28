try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
    from shiboken6 import wrapInstance

from . import constraints
from . import tools
import maya.OpenMayaUI as omui
import maya.cmds as cm
import os


def mayaMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mainWindowPtr), QWidget)


def addMultiConponents(layout, items):
    for item in items:
        if isinstance(item, QWidget):
            layout.addWidget(item)
        elif isinstance(item, QLayout):
            layout.addLayout(item)


index_rgb_map = [[0.5, 0.5, 0.5], [0, 0, 0], [0.247, 0.247, 0.247], [0.498, 0.498, 0.498], [0.608, 0, 0.157],
                 [0, 0.16, 0.376], [0, 0, 1], [0, 0.275, 0.094], [0.149, 0, 0.263], [0.78, 0, 0.78],
                 [0.537, 0.278, 0.2], [0.243, 0.133, 0.121], [0.6, 0.145, 0], [1, 0, 0], [0, 1, 0],
                 [0, 0.2549, 0.6], [1, 1, 1], [1, 1, 0], [0.388, 0.863, 1], [0.263, 1, 0.639], [1, 0.686, 0.686],
                 [0.89, 0.674, 0.474], [1, 1, 0.388], [0, 0.6, 0.329], [0.627, 0.411, 0.188], [0.619, 0.627, 0.188],
                 [0.408, 0.631, 0.188], [0.188, 0.631, 0.365], [0.188, 0.627, 0.627], [0.188, 0.403, 0.627],
                 [0.434, 0.188, 0.627], [0.627, 0.188, 0.411]]


class ShapeListWindow(QWidget):
    def __init__(self):
        super(ShapeListWindow, self).__init__()
        self.createWidgets()
        self.createLayout()
        self.createConnections()

    def createWidgets(self):
        self.shapeList = QListWidget()
        self.shapeList.setViewMode(QListWidget.IconMode)
        self.shapeList.setMovement(QListWidget.Static)
        self.shapeList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.shapeList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.shapeList.setIconSize(QSize(64, 64))
        self.shapeList.setResizeMode(QListWidget.Adjust)
        self.shapeList.setSelectionMode(QListWidget.ExtendedSelection)
        self.shapeList.itemDoubleClicked.connect(lambda x: tools.load_control(x.name))
        self.updateShapes()

        self.colorList = QListWidget()
        self.colorList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.colorList.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.colorList.setViewMode(QListWidget.IconMode)
        self.colorList.setMovement(QListWidget.Static)
        self.colorList.setIconSize(QSize(32, 32))
        self.colorList.setResizeMode(QListWidget.Adjust)
        self.colorList.setFixedHeight(35 * 2.2)
        self.updateColors()

        self.curWithSld = QSlider(Qt.Horizontal)
        self.curWithSld.setMinimum(1)
        self.curWithSld.setMaximum(10)
        self.curWithSld.setValue(1)

        self.scaleBtn = QPushButton("scale")
        self.mirrorBtn = QPushButton("mirror")
        self.replaceBtn = QPushButton("replace")
        self.freezeBtn = QPushButton("freeze")

    def createLayout(self):
        self.btnLayout = QHBoxLayout()
        addMultiConponents(self.btnLayout, [self.scaleBtn, self.mirrorBtn, self.replaceBtn, self.freezeBtn])

        self.sldLayout = QFormLayout()
        self.sldLayout.addRow("Line Width:", self.curWithSld)

        self.mainLayout = QVBoxLayout()
        addMultiConponents(self.mainLayout, [self.shapeList, self.colorList, self.sldLayout, self.btnLayout])

        self.setLayout(self.mainLayout)

    def createConnections(self):
        self.shapeList.itemDoubleClicked.connect(lambda x: tools.load_control(x.name))
        self.colorList.itemDoubleClicked.connect(lambda x: tools.set_color(self.colorList.indexFromItem(x).row()))
        self.curWithSld.valueChanged.connect(tools.line_with_control)
        self.scaleBtn.clicked.connect(tools.scale_control)
        self.mirrorBtn.clicked.connect(tools.mirror_control)
        self.replaceBtn.clicked.connect(tools.replace_control)
        self.freezeBtn.clicked.connect(tools.freeze_control)

    def updateShapes(self):
        # clear original menu
        self.shapeList.clear()
        # get data folder path
        data_dir = os.path.abspath(__file__ + "/../data/")
        # loop data folder item
        for file_name in os.listdir(data_dir):
            if not file_name.endswith(".jpg"):
                continue
            jpg_file = os.path.join(data_dir, file_name)
            item = QListWidgetItem(QIcon(jpg_file), "", self.shapeList)
            name, _ = os.path.splitext(file_name)
            item.name = name
            item.setSizeHint(QSize(67, 67))

    def updateColors(self):
        for rgb in index_rgb_map:
            pix = QPixmap(32, 16)
            pix.fill(QColor.fromRgbF(*rgb))
            item = QListWidgetItem(QIcon(pix), "", self.colorList)
            item.setSizeHint(QSize(35, 17))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(u"upload controller", tools.upload_control)
        menu.addAction(u"delete controller",
                       lambda: tools.delete_controls([item.name for item in self.shapeList.selectedItems()]))
        menu.exec_(event.globalPos())
        self.updateShapes()


class ConstraintsWindow(QWidget):
    def __init__(self):
        super(ConstraintsWindow, self).__init__()

        self.createWidgets()
        self.createLayout()
        self.createConnections()

    def createWidgets(self):
        self.rnPrefixLe = QLineEdit()
        self.rnTypeLe = QLineEdit()
        self.reNameBtn = QPushButton("Apply")

        self.ctrlSizeSld = QSlider(Qt.Horizontal)
        self.ctrlSizeSld.setMinimum(1)
        self.ctrlSizeSld.setMaximum(10)
        self.ctrlSizeSld.setValue(1)
        self.drvGrpCb = QCheckBox("DriGroup")
        self.makeHieraCb = QCheckBox("Hierarchy")
        self.parentCb = QCheckBox("Parent")
        self.singleCb = QCheckBox("Single")
        self.ctrlCreateBtn = QPushButton("Apply")

        self.polVecJontLe = QLineEdit()
        self.polVecIkhLe = QLineEdit()
        self.polVecXLe = QSpinBox()
        self.polVecXLe.setFixedWidth(50)
        self.polVecXLe.setRange(-100, 100)
        self.polVecYLe = QSpinBox()
        self.polVecYLe.setFixedWidth(50)
        self.polVecYLe.setRange(-100, 100)
        self.polVecZLe = QSpinBox()
        self.polVecZLe.setFixedWidth(50)
        self.polVecZLe.setRange(-100, 100)
        self.polVecBtn = QPushButton("Apply")

        self.curGenLe = QLineEdit()
        self.curGenSb = QSpinBox()
        self.curGenSb.setFixedWidth(60)
        self.curGenLocCb = QRadioButton("Locator")
        self.curGenJotCb = QRadioButton("Joint")
        self.curGenCluCb = QRadioButton("Cluster")
        self.curGenApplyBtn = QPushButton("Apply")

    def createLayout(self):
        self.renameBtnLayout = QHBoxLayout()
        self.renameBtnLayout.addStretch()
        self.renameBtnLayout.addWidget(self.reNameBtn)
        self.renameFormLayout = QFormLayout()
        self.renameFormLayout.addRow("Prefix:", self.rnPrefixLe)
        self.renameFormLayout.addRow("Type:", self.rnTypeLe)
        self.renameFormLayout.addRow("", self.renameBtnLayout)
        self.rNGroupBox = QGroupBox("Renamer")
        self.rNGroupBox.setFixedWidth(330)
        self.rNGroupBox.setLayout(self.renameFormLayout)

        self.cCCbLayout = QHBoxLayout()
        addMultiConponents(self.cCCbLayout, [self.drvGrpCb, self.makeHieraCb, self.parentCb, self.singleCb])

        self.cCBtnLayout = QHBoxLayout()
        self.cCBtnLayout.addStretch()
        self.cCBtnLayout.addWidget(self.ctrlCreateBtn)
        self.cCFormLayout = QFormLayout()
        self.cCFormLayout.addRow("Ctrl Size:", self.ctrlSizeSld)
        self.cCFormLayout.addRow("", self.cCCbLayout)
        self.cCFormLayout.addRow("", self.cCBtnLayout)
        self.cCGroupBox = QGroupBox("Ctrl Create")
        self.cCGroupBox.setFixedWidth(330)
        self.cCGroupBox.setLayout(self.cCFormLayout)

        self.polVecXLayout = QHBoxLayout()
        self.polVecXLayout.addStretch()
        self.polVecXLayout.addWidget(QLabel("X:"))
        self.polVecXLayout.addWidget(self.polVecXLe)

        self.polVecYLayout = QHBoxLayout()
        self.polVecYLayout.addStretch()
        self.polVecYLayout.addWidget(QLabel("Y:"))
        self.polVecYLayout.addWidget(self.polVecYLe)

        self.polVecZLayout = QHBoxLayout()
        self.polVecZLayout.addStretch()
        self.polVecZLayout.addWidget(QLabel("Z:"))
        self.polVecZLayout.addWidget(self.polVecZLe)

        self.polVecAxisLayout = QHBoxLayout()
        addMultiConponents(self.polVecAxisLayout, [self.polVecXLayout, self.polVecYLayout, self.polVecZLayout])
        self.polVecAxisLayout.addStretch()

        self.polVecApllyLayout = QHBoxLayout()
        self.polVecApllyLayout.addStretch()
        self.polVecApllyLayout.addWidget(self.polVecBtn)
        self.polVecFormLayout = QFormLayout()
        self.polVecFormLayout.addRow("Joint:", self.polVecJontLe)
        self.polVecFormLayout.addRow("IkHandle:", self.polVecIkhLe)
        self.polVecFormLayout.addRow("Offset:", self.polVecAxisLayout)
        self.polVecFormLayout.addRow("", self.polVecApllyLayout)
        self.polVecGroupBox = QGroupBox("Poler Vector")
        self.polVecGroupBox.setFixedWidth(330)
        self.polVecGroupBox.setLayout(self.polVecFormLayout)

        self.curGenCbLayout = QHBoxLayout()
        addMultiConponents(self.curGenCbLayout, [self.curGenLocCb, self.curGenJotCb, self.curGenCluCb])
        self.curGenBtnLayout = QHBoxLayout()
        self.curGenBtnLayout.addStretch()
        self.curGenBtnLayout.addWidget(self.curGenApplyBtn)
        self.curGenFormLayout = QFormLayout()
        self.curGenFormLayout.addRow("Input Curve:", self.curGenLe)
        self.curGenFormLayout.addRow("Index:", self.curGenSb)
        self.curGenFormLayout.addRow("Type:", self.curGenCbLayout)
        self.curGenFormLayout.addRow("", self.curGenBtnLayout)

        self.curGenGroupBox = QGroupBox("Generate by Curve")
        self.curGenGroupBox.setFixedWidth(330)
        self.curGenGroupBox.setLayout(self.curGenFormLayout)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.rNGroupBox)
        self.mainLayout.addWidget(self.cCGroupBox)
        self.mainLayout.addWidget(self.polVecGroupBox)
        self.mainLayout.addWidget(self.curGenGroupBox)

        self.scrollWidget = QWidget()
        self.scrollWidget.setLayout(self.mainLayout)

        self.scrollArea = QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        self.scrollLayout = QVBoxLayout()
        self.scrollLayout.addWidget(self.scrollArea)
        self.setLayout(self.scrollLayout)

    def createConnections(self):
        self.reNameBtn.clicked.connect(self.reNameApply)
        self.ctrlCreateBtn.clicked.connect(self.ctrlCreateApply)
        self.polVecBtn.clicked.connect(self.polerVecApply)
        self.curGenApplyBtn.clicked.connect(self.curGenerateApply)

    def reNameApply(self):
        prefix = self.rnPrefixLe.text()
        typ = self.rnTypeLe.text()
        tools.renamer(prefix=prefix, typ=typ)

    def ctrlCreateApply(self):
        size = self.ctrlSizeSld.value()
        drvGrp = self.drvGrpCb.isChecked()
        makeHiera = self.makeHieraCb.isChecked()
        parent = self.parentCb.isChecked()
        single = self.singleCb.isChecked()
        tools.creat_ctrl(size=size, drvGrp=drvGrp, makeHiera=makeHiera,
                         parent=parent, single=single)

    def polerVecApply(self):
        offsetX = self.polVecXLe.value()
        offsetY = self.polVecYLe.value()
        offsetZ = self.polVecZLe.value()
        joint = self.polVecJontLe.text()
        ikHandle = self.polVecIkhLe.text()
        tools.creat_polerVec(offset=[offsetX, offsetY, offsetZ], joint=joint, ikh=ikHandle)

    def curGenerateApply(self):
        curveTarget = self.curGenLe.text()
        index = self.curGenSb.value()
        if not curveTarget:
            return
        if self.curGenJotCb.isChecked():
            tools.creat_curJnt(cur=curveTarget, jointIndex=index)
        elif self.curGenLocCb.isChecked():
            tools.creat_curLoc(cur=curveTarget, locIndex=index)
        elif self.curGenCluCb.isChecked():
            tools.creat_curClu(cur=curveTarget)


class MainWindow(QDialog):
    def __init__(self, parent=mayaMainWindow()):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("ZzControlLib")
        self.resize(QSize(380, 470))

        self.createWidgets()
        self.createLayout()

    def createWidgets(self):
        self.tabWidget = QTabWidget()

        self.shapeListPage = ShapeListWindow()
        self.ConstraintsPage = ConstraintsWindow()
        self.tabWidget.addTab(self.shapeListPage, "Shape List")
        self.tabWidget.addTab(self.ConstraintsPage, "Constraints")

    def createLayout(self):
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.tabWidget)
        self.setLayout(self.mainLayout)


