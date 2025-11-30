LS2009 mods community Blender i3D 1.5 exporter
==============================================

For GIANTS Editor 0.2.5/0.3.0 - 4.0.0

https://komeo.xyz/ls2009mods/

Sources for development
-----------------------
https://docs.blender.org/api/2.49/
https://github.com/TheMorc/LS08-things/tree/master/docs/schema (i3d specification schematics)
https://web.archive.org/web/20081218155042/http://gdn.giants.ch/documentation.php#i3d_specification (complementary terminology for the schematics)

Installation on Windows
-----------------------
1. Download Blender.
   (https://download.blender.org/release/Blender2.48/)
   (https://download.blender.org/release/Blender2.49/)

2. Install Python Runtime
   https://www.python.org/downloads/release/python-254/ (Blender 2.48)
   https://www.python.org/downloads/release/python-266/ (blender 2.49)

3. Copy blenderI3DExport15C.py and Giants.png to Blenders scripts directory.
   (XP: C:\Documents and Settings\<USERNAME>\Application Data\Blender Foundation\Blender\.blender\scripts)
   (Vista+: %appdata%\Blender Foundation\Blender\.blender\scripts)
   (Portable Blender: .blender\scripts in the extracted Blender folder)
  
Installation on Linux
-------------------------
Install Wine and then follow the instructions in the Windows section. The original Linux native build no longer works on modern distros and the filepaths would be incompatible with Giants Editor.
I recommend using the portable version.
You can replace the emulated Windows terminal by starting the application from your Linux terminal with "wine [path]blender.exe terminal=true". This will launch
it in the open terminal in wow64 mode. Alternatively, create or edit an existing desktop/start menu shortcut in a text editor with the terminal option enabled.
Wine Bottles needs further experimentation.

Note!
After changes in mesh writing to be more like the original, you should pay more attention to texture size. The current version might not handle large textures
on smaller srufaces as well as the previous arrangement. See "Non-Power-of-Two textures": https://370network.github.io/reGIANTS-docs/gdn.giants.ch/documentation.html#artwork_guide_texturing
Object scaling is supported now, but regardless of it you should apply scale before exporitng objects (select & ctrl+a) to avoid translation and rotation issues.
Script links are disabled until they can be rewritten to work with i3d 1.5.
Currently you can only export one animation per object, ways to export more are being explored.

Known issues
------------
 - Directional lights, armature/bones and cameras are oriented incorrelty after export (for armature this is not critical)

Change log
----------

0.4.1 (30.11.2025)
----------------------
 - Added object and armature animation support
 - Added object scaling support
 - Fixed material export bug when default material is added
 - Fixed verbose logging temp mesh clearing error
 - Reformatted verbose logging prints
 - Help menu pop-up only appears on right and middle click
 - Updated help page

0.4.0 (25.9.2025)
----------------------
 - Added NURBS curve support (used for path creation)
 - Added materials per object support
 - Added armature support
 - Fixed and updated help page
 - Fixed file copy error
 - Fixed vertex colors
 - Optimized mesh creation
 - Disabled script links until they can be refactored
 - Refactored code to be more clean and readable

0.3.2 (14.8.2025)
----------------------
 - Added more texture export options
   - Added absolute path option
   - Added changeable texture folder name for relative path
   - Added file copying to export location for relative path
 - Added project file path export option
 - Added vertex color export option
 - Added verbose logging for trouble shooting
 - Fixed normal and UV export for untriangulated meshes
 - Improved lamp export
   - NoDiffuse and NoSpecular options disable diffuse and specular emission
   - Dist changes range
 - Optimized material export
 - Optimized mesh face creation

0.3.1 (7.6.2025)
----------------------
 - Fixed vertex and face normal hedgehog issue
 - Fixed multi-object export
 - Added multi-material support
 - Fixed specular value mismatch
 - Added emissive material support
 - Added ambient color support (limited to grayscale instead of RGB)
 - Added emissive map support
 - Added normal map bumpDepth (normal maps use the alpha channel for deep depths)
 - Added apply modifiers option
 - Removed unused 09 code

0.2.5-4.0.0 (20.9.2020)
----------------------
 - Modified to export i3d 1.5 format files
