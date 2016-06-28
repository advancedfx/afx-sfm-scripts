# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-06-28 by dominik.matrixstorm.com
#
# First changes:
# 2009-09-03 by dominik.matrixstorm.com


# 57.29577951308232087679815481410...
RAD2DEG = 57.2957795130823208767981548141



import sfm;
import sfmUtils;
import sfmApp;
from PySide import QtGui


def SetError(error):
	print 'ERROR:', error
	QtGui.QMessageBox.warning( None, "ERROR:", error )


# <summary> Formats a float value to be suitable for bvh output </summary>
def FloatToBvhString(value):
	return "{0:f}".format(value)


def WriteHeader(file, frames, frameTime):
	file.write("HIERARCHY\n")
	file.write("ROOT MdtCam\n")
	file.write("{\n")
	file.write("\tOFFSET 0.00 0.00 0.00\n")
	file.write("\tCHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
	file.write("\tEnd Site\n")
	file.write("\t{\n")
	file.write("\t\tOFFSET 0.00 0.00 -1.00\n")
	file.write("\t}\n")
	file.write("}\n")
	file.write("MOTION\n")
	file.write("Frames: "+str(frames)+"\n")
	file.write("Frame Time: "+FloatToBvhString(frameTime)+"\n")
	
def LimDeg(val):
	return val

def WriteFile(fileName, scale):
	shot = sfm.GetCurrentShot()
	animSet = sfm.GetCurrentAnimationSet()
	
	dag = sfm.FindDag("transform")
	
	if dag == None:
		SetError("Selected animation set does not have transform DAG node.")
		return False
	
	curFrame = 0
	fps = sfmApp.GetFramesPerSecond()
	frameTime = fps
	if not 0 == frameTime:
		frameTime = 1.0/float(frameTime)
	frameCount = shot.GetDuration().CurrentFrame(vs.DmeFramerate_t(fps))
	
	file = open(fileName, 'wb')
	if not file:
		SetError('Could not open file '+fileName+' for writing')
		return False

	oldFrame = sfm.GetCurrentFrame()
	try:
		WriteHeader(file, frameCount, frameTime)
		
		while curFrame<frameCount:
			sfm.SetCurrentFrame(curFrame)
			
			loc = sfm.GetPosition("transform", space="World")
			rot = sfm.GetRotation("transform", space="World")
			
			X = -loc[1] *scale
			Y =  loc[2] *scale
			Z = -loc[0] *scale
			
			ZR = -rot[0] #*RAD2DEG
			XR = -rot[1] #*RAD2DEG
			YR =  rot[2] #*RAD2DEG
				
			ZR = LimDeg(ZR)
			XR = LimDeg(XR)
			YR = LimDeg(YR)
			
			S = "" +FloatToBvhString(X) +" " +FloatToBvhString(Y) +" " +FloatToBvhString(Z) +" " +FloatToBvhString(ZR) +" " +FloatToBvhString(XR) +" " +FloatToBvhString(YR) + "\n"
			file.write(S)
			
			curFrame += 1
				
	finally:
		file.close()
		sfm.SetCurrentFrame(oldFrame)
	
	if not curFrame == frameCount:
		SetError("Could not write all frames.")
		return False
	
	return True


def ExportCamera():
	#value, ok = QtGui.QInputDialog.getDouble(None, "Enter export FPS", "Frames Per Second", 60, 0.001, 1000000, 3)
	#if not ok:
	#	return
	
	fileName, _ = QtGui.QFileDialog.getSaveFileName(None, "Save HLAE BVH File",  "", "HLAE BVH (*.bvh)")
	if not 0 < len(fileName):
		return
	
	sfm.SetOperationMode( "Play" )
	
	try:
		if WriteFile(fileName, 1.0):
			print 'Done.'
		else:
			print 'FAILED'
	finally:
		sfm.SetOperationMode( "Pass" )


ExportCamera()
