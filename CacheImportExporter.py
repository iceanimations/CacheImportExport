#--------------------------------------------
# Name:         matteWorker.py
# Purpose:      Customized QStandardItemModel and QStandardItem classes
# Author:       Hussain Parsaiyan
# License:      GPL v3
# Created       05/10/2012
# Copyright:    (c) ICE Animations. All rights reserved
# Python Version:   2.6
#--------------------------------------------
import plugins.utilities as util
from PyQt4 import QtGui, QtCore
import pymel.core as pc
import random, string
import os
import MayaInterface
op = os.path
reload(MayaInterface)
MI = MayaInterface
import xml.dom.minidom as xdm

Qt = QtCore.Qt

def getStartEndTimeAndFPS(filePath):
    dom = xdm.parse(filePath)
    timeRange = dom.getElementsByTagName("time")[0].getAttribute("Range").split("-")
    timePerFrame = int(dom.getElementsByTagName("cacheTimePerFrame")[0].getAttribute("TimePerFrame"))
    FPS = 6000/ timePerFrame
    return int(timeRange[0])/timePerFrame, int(timeRange[1])/timePerFrame , FPS

def createClass(*arg):
    #This function is used to dynamically create the GUI class
    #@param arg[0]: The directory in which this module exists
    #@param arg[1]: The UI class
    #@param arg[2]: The base class QMainWindow
    class GUI(arg[1], arg[2]):

        def __init__(self, parent = util.getMayaWindow()):
            super(GUI, self).__init__()
            self.setupUi(self)
            parent.addDockWidget(Qt.DockWidgetArea(0x2),self)

            self.pluginDir = arg[0]

            self.setItems = {}
            self.fillItems()

            self.exportFileDialog = QtGui.QFileDialog(self)
            self.exportFileDialog.setModal(True)
            self.exportFileDialog.setFileMode(QtGui.QFileDialog.FileMode(2))


            self.splitter_2.addWidget(self.createCustomFileDialog("Maya File (*.ma *.mb)", True))
            self.splitter_3.addWidget(self.createCustomFileDialog("XML (*.xml)"))

            self.cacheDirLineEdit.setText(self.cacheDir)

            self.fpsDisplay.display({"pal": 25, "ntsc": 30, "film": 24}[pc.general.currentUnit(q= True, t = True)])
            self.fpsDisplay.mousePressEvent = self.lcdClick

            self.cacheItems = {}
            self.cacheTableWidget.viewport().setAcceptDrops(True)
            self.cacheTableWidget.dragEnterEvent = self.cacheTableWidget.dragMoveEvent = self.cacheDragMovement
            self.cacheTableWidget.dropEvent = self.addCacheToMesh
            self.cacheTableWidget.dragLeaveEvent = self.cacheDragLeave

            self.refItems = {}
            self.refListWidget.viewport().setAcceptDrops(True)
            self.refListWidget.dragEnterEvent = self.refListWidget.dragMoveEvent = self.refDragMovement
            self.refListWidget.dropEvent = self.addReferenceToList
            self.refListWidget.dragLeaveEvent = self.refDragLeave


            self.makeConnections()


        def cacheDragMovement(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def addCacheToMesh(self, drop):
            item = self.cacheTableWidget.itemAt(drop.pos())
            index = self.cacheTableWidget.indexFromItem(item)
            if drop.mimeData().hasUrls() and hasattr(item, "default"):
                mesh = self.cacheTableWidget.item(index.row(), 0).text()
                replacer = lambda x: x.toString().replace(r"file:///","")
                refs = [replacer(url) for url in drop.mimeData().urls() if not QtCore.QFileInfo(replacer(url)).isDir()]
                if refs and refs[0].split(r"file:")[0]:
                    refs = refs[0] #contain no or one item
                else:
                    return
                item.setText(refs)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.cacheItems[mesh] = refs
                start_end_fps = getStartEndTimeAndFPS(refs)
                map(lambda x: self.cacheTableWidget.item(index.row(), x + 2).setText(str(start_end_fps[x])), xrange(len(start_end_fps)))
                drop.acceptProposedAction()

        def cacheDragLeave(self, event):
            event.accept()



        def refDragLeave(self, event):
            event.accept()

        def addReferenceToList(self, drop):
            replacer = lambda x: x.toString().replace(r"file:///","")
            refs = [replacer(url) for url in drop.mimeData().urls() if not QtCore.QFileInfo(replacer(url)).isDir()]
            for ref in [ref for ref in refs if ref not in self.refItems.keys() and ref.split(r"file:")[0]]:
                self.refItems[ref] = QtGui.QListWidgetItem(ref)
                self.refListWidget.addItem(self.refItems[ref])
            drop.acceptProposedAction()

        def refDragMovement(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def lcdClick(self, event):
            try:
                click = pc.promptDialog(t = "Please enter FPS", m = "Please enter FPS:", b = ["OK", "CANCEL"], db = "OK", cb = "CANCEL", tx = {"pal": 25, "ntsc": 30, "film": 24}[pc.general.currentUnit(q= True, t = True)])
                fps = pc.promptDialog(q = True, tx = True)
                values = {"pal": 25, "ntsc": 30, "film": 24}
                if int(fps) in values.values() and click == 'OK' :
                    pc.promptDialog(t = "Update Animation", m = "Do you want to Keep keys at current frame: (Y/N):",  b = ["OK"], db = "OK", tx = "No")
                    ua = pc.promptDialog(q = True, tx = True).lower()
                    ua = ua[0] if ua else None
                    pc.general.currentUnit(t = filter(None,map(lambda x: x if values[x] == int(fps) else None, values.keys() ))[0], ua = False if ua == "y" else True)
                    self.fpsDisplay.display({"pal": 25, "ntsc": 30, "film": 24}[pc.general.currentUnit(q= True, t = True)])
            except:
                pass
        
        def changePath(self, fileDialog, lineEdit):
            path = str(lineEdit.text()).strip('"')
            if op.exists(path):
                fileDialog.setDirectory(path)
            else:
                lineEdit.selectAll()
                pc.warning("Invalid path: %s" %path)
           

        def createCustomFileDialog(self, fileType, multiple = False):

            dialogFor = "ref_favs" if fileType[0] == "M" else "cache_favs"

            fileDialog = QtGui.QFileDialog(self)
            fileDialog.setNameFilter(fileType)
            
            fileDialog.setSizeGripEnabled(False)
            if multiple: fileDialog.setFileMode(QtGui.QFileDialog.FileMode(3))
            default = set([os.path.abspath(url.path()+"/"*2) for url in fileDialog.sidebarUrls()])
            favorites = set([os.path.abspath(url+"/"*2) for url in pc.optionVar.get(dialogFor , [])])
            fileDialog.setSidebarUrls(fileDialog.sidebarUrls() + [QtCore.QUrl(r"file:///"+os.path.abspath(url+"/"*2)) for url in favorites])
            thisIsMyFileDialog = QtGui.QWidget(self)
            thisIsMyFileDialog.setLayout(QtGui.QGridLayout())
            theFileDialog = fileDialog.children()
            layout = QtGui.QHBoxLayout()
            map(lambda x: layout.addWidget(theFileDialog[2+x]), xrange(8))
            thisIsMyFileDialog.layout().addLayout(layout,0,0)
            thisIsMyFileDialog.layout().addWidget(theFileDialog[10])
            lineEdit = QtGui.QLineEdit(self)
            lineEdit.setText(fileDialog.directory().path())
            model = theFileDialog[10].children()[1].model()
            lineEdit.setToolTip("Set path")
            lineEdit.returnPressed.connect(lambda: self.changePath(fileDialog, lineEdit))
            thisIsMyFileDialog.layout().addWidget(lineEdit)
            def update_fav(*args):
                model = theFileDialog[10].children()[1].model()
                allUrls = []
                for x in xrange(model.rowCount()):
                    allUrls.append(os.path.abspath(model.index(x, 0).data(3)+"/"*2))#.data(3))

                newFavs = [url for url in allUrls if (url not in favorites) and (url not in default) ]

                if newFavs:
                    map(lambda x: pc.optionVar(sva = (dialogFor, x)), newFavs)
                    map(favorites.add, newFavs)

                else:
                    urlsToRemove = []
                    for url in favorites:
                        if url not in allUrls:
                            stale = pc.optionVar(q = dialogFor)
                            stale.pop(stale.index(url))
                            pc.optionVar(ca = dialogFor)
                            map(lambda x: pc.optionVar(sva = (dialogFor, x)), stale)
                            urlsToRemove.append(url)
                    map(favorites.remove, urlsToRemove)
            model.dataChanged.connect(update_fav)
            model.rowsRemoved.connect(update_fav)
            return thisIsMyFileDialog

        def addSelection(self):
            for selection in self.getSelection():
                if selection not in self.setItems.keys():
                    self.setItems[selection] = QtGui.QListWidgetItem(selection)
                    self.setListWidget.addItem(self.setItems[selection])

        def getSelection(self):
            setSelections = [x.name() for x in pc.ls(sl = True, type = "objectSet") if (type(x) == pc.nt.ObjectSet and x.members() and isinstance(x.members()[0], pc.nt.Transform) and x.members()[0].getShape(ni=True, type= "mesh"))]
            setSelections += [x.name() for x in pc.ls(sl = True, type = "mesh", dag = True, ni = True)]
            return setSelections

        def makeConnections(self):
            self.exportCacheButton.clicked.connect(self.exportCache)
            self.startendButton.toggled.connect(self.setStartEnd)
            self.setListWidget.doubleClicked.connect(self.sceneSelect)
            map(lambda x: x.pressed.connect(self.toggle), [self.timeSliderButton, self.startendButton])
            self.dirSelectButton.clicked.connect(self.locationSelect)
            self.exportFileDialog.fileSelected.connect(self.cacheDirLineEdit.setText)
            self.cacheDirLineEdit.textChanged.connect(self.setCacheDir)
            self.addSelectionButton.clicked.connect(self.addSelection)
            self.removeSetButton.clicked.connect(self.removeSet)
            self.clearListButton.clicked.connect(self.clearSetList)
            self.remRefButton.clicked.connect(self.remRef)
            self.addRefButton.clicked.connect(self.addRef)
            self.addImpSelButton.clicked.connect(self.addToImpCacheList)
            self.cacheTableWidget.cellDoubleClicked.connect(self.revertToDefault)
            self.clearImpButton.clicked.connect(self.clearCacheList)
            self.remImpSelButton.clicked.connect(self.remSelectedCache)
            self.applyImpCacheButton.clicked.connect(self.applyCache)

        def applyCache(self):
            selection = pc.ls(sl = True)

            #finding the minimum start time and the maximum end time
            #and adjust the render global settings and the timeline accordingly
            minStartTime, maxEndTime = getStartEndTimeAndFPS(self.cacheItems[self.cacheItems.keys()[0]])[0:2]
            for node in self.cacheItems:
                startTime, endTime = getStartEndTimeAndFPS(self.cacheItems[node])[0:2]

                #check if current startTime and endTime is less and greater
                #then the minStartTime and maxEndTime.
                if minStartTime > startTime:
                    minStartTime = startTime
                elif maxEndTime < endTime:
                    maxEndTime = endTime

                if isinstance(pc.PyNode(node), pc.nt.Mesh):
                    MI.applyCache(node, self.cacheItems[node])
                else:
                    meshes = [shape for transform in pc.PyNode(node).dsm.inputs(type = "transform") for shape in transform.getShapes(type = "mesh", ni = True)]
                    result = pc.polyUnite(*meshes, ch = True)
                    pc.rename(result[0].getShapes(ni = True, type = "mesh")[0], node.split(":")[-1]+"_shape_combined")
                    pc.rename(result[0], node.split(":")[-1]+"_combined")
                    MI.applyCache(result[0].getShapes(ni = True, type = "mesh")[0].name(), self.cacheItems[node])
            pc.select(selection)

            #setting the timeline and render settings:
            pc.playbackOptions(max = maxEndTime, aet = maxEndTime, min = minStartTime, ast = minStartTime)
            pc.PyNode("defaultRenderGlobals").startFrame.set(minStartTime)
            pc.PyNode("defaultRenderGlobals").endFrame.set(maxEndTime)

            #clear the list
            self.clearCacheList()

        def remSelectedCache(self):
            for selection in self.cacheTableWidget.selectedItems():
                if not hasattr(selection, "default"):
                    try:
                        self.cacheItems.pop(selection.text())
                    except:
                        continue
            map(lambda x: self.cacheTableWidget.removeRow(self.cacheTableWidget.row(x)), [item for item in self.cacheTableWidget.selectedItems() if hasattr(item, "default")])


        def clearCacheList(self):
            self.cacheItems.clear()
            self.cacheTableWidget.clearSpans()
            self.cacheTableWidget.setRowCount(0)

        def revertToDefault(self, row, column):
            if column == 1:
                item = self.cacheTableWidget.item(row, column)
                item.setText(item.default)
                font = item.font()
                font.setBold(False)
                item.setFont(font)

        def addToImpCacheList(self):
            for selection in self.getSelection():
                if selection not in self.cacheItems:
                    rowCount = self.cacheTableWidget.rowCount()

                    self.cacheTableWidget.insertRow(rowCount)
                    setOrNot = type(pc.PyNode(selection)) == pc.nt.ObjectSet
                    self.cacheItems[selection] = " " if setOrNot else MI.cacheApplied(selection).getFileName()[0] if MI.cacheApplied(selection) else None
                    nameTableItem = QtGui.QTableWidgetItem(selection)
                    nameTableItem.setFlags(Qt.ItemFlags(1+4+8+32))
                    self.cacheTableWidget.setItem(rowCount, 0, nameTableItem)

                    cacheTableItem = QtGui.QTableWidgetItem(self.cacheItems[selection])
                    cacheTableItem.setFlags(Qt.ItemFlags(1+4+8+32))
                    self.cacheTableWidget.setItem(rowCount, 1, cacheTableItem)
                    cacheTableItem.setToolTip("Double Click to revert to default")
                    cacheTableItem.default = cacheTableItem.text()

                    def itemCreator(xml):
                        item = QtGui.QTableWidgetItem(xml)
                        item.setFlags(Qt.ItemFlags(1+4+8+32))
                        return item
                    xml = ""
                    if not setOrNot: xml = MI.cacheApplied(selection).getFileName(q= 1)[0] if MI.cacheApplied(selection) else ""
                    details = tuple(["","",""])
                    if xml: details = tuple(getStartEndTimeAndFPS(xml))
                    self.cacheTableWidget.setItem(rowCount, 2, itemCreator(str(details[0]) if details else ""))
                    self.cacheTableWidget.setItem(rowCount, 3, itemCreator(str(details[1]) if details else ""))
                    self.cacheTableWidget.setItem(rowCount, 4, itemCreator(str(details[2]) if details else ""))



        def addRef(self):
            MI.addReferences(self.refItems.keys())
            self.refItems.clear()
            self.refListWidget.clear()

        def remRef(self):
            selections = self.refListWidget.selectedItems()
            map(self.refItems.pop, map(lambda x : x.text(), selections))
            map(lambda x: self.refListWidget.takeItem(self.refListWidget.indexFromItem(x).row()), selections)

        def removeSet(self):
            selections = self.setListWidget.selectedItems()
            map(self.setItems.pop, map(lambda x : x.text(), selections))
            map(lambda x: self.setListWidget.takeItem(self.setListWidget.indexFromItem(x).row()), selections)

        def clearSetList(self):
            self.setListWidget.clear()
            self.setItems = {}

        def setCacheDir(self, text):
            self.cacheDir = os.path.abspath(text)

        def locationSelect(self):
            self.exportFileDialog.setDirectory(self.cacheDirLineEdit.text())
            self.exportFileDialog.show()

        def toggle(self):
            stateTimer, stateStartEnd = self.timeSliderButton.isEnabled(),  self.startendButton.isEnabled()
            self.timeSliderButton.setEnabled(stateStartEnd)
            self.startendButton.setEnabled(stateTimer)

        def sceneSelect(self, index):
            pc.select(self.setListWidget.itemFromIndex(index).text())

        def setStartEnd(self, enable):
            map(lambda x : x.setEnabled(enable), [self.startendLabel, self.endTime, self.startTime])

        def exportCache(self):

            selection = pc.ls(sl = True)
            flags = {"version": 5,
                     "time_range_mode": 2 if self.timeSliderButton.isChecked() else 0,
                     "start_time": self.startTime.text(),
                     "end_time": self.endTime.text(),
                     "cache_file_dist": "OneFile",
                     "refresh_during_caching": 0,
                     "cache_dir": self.cacheDir.replace('\\', "/"),
                     "cache_per_geo": "1",
                     "cache_name": "",
                     "cache_name_as_prefix": 0,
                     "action_to_perform": "export",
                     "force_save": 0,
                     "simulation_rate": 1,
                     "sample_multiplier": 1,
                     "inherit_modf_from_cacha": 1,
                     "store_doubles_as_float":1,
                     "cache_format": "mcc"}

            combineMeshes = []
            for objectSet in [setName for setName in self.setItems if type(pc.PyNode(setName)) != pc.nt.Mesh]:
                pc.select(pc.PyNode(objectSet).members())
                meshes = [shape for transform in pc.PyNode(objectSet).dsm.inputs(type = "transform") for shape in transform.getShapes(type = "mesh", ni = True)]
                combineMesh = pc.createNode("mesh")
                pc.rename(combineMesh, objectSet.split(":")[-1]+"_cache")
                combineMeshes.append(combineMesh)
                polyUnite = pc.createNode("polyUnite")
                for i in xrange(0, len(meshes)):
                    meshes[i].outMesh >> polyUnite.inputPoly[i]
                    meshes[i].worldMatrix[0] >> polyUnite.inputMat[i]
                polyUnite.output >> combineMesh.inMesh
            pc.select(combineMeshes + [mesh for mesh in self.setItems if type(pc.PyNode(mesh)) == pc.nt.Mesh])

            try:
                command =  'doCreateGeometryCache2 {version} {{ "{time_range_mode}", "{start_time}", "{end_time}", "{cache_file_dist}", "{refresh_during_caching}", "{cache_dir}", "{cache_per_geo}", "{cache_name}", "{cache_name_as_prefix}", "{action_to_perform}", "{force_save}", "{simulation_rate}", "{sample_multiplier}", "{inherit_modf_from_cacha}", "{store_doubles_as_float}", "{cache_format}"}};'.format(**flags)
                pc.Mel.eval(command)

            finally:
                pc.delete(map(lambda x: x.getParent(),combineMeshes))
                pc.select(selection)
                pc.informBox("Exported", "All meshes in the list have been exported", "OK")

        def fillItems(self):
            if "diskCache" not in pc.Workspace.fileRules.keys():
                pc.Workspace.fileRules["diskCache"] = u"data"
            self.diskCache = pc.Workspace.fileRules["diskCache"]
            diskCache = self.diskCache
            sceneName = self.sceneName = pc.sceneName()
            projectPath = pc.Workspace.getPath()
            self.cacheDir = cacheDir = os.path.abspath(os.path.join(projectPath, diskCache, ".".join(os.path.basename(sceneName).split(".")[0:-1])))
            for item in self.setItems:
                item.cacheDir = cacheDir
                item.cacheName = item.text().split(":")[-1] + "_cache"


    return GUI


def cacheImportExporter(*arg):

    #Helper function which, if, takes inputs
    #and create a global class which can
    #later have multiple instances
    #@param arg[0]: Directory of the module
    #@param arg[1]: Ui_MainWindow
    #@param arg[2]: QMainWindow. The base class
    if len ( arg ) == 3:
        global gui
        gui = createClass(*arg)
    while True:
        rand = "".join(random.sample(string.ascii_letters,10))
        uiName = __name__+"." + rand
        if uiName not in globals():
            exec('global {0}; {0} = gui(); {0}.show()'.format(rand))
            print uiName
            break
