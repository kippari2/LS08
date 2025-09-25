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

2. Install Python Runtime 2.6 (http://www.python.org/ftp/python/2.6/python-2.6.msi)

3. Copy blenderI3DExport15C.py and Giants.png to Blenders scripts directory.
   (XP: C:\Documents and Settings\<USERNAME>\Application Data\Blender Foundation\Blender\.blender\scripts)
   (Vista+: %appdata%\Blender Foundation\Blender\.blender\scripts)
  
Installation Linux
------------------
You'll find a hidden directory called ".blender" in your home directory. Inside there's a sub-directory
called "scripts", place the file blenderI3DExport15C.py and Giants.png there. Restart Blender.

Note!
For Linux users, it is recommended to run the Windows version in Wine to get working file paths for Windows games. I recommend using the portable version.
After changes in mesh writing to be more like the original, you should pay more attention to texture size. The current version might not handle large textures
on smaller srufaces as well as the previous arrangement. See "Non-Power-of-Two textures": https://370network.github.io/reGIANTS-docs/gdn.giants.ch/documentation.html#artwork_guide_texturing

Known issues
------------
 - Exporting an i3d made by this exporter to .obj will fragment the mesh into individual triangles

Change log
----------

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
