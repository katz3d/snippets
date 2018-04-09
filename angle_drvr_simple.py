'''
import angle_drvr_simple
reload(angle_drvr_simple)
angle_drvr_simple.build()
'''

import maya.cmds as cmds
import random

def build(count=3, driver_axis=1, max_size=3, min_size=0.1):
    """ build the driver node, target nodes, and wire them up """

    # build driver
    drvr = cmds.polyCone(radius=0.5, height=1.0, name='driver')[0]
    cmds.xform(drvr, ro=[90,0,0])

    # vectorProduct to isolate driver_axis from driver's worldmatrix
    vp_drv = cmds.createNode('vectorProduct', name='vpn_driver')
    cmds.setAttr(vp_drv+'.operation', 3) # vector Matrix Product
    cmds.setAttr(vp_drv + '.normalizeOutput', 1)
    cmds.setAttr(vp_drv+'.input1'+['X','Y','Z'][driver_axis], 1.0) # isolate driver axis as output vector
    cmds.connectAttr(drvr + '.worldMatrix', vp_drv + '.matrix')

    # vectorProduct to get driver translate
    vp_drv_pos = cmds.createNode('vectorProduct', name='vpn_driver')
    cmds.setAttr(vp_drv_pos + '.operation', 3)  # vector Matrix Product
    cmds.connectAttr(drvr + '.worldMatrix', vp_drv_pos + '.matrix')

    for i in range(count):
        target = cmds.polySphere(radius=0.25)[0]
        cmds.xform(target, ws=1, t=[((0.5 - random.random()) * 10), 0, ((0.5 - random.random()) * 10)])  # just on xz plane to test

        # decomposeMatrix to get target translate
        dm_target = cmds.createNode('decomposeMatrix', name='dmn_'+target)
        cmds.connectAttr(target+'.worldMatrix', dm_target+'.inputMatrix')

        # get vector between driver and target
        pma_target = cmds.createNode('plusMinusAverage', name='pma_'+target)
        cmds.setAttr(pma_target+'.operation', 2) #subtract
        cmds.connectAttr(dm_target+'.outputTranslate', pma_target+'.input3D[0]')
        cmds.connectAttr(vp_drv_pos+'.output', pma_target+'.input3D[1]')

        # normalize driver-target vector
        vp_norm = cmds.createNode('vectorProduct', name='vp_norm_'+target)
        cmds.setAttr(vp_norm+'.operation', 0)
        cmds.setAttr(vp_norm+'.normalizeOutput', 1)
        cmds.connectAttr(pma_target+'.output3D', vp_norm+'.input1')

        # dot product
        vp_dot = cmds.createNode('vectorProduct', name='vp_dot_'+target)
        cmds.setAttr(vp_dot+'.operation', 1)
        cmds.setAttr(vp_dot+'.normalizeOutput', 1)
        cmds.connectAttr(vp_drv+'.output', vp_dot+'.input1')
        cmds.connectAttr(vp_norm+'.output', vp_dot+'.input2')

        # clamp output with setRange node
        sr_target = cmds.createNode('setRange', name='srn_'+target)
        cmds.setAttr(sr_target+'.minX', min_size)
        cmds.setAttr(sr_target+'.maxX', max_size)
        cmds.setAttr(sr_target+'.oldMinX', 0)
        cmds.setAttr(sr_target+'.oldMaxX', 1)
        cmds.connectAttr(vp_dot+'.outputX', sr_target+'.valueX')

        # connect to target scale
        for axis in ['X','Y','Z']:
            cmds.connectAttr(sr_target+'.outValueX', target+'.scale'+axis)
