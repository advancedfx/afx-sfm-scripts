# Copyright (c) advancedfx.org
#
# Last changes:
# 2017-06-26 by dominik.matrixstorm.com
#
# First changes:
# 2016-07-13 by dominik.matrixstorm.com


# DEG2RAD = 0.0174532925199432957692369076849
# PI = 3.14159265358979323846264338328


import sfm
import sfmUtils
import sfmApp
from PySide import QtGui
import gc
import struct
import math

def SetError(error):
	print 'ERROR:', error
	QtGui.QMessageBox.warning( None, "ERROR:", error )
	
# <remarks>Slow as fuck!</remarks>
def FindChannel(channels,name):
	for i in channels:
		if name == i.GetName():
			return i
	return None

def InitalizeAnimSet(animSet,makeVisibleChannel = True):
	shot = sfm.GetCurrentShot()

	channelsClip = sfmUtils.GetChannelsClipForAnimSet(animSet, shot)
	
	visibleChannel = None
	
	if makeVisibleChannel:
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
	
	if visibleChannel:
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

def MakeKeyFrameTransform(channelCache,animSet,channelName,time,vec,quat,shortestPath=False,posSuffix='_p',rotSuffix='_o'):
	positionChan = channelCache.GetChannel(animSet, channelName+posSuffix)
	orientationChan = channelCache.GetChannel(animSet, channelName+rotSuffix)
	
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
	
class BufferedFile:
	def __init__(self,filePath):
		self.b = bytearray(1048576)
		self.index = 0
		self.numread = 0
		self.file = open(filePath, 'rb')
		self.filePos = 0
		if self.file:
			self.file.seek(0, 2)
			self.fileSize = self.file.tell()
			self.file.seek(0, 0)
		else:
			self.fileSize = 0
	
	def Read(self,readBytes):
		result = bytearray()

		if self.file is None:
			return result
		
		while 0 < readBytes:
			bytesLeft = self.numread -self.index
			bytesNow = min(bytesLeft, readBytes)
			
			if 0 >= bytesNow:
				self.index = 0
				self.numread = self.file.readinto(self.b)
				if not self.numread:
					return result
				continue
			
			result += self.b[self.index : (self.index +bytesNow)]
			self.index += bytesNow
			self.filePos += bytesNow
			readBytes -= bytesNow
		
		return result
		
	def FileSize(self):
		if not self.file:
			return None
			
		return self.fileSize
		
	def Tell(self):
		if not self.file:
			return None
		
		return self.filePos;
		
	
	def Close(self):
		if self.file is not None:
			self.file.close();
			self.file = None

def ReadString(file):
	buf = bytearray()
	while True:
		b = file.Read(1)
		if len(b) < 1:
			return None
		elif b == '\0':
			return str(buf)
		else:
			buf.append(b[0])

def ReadBool(file):
	buf = file.Read(1)
	if(len(buf) < 1):
		return None
	return struct.unpack('?', buf)[0]

def ReadInt(file):
	buf = file.Read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('i', buf)[0]
	
def ReadFloat(file):
	buf = file.Read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('f', buf)[0]

def ReadDouble(file):
	buf = file.Read(8)
	if(len(buf) < 8):
		return None
	return struct.unpack('d', buf)[0]
	
def ReadVector(file):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z):
		x = 0
		y = 0
		z = 0
	
	return vs.Vector(x,y,z)

def ReadQAngle(file):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
		
	if math.isinf(x) or math.isinf(y) or math.isinf(z):
		x = 0
		y = 0
		z = 0
	
	return vs.QAngle(x,y,z)

def ReadQuaternion(file):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
	w = ReadFloat(file)
	if w is None:
		return None
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z) or math.isinf(w):
		w = 1
		x = 0
		y = 0
		z = 0
	
	return vs.Quaternion(x,y,z,w)

