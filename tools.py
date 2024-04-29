from maya import cmds
from .control import Control
import os
import json


def undo(fun):
    """
    ctrl+z withdraw all method operation at once
    The default structure of a decorator is a function that contains a nested function
    The values passed when calling functions which modified by decorator
    The nested function will first receive the input value in (*args, **kwargs)
    """
    def undo_fun(*args, **kwargs):
        #open undo record
        cmds.undoInfo(openChunk=1)
        #save current selected object
        long_name = cmds.ls(sl=1, l=1)
        #call input function
        fun(*args, **kwargs)
        #keep selection
        cmds.select(cmds.ls(long_name))
        #close undo record
        cmds.undoInfo(closeChunk=1)

    return undo_fun

def set_selected_controls(*args, **kwargs):
    # get selected node or joint
    controls = cmds.ls(sl=1, l=1, type=["joint", "transform"])
    for ctrl in controls:
        # args receive all reserved attributes such as "color", "radius"
        # get reserved attributes and renew to kwargs
        kwargs.update({key: getattr(Control(ctrl), "get_" + key)() for key in args})
        # set kwargs attributes
        Control(ctrl, **kwargs)
    cmds.dgdirty(controls)

@undo
def set_color(color):
    set_selected_controls(color=color)

@undo
def load_control(shape):
    cmds.ls(sl=1, l=1, type=["joint", "transform"]) or cmds.group(em=1, n=shape)
    set_selected_controls("color", "outputs", "radius", shape=shape)

@undo
def upload_control():
    # get controller data path
    data_path = os.path.abspath(__file__ + "/../data")
    # if path nonexistence，create path
    if not os.path.isdir(data_path):
        os.makedirs(data_path)

    for ctrl in cmds.ls(sl=1, l=1, type=["joint", "transform"]):
        ctrl = Control(ctrl)
        # get controller jason path from name
        data_file = os.path.join(data_path, ctrl.get_name()+".json")
        # write shape data to json file
        with open(data_file, "w") as fp:
            json.dump(ctrl.get_shape(), fp, indent=4)

        # hide viewport display
        for hud in cmds.headsUpDisplay(lh=1):
            cmds.headsUpDisplay(hud, e=1, vis=False)
        # copy viewport
        panel = "control_model_panel"
        if not cmds.modelPanel(panel, ex=1):
            cmds.modelPanel(panel, tearOff=True, toc=1)
        # set viewport only display curve
        cmds.modelEditor(panel, e=1, alo=0, nc=1, gr=False)
        # set active viewport
        cmds.setFocus(panel)

        # create temp controller
        temp = Control()
        # set temp controller shape to selected controller shape
        temp.set_shape(ctrl.get_shape())
        # select controller
        cmds.select(temp.get_transform())

        # set camera rotation
        cmds.setAttr("persp.r", -27.938, 45, 0)
        # focuses selected controller
        cmds.viewFit("persp", an=0)
        # isolate display selection
        cmds.isolateSelect(panel, state=1)
        cmds.isolateSelect(panel, addSelected=1)

        # screenshot one frame, save as jpg file
        jpg_path = os.path.join(data_path, ctrl.get_name())
        file_name = cmds.playblast(fmt="image", f=jpg_path, c="jpg",
                                   wh=[128, 128], st=0, et=0, viewer=False,
                                   percent=100, quality=100, fp=1)

        # modify picture name
        src_path = file_name.replace("#", "0")
        dst_path = file_name.replace("#.", "").replace("#", "")
        if os.path.isfile(src_path):
            # 如果存在旧图片,则删除
            if os.path.isfile(dst_path):
                os.remove(dst_path)
            os.rename(src_path, dst_path)

        # if screenshot viewport exist, delete it
        if cmds.modelPanel(panel, ex=1):
            cmds.deleteUI(panel, panel=True)
        # delete temp controller
        cmds.delete(temp.get_transform())

@undo
def delete_controls(shapes):
    for s in shapes:
        # check json file existence and delete
        path = os.path.abspath(__file__ + "/../data/{s}.json".format(s=s))
        if os.path.isfile(path):
            os.remove(path)
        # check relative jpg file existence and delete
        path = os.path.abspath(__file__ + "/../data/{s}.jpg".format(s=s))
        if os.path.isfile(path):
            os.remove(path)

@undo
def scale_control():
    set_selected_controls(radius=cmds.softSelect(q=1, ssd=1))

@undo
def mirror_control():
    controls = cmds.ls(sl=1, l=1, type=["joint", "transform"])
    if len(controls) != 2:
        return
    src, dst = controls

    def mirror_callback(copy_ctrl):
        Control(copy_ctrl, shape=Control(src).get_shape())
        cmds.xform(copy_ctrl, ws=1, m=cmds.xform(src, ws=1, q=1, m=1))
        cmds.makeIdentity(copy_ctrl, apply=1, t=1, r=1, s=1)
        cmds.xform(copy_ctrl, piv=[0, 0, 0])
        cmds.setAttr(copy_ctrl + ".sx", -1)
        cmds.makeIdentity(copy_ctrl, apply=1, t=1, r=1, s=1)
        cmds.xform(copy_ctrl, piv=[0, 0, 0])
        cmds.parent(copy_ctrl, dst)

    Control(dst).edit_shape_by_copy_ctrl(mirror_callback)

@undo
def replace_control():
    controls = cmds.ls(sl=1, l=1, type=["joint", "transform"])
    if controls:
        set_selected_controls("color", "outputs", shape=Control(controls[-1]).get_shape())

@undo
def freeze_control():
    controls = cmds.ls(sl=1, l=1, type=["joint", "transform"])
    for ctrl in controls:
        Control(ctrl).edit_shape_by_copy_ctrl(lambda copy_ctrl:
                                              cmds.xform(copy_ctrl, m=cmds.xform(ctrl, q=1, m=1)))
        cmds.xform(ctrl, ws=0, m=[1, 0, 0, 0,
                                  0, 1, 0, 0,
                                  0, 0, 1, 0,
                                  0, 0, 0, 1])