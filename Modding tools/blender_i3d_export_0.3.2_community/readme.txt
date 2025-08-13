LS2009 mods community Blender i3d 1.5 exporter
==============================================

For GIANTS Editor 0.2.5/0.3.0 - 4.0.0
Based on Morc's modified Blender 4.1.2 exporter.

https://komeo.xyz/ls2009mods/

Installation on Windows
-----------------------
1. Download Blender.
   (https://download.blender.org/release/Blender2.48/)
   (https://download.blender.org/release/Blender2.49/)

2. Install Python Runtime 2.6 (http://www.python.org/ftp/python/2.6/python-2.6.msi)

3. Copy blenderI3DExport15C.py to Blenders scripts directory.
   (XP: C:\Documents and Settings\<USERNAME>\Application Data\Blender Foundation\Blender\.blender\scripts)
   (Vista+: %appdata%\Blender Foundation\Blender\.blender\scripts)
  
Installation Linux
------------------
You'll find a hidden directory called ".blender" in your home directory. Inside there's a sub-directory
called "scripts", place the file blenderI3DExport.py there. Restart Blender.

NOTE: This woks only with old distro versions (Python 2.6 is not supported and the executable won't launch on new distro versions).
Use a virtual machine or the Windows version in Wine or run it in a container.

Known issues
------------
 - Exporting an i3d made by this exporter to .obj will fragment the mesh into individual triangles

Change log
----------

0.3.2 (13.8.2025)
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