def ReadAgrVersion(file):
	buf = file.Read(14)
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
		file = BufferedFile(fileName)
		
		version = ReadAgrVersion(file)
		
		if version is None:
			SetError('Invalid file format.')
			return False
			
		if 1 != version:
			SetError('Version '+str(version)+' is not supported!')
			return False

		shot = sfm.GetCurrentShot()
		
		firstTime = None
		
		knownAnimSetNames = set()
		
		dict = AgrDictionary()
		channelCache = ChannelCache()
		knownHandleToDagName = {}
		
		stupidCount = 0
		
		afxCam = None
		
		while True:
			stupidCount = stupidCount +1
			
			if 4096 <= stupidCount:
				stupidCount = 0
				gc.collect()
				#break
				#reply = QtGui.QMessageBox.question(None, 'Message', 'Imported another 4096 packets - Continue?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
				#if reply == QtGui.QMessageBox.No:
				#	break
			
			node0 = dict.Read(file)
			
			if node0 is None:
				break
				
			elif 'deleted' == node0:
				handle = ReadInt(file)
				time = ReadFloat(file)
				
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
				visible = None
				time = None
				dagName = None
				dagAnimSet = None
				handle = ReadInt(file)
				if dict.Peekaboo(file,'baseentity'):
					time = ReadFloat(file)
					if None == firstTime:
						firstTime = time
					time = vs.DmeTime_t(time -firstTime)
					
					modelName = dict.Read(file)
					
					dagName = knownHandleToDagName.get(handle, None)
					if dagName is not None:
						# Switched model, make old model invisible:
						sfm.UsingAnimationSet(dagName)
						dagAnimSet = sfm.GetCurrentAnimationSet()
						channelsClip = sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)
						rtime = time -channelsClip.timeFrame.start.GetValue()
						MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', rtime, False)
					
					dagName = "afx." +str(handle) + " " + modelName
					
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
						
					visible = ReadBool(file)
					
					MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', time, visible)
					
					renderOrigin = ReadVector(file)
					renderAngles = ReadQAngle(file)
					
					if True == visible:
						# Only key-frame if visible
						MakeKeyFrameTransform(channelCache, dagAnimSet, "rootTransform", time, renderOrigin, QuaternionFromQAngle(renderAngles), True)
					
				if dict.Peekaboo(file,'baseanimating'):
					skin = ReadInt(file)
					body = ReadInt(file)
					sequence  = ReadInt(file)
					hasBoneList = ReadBool(file)
					if hasBoneList:
						dagModel = None
						if dagAnimSet is not None and hasattr(dagAnimSet,'gameModel'):
							dagModel = dagAnimSet.gameModel
						
						numBones = ReadInt(file)
						
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
				
				viewModel = ReadBool(file)
			
			elif 'afxCam' == node0:
				
				if afxCam is None:
					dmeAfxCam = vs.CreateElement( "DmeCamera", "afxCam", shot.GetFileId())
					afxCam = sfm.CreateAnimationSet( "afxCam", target=dmeAfxCam)
					InitalizeAnimSet(afxCam,makeVisibleChannel=False)
					channelsClip = sfmUtils.GetChannelsClipForAnimSet(afxCam, sfm.GetCurrentShot())
					scaled_fieldOfView_channel = FindChannel(channelsClip.channels, "scaled_fieldOfView_channel")
					scaled_fieldOfView_channel.fromElement.lo = 0
					scaled_fieldOfView_channel.fromElement.hi = 180
					shot.scene.GetChild(shot.scene.FindChild("Cameras")).AddChild(dmeAfxCam)
				
				time = ReadFloat(file)
				if None == firstTime:
					firstTime = time
				time = vs.DmeTime_t(time -firstTime)
				
				renderOrigin = ReadVector(file)
				renderAngles = ReadQAngle(file)
				fov = ReadFloat(file)
				fov = fov / 180.0
				
				channelsClip = sfmUtils.GetChannelsClipForAnimSet(afxCam, shot)
				
				time = time -channelsClip.timeFrame.start.GetValue()
				
				MakeKeyFrameValue(channelCache, afxCam, 'fieldOfView', time, fov)
				MakeKeyFrameTransform(channelCache, afxCam, 'transform', time, renderOrigin, QuaternionFromQAngle(renderAngles), False, '_pos', '_rot')
				
			else:
				SetError('Unknown packet: ')
				return False
	finally:
		if file is not None:
			file.Close()
	
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
