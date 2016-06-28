Installation:

Place the *.py files
in the "SourceFilmmaker\game\platform\scripts\sfm\animset" folder.


How to use advancedfx_import_bvh:

BE SURE TO NOT FORGET STEP 4!

1. Edit a clip
2. Add a camera: Right click in empty space on Animation Set Editor and select
   "Create Animation Set for New Camera"
3. Position the head on the timeline, where you want the keyframes to be imported.
4. BE SURE TO TURN OFF "SNAP" AND "SAP FRAME" in the graph editor before importing, otherwise the precision is limited by your project output FPS!
5. Right click the camera in Animation Set Editor and select Rig -> advancedfx_import_bvh

It is possible to import into an camera with existing keyframes, keyframes
in the imported timespan will be removed.

The import will not set the correct FOV for the camera (the BVH file also does
not contain FOV information), that is left up to the user.
Also be aware that CS:GO actually uses an higher FOV than you set in-game:
http://advancedfx.style-productions.net/forum/viewtopic.php?f=17&t=1811


How to use advancedfx_export_bvh:

1. Select a clip
5. Right click the camera your want to export in Animation Set Editor and
   select Rig -> advancedfx_export_bvh

The FPS exported is determined by your project output FPS.




Changelog:

1.0.0
- advancedfx_import_bvh:
  - Minor imporvements
- advancedfx_export_bvh:
  - First version

0.1.0:
- advancedfx_import_bvh:
  - Fixed awkward camera movment / rolling
  - Now allows to import into existing graph data (so you can append / insert into existing camera)

0.0.1:
- advancedfx_import_bvh:
  - First version

