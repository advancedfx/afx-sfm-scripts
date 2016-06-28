Installation:

Place the advancedfx_import_bvh.py file
in the "SourceFilmmaker\game\platform\scripts\sfm\animset" folder.


How to use advancedfx_import_bvh:

Usage:
1. Edit a clip
2. Add a camera: Right click in empty space on Animation Set Editor and select
   "Create Animation Set for New Camera"
3. Position the head on the timeline, where you want the keyframes to be imported.
4. Right click the camera in Animation Set Editor and select Rig -> advancedfx_import_bvh

It is possible to import into an camera with existing keyframes, keyframes
in the imported timespan will be removed.

The import will not set the correct FOV for the camera (the BVH file also does
not contain FOV information), that is left up to the
pros atm (maybe I will make a feature for that in the future).
Also be aware that CS:GO actually uses an higher FOV than you set in-game:
http://advancedfx.style-productions.net/forum/viewtopic.php?f=17&t=1811


advancedfx_export_bvh is still in the making (sorry).


Changelog:

0.1.0:
- advancedfx_import_bvh:
  - Fixed awkward camera movment / rolling
  - Now allows to import into existing graph data (so you can append / insert into existing camera)

0.0.1:
- First version

