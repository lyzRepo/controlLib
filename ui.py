# coding=utf-8
from . import tools
import os
try:
    from PySide.QtGui import *
    from PySide.QtCore import *
except ImportError:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *


class ShapeList(QListWidget):
    # controller list
    def __init__(self):
        QListWidget .__init__(self)
        # set to logo mode
        self.setViewMode(self.IconMode)
        # banned movement
        self.setMovement(self.Static)
        # Hide horizontal scroll bar, display vertical scroll bar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # set controller icon size
        self.setIconSize(QSize(64, 64))
        # open refresh layout
        self.setResizeMode(self.Adjust)
        # enable multi selection
        self.setSelectionMode(self.ExtendedSelection)
        # double click event
        self.itemDoubleClicked.connect(lambda x: tools.load_control(x.name))
        # update elements
        self.update_shapes()

    def update_shapes(self):
        # clear original menu
        self.clear()
        # get data folder path
        data_dir = os.path.abspath(__file__ + "/../data/")
        # loop data folder item
        for file_name in os.listdir(data_dir):
            # escape non-jpg file
            if not file_name.endswith(".jpg"):
                continue
            # get icon path
            jpg_file = os.path.join(data_dir, file_name)
            # build icon
            item = QListWidgetItem(QIcon(jpg_file), "", self)
            # record file name
            name, _ = os.path.splitext(file_name)
            item.name = name
            # set icon size
            item.setSizeHint(QSize(67, 67))

    def contextMenuEvent(self, event):
        QListWidget.contextMenuEvent(self, event)
        # build right click menu
        menu = QMenu(self)
        menu.addAction(u"upload controller", tools.upload_control)
        menu.addAction(u"delete controller", lambda: tools.delete_controls([item.name for item in self.selectedItems()]))
        menu.exec_(event.globalPos())
        self.update_shapes()


index_rgb_map = [
    [0.5, 0.5, 0.5],
    [0, 0, 0],
    [0.247, 0.247, 0.247],
    [0.498, 0.498, 0.498],
    [0.608, 0, 0.157],
    [0, 0.16, 0.376],
    [0, 0, 1],
    [0, 0.275, 0.094],
    [0.149, 0, 0.263],
    [0.78, 0, 0.78],
    [0.537, 0.278, 0.2],
    [0.243, 0.133, 0.121],
    [0.6, 0.145, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0.2549, 0.6],
    [1, 1, 1],
    [1, 1, 0],
    [0.388, 0.863, 1],
    [0.263, 1, 0.639],
    [1, 0.686, 0.686],
    [0.89, 0.674, 0.474],
    [1, 1, 0.388],
    [0, 0.6, 0.329],
    [0.627, 0.411, 0.188],
    [0.619, 0.627, 0.188],
    [0.408, 0.631, 0.188],
    [0.188, 0.631, 0.365],
    [0.188, 0.627, 0.627],
    [0.188, 0.403, 0.627],
    [0.434, 0.188, 0.627],
    [0.627, 0.188, 0.411],
]


class ColorList(QListWidget):
    # color list
    def __init__(self):
        QListWidget .__init__(self)
        # banned horizontal scroll bar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # set to icon mode
        self.setViewMode(self.IconMode)
        # banned movement
        self.setMovement(self.Static)
        # set icon size
        self.setIconSize(QSize(32, 32))
        # open refresh layout
        self.setResizeMode(self.Adjust)
        # lock height
        self.setFixedHeight(35*2.2)
        for i, rgb in enumerate(index_rgb_map):
            # create pure color icon
            pix = QPixmap(32, 16)
            pix.fill(QColor.fromRgbF(*rgb))
            item = QListWidgetItem(QIcon(pix), "", self)
            # set item size, bigger than icon go get some gap
            item.setSizeHint(QSize(35, 17))
        self.itemDoubleClicked.connect(lambda x: tools.set_color(self.indexFromItem(x).row()))


def get_app():
    # get maya menu
    top = QApplication.activeWindow()
    if top is None:
        return
    while True:
        parent = top.parent()
        if parent is None:
            return top
        top = parent


def q_add(layout, *elements):
    for elem in elements:
        if isinstance(elem, QLayout):
            layout.addLayout(elem)
        elif isinstance(elem, QWidget):
            layout.addWidget(elem)
    return layout


def q_button(text, action):
    # create and return button, set button name and click event
    but = QPushButton(text)
    but.clicked.connect(action)
    return but


class ControlsWindow(QDialog):

    def __init__(self):
        QDialog .__init__(self, get_app())
        self.setWindowTitle("controls")
        self.resize(QSize(318, 470))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(10)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(tools.line_with_control)

        sl_label = QLabel("Line With:")
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(sl_label)
        sl_layout.addWidget(self.slider)

        layout = QVBoxLayout()
        layout.addLayout(q_add(
            QVBoxLayout(),
            ShapeList(),
            ColorList(),
            sl_layout,
            q_add(
                QHBoxLayout(),
                q_button(u"scale", tools.scale_control),
                q_button(u"mirror", tools.mirror_control),
                q_button(u"replace", tools.replace_control),
                q_button(u"freeze", tools.freeze_control),
            ),
        ))
        self.setLayout(layout)

        for but in self.findChildren(QPushButton):
            but.setMinimumWidth(20)


window = None


def show():
    global window
    if window is None:
        window = ControlsWindow()
    window.show()


if __name__ == '__main__':
    _app = QApplication([])
    window = ControlsWindow()
    window.show()
    _app.exec_()
