# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-07-14 by dominik.matrixstorm.com
#
# First changes:
# 2016-07-13 by dominik.matrixstorm.com


# DEG2RAD = 0.0174532925199432957692369076849
# PI = 3.14159265358979323846264338328


import sfm;
import sfmUtils;
import sfmApp;
from PySide import QtGui
import xml.etree.ElementTree as ET
import ctypes

def SetError(error):
	print 'ERROR:', error
	QtGui.QMessageBox.warning( None, "ERROR:", error )

def InitalizeAnimSet(animSet):
	controls = animSet.controls
	for ctrl in controls:
		if isinstance(ctrl,vs.CDmeTransformControl):
			ctrl.GetPositionChannel().ClearLog()
			ctrl.GetOrientationChannel().ClearLog()

def MakeKeyFrameTransform(animSet,controlName,time,vec,quat,shortestPath=False):
	rootControlGroup = animSet.GetRootControlGroup()
	
	control = rootControlGroup.FindControlByName(controlName, True)
	positionChan = control.GetPositionChannel()
	orientationChan = control.GetOrientationChannel()
	
	positionChan.log.SetKey(time, vec)
	#positionChan.log.AddBookmark(time, 0) # We cannot afford bookmarks (waste of memory)
	#positionChan.log.AddBookmark(time, 1) # We cannot afford bookmarks (waste of memory)
	#positionChan.log.AddBookmark(time, 2) # We cannot afford bookmarks (waste of memory)
	
	if(shortestPath):
		# Make sure we travel the short way:
		lastQuatKeyIdx = orientationChan.log.FindKey(time)
		if(0 <= lastQuatKeyIdx and lastQuatKeyIdx < orientationChan.log.GetKeyCount()):
			lastQuat = orientationChan.log.GetValue(orientationChan.log.GetKeyTime(lastQuatKeyIdx))
			dp = vs.QuaternionDotProduct(lastQuat,quat)
			if dp < 0:
				quat = vs.Quaternion(-quat.x,-quat.y,-quat.z,-quat.w)
	
	orientationChan.log.SetKey(time, quat)
	# orientationChan.log.AddBookmark(time, 0) # We cannot afford bookmarks (waste of memory)
	# orientationChan.log.AddBookmark(time, 1) # We cannot afford bookmarks (waste of memory)
	# orientationChan.log.AddBookmark(time, 2) # We cannot afford bookmarks (waste of memory)
	
def QuaternionFromQAngle(qangle):
	quat = vs.Quaternion()
	vs.AngleQuaternion(qangle, quat)
	return quat
	
def Quaternion(x,y,z,w):
	quat = vs.Quaternion()
	quat.x = x;
	quat.y = y;
	quat.z = z;
	quat.w = w
	return quat


