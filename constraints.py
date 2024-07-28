import maya.cmds as cm


def objectCtrlorCreate(size=1, drvGrp=False, makeHiera=False, parent=False, single=False):

    selected_objects = cm.ls(selection=True)
    if not selected_objects:
        raise ValueError("No objects selected")
    joint = cm.ls(selection=True)

    # get all child joint in this chain, append first joint and reverse the list
    # if signle joint, reset the list
    if single:
        jointList = joint
    else:
        jointList = cm.listRelatives(joint, allDescendents=True, children=True)
        jointList.append(joint[0])
        jointList.reverse()

    # create a curve circle as base ctrl shape
    baseCur = cm.circle(center=[0, 0, 0], normal=[0, 1, 0], sweep=360,
                        radius=size, degree=3, tolerance=0.01, sections=8)[0]
    cm.DeleteHistory(baseCur)

    # add ctrl list and offset group list for chain hierarchy
    ctrlGrpList = []
    ctrlList = []

    for jn in jointList:
        # duplicate ctrl and add offset group
        ctrl = cm.duplicate(baseCur, name="{0}_ctrl".format(jn))[0]
        ctrlOffsetGrp = cm.group(ctrl, name="{0}_offset".format(ctrl))

        # if driven gourp selected, add drv group
        if drvGrp:
            ctrlDrvGrp = cm.group(ctrl, name="{0}_drv".format(ctrl))

        # constaint or parent
        cm.delete(cm.parentConstraint(jn, ctrlOffsetGrp, maintainOffset=False, weight=1))
        if parent:
            cm.parent(jn, ctrl)
        else:
            cm.parentConstraint(ctrl, jn, maintainOffset=False, weight=1)

        # add to ctrl and offsetGrp list
        ctrlGrpList.append(ctrlOffsetGrp)
        ctrlList.append(ctrl)

    if makeHiera:
        # get a reversed int list base on len of ctrl list
        for i in range(len(ctrlList) - 1, 0, -1):
            # parent offset group to upper ctrl
            cm.parent(ctrlGrpList[i], ctrlList[i - 1])
    cm.delete(baseCur)


def polerVecCreate(offset=None, joint=None, ikh=None):
    startJoint = cm.listRelatives(joint, parent=True)

    ctrl = cm.circle(center=[0, 0, 0], normal=[0, 1, 0], sweep=360,
                     radius=1, degree=3, tolerance=0.01, sections=8)[0]
    cm.DeleteHistory(ctrl)

    ctrlOffsetGrp = cm.group(ctrl, name="{0}_offset".format(ctrl))
    ctrlDisGrp = cm.group(ctrl, name="{0}_dis".format(ctrl))

    cm.delete(cm.parentConstraint(joint, ctrlOffsetGrp, maintainOffset=False, weight=1))
    cm.setAttr("{0}.t".format(ctrlDisGrp), offset[0], offset[1], offset[2])
    cm.poleVectorConstraint(ctrl, ikh)


def curGenerateLoc(cur=None, locIndex=0):
    for i in range(locIndex):
        cm.undoInfo(openChunk=True)
        loc = cm.spaceLocator(name="{0}_{1}_loc".format(cur, (i + 1)))[0]
        path = cm.pathAnimation(loc, cur, followAxis="x", upAxis='y', worldUpType='vector',
                                worldUpVector=(0, 1, 0), fractionMode=True, follow=True,
                                inverseUp=False, inverseFront=False, bank=False)
        nodes = cm.listConnections(loc)
        cm.setAttr(path + ".uValue", i / locIndex)
        locPos = cm.xform(loc, query=True, worldSpace=True, translation=True)
        cm.xform(loc, translation=locPos)
        cm.delete(nodes)
        cm.makeIdentity(loc, apply=True, rotate=True)
    cm.undoInfo(closeChunk=True)


def curGenerateJon(cur=None, jointIndex=0):
    jointList = []
    for i in range(jointIndex):
        loc = cm.spaceLocator(name="{0}_{1}_loc".format(cur, (i + 1)))[0]
        path = cm.pathAnimation(loc, cur, followAxis="x", upAxis='y', worldUpType='vector',
                                worldUpVector=(0, 1, 0), fractionMode=True, follow=True,
                                inverseUp=False, inverseFront=False, bank=False)
        cm.setAttr(path + ".uValue", i / jointIndex)
        locPos = cm.xform(loc, query=True, worldSpace=True, translation=True)

        cm.select(clear=True)
        jnt = cm.joint(position=locPos, name="{0}_{1}_joint".format(cur, (i + 1)))

        cm.delete(loc)
        jointList.append(jnt)

    for i in range(len(jointList) - 1):
        cm.parent(jointList[i + 1], jointList[i])


def curGenerateCluster(cur=None):
    curVerts = cm.ls(cur + '.cv[*]', flatten=True)
    for i, vert in enumerate(curVerts):
        cluster = cm.cluster(vert)[1]
        cm.rename(cluster, "{0}_{1}_clu".format(cur, (i + 1)))
    cm.select(clear=True)
