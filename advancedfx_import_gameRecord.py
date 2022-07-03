
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
	
def ReadString(file):
	buf = bytearray()
	while True:
		b = file.read(1)
		if len(b) < 1:
			return None
		elif b == '\0':
			return str(buf)
		else:
			buf.append(b[0])

def ReadBool(file):
	buf = file.read(1)
	if(len(buf) < 1):
		return None
	return struct.unpack('<?', buf)[0]

def ReadInt(file):
	buf = file.read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('<i', buf)[0]
	
def ReadFloat(file):
	buf = file.read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('<f', buf)[0]

def ReadDouble(file):
	buf = file.read(8)
	if(len(buf) < 8):
		return None
	return struct.unpack('<d', buf)[0]
	
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
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z) or math.isnan(x) or math.isnan(y) or math.isnan(z):
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
		
	if math.isinf(x) or math.isinf(y) or math.isinf(z) or math.isnan(x) or math.isnan(y) or math.isnan(z):
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
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z) or math.isinf(w) or math.isnan(x) or math.isnan(y) or math.isnan(z) or math.isnan(w):
		w = 1
		x = 0
		y = 0
		z = 0
	
	return vs.Quaternion(x,y,z,w)
	
def ReadMatrix3x4(file):
	mat = vs.mathlib.matrix3x4_t()
	for i in range(3):
		for j in range(4):
			val = ReadFloat(file)
			if val is None:
				return None
			if math.isinf(val):
				val = 0
			mat[i*4+j] = val
	
	return mat

def ReadAgrVersion(file):
	buf = file.read(14)
	if len(buf) < 14:
		return None
	
	cmp = b"afxGameRecord\0"
	
	if buf != cmp:
		return None
	
	return ReadInt(file)

class AgrDictionary:
	def __init__(self):
		self.dict = {}
		self.peeked = None
	
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
		
class ModelHandle:
	def __init__(self,objNr,modelName):
		self.objNr = objNr
		self.modelName = modelName
		self.modelData = False
		self.lastRenderOrigin = None
		self.camera = None
#
#	def __hash__(self):
#		return hash((self.handle, self.modelName))
#
#	def __eq__(self, other):
#		return (self.handle, self.modelName) == (other.handle, other.modelName)

class AgrTimeConverter:
	def __init__(self):
		self.time = 0
		self.frameTime = 0
		self.newTime = 0
		
	def Frame(self,frameTime):
		self.time = self.newTime
		self.frameTime = frameTime
		
		
	def FrameEnd(self):
		self.newTime = self.time + self.frameTime
		
	def GetTime(self,channelsClip):
		return vs.DmeTime_t(self.time) -channelsClip.timeFrame.start.GetValue()