def ReadFile(fileName):
	shot = sfm.GetCurrentShot()
	
	tree = ET.parse(fileName)
	root = tree.getroot()
	
	firstTime = None
	
	knownAnimSetNames = set()
	
	for entity_state in root.findall('entity_state'):
		time = None
		dagName = None
		dagAnimSet = None
		handle = int(entity_state.get('handle'))
		viewModel = bool(entity_state.get('viewmodel'))
		baseentity = entity_state.find('baseentity')
		if(None != baseentity):
			time = float(baseentity.get('time'))
			if None == firstTime:
				firstTime = time
			time = time -firstTime
			
			modelName = baseentity.get('modelName')
			
			dagName = "afx/" + modelName + "/" +str(handle)
			
			sfm.ClearSelection()
			sfm.Select(dagName+':rootTransform')
			dagRootTransform = sfm.FirstSelectedDag()
			if(None == dagRootTransform):
				dagAnimSet = sfmUtils.CreateModelAnimationSet(dagName,modelName)
				sfm.ClearSelection()
				sfm.Select(dagName+":rootTransform")
				dagRootTransform = sfm.FirstSelectedDag()
			else:
				sfm.UsingAnimationSet(dagName)
				dagAnimSet = sfm.GetCurrentAnimationSet()
			
			if dagName not in knownAnimSetNames:
				print "Initalizing animSet " + dagName
				InitalizeAnimSet(dagAnimSet)
				knownAnimSetNames.add(dagName)
			
			channelsClip = sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)
			
			time = vs.DmeTime_t(time) -channelsClip.timeFrame.start.GetValue()
				
			visbile = bool(baseentity.get('visible'))
			
			xRenderOrigin = baseentity.find('renderOrigin')
			renderOrigin = vs.Vector(float(xRenderOrigin.get('x')), float(xRenderOrigin.get('y')), float(xRenderOrigin.get('z')))
			
			xRenderAngles = baseentity.find('renderAngles')
			renderAngles = vs.QAngle(float(xRenderAngles.get('x')), float(xRenderAngles.get('y')), float(xRenderAngles.get('z')))
			
			MakeKeyFrameTransform(dagAnimSet, "rootTransform", time, renderOrigin, QuaternionFromQAngle(renderAngles), True)
		
		baseanimating = entity_state.find('baseanimating')
		if(None != dagAnimSet and None != baseanimating):
			skin = int(baseanimating.get('skin'))
			body = int(baseanimating.get('body'))
			sequence = int(baseanimating.get('sequence'))
			boneList  = baseanimating.find('boneList')
			if(None != boneList and hasattr(dagAnimSet,'gameModel')):
				dagModel = dagAnimSet.gameModel
				for b in boneList.findall('b'):
					i = int(b.get('i'))
					x = float(b.get('x'))
					y = float(b.get('y'))
					z = float(b.get('z'))
					qx = float(b.get('qx'))
					qy = float(b.get('qy'))
					qz = float(b.get('qz'))
					qw = float(b.get('qw'))
					
					if(qx == 0 and qy == 0 and qz == 0 and qw == 0):
						# The fuq?
						qw = float(1)
					
					if(i < len(dagModel.bones)):
						name = dagModel.bones[i].GetName()
						
						name = name[name.find('(')+1:]
						name = name[:name.find(')')]
						
						MakeKeyFrameTransform(dagAnimSet, name, time, vs.Vector(x,y,z), Quaternion(qx,qy,qz,qw))
	
	return True

def GetSnapButtons():
	snap = None
	snapFrame = None
	for x in sfmApp.GetMainWindow().findChildren(QtGui.QToolButton):
		toolTip = x.toolTip()
		if "Snap" == toolTip:
			snap = x
		else:
			if "Snap Frame" == toolTip:
				snapFrame = x
	
	return snap, snapFrame

def ImportGameRecord():
	fileName, _ = QtGui.QFileDialog.getOpenFileName(None, "Open HLAE GameRecord File",  "", "HLAE GameRecord (*.xml)")
	if not 0 < len(fileName):
		return
	
	oldTimelineMode = sfmApp.GetTimelineMode()

	snap, snapFrame = GetSnapButtons()

	snapChecked = snap.isChecked()
	snapFrameChecked = snapFrame.isChecked()
	
	try:
		#sfm.SetOperationMode("Record")
		sfmApp.SetTimelineMode(3) # Work around timeline bookmark update bug (can't be in Graph Editor or it won't update)
		
		# Work around bug/feature causing programatically inserted keyframes to be snapped:
		if(snapChecked):
			snap.click()
		if(snapFrameChecked):
			snapFrame.click()
			
		if ReadFile(fileName):
			print 'Done.'
		else:
			print 'FAILED'
			
	finally:
		checked = ""
		if(snapFrameChecked):
			#snapFrame.click() # if we unheck here it will still snap ...
			checked = "'Snap Frame'"
		if(snapChecked):
			#snap.click() # if we uncheck here it will still snap ...
			if 0 < len(checked):
				checked = " and " + checked
			checked = "'Snap'" + checked
		
		if 0 < len(checked):
			QtGui.QMessageBox.information( None, "Attention", "Had to un-push " + checked + " tool button in timeline! Push again (if wanted)." )
		
		sfmApp.SetTimelineMode(oldTimelineMode)
		#sfm.SetOperationMode("Pass")

ImportGameRecord()
