Installation:

Place the *.py files
in the "SourceFilmmaker\game\platform\scripts\sfm\animset" folder.




How to use advancedfx_import_bvh:

1. Edit a clip
2. Add a camera: Right click in empty space on Animation Set Editor and select
   "Create Animation Set for New Camera"
3. Position the head on the timeline, where you want the keyframes to be imported.
4. Right click the camera in Animation Set Editor and select Rig -> advancedfx_import_bvh

It is possible to import into an camera with existing keyframes, keyframes
in the imported timespan will be removed.

The import will not set the correct FOV for the camera (the BVH file also does
not contain FOV information), that is left up to the user.
Also be aware that CS:GO actually uses an higher FOV than you set in-game:
http://advancedfx.style-productions.net/forum/viewtopic.php?f=17&t=1811




How to use advancedfx_export_bvh:

1. Select a clip
5. Right click the camera you want to export in Animation Set Editor and
   select Rig -> advancedfx_export_bvh

The FPS exported is determined by your project output FPS.




How to use advancedfx_import_gameRecord:

Create an afxGameRecording in HLAE / AfxHookSource, preferably with
low FPS / host_framerate (i.e. 30) and not too long,
because otherwise you will run out of memory upon importing
into SFM!
You can do that using the "mirv_streams record agr" command in HLAE /
AfxHookSource.

To import the recording in SFM:

1. Create an dummy animation set (i.e. camera) on the clip where you want to
   import
2. Right click the created set and in Animation Set Editor and
   select Rig -> advancedfx_import_gameRecord

Attention:

Automatic importing of faulty / broken models (i.e. from the
models\player\custom_player\legacy folder, which is used in older de_cache
demos for example) will cause memory
corruptions that usually lead to a crash of SFM.
To avoid those crashes, don't make such models available to SFM!

Notes:

In the current version keyframes will only be created when the
gameModel is visible, otherwise we save some memory.

Currently this feature is mainly meant to import player models.
It will import some viewmodels too, however those
might be missing arms or have the Error model in SFM, due to being
a custom (skin) model (modelName is '?' then).



Changelog:

1.2.1 (2016-07-16T10:43Z):
 - advancedfx_import_bvh:
   - Now sets gameModel.evaluateProceduralBones = False, to avoid player
     models wrapping and hopefully also avoid crashing SFM (this is
     relevant for demos using the new models in 

1.2.0 (2016-07-15T13:37Z):
 - advancedfx_import_bvh:
   - Improved for AfxHookSource 1.6.0, now handles entity delete envents
     properly and model switching.

1.1.0 (2016-07-15T13:37Z):
 - advancedfx_import_gameRecord:
   - First version
 - advancedfx_import_bvh:
   - Does not create bookmarks for keys anymore, in order to save memory
     (you can add and edit bookmarks manually).

1.0.1 (2016-06-30T19:10Z):
 - advancedfx_import_bvh:
  - Now un-pushes the Snap / Snap Frame tool buttons in timeline if required.

1.0.0 (2016-06-28T21:16Z):
- advancedfx_import_bvh:
  - Minor imporvements
- advancedfx_export_bvh:
  - First version

0.1.0 (2016-06-28T06:07Z):
- advancedfx_import_bvh:
  - Fixed awkward camera movment / rolling
  - Now allows to import into existing graph data (so you can append / insert
    into existing camera)

0.0.1 (2016-06-27T20:58Z):
- advancedfx_import_bvh:
  - First version
