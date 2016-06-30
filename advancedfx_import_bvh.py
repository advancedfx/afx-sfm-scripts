# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-06-29 by dominik.matrixstorm.com
#
# First changes:
# 2009-09-01 by dominik.matrixstorm.com


# DEG2RAD = 0.0174532925199432957692369076849
# PI = 3.14159265358979323846264338328


import sfm;
import sfmUtils;
import sfmApp;
from PySide import QtGui


def SetError(error):
	print 'ERROR:', error
	QtGui.QMessageBox.warning( None, "ERROR:", error )


# <summary> reads a line from file and separates it into words by splitting whitespace </summary>
# <param name="file"> file to read from </param>
# <returns> list of words </returns>
def ReadLineWords(file):
	line = file.readline()
	words = [ll for ll in line.split() if ll]	
	return words


# <summary> searches a list of words for a word by lower case comparison </summary>
# <param name="words"> list to search </param>
# <param name="word"> word to find </param>
# <returns> less than 0 if not found, otherwise the first list index </returns>
def FindWordL(words, word):
	i = 0
	word = word.lower()
	while i < len(words):
		if words[i].lower() == word:
			return i
		i += 1
	return -1


# <summary> Scans the file till a line containing a lower case match of filterWord is found </summary>
# <param name="file"> file to read from </param>
# <param name="filterWord"> word to find </param>
# <returns> False on fail, otherwise same as ReadLineWords for this line </returns>
def ReadLineWordsFilterL(file, filterWord):
	while True:
		words = ReadLineWords(file)
		if 0 < len(words):
			if 0 <= FindWordL(words, filterWord):
				return words
		else:
			return False


# <summary> Scans the file till the channels line and reads channel information </summary>
# <param name="file"> file to read from </param>
# <returns> False on fail, otherwise channel indexes as follows: [Xposition, Yposition, Zposition, Zrotation, Xrotation, Yrotation] </returns>
def ReadChannels(file):
	words = ReadLineWordsFilterL(file, 'CHANNELS')
	
	if not words:
		return False

	channels = [\
	FindWordL(words, 'Xposition'),\
	FindWordL(words, 'Yposition'),\
	FindWordL(words, 'Zposition'),\
	FindWordL(words, 'Zrotation'),\
	FindWordL(words, 'Xrotation'),\
	FindWordL(words, 'Yrotation')\
	]
	
	idx = 0
	while idx < 6:
		channels[idx] -= 2
		idx += 1
			
	for channel in channels:
		if not (0 <= channel and channel < 6):
			return False
			
	return channels
	

def ReadRootName(file):
	words = ReadLineWordsFilterL(file, 'ROOT')
	
	if not words or len(words)<2:
		return False
		
	return words[1]
	
	
def ReadFrames(file):
	words = ReadLineWordsFilterL(file, 'Frames:')
	
	if not words or len(words)<2:
		return -1
		
	return int(words[1])

def ReadFrameTime(file):
	words = ReadLineWordsFilterL(file, 'Time:')
	
	if not words or len(words)<3:
		return -1
		
	return float(words[2])
	

def ReadFrame(file, channels):
	line = ReadLineWords(file)
	
	if len(line) < 6:
		return False;
	
	Xpos = float(line[channels[0]])
	Ypos = float(line[channels[1]])
	Zpos = float(line[channels[2]])
	Zrot = float(line[channels[3]])
	Xrot = float(line[channels[4]])
	Yrot = float(line[channels[5]])
	
	return [Xpos, Ypos, Zpos, Zrot, Xrot, Yrot]


def ClearBookmarks(log, component, start, end):
	idx = 0
	while idx < log.GetNumBookmarks(component):
		time = log.GetBookmarkTime(component, idx)
		if(start <= time and time <= end):
			log.RemoveBookmark(component, time)
		else:
			idx = idx + 1


def ClearKeys(log, start, end):
	idx = 0
	while idx < log.GetKeyCount():
		time = log.GetKeyTime(idx)
		if(start <= time and time <= end):
			log.RemoveKey(idx)
		else:
			idx = idx + 1


