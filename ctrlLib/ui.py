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
    # 控制器列表
    def __init__(self):
        QListWidget .__init__(self)
        # 设置为图标模式
        self.setViewMode(self.IconMode)
        # 设置禁止移动
        self.setMovement(self.Static)
        # 隐藏横向滑条，显示竖向滑条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 设置图标尺寸
        self.setIconSize(QSize(64, 64))
        # 设置图标排列实施更新
        self.setResizeMode(self.Adjust)
        # 设置选择模式，可以多选
        self.setSelectionMode(self.ExtendedSelection)
        # 双击事件
        self.itemDoubleClicked.connect(lambda x: tools.load_control(x.name))
        # 更新组件
        self.update_shapes()

    def update_shapes(self):
        # 清空原有组件
        self.clear()
        # __file__为当前代码文件路径
        # 通过相对路径获取控制器图标路径
        data_dir = os.path.abspath(__file__ + "/../data/")
        # 遍历文件夹下的文件
        for file_name in os.listdir(data_dir):
            # 过滤掉非图片
            if not file_name.endswith(".jpg"):
                continue
            # 获取图标路径
            jpg_file = os.path.join(data_dir, file_name)
            # 创建item
            item = QListWidgetItem(QIcon(jpg_file), "", self)
            # 记录文件名
            name, _ = os.path.splitext(file_name)
            item.name = name
            # 设置item尺寸
            item.setSizeHint(QSize(67, 67))

    def contextMenuEvent(self, event):
        QListWidget.contextMenuEvent(self, event)
        # 创建右键菜单
        menu = QMenu(self)
        menu.addAction(u"上传控制器", tools.upload_control)
        menu.addAction(u"删除控制器", lambda: tools.delete_controls([item.name for item in self.selectedItems()]))
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
    # 颜色列表
    def __init__(self):
        QListWidget .__init__(self)
        # 关闭横纵向滑条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 设置列表组件为图标模式
        self.setViewMode(self.IconMode)
        # 设置禁止移动
        self.setMovement(self.Static)
        # 设置图标尺寸
        self.setIconSize(QSize(32, 32))
        # 设置图标排列实施更新
        self.setResizeMode(self.Adjust)
        # 锁定高度
        self.setFixedHeight(35*4)
        for i, rgb in enumerate(index_rgb_map):
            # 生成纯色图标
            pix = QPixmap(32, 32)
            pix.fill(QColor.fromRgbF(*rgb))
            item = QListWidgetItem(QIcon(pix), "", self)
            # 设置item尺寸，item尺寸比图标大，图标之间才会有间距
            item.setSizeHint(QSize(35, 34))
        self.itemDoubleClicked.connect(lambda x: tools.set_color(self.indexFromItem(x).row()))


def get_app():
    # 获取maya主窗口
    top = QApplication.activeWindow()
    if top is None:
        return
    while True:
        parent = top.parent()
        if parent is None:
            return top
        top = parent


def q_add(layout, *elements):
    # 自动判断元素element是布局还是组件，添加到布局layout中
    for elem in elements:
        if isinstance(elem, QLayout):
            layout.addLayout(elem)
        elif isinstance(elem, QWidget):
            layout.addWidget(elem)
    return layout


def q_button(text, action):
    # 创建并返回按钮，设置按钮名称和点击事件
    but = QPushButton(text)
    but.clicked.connect(action)
    return but


class ControlsWindow(QDialog):

    def __init__(self):
        QDialog .__init__(self, get_app())
        self.setWindowTitle("controls")
        self.resize(QSize(307, 472))
        self.setLayout(q_add(
            QVBoxLayout(),
            ShapeList(),
            ColorList(),
            q_add(
                QHBoxLayout(),
                q_button(u"缩放", tools.scale_control),
                q_button(u"镜像", tools.mirror_control),
                q_button(u"替换", tools.replace_control),
                q_button(u"冻结", tools.freeze_control),
            ),
        ))
        for but in self.findChildren(QPushButton):
            but.setMinimumWidth(20)


window = None


def show():
    u"""
    显示界面:
    """
    global window
    if window is None:
        window = ControlsWindow()
    window.show()


if __name__ == '__main__':
    _app = QApplication([])
    window = ControlsWindow()
    window.show()
    _app.exec_()