def ReadFile(fileName):
	file	 = None
	
	try:
		file = open(fileName, 'rb')
		
		if file is None:
			self.error('Could not open file.')
			return False
		
		version = ReadAgrVersion(file)
		
		if version is None:
			SetError('Invalid file format.')
			return False
			
		if(5 != version and 6 != version):
			SetError('Version '+str(version)+' is not supported!')
			return False

		shot = sfm.GetCurrentShot()
		
		timeConverter = AgrTimeConverter()
		dict = AgrDictionary()
		handleToLastModelHandle = {}
		unusedModelHandles = []
		
		channelCache = ChannelCache()
		afxCam = None
		
		stupidCount = 0
		
		objNr = 0
		
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
				
			elif 'afxFrame' == node0:
				time = ReadFloat(file)
				
				timeConverter.Frame(time)
			
				afxHiddenOffset = ReadInt(file)
				if afxHiddenOffset:
					curOffset = file.tell()
					file.seek(afxHiddenOffset -4, 1)
					
					numHidden = ReadInt(file)
					for i in range(numHidden):
						handle = ReadInt(file)
						
						modelHandle = handleToLastModelHandle.pop(handle, None)
						if modelHandle is not None:
							dagAnimSet = modelHandle.modelData
							if dagAnimSet:
								# Make ent invisible:
								MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), False)
							
							unusedModelHandles.append(modelHandle)
							#print("Marking %i (%s) as hidden/reusable." % (modelHandle.objNr,modelHandle.modelName))
						
					file.seek(curOffset,0)
					
			elif 'afxFrameEnd' == node0:
				timeConverter.FrameEnd()
				
			elif 'afxHidden' == node0:
				# skipped, because will be handled earlier by afxHiddenOffset
				
				numHidden = ReadInt(file)
				for i in range(numHidden):
					handle = ReadInt(file)
		
			elif 'deleted' == node0:
				handle = ReadInt(file)
				
				modelHandle = handleToLastModelHandle.pop(handle, None)
				if modelHandle is not None:
					dagAnimSet = modelHandle.modelData
					if dagAnimSet:
						# Make removed ent invisible:
						MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), False)
						
					unusedModelHandles.append(modelHandle)
					print("Marking %i (%s) as hidden/reusable." % (modelHandle.objNr,modelHandle.modelName))
			
			elif 'entity_state' == node0:
				visible = None
				dagAnimSet = None
				handle = ReadInt(file)
				if dict.Peekaboo(file,'baseentity'):
					
					modelName = dict.Read(file)
					
					visible = ReadBool(file)
					
					renderOrigin = vs.Vector(0,0,0)
					renderRotation = vs.Quaternion(0,0,0,1)
					
					if version == 6:
						matrix3x4 = ReadMatrix3x4(file)
						vs.mathlib.MatrixPosition(matrix3x4,renderOrigin)
						vs.mathlib.MatrixQuaternion(matrix3x4,renderRotation)
					else:
						renderOrigin = ReadVector(file)
						renderAngles = ReadQAngle(file)
						renderRotation = QuaternionFromQAngle(renderAngles)
					
					modelHandle = handleToLastModelHandle.get(handle, None)
					
					if (modelHandle is not None) and (modelHandle.modelName != modelName):
						# Switched model, make old model invisible:
						dagAnimSet = modelHandle.modelData
						if dagAnimSet:
							MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), False)
						
						modelHandle = None
						
					if modelHandle is None:
						
						# Check if we can reuse s.th. and if not create new one:
						
						bestIndex = 0
						bestLength = 0
						
						for idx,val in enumerate(unusedModelHandles):
							if (val.modelName == modelName) and ((modelHandle is None) or (modelHandle.modelData and (modelHandle.lastRenderOrigin is not None) and ((modelHandle.lastRenderOrigin -renderOrigin).Length() < bestLength))):
								modelHandle = val
								bestLength = (modelHandle.lastRenderOrigin -renderOrigin).Length()
								bestIndex = idx
						
						if modelHandle is not None:
							# Use the one we found:
							del unusedModelHandles[bestIndex]
							print("Reusing %i (%s)." % (modelHandle.objNr,modelHandle.modelName))
						else:
							# If not then create a new one:
							objNr = objNr + 1
							modelHandle = ModelHandle(objNr, modelName)
							print("Creating %i (%s)." % (modelHandle.objNr,modelHandle.modelName))
						
						handleToLastModelHandle[handle] = modelHandle
					
					dagAnimSet = modelHandle.modelData
					if dagAnimSet is False:
						# We have not tried to import the model for this (new) handle yet, so try to import it:
						dagName = modelName.rsplit('/',1)
						dagName = dagName[len(dagName) -1]
						dagName = (dagName[:60] + '..') if len(dagName) > 60 else dagName
						dagName = "afx." +str(modelHandle.objNr)+ " " + dagName
						
						dagAnimSet = sfmUtils.CreateModelAnimationSet(dagName,modelName)
						
						if(hasattr(dagAnimSet,'gameModel')):
							dagAnimSet.gameModel.evaluateProceduralBones = False # This will look awkwardly and crash SFM otherwise
							
						print "Initalizing animSet " + dagName
						InitalizeAnimSet(dagAnimSet)
						
						modelHandle.modelData = dagAnimSet
						
					modelHandle.lastRenderOrigin = renderOrigin
					
					MakeKeyFrameValue(channelCache, dagAnimSet, 'visible_channel', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), visible)
					
					MakeKeyFrameTransform(channelCache, dagAnimSet, "rootTransform", timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), renderOrigin, renderRotation, True)
					
				if dict.Peekaboo(file,'baseanimating'):
					#skin = ReadInt(file)
					#body = ReadInt(file)
					#sequence  = ReadInt(file)
					hasBoneList = ReadBool(file)
					if hasBoneList:
						dagModel = None
						if dagAnimSet is not None and hasattr(dagAnimSet,'gameModel'):
							dagModel = dagAnimSet.gameModel
						
						numBones = ReadInt(file)
						
						for i in xrange(numBones):
							vec = vs.Vector(0,0,0)
							quat = vs.Quaternion(0,0,0,1)
							if version == 6:
								matrix3x4 = ReadMatrix3x4(file)
								vs.mathlib.MatrixPosition(matrix3x4,vec)
								vs.mathlib.MatrixQuaternion(matrix3x4,quat)
							else:
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
								
								MakeKeyFrameTransform(channelCache, dagAnimSet, name, timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(dagAnimSet, shot)), vec, quat)
				
				if dict.Peekaboo(file,'camera'):
					thidPerson = ReadBool(file)
					renderOrigin = ReadVector(file)
					renderAngles = ReadQAngle(file)
					fov = ReadFloat(file)
					fov = fov / 180.0
					
					modelCamera = modelHandle.camera
					if modelCamera is None:
						camName = "camera."+str(modelHandle.objNr)
						dmeAfxCam = vs.CreateElement( "DmeCamera", camName, shot.GetFileId())
						modelCamera = sfm.CreateAnimationSet( camName, target=dmeAfxCam)
						InitalizeAnimSet(modelCamera,makeVisibleChannel=False)
						channelsClip = sfmUtils.GetChannelsClipForAnimSet(modelCamera, sfm.GetCurrentShot())
						scaled_fieldOfView_channel = FindChannel(channelsClip.channels, "scaled_fieldOfView_channel")
						scaled_fieldOfView_channel.fromElement.lo = 0
						scaled_fieldOfView_channel.fromElement.hi = 180
						shot.scene.GetChild(shot.scene.FindChild("Cameras")).AddChild(dmeAfxCam)
						modelHandle.camera = modelCamera
					
					MakeKeyFrameValue(channelCache, modelCamera, 'fieldOfView', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(modelCamera, shot)), fov)
					MakeKeyFrameTransform(channelCache, modelCamera, 'transform', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(modelCamera, shot)), renderOrigin, QuaternionFromQAngle(renderAngles), True, '_pos', '_rot')
				
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
				
				renderOrigin = ReadVector(file)
				renderAngles = ReadQAngle(file)
				fov = ReadFloat(file)
				fov = fov / 180.0
				
				MakeKeyFrameValue(channelCache, afxCam, 'fieldOfView', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(afxCam, shot)), fov)
				MakeKeyFrameTransform(channelCache, afxCam, 'transform', timeConverter.GetTime(sfmUtils.GetChannelsClipForAnimSet(afxCam, shot)), renderOrigin, QuaternionFromQAngle(renderAngles), True, '_pos', '_rot')
				
			else:
				SetError('Unknown packet: ')
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
