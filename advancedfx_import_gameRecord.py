# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-07-16 by dominik.matrixstorm.com
#
# First changes:
# 2016-07-13 by dominik.matrixstorm.com


# DEG2RAD = 0.0174532925199432957692369076849
# PI = 3.14159265358979323846264338328


import sfm;
import sfmUtils;
import sfmApp;
from PySide import QtGui
import gc
import struct

def SetError(error):
	print 'ERROR:', error
	QtGui.QMessageBox.warning( None, "ERROR:", error )
	
# <remarks>Slow as fuck!</remarks>
def FindChannel(channels,name):
	for i in channels:
		if name == i.GetName():
			return i
	return None

def InitalizeAnimSet(animSet):
	shot = sfm.GetCurrentShot()

	channelsClip = sfmUtils.GetChannelsClipForAnimSet(animSet, shot)
	
	# Ensure additional channels:
	visibleChannel = FindChannel(channelsClip.channels,'visible_channel')
	if visibleChannel is None:
		visibleChannel = sfmUtils.CreateControlAndChannel('visible', vs.AT_BOOL, False, animSet, shot).channel
		visibleChannel.mode = 3
		visibleChannel.fromElement = animSet.gameModel
		visibleChannel.fromAttribute = 'visible'
		visibleChannel.toElement = animSet.gameModel
		visibleChannel.toAttribute = 'visible'
	
	# clear channel logs:
	for chan in channelsClip.channels:
		chan.ClearLog()
	
	# Not visible initially:
	visibleChannel.log.SetKey(-channelsClip.timeFrame.start.GetValue(), False)

class ChannelCache:
	dict = {}
	
	def GetChannel(self,animSet,channelName):
		key = animSet.GetName() + channelName
		value = self.dict.get(key, False)
		if False == value:
			channelsClip = sfmUtils.GetChannelsClipForAnimSet(animSet, sfm.GetCurrentShot())
			value = FindChannel(channelsClip.channels, channelName)
			self.dict[key] = value
			
		return value
		
def MakeKeyFrameValue(channelCache,animSet,channelName,time,value):
	chan = channelCache.GetChannel(animSet, channelName)
	chan.log.SetKey(time, value)

def MakeKeyFrameTransform(channelCache,animSet,channelName,time,vec,quat,shortestPath=False):
	positionChan = channelCache.GetChannel(animSet, channelName+'_p')
	orientationChan = channelCache.GetChannel(animSet, channelName+'_o')
	
	positionChan.log.SetKey(time, vec)
	# positionChan.log.AddBookmark(time, 0) # We cannot afford bookmarks (waste of memory)
	# positionChan.log.AddBookmark(time, 1) # We cannot afford bookmarks (waste of memory)
	# positionChan.log.AddBookmark(time, 2) # We cannot afford bookmarks (waste of memory)
	
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

def ReadString(file):
	buf = bytearray()
	while True:
		b = file.read(1)
		if len(b) < 1:
			return None
		elif b == '\0':
			return str(buf)
		else:
			buf.append(b)

def ReadBool(file):
	buf = file.read(1)
	if(len(buf) < 1):
		return None
	return struct.unpack('?', buf)[0]

def ReadInt(file):
	buf = file.read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('i', buf)[0]

def ReadDouble(file):
	buf = file.read(8)
	if(len(buf) < 8):
		return None
	return struct.unpack('d', buf)[0]
	
def ReadVector(file):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	
	return vs.Vector(x,y,z)

def ReadQAngle(file):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	
	return vs.QAngle(x,y,z)

def ReadQuaternion(file):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	w = ReadDouble(file)
	if w is None:
		return None
	
	return vs.Quaternion(x,y,z,w)

def ReadAgrVersion(file):
	buf = file.read(14)
	if len(buf) < 14:
		return None
	
	cmp = 'afxGameRecord\0'
	
	if buf != cmp:
		return None
	
	return ReadInt(file)

class AgrDictionary:
	dict = {}
	peeked = None
	
	def Read(self,file):
		if self.peeked is not None:
			oldPeeked = self.peeked
			self.peeked = None
			return oldPeeked
		
		idx = ReadInt(file)
		
		if idx is None:
			return None
		
		if -1 == idx:
			str = ReadString(file)
			if str is None:
				return None
			self.dict[len(self.dict)] = str
			return str
			
		return self.dict[idx]
		
	def Peekaboo(self,file,what):
		if self.peeked is None:
			self.peeked = self.Read(file)
			
		if(what == self.peeked):
			self.peeked = None
			return True
		
		return False