def ReadFile(fileName, scale, camFov):
	shot = sfm.GetCurrentShot()
	animSet = sfm.GetCurrentAnimationSet()
	
	channelsClip = sfmUtils.GetChannelsClipForAnimSet(animSet, shot)
	
	if channelsClip == None:
		SetError("Selected animation set does not have channels clip.")
		return False
	
	rootControlGroup = animSet.GetRootControlGroup()

	if None == rootControlGroup:
		SetError("Selected animation set does not have rootControlGroup.")
		return False
	
	transformCtrl = rootControlGroup.FindControlByName("transform", True)
	
	if None == transformCtrl:
		SetError("Selected animation set does not have transform control.")
		return False
	
	positionChan = transformCtrl.GetPositionChannel()
	orientationChan = transformCtrl.GetOrientationChannel()
	
	file = open(fileName, 'rU')
	
	rootName = ReadRootName(file)
	if not rootName:
		SetError('Failed parsing ROOT.')
		return False
		
	print 'ROOT:', rootName

	channels = ReadChannels(file)
	if not channels:
		SetError('Failed parsing CHANNELS.')
		return False
		
	frames = ReadFrames(file);
	if frames < 0:
		SetError('Failed parsing Frames.')
		return False
		
	if 0 == frames: frames = 1
	
	frames = float(frames)
		
	frameTime = ReadFrameTime(file)
	if not frameTime:
		SetError('Failed parsing Frame Time.')
		return False
		
	timeOffset = (shot.ToChildMediaTime(vs.DmeTime_t(sfmApp.GetHeadTimeInSeconds()),False) -channelsClip.timeFrame.start.GetValue())
		
	# Prepare curves:
	timeStart = timeOffset
	timeEnd = vs.DmeTime_t(float(frameTime) * float(frames)) +timeOffset
	ClearKeys(positionChan.log,timeStart,timeEnd)
	ClearBookmarks(positionChan.log,0,timeStart,timeEnd)
	ClearBookmarks(positionChan.log,1,timeStart,timeEnd)
	ClearBookmarks(positionChan.log,2,timeStart,timeEnd)
	ClearKeys(orientationChan.log,timeStart,timeEnd)
	ClearBookmarks(orientationChan.log,0,timeStart,timeEnd)
	ClearBookmarks(orientationChan.log,1,timeStart,timeEnd)
	ClearBookmarks(orientationChan.log,2,timeStart,timeEnd)
	
	frameCount = float(0)
	
	lastQuat = None
	
	while True:
		frame = ReadFrame(file, channels)
		if not frame:
			break
		
		frameCount += 1
		
		BTT = vs.DmeTime_t(float(frameTime) * float(frameCount-1)) +timeOffset

		BYP = -frame[0] *scale
		BZP =  frame[1] *scale
		BXP = -frame[2] *scale

		BZR = -frame[3]
		BXR = -frame[4]
		BYR =  frame[5]
		
		positionChan.log.SetKey(BTT, vs.Vector(BXP, BYP, BZP))
		positionChan.log.AddBookmark(BTT, 0)
		positionChan.log.AddBookmark(BTT, 1)
		positionChan.log.AddBookmark(BTT, 2)
		
		quat = vs.Quaternion()
		vs.AngleQuaternion(vs.QAngle(BXR,BYR,BZR), quat)
		
		# Make sure we travel the short way:
		if lastQuat:
			dp = vs.QuaternionDotProduct(lastQuat,quat)
			if dp < 0:
				quat = vs.Quaternion(-quat.x,-quat.y,-quat.z,-quat.w)
		
		lastQuat = quat
		
		orientationChan.log.SetKey(BTT, quat)
		orientationChan.log.AddBookmark(BTT, 0)
		orientationChan.log.AddBookmark(BTT, 1)
		orientationChan.log.AddBookmark(BTT, 2)
	
	if not frameCount == frames:
		SetError("Frames are missing in BVH file.")
		return False
	
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

def ImportCamera():
	fileName, _ = QtGui.QFileDialog.getOpenFileName(None, "Open HLAE BVH File",  "", "HLAE BVH (*.bvh)")
	if not 0 < len(fileName):
		return
	
	oldTimelineMode = sfmApp.GetTimelineMode()

	snap, snapFrame = GetSnapButtons()

	snapChecked = snap.isChecked()
	snapFrameChecked = snapFrame.isChecked()
	
	try:
		sfmApp.SetTimelineMode(3) # Work around timeline bookmark update bug (can't be in Graph Editor or it won't update)
		
		# Work around bug/feature causing programatically inserted keyframes to be snapped:
		if(snapChecked):
			snap.click()
		if(snapFrameChecked):
			snapFrame.click()
			
		if ReadFile(fileName, 1.0, 90.0):
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

ImportCamera()
