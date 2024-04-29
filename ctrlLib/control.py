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
        keys = [("t", "transform"), ("n", "name"), ("p", "parent"),
                ("s", "shape"), ("c", "color"), ("r", "radius"),
                ("ro", "rotate"), ("o", "offset"), ("l", "locked"), ("ou", "outputs")]
        for index,(short, long) in enumerate (keys):
            # try to get value from long name
            arg = kwargs.get(long, None)
            # if it's none, try to get value from short name
            if arg is None:
                arg = kwargs.get(short, None)
            # if still not found, get it from arg list
            if arg is None and index < len(args):
                arg = args[index]
            # get value, and run relative function to save
            if arg is not None:
                getattr(self, "set_" + long)(arg)

    def set_transform(self, transform):
        # get control uuid
        uuids = cmds.ls(transform, type=["transform", "joint"], o=1, uid=1)
        if len(uuids) != 1:
            #if there is more or zero uuid, find operation failed, return to end method
            return
        self.uuid = uuids[0]
        return self

    def get_transform(self):
        #get transform node long name through uuid
        transforms = cmds.ls(self.uuid, l=1)
        if len(transforms) == 1:
            return transforms[0]
        #if there is more or zero transform node found by uuid, find operation failed
        #create empty group and recall this function
        else:
            self.set_transform(cmds.group(em=1, n="control"))
            return self.get_transform()

    def set_parent(self, parent):
        # set parent object
        cmds.parent(self.get_transform(), parent)
        # transformation reset
        cmds.xform(self.get_transform(), ws=0, m=[1, 0, 0, 0,
                                                  0, 1, 0, 0,
                                                  0, 0, 1, 0,
                                                  0, 0, 0, 1])
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

    def get_shape_names(self):
        #get all shape node under transform node that type is nurbsCurve
        shapes = cmds.listRelatives(self.get_transform(), s=True, f=True) or []
        return [shape for shape in shapes if cmds.nodeType(shape) == "nurbsCurve"]

    def set_color(self, color):
        # get color
        for shape in self.get_shape_names():
            cmds.setAttr(shape + ".overrideEnabled", True)
            cmds.setAttr(shape + ".overrideColor", color)

    def get_color(self):
        for shape in self.get_shape_names():
            # if overrideEnabled set to True, return color
            if cmds.setAttr(shape + ".overrideEnabled"):
                return cmds.getAttr(shape + ".overrideColor")

    def set_shape(self, shape):
        # delete original shape node
        if self.get_shape_names():
            cmds.delete(self.get_shape_names())

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
            # turn points from one-dimensional list to float3
            points = data["points"]
            points = [points[i:i+3] for i in range(0, len(points), 3)]

            # if shape is closed
            # get "degree" number points and move to the end of list
            if data["periodic"]:
                points = points +points[:data["degree"]]

            # create temp curve and parent to the transform node
            # delete temp curve after in the end
            curve = cmds.curve(degree=data["degree"], knot=data["knot"],
                               periodic=data["periodic"], p=points)
            cmds.parent(cmds.listRelatives(curve, s=1, f=1),
                        self.get_transform(), s=1, add=1)
            cmds.delete(curve)

        # rename shape node name
        for shape in self.get_shape_names():
            cmds.rename(shape, self.get_name()+"Shape")
        return self

    def get_shape(self):
        # get all shape node in for loop
        return [dict(
            points=cmds.xform(shape + ".cv[*]", q=1, t=1, ws=0),      #point position
            periodic=cmds.getAttr(shape + ".form") == 2,                    #whether periodic
            degree=cmds.getAttr(shape + ".degree"),                         #curve degree
            knot=list(MFnNurbsCurve(api_ls(shape).getDagPath(0)).knots()),  #curve knots
        ) for shape in self.get_shape_names()]

    def set_locked(self, locked):
        """
        if input s, transfer it to sx, sy, sz
        The following code use comprehension to quickly create dictionary
        the normal way of writing it is as follows:

                trs_xyz_map = {}
                for trs in "trs":
                    trs_xyz_map[trs] = []
                    for xyz in "xyz":
                        trs_xyz_map[trs].append(trs + xyz)

        """
        trs_xyz_map = {trs: [trs+xyz for xyz in "xyz"] for trs in "trs"}
        """
        dic.get() 
        Return relative dic key's value
        If input "tx", get() will find key 't' and return key 't''s value
        The result will be ["tx","ty","tz"], although you did not input "ty" and "tz"
        
        sum([], [])
        sum([]) will return the sum of input list
        sum([], []) will combine two list and return a new list
        """
        locked = sum([trs_xyz_map.get(attr, [attr]) for attr in locked], [])
        """
        l=attr in locked, k=attr not in locked
        Avoid manually unlock attributes after miss locking
        """
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
            cmds.setAttr(self.get_transform()+"."+attr,
                         l=attr in locked, k=attr not in locked)

    def get_locked(self):
        attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
        return [attr for attr in attrs
                if cmds.getAttr(self.get_transform()+"."+attr, l=1)]

    def set_outputs(self, outputs):
        for src, dst in outputs:
            for shape_name in self.get_shape_names():
                cmds.connectAttr(shape_name+"."+src, dst, f=1)
                break
        return self

    def get_outputs(self):
        for shape in self.get_shape_names():
            outputs = cmds.listConnections(shape, d=1, p=1, c=1) or []
            outputs = [outputs[i:i+2] for i in range(0, len(outputs), 2)]
            outputs = [(cmds.attributeName(src, l=1), dst) for src, dst in outputs]
            return outputs

    def set_radius(self, radius):
        # 获取旧半径
        old_radius = self.get_radius()
        # 半径过小或为None,不设置半径
        if old_radius is None or radius < 0.000001 or old_radius < 0.000001:
            return self
        # 求缩放值
        scale = radius / old_radius
        # 通过设置copy_ctrl的scale修改shape
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".s", scale, scale, scale))
        return self

    def get_radius(self):
        points = sum([cmds.xform(shape + ".cv[*]", q=1, t=1) for shape in self.get_shape_names()], [])
        points = [points[i:i + 3] for i in range(0, len(points), 3)]
        lengths = [sum([v ** 2 for v in point])**0.5 for point in points]
        if len(lengths) > 0:
            return max(lengths)

    def set_rotate(self, rotate):
        # 通过设置copy_ctrl的rotate修改shape
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".rotate", *rotate))
        return self

    def set_offset(self, offset):
        # 通过设置copy_ctrl的offset修改shape
        self.edit_shape_by_copy_ctrl(lambda copy_ctrl: cmds.setAttr(copy_ctrl+".translate", *offset))
        return self

    def edit_shape_by_copy_ctrl(self, callback):
        copy_ctrl = Control(shape=self.get_shape())
        callback(copy_ctrl.get_transform())
        cmds.makeIdentity(copy_ctrl.get_transform(), apply=1, t=1, r=1, s=1)
        cmds.xform(copy_ctrl.get_transform(), piv=[0, 0, 0])

        # set controller shape to temp ctrl shape
        Control(self.get_transform(), shape=copy_ctrl.get_shape(),
                color=self.get_color(), outputs=self.get_outputs())
        # delete temp ctrl
        cmds.delete(copy_ctrl.get_transform())



if __name__ == "__main__":
    control = Control()
    name = control.get_shape()