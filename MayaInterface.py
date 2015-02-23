"""
This module contains the function which are required to create reference from a
a given Maya file, and query and attach Cache Nodes on a Mesh
"""
#--------------------------------------------
# Name:         MayaInterface.py
# Purpose:      Making references, attaching cache nodes to a mesh, and query
#               cache nodes already attached to it
# Author:       Hussain Parsaiyan and Qurban Ali
# License:      GPL v3
# Created       10/10/2012
# Copyright:    (c) ICE Animations. All rights reserved
# Python Version:   2.6
#--------------------------------------------


import maya.cmds as mc
import pymel.all as pc

def addReferences(paths):
    '''
        This function creates a reference of the specified file
        if the file is already refenced, this function loads the file if
        it is unloaded mode.

        @params: List of paths to be reherenced
    '''
    for path in paths:
        try:
            mc.file(path, r = True)
        except Exception as ex:
            mc.error(str(ex))
            
def importFiles(paths):
    for path in paths:
        try:
            mc.file(path, i=True)
        except Exception as ex:
            mc.error(str(ex))

def applyCache(node, xmlFilePath):
    pc.mel.doImportCacheFile(xmlFilePath, "", [node], list())

def cacheApplied(mesh):
    cacheFiles = [node for node in pc.PyNode(mesh).listHistory()
                  if isinstance(node, pc.nt.CacheFile)]
    for cacheFile in cacheFiles:
        if cacheFile.getFileName():
            return cacheFile
    return None