def ReadFile(fileName):
	file	 = None
	
	try:
		file = open(fileName, 'rb')
		
		version = ReadAgrVersion(file)
		
		if version is None:
			SetError('Invalid file format.')
			return False
			
		if 0 != version:
			SetError('Version '+str(version)+' is not supported!')

		shot = sfm.GetCurrentShot()
		
		firstTime = None
		
		knownAnimSetNames = set()
		
		dict = AgrDictionary()
		channelCache = ChannelCache()
		knownHandleToDagName = {}
		
		stupidCount = 0
		
		while True:
			node0 = dict.Read(file)
			
			if node0 is None:
				break
				
			elif 'deleted' == node0:
				handle = ReadInt(file)
				time = ReadDouble(file)
				
				dagName = knownHandleToDagName.get(handle, None)
				if dagName is not None:
					# Make removed ent invisible:
					sfm.UsingAnimationSet(dagName)
					dagAnimSet = sfm.GetCurrentAnimationSet()
					channelsClip = sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)
					time = time -firstTime
					time = vs.DmeTime_t(time) -channelsClip.timeFrame.start.GetValue()
					MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', time, False)
			
			elif 'entity_state' == node0:
				stupidCount = stupidCount +1
				
				if 4096 <= stupidCount:
					stupidCount = 0
					gc.collect()
					#break
					#reply = QtGui.QMessageBox.question(None, 'Message', 'Imported another 4096 packets - Continue?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
					#if reply == QtGui.QMessageBox.No:
					#	break
				
				visible = None
				time = None
				dagName = None
				dagAnimSet = None
				handle = ReadInt(file) if dict.Peekaboo(file,'handle') else None
				if dict.Peekaboo(file,'baseentity'):
					time = ReadDouble(file) if dict.Peekaboo(file, 'time') else None
					if None == firstTime:
						firstTime = time
					time = vs.DmeTime_t(time -firstTime)
					
					modelName = dict.Read(file) if dict.Peekaboo(file, 'modelName') else None
					
					dagName = knownHandleToDagName.get(handle, None)
					if dagName is not None:
						# Switched model, make old model invisible:
						sfm.UsingAnimationSet(dagName)
						dagAnimSet = sfm.GetCurrentAnimationSet()
						channelsClip = sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)
						rtime = time -channelsClip.timeFrame.start.GetValue()
						MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', rtime, False)
					
					dagName = "afx/" + modelName + "/" +str(handle)
					
					knownHandleToDagName[handle] = dagName
					
					sfm.ClearSelection()
					sfm.Select(dagName+':rootTransform')
					dagRootTransform = sfm.FirstSelectedDag()
					if(None == dagRootTransform):
						dagAnimSet = sfmUtils.CreateModelAnimationSet(dagName,modelName)
						if(hasattr(dagAnimSet,'gameModel')):
							dagAnimSet.gameModel.evaluateProceduralBones = False # This will look awkwardly and crash SFM otherwise
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
					
					time = time -channelsClip.timeFrame.start.GetValue()
						
					visible = ReadBool(file) if dict.Peekaboo(file, 'visible') else None
					
					MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', time, visible)
					
					renderOrigin = ReadVector(file) if dict.Peekaboo(file, 'renderOrigin') else None
					renderAngles = ReadQAngle(file) if dict.Peekaboo(file, 'renderAngles') else None
					
					if True == visible:
						# Only key-frame if visible
						MakeKeyFrameTransform(channelCache, dagAnimSet, "rootTransform", time, renderOrigin, QuaternionFromQAngle(renderAngles), True)
					
					dict.Peekaboo(file,'/')
				
				if (dagAnimSet is not None) and dict.Peekaboo(file,'baseanimating'):
					skin = ReadInt(file) if dict.Peekaboo(file,'skin') else None
					body = ReadInt(file) if dict.Peekaboo(file,'body') else None
					sequence  = ReadInt(file) if dict.Peekaboo(file,'sequence') else None
					if dict.Peekaboo(file,'boneList'):
						dagModel = None
						if hasattr(dagAnimSet,'gameModel'):
							dagModel = dagAnimSet.gameModel
						
						numBones = ReadInt(file)
						
						#print "bones" + str(numBones)
						
						for i in xrange(numBones):
							vec = ReadVector(file)
							quat = ReadQuaternion(file)
							
							if dagModel is None:
								continue
							
							if(i < len(dagModel.bones)):
								name = dagModel.bones[i].GetName()
								#print name
								
								name = name[name.find('(')+1:]
								name = name[:name.find(')')]
								#print name
								
								if True == visible:
									# Only key-frame if visible
									MakeKeyFrameTransform(channelCache, dagAnimSet, name, time, vec, quat)
					
					dict.Peekaboo(file,'/')
				
				viewModel = ReadBool(file) if dict.Peekaboo(file,'viewmodel') else None
				
				dict.Peekaboo(file,'/')
			
			else:
				SetError('Unknown packet')
				return False
	finally:
		if file is not None:
			file.close()
	
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
	fileName, _ = QtGui.QFileDialog.getOpenFileName(None, "Open HLAE GameRecord File",  "", "afxGameRecord (*.agr)")
	if not 0 < len(fileName):
		return
	
	oldTimelineMode = sfmApp.GetTimelineMode()

	snap, snapFrame = GetSnapButtons()

	snapChecked = snap.isChecked()
	snapFrameChecked = snapFrame.isChecked()
	
	try:
		gc.collect() # Free memory, since we need much of it
		
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
		gc.collect() # Free memory, since we needed much of it
	
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
