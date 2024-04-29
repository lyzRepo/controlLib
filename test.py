from importlib import  reload
from . import ui
from . import control
reload(control)
reload(ui)

def test_ui():
    ui.show()

def test():
    pass

