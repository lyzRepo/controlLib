import json
import os.path

from maya import cmds
from maya.api.OpenMaya import *

def api_ls(*names):
    selection_list = MSelectionList()
    for name in names:
        selection_list.add(name)
    return selection_list


class Control(object):
    """
    Control param list
    :param: -t -transform string/Control            object
    :param: -n -name string                         name
    :param: -p -parent string/node                  parent
    :param: -s -shape data/name                     shape node
    :param: -c -color int                           color
    :param: -r -radius float                        radius/size
    :param: -ro -rotate [float, float,float]        rotation
    :param: -o -offset [float, float,float]         translation
    :param: -l -locked [str, ...]                   lock attribute
    :parma: -ou -outputs [str, str]                 output attribute
    """
    def __init__(self, *args, **kwargs):
        self.uuid = None
        keys = [("t", "transform"), ("n", "name"), ("p", "parent"), ("s", "shape"),
                ("c", "color"), ("r", "radius"), ("ro", "rotate"),
                ("o", "offset"), ("l", "locked"), ("ou", "outputs")]

        # try to get value from long, short, index words
        for index,(short, long) in enumerate(keys):
            arg = kwargs.get(long, None)
            if arg is None:
                arg = kwargs.get(short, None)
            if arg is None and index < len(args):
                arg = args[index]

            # get value, and run relative function to save
            if arg is not None:
                getattr(self, "set_" + long)(arg)

    def set_transform(self, transform):
        # get control uuid
        uuids = cmds.ls(transform, type=["transform", "joint"], o=1, uid=1)
        # if there is more or zero uuid, find operation failed, return to end method
        if len(uuids) != 1:
            return
        self.uuid = uuids[0]
        return self

    def get_transform(self):
        transforms = cmds.ls(self.uuid, l=1)
        # get transform node long name through uuid
        if len(transforms) == 1:
            return transforms[0]
        # if there is more or zero transform node founded, create empty group
        else:
            self.set_transform(cmds.group(em=1, n="control"))
            return self.get_transform()

    def set_parent(self, parent):
        # set parent object
        cmds.parent(self.get_transform(), parent)
        # transformation reset
        cmds.xform(self.get_transform(), ws=0, m=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
        return self

    def get_parent(self):
        # if no parent object, listRelative return None, so parent will be [None]
        parent = cmds.listRelatives(self.get_transform(), p=1, f=1) or [None]
        return parent[0]

    def set_name(self, name):
        # rename
        cmds.rename(self.get_transform(), name)
        return self

    def get_name(self):
        # remove space prefix to get short name
        return self.get_transform().split("|")[-1].split(":")[-1]

    def set_color(self, color):
        # set shape node override color
        for shape in self.get_shapelist():
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + ".overrideColor", color)

    def get_color(self):
        # if overrideEnabled set to True, return color
        for shape in self.get_shapelist():
            if cmds.setAttr(shape + ".overrideEnabled"):
                return cmds.getAttr(shape + ".overrideColor")

    def get_shapelist(self):
        #get all shape node under transform node that type is nurbsCurve
        shapes = cmds.listRelatives(self.get_transform(), s=True, f=True) or []
        return [shape for shape in shapes if cmds.nodeType(shape) == "nurbsCurve"]

    def set_shape(self, shape):
        # delete original shape node
        if self.get_shapelist():
            cmds.delete(self.get_shapelist())

        # if shape is string. read relative json file
        if not isinstance(shape, list):
            data_file = os.path.abspath(__file__ + "/../data/{shape}.json".format(shape=shape))
            if os.path.isfile(data_file):
                with open(data_file, "r") as fp:
                    shape = json.load(fp)
            else:
                shape=[]

        # if shape is a list, means returned from get_shape
        for data in shape:
            # turn points from one-dimensional list to float3 list
            points = data["points"]
            points = [points[i:i+3] for i in range(0, len(points), 3)]

            # if shape is closed
            # get "degree" number points and move to the end of list
            if data["periodic"]:
                points = points +points[:data["degree"]]

            # create temp curve and parent to the transform node
            # delete temp curve after in the end
            curve = cmds.curve(degree=data["degree"], knot=data["knot"], periodic=data["periodic"], p=points)
            cmds.parent(cmds.listRelatives(curve, s=1, f=1), self.get_transform(), s=1, add=1)
            cmds.delete(curve)

        # rename shape node name
        for shape in self.get_shapelist():
            cmds.rename(shape, self.get_name()+"Shape")
        return self

    def get_shape(self):
        # get all shape node in for loop
        return [dict(
            points=cmds.xform(shape + ".cv[*]", q=1, t=1, ws=0),            #point position
            periodic=cmds.getAttr(shape + ".form") == 2,                    #whether periodic
            degree=cmds.getAttr(shape + ".degree"),                         #curve degree
            knot=list(MFnNurbsCurve(api_ls(shape).getDagPath(0)).knots()),  #curve knots
        ) for shape in self.get_shapelist()]

    def set_locked(self, locked):
        # if input s, transfer it to sx, sy, sz
        trs_xyz_map = {trs: [trs+xyz for xyz in "xyz"] for trs in "trs"}

        # return relative dic key's value, use sum to create new list
        locked = sum([trs_xyz_map.get(attr, [attr]) for attr in locked], [])

        #Avoid manually unlock attributes after miss locking
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
            cmds.setAttr(self.get_transform()+"."+attr, l=attr in locked, k=attr not in locked)

    def get_locked(self):
        # get all locked attributes
        attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
        return [attr for attr in attrs
                if cmds.getAttr(self.get_transform()+"."+attr, l=1)]

    def set_outputs(self, outputs):
        for src, dst in outputs:
            for shape_name in self.get_shapelist():
                cmds.connectAttr(shape_name+"."+src, dst, f=1)
                break
        return self

    def get_outputs(self):
        for shape in self.get_shapelist():
            # get output attr
            outputs = cmds.listConnections(shape, d=1, p=1, c=1) or []
            # turn the list to (outputAttr, outNode) form
            outputs = [outputs[i:i+2] for i in range(0, len(outputs), 2)]
            outputs = [(cmds.attributeName(src, l=1), dst) for src, dst in outputs]
            return outputs

    def set_radius(self, radius):
        # get old radius
        old_radius = self.get_radius()
        # radius too low or None, return
        if old_radius is None or radius < 0.000001 or old_radius < 0.000001:
            return self

        # get scale value
        scale = radius / old_radius
        # modify shape node through copy_ctrl
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".s", scale, scale, scale))
        return self

    def get_radius(self):
        points = sum([cmds.xform(shape + ".cv[*]", q=1, t=1) for shape in self.get_shapelist()], [])
        points = [points[i:i + 3] for i in range(0, len(points), 3)]
        lengths = [sum([v ** 2 for v in point])**0.5 for point in points]
        if len(lengths) > 0:
            return max(lengths)

    def set_rotate(self, rotate):
        # set shape rotation through copt_ctrl
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".rotate", *rotate))
        return self

    def set_offset(self, offset):
        # set shape offset through copt_ctrl
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".translate", *offset))
        return self

    def edit_shape_by_copy_ctrl(self, callback):
        # callback receive a method, use to modify control transformation
        # create a tempCtrl use self shape
        copy_ctrl = Control(shape=self.get_shape())
        # apply callback function to modify transformation
        callback(copy_ctrl.get_transform())
        # freeze transformation data
        cmds.makeIdentity(copy_ctrl.get_transform(), apply=1, t=1, r=1, s=1)
        cmds.xform(copy_ctrl.get_transform(), piv=[0, 0, 0])

        # replace ctrl shape with tempCtrl shape
        Control(self.get_transform(), shape=copy_ctrl.get_shape(), color=self.get_color(), outputs=self.get_outputs())
        # delete temp ctrl
        cmds.delete(copy_ctrl.get_transform())


if __name__ == "__main__":
    control = Control()
    name = control.get_shape()