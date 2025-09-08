#!BPY

"""
Name: 'GIANTS Engine 0.2.5 - 4.0.0 (.i3d)...'
Blender: 248
Group: 'Export'
Tooltip: 'Export to a GIANTS i3D file'
"""

__author__ = "Kippari2 (KLS Mods)"
__url__ = ("Kippari2 Github, https://github.com/kippari2/", "Published on, https://komeo.xyz/ls2009mods/")
__version__ = "0.4.0"
__email__ = "kipparizz34@gmail.com"
__bpydoc__ = """\
Exports to Giants .i3d file.

Supported:<br>
Objects<br>
-Empty<br>
-Lights (directional, spot, point)<br>
-Camera (persp)<br>
-NURBS curves<br>
Mesh types<br>
-Basic meshes<br>
-Armature deform (skinned mesh)<br>
Material specular shaders<br>
-Phong<br>
-CookTorr<br>
Material color shaders<br>
-Solid color (diffuse)<br>
-Vertex color<br>
-Emissive<br>
-Transparent/transluscent (Ztransp)<br>
-Ambient color<br>
Material links<br>
-Linked to object<br>
-Linked to mesh<br>
Image maps<br>
-Texture<br>
-Specular<br>
-Emissive<br>
-Normal

Usage:<br>
-Place this script in %appdata%/Blender Foundation/Blender/.blender/scripts directory.<br>
-Open file menu in blender.<br>
-Choose Export -> GIANTS Engine 0.2.5 - 4.0.0 (.i3d)...

Note!<br>
-Skin weights and modifiers options can't be used at the same time! This is due to the inability to exclude the armature modifier without actually deforming the mesh and causing headaches for you.<br>
-If your object turns out pink you probably forgot to assign a material.<br>
-If its black you probably forgot to UV unwrap it.<br>
-Mat script and obj script links are not functional yet. I haven't figured out how they work.
"""

from Blender import Scene, Mesh, Window, sys, Mathutils, Draw, Image, BGL, Get, Material, Text, Texture, Get, ShowHelp, Object, Curve
import BPyMessages
import bpy
import math
import os
import shutil
from xml.dom.minidom import Document, parseString
true = 1
false = 0

class I3d:
	def __init__(self, name="untitled"):
		if verboseLogging:
			print("LS2009 Mods community i3D 1.5 exporter version 0.4.0")
			print("enabled export options (1=true, 0=false)")
			exportOptionsToPrint = {
				"modifiers": exportModifiers,
				"skin weights": exportSkinWeights,
				"vertex colors": exportVertexColors,
				"UV maps": exportUVMaps,
				"triangulated": exportTriangulated,
				"normals": exportNormals,
				"export selection": exportSelection,
				"project path": exportProjectPath,
				"texture relative path": relative}
			for k, v in exportOptionsToPrint.items():
				print("%s: %i" %(k, v))
			del exportOptionsToPrint
			print("------------------------")
			print("starting export to file")
		self.doc = Document()
		self.root = self.doc.createElement("i3D")
		self.root.setAttribute("name", name)
		self.root.setAttribute("version", "1.5")
		self.root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
		self.root.setAttribute("exporter", "LS2009 mods community i3D exporter")
		self.root.setAttribute("xsi:noNamespaceSchemaLocation", "https://github.com/TheMorc/LS08-things/blob/master/docs/schema/i3d-1.5f.xsd")		
		self.doc.appendChild(self.root)
		
		self.asset = self.doc.createElement("Asset")
		if exportProjectPath:
			self.asset.setAttribute("filename", "%s" % Get("filename"))
		self.root.appendChild(self.asset)
		exportProgram = self.doc.createElement("Export")
		exportProgram.setAttribute("program", "Blender %s.%s" %(str(Get("version"))[:1], str(Get("version"))[-2:]))
		exportProgram.setAttribute("version", "0.4.0")
		self.asset.appendChild(exportProgram)
		
		self.files = self.doc.createElement("Files")
		self.root.appendChild(self.files)
		self.materials = self.doc.createElement("Materials")
		self.defaultMat = false
		self.root.appendChild(self.materials)
		self.shapes = self.doc.createElement("Shapes")
		self.root.appendChild(self.shapes)
		self.scene = self.doc.createElement("Scene")
		self.root.appendChild(self.scene)
		self.lastNodeId = 0 #Needed until obj script links gets reworked
		#self.texturCount = 0
		self.animation = self.doc.createElement("Animation")
		self.animationSets = self.doc.createElement("AnimationSets")
		self.animation.appendChild(self.animationSets)
		self.root.appendChild(self.animation)
		self.userAttributes = self.doc.createElement("UserAttributes")
		self.root.appendChild(self.userAttributes)
		self.meshesToClear = []
		self.boneNames = None
	
	def setTranslation(self, node, pos):
		node.setAttribute("translation", "%f %f %f" %(pos[0], pos[2], -pos[1]))

	def setRotation(self, node, rot, rotX90, armature=false):
		ro1, ro2, ro3 = rot[0], rot[2], -rot[1]
		rot[0], rot[1], rot[2] = math.degrees(rot[0]), math.degrees(rot[2]), math.degrees(-rot[1])
		if armature:
			rot[0], rot[1], rot[2] = ro1, ro2, ro3
		RotationMatrix= Mathutils.RotationMatrix
		MATRIX_IDENTITY_3x3 = Mathutils.Matrix([1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])
		x,y,z = rot[0]%360,rot[1]%360,rot[2]%360 # Clamp all values between 0 and 360, values outside this raise an error
		xmat = RotationMatrix(x,3,'x')
		ymat = RotationMatrix(y,3,'y')
		zmat = RotationMatrix(z,3,'z')
		eRot = (xmat*(zmat * (ymat * MATRIX_IDENTITY_3x3))).toEuler()
		if rotX90:
			eRot.x = eRot.x-90
		node.setAttribute("rotation", "%f %f %f" %(eRot.x, eRot.y, eRot.z))

	#Parse ScriptLink file and merge xml into i3d
	#Most likely broken, untested due to lack in skills :/
	def addObjScriptLinks(self, obj):
		for sl in obj.getScriptLinks("FrameChanged") + obj.getScriptLinks("Render") + obj.getScriptLinks("Redraw") + obj.getScriptLinks("ObjectUpdate") + obj.getScriptLinks("ObDataUpdate"):
			if sl.endswith(".i3d"):
				if verboseLogging:
					print("parsing object script link %s" %sl)
				xmlText = ""
				#print Text.Get(sl).asLines()
				for l in Text.Get(sl).asLines():
					xmlText = xmlText + l.replace("i3dNodeId", "%i" %self.lastNodeId)
				#print "xml: ",xmlText
				#slDom = parseString(xmlText)
				slDom = None
				try:
					slDom = parseString(xmlText)
				except:
					print("WARNING: cant parse object script link %s" %sl)
				if not slDom is None:
					for ua in slDom.getElementsByTagName("UserAttribute"):
						self.userAttributes.appendChild(ua)

					for st in slDom.getElementsByTagName("SceneType"):
						i = 0
						while i < st.attributes.length:
							attr = st.attributes.item(i)
							node.setAttribute(attr.nodeName, attr.nodeValue)
							i = i+1
	
	def addObject(self, obj): #Adds a scene node.
		#print("add object %s" %(obj.getName()))
		node = None
		parentNode = self.scene
		if not obj.getParent() is None:
			#Searching parent assuming it is already in i3d (must export ordered by hierarchy)
			for sceneNode in self.scene.getElementsByTagName("Shape"):
				if sceneNode.getAttribute("name") == obj.getParent().getName():
					parentNode = sceneNode
					break
			if parentNode == self.scene:
				for sceneNode in self.scene.getElementsByTagName("TransformGroup"):
					if sceneNode.getAttribute("name") == obj.getParent().getName():
						parentNode = sceneNode
						break
			if parentNode == self.scene:
				print("parent not found for object %s" % obj.getName())
		rotX90 = false

		if verboseLogging:
			print("adding object %s with type %s" %(obj.getName(), obj.getType()))
		
		if obj.type == "Mesh":
			me = obj.getData(mesh=1)
			if exportModifiers and len(obj.modifiers) > 0: #Unfortunately, it seems like it is not possible to exclude armature form getting applied
				me = bpy.data.meshes.new()
				me.getFromObject(obj)
				self.meshesToClear.append(me)
			node = self.doc.createElement("Shape")

			#Materials are linked using a colbit
			#1 for mat per object, 0 for obData
			materialList = None
			if len(obj.getMaterials()) > 0 and obj.colbits == 1:
				materialList = obj.getMaterials()
				if verboseLogging:
					print("materials for object %s are linked to object" %obj.getName())
			elif len(me.materials) > 0 and obj.colbits == 0:
				materialList = me.materials
				if verboseLogging:
					print("materials for object %s are linked to mesh" %obj.getName())
			self.addMesh(me, materialList)
			node.setAttribute("ref", "%s" %me.name)

			if self.boneNames is not None:
				skinBinds = ""
				for bn in self.boneNames:
					if skinBinds == "":
						skinBinds = bn
					else:
						skinBinds = "%s %s" %(skinBinds, bn)
				node.setAttribute("skinBindNodes", "%s" %skinBinds)
				if verboseLogging:
					print("object %s has skin binds: %s" %(obj.getName(), skinBinds))
			
			#Shading properties are stored per object in Giants: getting them from first Blender material
			if not materialList is None and materialList[0]:
				mat = materialList[0]
				if mat.getMode() & Material.Modes['SHADOWBUF']:
					node.setAttribute("castsShadows", "true")
				else:
					node.setAttribute("castsShadows", "false")
				if mat.getMode() & Material.Modes['SHADOW']:
					node.setAttribute("receiveShadows", "true")
				else:
					node.setAttribute("receiveShadows", "false")
			else:
				node.setAttribute("castsShadows", "false")
				node.setAttribute("receiveShadows", "false")
		elif obj.type == "Empty":
			node = self.doc.createElement("TransformGroup")
		elif obj.type == "Armature":
			node = self.doc.createElement("TransformGroup")
			self.boneNames = self.addArmature(node, obj.getData(), obj)
		elif obj.type == "Camera":
			rotX90 = true
			node = self.doc.createElement("Camera")
			node.setAttribute("fov", "%f" %(obj.getData().lens))
			node.setAttribute("nearClip", "%f" %(obj.getData().clipStart))
			node.setAttribute("farClip", "%f" %(obj.getData().clipEnd))
		elif obj.type == "Lamp":
			rotX90 = true #Lamps suffer from similar orientation issue as bones do
			node = self.doc.createElement("Light")
			lamp = obj.getData()
			lampType = ["point", "directional", "spot", "ambient"]
			if lamp.getType() > 3:
				node.setAttribute("type", lampType[0])
				print("WARNING: lamp type not supported")
			else:
				node.setAttribute("type", lampType[lamp.getType()])
			node.setAttribute("diffuseColor", "%f %f %f" %(lamp.R*lamp.energy, lamp.G*lamp.energy, lamp.B*lamp.energy))
			if lamp.getMode() & lamp.Modes['NoDiffuse']:
				node.setAttribute("emitDiffuse", "false")
			else:
				node.setAttribute("emitDiffuse", "true")
			node.setAttribute("specularColor", "%f %f %f" %(lamp.R*lamp.energy, lamp.G*lamp.energy, lamp.B*lamp.energy))
			if lamp.getMode() & lamp.Modes['NoSpecular']:
				node.setAttribute("emitSpecular", "false")
			else:
				node.setAttribute("emitSpecular", "true")
			node.setAttribute("decayRate", "%f" %(5000-lamp.getDist()))
			node.setAttribute("range", "%f" %lamp.getDist())
			if lamp.getMode() & lamp.Modes['Shadows']:
				node.setAttribute("castShadowMap", "true")
			else:
				node.setAttribute("castShadowMap", "false")
			node.setAttribute("depthMapBias", "%f" %(lamp.bias/1000))
			node.setAttribute("depthMapResolution", "%i" %lamp.bufferSize)
			node.setAttribute("coneAngle", "%f" %(lamp.getSpotSize()))
			node.setAttribute("dropOff", "%f" %(lamp.getSpotBlend()*5))
		elif obj.type == "Curve":
			curve = obj.getData()
			if curve.isNurb():
				node = self.doc.createElement("Shape")
				self.addCurve(curve)
				node.setAttribute("ref", "%s" %(curve.name))
			else:
				print("ERROR: can't export curve %s with type %s" %(obj.name, curve.getType()))

		if not node is None:
			node.setAttribute("name", obj.getName())
			#getLocation("localspace") seems to be buggy!
			#http://blenderartists.org/forum/showthread.php?t=117421
			localMat = Mathutils.Matrix(obj.matrixLocal)
			self.setTranslation(node, localMat.translationPart())			
			self.setRotation(node, obj.getEuler("localspace"), rotX90)
			parentNode.appendChild(node)
			self.addObjScriptLinks(obj)
		else:
			print("ERROR: cant export %s: %s" %(obj.type, obj.getName()))

	def addCurve(self, curve):
		controlVerts = self.doc.createElement("NurbsCurve")
		controlVerts.setAttribute("name", "%s" %curve.name)
		controlVerts.setAttribute("degree", "%s" %curve.getResolu())
		if curve.isCyclic():
			form = "close" #There is a third form called "periodic" that will be supported later
		else:
			form = "open"
		controlVerts.setAttribute("form", "%s" %form)
		#Giants Engine will read multiple curves within an object as one continuous curve
		#Use separate curve objects if you want more than one curve
		if len(curve) > 1:
			print("WARNING: no more than 1 curve per object supported in object %s" %curve.name)
		for i in range(len(curve[0])):
			cv = self.doc.createElement("cv")
			cv.setAttribute("c", "%f %f %f" %(curve[0][i][0], curve[0][i][2], -curve[0][i][1]))
			controlVerts.appendChild(cv)
		self.shapes.appendChild(controlVerts)

	def addArmature(self, parentNode, arm, obj):
		#print("adding armature %s" %(arm.name))
		boneNameIndex = []
		def addBone(self, parent, bone):
			#print "adding bone %s to %s"%(bone.name, parent.getAttribute("name"))
			boneNode = self.doc.createElement("TransformGroup")
			boneNode.setAttribute("name", bone.name)
			parentBone = bone.parent
			#parentMatrix is the matrix of the bone in parent space
			#Ported from md5 exporter
			if not parentBone is None:
				parentMatrix = Mathutils.Matrix(bone.matrix['ARMATURESPACE'])*Mathutils.Matrix(parentBone.matrix['ARMATURESPACE']).invert()
			else:
				parentMatrix = Mathutils.Matrix(bone.matrix['ARMATURESPACE'])
			boneNameIndex.append(bone.name)
			self.setTranslation(boneNode, parentMatrix.translationPart())
			self.setRotation(boneNode, parentMatrix.rotationPart().toEuler(), false, true)
			#Make Y point where the Z axis points
			#Tried rotX90 while swapping Z translation to be the Y, but some things break because of it
			#Maybe I could do some disgusting hack that uses a rotated temp mesh and skeleton, but that sounds like problems waiting to happen
			#Plsss hellppp I have 0 clue how to do this :(
			#Another thing to do would be inverse kinematics, but there's literally 0 i3d docs on that
			parent.appendChild(boneNode)
			for b in bone.children:
				addBone(self, boneNode, b)

		for bone in arm.bones.values():
			if bone.hasParent()==0:
				addBone(self, parentNode, bone)
		return boneNameIndex

	def addSkinWeights(self, mesh, vert):
		vertexGroups = getVGroup(vert.index, mesh)
		boneWeights = ""
		boneIndices = ""
		weights = []
		for vg in vertexGroups:
			bi = 0
			for bn in self.boneNames:
				if vg[0] == bn and not vg[1] == 0:
					weights.append(vg[1])
					if boneIndices == "":
						boneIndices = "%i" %bi
					else:
						boneIndices = "%s %i" %(boneIndices, bi)
				bi = bi + 1
		newWeights = calculateWeights(weights)
		for w in newWeights:
			if boneWeights == "":
				boneWeights = "%f" %w
			else:
				boneWeights = "%s %f" %(boneWeights, w)
		cv = self.doc.createElement("cv")
		cv.setAttribute("w", boneWeights)
		cv.setAttribute("bi", boneIndices)
		return cv

	def createTriFace(self, mesh, vertexOrder, face):
		tri = self.doc.createElement("f")
		tri.setAttribute("vi", "%i %i %i" %(face.v[vertexOrder[0]].index, face.v[vertexOrder[1]].index, face.v[vertexOrder[2]].index))
		if exportVertexColors and mesh.vertexColors:
			realColorR = []
			realColorG = []
			realColorB = []
			for vertCol in face.col:
				for i in range(3):
					realColorR.append(vertCol.r/255.0) #Not sure if vertex colors are supposed to look so washed
					realColorG.append(vertCol.g/255.0)
					realColorB.append(vertCol.b/255.0)
					#print("vertex %i %f %f %f" %(i, realColorR[i], realColorG[i], realColorB[i]))
			tri.setAttribute("c", "%f %f %f %f %f %f %f %f %f" %(realColorR[0], realColorG[0], realColorB[0], realColorR[1], realColorG[1], realColorB[1], realColorR[2], realColorG[2], realColorB[2]))
		if evtExportUVMaps and mesh.faceUV:
			#Attempetd multi-UV support, but it only loads one texture (yes the other one was transparent and coords correct)
			#How does it even work????? There are no examples!!!
			#for i in range(self.texturCount):
				#tri.setAttribute("t%i" % i, "%f %f %f %f %f %f" % (face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y))
			tri.setAttribute("t0", "%f %f %f %f %f %f" %(face.uv[vertexOrder[0]].x, face.uv[vertexOrder[0]].y, face.uv[vertexOrder[1]].x, face.uv[vertexOrder[1]].y, face.uv[vertexOrder[2]].x, face.uv[vertexOrder[2]].y))
		if exportNormals:
			if face.smooth:
				tri.setAttribute("n", "%f %f %f %f %f %f %f %f %f" %(face.v[vertexOrder[0]].no.x, face.v[vertexOrder[0]].no.z, -face.v[vertexOrder[0]].no.y, face.v[vertexOrder[1]].no.x, face.v[vertexOrder[1]].no.z, -face.v[vertexOrder[1]].no.y, face.v[vertexOrder[2]].no.x, face.v[vertexOrder[2]].no.z, -face.v[vertexOrder[2]].no.y))
			else:
				tri.setAttribute("n", "%f %f %f %f %f %f %f %f %f" %(face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y))
		tri.setAttribute("ci", "%i" %(face.mat if face.mat is not None else 0))
		return tri

	def createQuadFace(self, mesh, vertexOrder, face):
		quad = self.doc.createElement("f")
		quad.setAttribute("vi", "%i %i %i %i" %(face.v[vertexOrder[0]].index, face.v[vertexOrder[1]].index, face.v[vertexOrder[2]].index, face.v[vertexOrder[3]].index))
		if exportVertexColors and mesh.vertexColors:
			realColorR = []
			realColorG = []
			realColorB = []
			for vertCol in face.col:
				for i in range(4):
					realColorR.append(vertCol.r/255.0)
					realColorG.append(vertCol.g/255.0)
					realColorB.append(vertCol.b/255.0)
					#print("vertex %i %f %f %f" %(i, realColorR[i], realColorG[i], realColorB[i]))
			quad.setAttribute("c", "%f %f %f %f %f %f %f %f %f %f %f %f" %(realColorR[0], realColorG[0], realColorB[0], realColorR[1], realColorG[1], realColorB[1], realColorR[2], realColorG[2], realColorB[2], realColorR[3], realColorG[3], realColorB[3]))
		if evtExportUVMaps and mesh.faceUV:
			#for i in range(self.texturCount):
				#quad.setAttribute("t%i" % i, "%f %f %f %f %f %f" % (face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y))
			quad.setAttribute("t0", "%f %f %f %f %f %f %f %f" %(face.uv[vertexOrder[0]].x, face.uv[vertexOrder[0]].y, face.uv[vertexOrder[1]].x, face.uv[vertexOrder[1]].y, face.uv[vertexOrder[2]].x, face.uv[vertexOrder[2]].y, face.uv[vertexOrder[3]].x, face.uv[vertexOrder[3]].y))
		if exportNormals:
			if face.smooth:
				quad.setAttribute("n", "%f %f %f %f %f %f %f %f %f %f %f %f" %(face.v[vertexOrder[0]].no.x, face.v[vertexOrder[0]].no.z, -face.v[vertexOrder[0]].no.y, face.v[vertexOrder[1]].no.x, face.v[vertexOrder[1]].no.z, -face.v[vertexOrder[1]].no.y, face.v[vertexOrder[2]].no.x, face.v[vertexOrder[2]].no.z, -face.v[vertexOrder[2]].no.y, face.v[vertexOrder[3]].no.x, face.v[vertexOrder[3]].no.z, -face.v[vertexOrder[3]].no.y))
			else:
				quad.setAttribute("n", "%f %f %f %f %f %f %f %f %f %f %f %f" %(face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y))
		quad.setAttribute("ci", "%i" %(face.mat if face.mat is not None else 0))
		return quad

	def addMesh(self, mesh, materialList):
		faces = self.doc.createElement("Faces")
		ifs = self.doc.createElement("IndexedFaceSet")
		ifs.setAttribute("name", mesh.name)
		self.shapes.appendChild(ifs)
		verts = self.doc.createElement("Vertices")
		if not self.boneNames is None and exportSkinWeights:
			skinWeights = self.doc.createElement("SkinWeights")

		if verboseLogging:
			print("adding mesh %s with %i vertices" %(mesh.name, len(mesh.verts)))

		for vert in mesh.verts:
			v = self.doc.createElement("v")
			v.setAttribute("c", "%f %f %f" %(vert.co.x, vert.co.z, -vert.co.y))
			verts.appendChild(v)
			if not self.boneNames is None and exportSkinWeights:
				skinWeights.appendChild(self.addSkinWeights(mesh, vert))

		def defineFace(self, face):
			if exportTriangulated and len(face.v) == 4: #It's a quad and user chose to triangulate along shortest edge
				if (face.v[0].co - face.v[2].co).length < (face.v[1].co - face.v[3].co).length:
					vertexOrder = [0, 1, 2]
					faces.appendChild(self.createTriFace(mesh, vertexOrder, face))
					vertexOrder = [2, 3, 0]
					faces.appendChild(self.createTriFace(mesh, vertexOrder, face))
				else:
					vertexOrder = [1, 2, 3]
					faces.appendChild(self.createTriFace(mesh, vertexOrder, face))
					vertexOrder = [3, 0, 1]
					faces.appendChild(self.createTriFace(mesh, vertexOrder, face))
			else:
				if len(face.v)==4: #It's a quad and is exported as one
					vertexOrder = [0, 1, 2, 3]
					faces.appendChild(self.createQuadFace(mesh, vertexOrder, face))
				else: #It should be a triangle since Blender doesn't support ngons, or the face is a triangle
					vertexOrder = [0, 1, 2]
					faces.appendChild(self.createTriFace(mesh, vertexOrder, face))

		shaderlist = ""
		materialCount = 0
		for mat in materialList:
			materialCount = materialCount + 1
			self.addMaterial(mat)
			if not mat is None and shaderlist == "":
				shaderlist = mat.name
			elif not mat is None:
				shaderlist = "%s, %s" %(shaderlist, mat.name)
			else:
				shaderlist = "Default"
			#We could have done this a much faster and cleaner way, but the Giants engine just can't handle it when material indices are not in a particular order
			#DON'T TOUCH THE LOGIC UNLESS YOU WANT TO HAVE HOLES IN YOUR MESH!!!
			for face in mesh.faces:
				if face.mat == materialCount-1:
					defineFace(self, face)

		faces.setAttribute("shaderlist", "%s" %(shaderlist))

		ifs.appendChild(verts)
		if not self.boneNames is None and exportSkinWeights:
			ifs.appendChild(skinWeights)
		ifs.appendChild(faces)

	def addImageMaps(self, textur):
		path = textur.tex.getImage().getFilename()
		if textur.mtNor: #Map To Nor
			if verboseLogging:
				print("adding normal map %s" %textur.tex.getName())
			if textur.mtNor == -1:
				print("WARNING: normalmap %s cannot be inverted by the exporter" %textur.tex.getName())
			i3dTex = self.doc.createElement("Normalmap")
			if textur.norfac > 0:
				i3dTex.setAttribute("bumpDepth", "%f" %textur.norfac) #Can't test this properly until proper transparent normal maps can be created
			i3dTex.setAttribute("name", "%s" %self.addFile(path))
			#print(textur.norfac)
		elif textur.mtCsp: #Map To Spec
			if verboseLogging:
				print("adding specular map %s" %textur.tex.getName())
			if textur.mtSpec == -1:
				print("WARNING: specularmap %s cannot be inverted by the exporter" %textur.tex.getName())
			i3dTex = self.doc.createElement("Glossmap")
			i3dTex.setAttribute("name", "%s" %self.addFile(path))
		elif textur.mtEmit: #Map To Emit
			if verboseLogging:
				print("adding emissive map %s" %textur.tex.getName())
			if textur.mtEmit == -1:
				print("WARNING: emissivemap %s cannot be inverted by the exporter" %textur.tex.getName())
			i3dTex = self.doc.createElement("Emissivemap")
			i3dTex.setAttribute("name", "%s" %self.addFile(path))
		elif textur.mtCol: #Map To Col
			if verboseLogging:
				print("adding image texture %s" %textur.tex.getName())
			i3dTex = self.doc.createElement("Texture")
			i3dTex.setAttribute("name", "%s" %self.addFile(path))
		#TODO: other maps
		return i3dTex

	#Parse material ScriptLink file and merge xml into i3d (if it ends with .i3d)
	def addMatScriptLink(self, mat, m):
		for sl in mat.getScriptLinks("FrameChanged") + mat.getScriptLinks("Render") + mat.getScriptLinks("Redraw") + mat.getScriptLinks("ObjectUpdate") + mat.getScriptLinks("ObDataUpdate"):
			if sl.endswith(".i3d"):
				if verboseLogging:
					print("parsing material script link %s" %sl)
				xmlText = ""
				for l in Text.Get(sl).asLines():
					xmlText = xmlText + l
				slDom = None
				try:
					slDom = parseString(xmlText)
				except:
					print "WARNING: cant parse material script link %s" %sl
					slDom = None
				if not slDom is None:
					for n in slDom.getElementsByTagName("Material"):
						i = 0
						while i < n.attributes.length: #Copy attributes
							attr = n.attributes.item(i)
							if attr.nodeValue.startswith(folderName+"/"):
								m.setAttribute(attr.nodeName, "%i" %self.addFile(attr.nodeValue))
							else:
								m.setAttribute(attr.nodeName, attr.nodeValue)
							i = i+1
						for cn in n.childNodes: #Copy child elements
							if cn.nodeType == cn.ELEMENT_NODE:
								#print cn
								if not cn.attributes is None:
									i = 0
									while i < cn.attributes.length:
										attr = cn.attributes.item(i)
										if attr.nodeValue.startswith(folderName+"/"):
											attr.nodeValue = "%i" %self.addFile(attr.nodeValue) #Nesting hell O-o
										i = i+1
								m.appendChild(cn)

	def addMaterial(self, mat):
		if mat is None and not self.defaultMat: #Create a nice pink default materials
			m = self.doc.createElement("Material")
			m.setAttribute("name", "Default")
			m.setAttribute("diffuseColor", "%f %f %f %f" %(1, 0, 1, 1))
			self.materials.appendChild(m)
			self.defaultMat = true
			print("WARNING: no materials assigned -> added pink default material")
			return

		duplicateMaterial = false
		for m in self.materials.getElementsByTagName("Material"):
			if m.getAttribute("name") == mat.getName():
				#print(m.getAttribute("name"))
				duplicateMaterial = true

		if not duplicateMaterial:
			if verboseLogging:
				print("adding material %s" %mat.name)

			m = self.doc.createElement("Material")
			m.setAttribute("name", mat.name)

			if not mat.getEmit() > 0:
				m.setAttribute("diffuseColor", "%f %f %f %f" %(mat.getRGBCol()[0]*mat.ref, mat.getRGBCol()[1]*mat.ref, mat.getRGBCol()[2]*mat.ref, mat.getAlpha()))
			if mat.getAlpha() < 1:
				m.setAttribute("alphaBlending", "true")
			if mat.getSpec() > 0:
				m.setAttribute("specularColor", "%f %f %f" %(mat.getSpecCol()[0]*mat.getSpec()/2, mat.getSpecCol()[1]*mat.getSpec()/2, mat.getSpecCol()[2]*mat.getSpec()/2))
			if mat.getHardness() > 0:
				m.setAttribute("cosPower", "%i" %mat.getHardness())
			if mat.getEmit() > 0:
				m.setAttribute("emissiveColor", "%f %f %f" %(mat.getRGBCol()[0]*mat.getEmit()/2, mat.getRGBCol()[1]*mat.getEmit()/2, mat.getRGBCol()[2]*mat.getEmit()/2))
			if mat.getMode() & Material.Modes['NOMIST']:
				m.setAttribute("allowFog", "false")
			if mat.getAmb() > 0:
				m.setAttribute("ambientColor", "%f %f %f" %(mat.getAmb(), mat.getAmb(), mat.getAmb())) #mat.getRGBCol()[0]*mat.amb

			texturNum = 0
			for textur in mat.getTextures():
				texturEnabled = 0
				for t in mat.enabledTextures:
					if t == texturNum:
						texturEnabled = true
						break
				if texturEnabled and exportUVMaps:
					if textur.tex.getImage() is None or textur.tex.getImage().getFilename() is None:
						print("WARNING: cannot export texture named %s, it's not an image!" %textur.tex.getName())
					else:
						m.appendChild(self.addImageMaps(textur))
				texturNum = texturNum + 1
		
			self.addMatScriptLink(mat, m)
		self.materials.appendChild(m)

	def copyAssets(self, assetPath):
		j, assetName = os.path.split(assetPath)
		del j #We don't like this variable
		head, path = os.path.split(exportPath.val)
		path = os.path.join(head, folderName)
		if not os.path.isdir(path) and folderName is not None:
			os.mkdir(path)
			if verboseLogging:
				print("created texure folder at %s" %path)
		if not assetPath == os.path.join(path, assetName):
			shutil.copy(assetPath, path)
			if verboseLogging:
				print("copying asset %s to: %s" %(assetName, path))

	def addFile(self, path):
		newFileId = 1
		for f in self.files.childNodes:
			if f.getAttribute("filename") == path:
				#print("file %s is already added, its id is %s" %(path, f.getAttribute("name")))
				return f.getAttribute("name")
			stringName = f.getAttribute("name")
			stringName = stringName.replace("file", "")
			#print(stringName)
			fileId = int(stringName) #This int->string juggling is unnecessary, but we are using the original naming shceme for lulz
			if fileId >= newFileId:
				newFileId = fileId + 1
		f = self.doc.createElement("File")
		if relative:
			absolutePath = path
			path, tail = os.path.split(path)
			path = os.path.join(folderName, tail)
			if verboseLogging:
				print("adding file path %s" %path)
			f.setAttribute("relativePath", "true")
			self.copyAssets(absolutePath)
		else:
			if verboseLogging:
				print("adding file path %s" %path)
			f.setAttribute("relativePath", "false")
		f.setAttribute("name", "file%i" %newFileId)
		f.setAttribute("filename", path)
		self.files.appendChild(f)
		return f.getAttribute("name")
	
	def clearTempMesh(self):
		for me in self.meshesToClear:
			if verboseLogging:
				print("clearing temp mesh %s" %me.getName())
			me.verts = None
	
	def printToFile(self, filepath):
		out = file(filepath, 'w')
		out.write(self.doc.toprettyxml())
		out.close()
		self.clearTempMesh()

#-------END of i3d class------------------------------------------------------------------

#get a list of vertexGroups and asociated weights this vertex belongs to
def getVGroup(vertIndex, mesh):
	groupWeight = []
	for group in mesh.getVertGroupNames():
		singleElement = mesh.getVertsFromGroup(group, 1, [vertIndex])
		if len(singleElement) == 1:
			groupWeight.append({0:group, 1:singleElement[0][1]})
		elif len(singleElement) == 0:
			pass
		else:
			print "SCARRY!"
	return groupWeight

#Blender does not adhere to the rule where all weights add up to 1 and we have to recalculate them
#Weight to weight ratios have to be kept the same
def calculateWeights(calculate):
	calculated = []
	weightCount = len(calculate)
	if weightCount > 1:
		weightSum = sum(calculate)
		if weightSum < 1:
			increment = (1-weightSum)/weightCount
			calculated = [w + increment for w in calculate]
		if weightSum > 1:
			subtract = (weightSum-1)/weightCount
			calculated = [w - subtract for w in calculate]
	elif weightCount  == 1 and calculate[0] < 1:
		calculated = [1]
	else:
		calculated = calculate
	return calculated

#GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI
#  GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI
#    GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI
#  GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI
#GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI      GUI

# Assign event numbers to buttons
evtExport = 1
evtNameChanged = 2
evtBrows = 3
evtExportSelection = 4
evtExportNormals = 5
evtExportTriangulated = 6
evtAddObjExtension = 7
evtAddMatExtension = 8
evtExportModifiers = 9
evtExportProjectPath = 10
evtRelativePath = 11
evtDoNothing = 12
evtExportProjectPath = 13
evtExportSkinWeights = 14
evtExportVertexColors = 15
evtExportUVMaps = 16
evtVerboseLogging = 17

#Toggle button states
exportModifiers = true
exportSkinWeights = false
exportVertexColors = true
exportUVMaps = true
exportSelection = false
exportNormals = true
exportTriangulated = true
exportProjectPath = false
verboseLogging = false
relative = true

#Global button return values to avoid memory leaks
guiExport = 0
guiRelativePath = 0
guiBrows = 0
guiExportModifiers = 0
guiExportSkinWeights = 0
guiExportVertexColors = 0
guiExportUVMaps = 0
guiExportNormals = 0
guiExportTriangulated = 0
guiAddObjExtension = 0
guiAddMatExtension = 0
guiExportSelection = 0
guiExportProjectPath = 0
guiVeboseLogging = 0
guiLogo = 0
stop = 0
showHelp = 0
guiPopup = 0

#Text boxes
folderName = "assets"
exportPath = Draw.Create(Get("filename")[0:Get("filename").rfind(".")]+".i3d")

#mouse x/y (just for fun)
#mouseX = 0
#mouseY = 0

logo = false
try:
	logo = Image.Load(Get("scriptsdir")+"/Giants.png")
except:
	logo = false
	

def gui():
	global evtExport, evtNameChanged, evtBrows, evtPathChangedActive, evtDoNothing
	global exportPath, texturePath, folderName
	global guiExport, guiBrows, guiRelativePath, guiExportModifiers, guiExportSkinWeights, guiExportVertexColors, guiExportUVMaps, guiExportTriangulated, guiExportNormals, guiExportSelection, guiVeboseLogging, guiAddObjExtension, guiAddMatExtension, guiLogo
	
	guiAddObjExtension = Draw.PushButton("Add obj script link", evtAddObjExtension, 10, 250, 150, 25, "Add a text file for more i3d object properties and link it to the active object via script links")
	guiAddMatExtension = Draw.PushButton("Add mat script link", evtAddMatExtension, 175, 250, 155, 25, "Add a text file for more i3d material properties and link it to the active material via script links")
	guiExportModifiers = Draw.Toggle("Apply modifiers", evtExportModifiers, 10, 215, 100, 25, exportModifiers, "Apply modifiers to exported objects (disables skin weights option)")
	guiExportSkinWeights = Draw.Toggle("Skin weights", evtExportSkinWeights, 120, 215, 100, 25, exportSkinWeights, "Export skin weights for armature (disables modifiers option)")
	guiExportVertexColors = Draw.Toggle("Vertex colors", evtExportVertexColors, 230, 215, 100, 25, exportVertexColors, "Export vertex colors")
	guiExportUVMaps = Draw.Toggle("UV maps", evtExportUVMaps, 10, 180, 100, 25, exportUVMaps, "Export UV textue maps")
	guiExportTriangulated = Draw.Toggle("Triangulate", evtExportTriangulated, 120, 180, 100, 25, exportTriangulated, "Convert quads to triangles")
	guiExportNormals = Draw.Toggle("Normals", evtExportNormals, 230, 180, 100, 25, exportNormals, "Export vertex normals")
	guiExportSelection = Draw.Toggle("Only selected", evtExportSelection, 10, 145, 100, 25, exportSelection, "Only export selected objects")
	guiExportProjectPath = Draw.Toggle("Project path", evtExportProjectPath, 120, 145, 100, 25, exportProjectPath, "Export with a path to current blender file")
	guiVeboseLogging = Draw.Toggle("Verbose", evtVerboseLogging, 230, 145, 100, 25, verboseLogging, "Enable detailed logging for troubleshooting")
	exportPath = Draw.String("Export to: ", evtDoNothing, 10, 80, 260, 25, exportPath.val, 256,"Export to %s" %exportPath.val)
	guiBrows = Draw.PushButton("Brows", evtBrows, 280, 80, 50, 25, "Open file browser to choose export location")
	guiRelativePath = Draw.Toggle("Relative", evtRelativePath, 280, 110, 50, 25, relative, "Enable relative path")
	if relative:
		texturePath = Draw.String("Texure folder: ", evtNameChanged, 10, 110, 260, 25, folderName, 256, "Folder name to copy assets to (leave blank if you don't want to copy to a folder)")
	else:
		texturePath = Draw.String("Texure folder: ", evtDoNothing, 10, 110, 260, 25, "absolute", 256, "Folder name to copy assets to (leave blank if you don't want to copy to a folder)")
	if exportSelection:
		guiExport = Draw.PushButton("Export Selection", evtExport, 70, 10, 260, 50, "Write i3d to selected file")
	else:
		guiExport = Draw.PushButton("Export Scene", evtExport, 70, 10, 260, 50, "Write i3d to selected file")
	if logo:
		BGL.glEnable( BGL.GL_BLEND ) # Only needed for alpha blending images with background.
		BGL.glBlendFunc(BGL.GL_SRC_ALPHA, BGL.GL_ONE_MINUS_SRC_ALPHA)
		guiLogo = Draw.Image(logo, 11, 10)
		BGL.glDisable( BGL.GL_BLEND )

def event(evt, val):  # Function that handles keyboard and mouse events
	#global mouseX, mouseY
	global stop, showHelp
	if evt == Draw.ESCKEY or evt == Draw.QKEY:
		stop = Draw.PupMenu("OK?%t|Stop script %x1")
		if stop == 1:
			Draw.Exit()
			return
	if evt in [Draw.LEFTMOUSE, Draw.MIDDLEMOUSE, Draw.RIGHTMOUSE] and val:
		showHelp = Draw.PupMenu("Show Help?%t|Ok%x1")
		if showHelp == 1:
			ShowHelp("blenderI3DExport15C.py")

def buttonEvt(evt):
	global evtExport, evtNameChanged, evtBrows, evtExportSelection, evtDoNothing, exportModifiers, exportSkinWeights, exportVertexColors, exportUVMaps, exportTriangulated, exportNormals, exportSelection, verboseLogging, exportProjectPath, relative, folderName
	global exportPath, texturePath
	global guiPopup
	if evt == evtExport:
		i3d = I3d()
		sce = bpy.data.scenes.active
		if exportSelection:
			for obj in sce.objects.selected:
				i3d.addObject(obj)
		else:
			for obj in sce.objects:
				i3d.addObject(obj)
		i3d.printToFile(exportPath.val)
		
		print("exported to %s" %exportPath.val)
	if evt == evtDoNothing:
		pass
	if evt == evtNameChanged:
		folderName = texturePath.val
	if evt == evtBrows:
		Window.FileSelector(selectExportFile, "Ok", exportPath.val)
	if evt == evtExportProjectPath:
		exportProjectPath = 1 - exportProjectPath
		Draw.Redraw(1)
	if evt == evtExportModifiers:
		exportModifiers = 1 - exportModifiers
		if exportSkinWeights:
			exportSkinWeights = false
		Draw.Redraw(1)
	if evt == evtExportSkinWeights:
		exportSkinWeights = 1 - exportSkinWeights
		if exportModifiers:
			exportModifiers = false
		Draw.Redraw(1)
	if evt == evtExportVertexColors:
		exportVertexColors = 1 - exportVertexColors
		Draw.Redraw(1)
	if evt == evtExportUVMaps:
		exportUVMaps = 1 - exportUVMaps
		Draw.Redraw(1)
	if evt == evtExportTriangulated:
		exportTriangulated = 1 - exportTriangulated
		Draw.Redraw(1)
	if evt == evtExportNormals:
		exportNormals = 1 - exportNormals
		Draw.Redraw(1)
	if evt == evtExportSelection:
		exportSelection = 1 - exportSelection
		Draw.Redraw(1)
	if evt == evtRelativePath:
		relative = 1 - relative
		Draw.Redraw(1)
	if evt == evtVerboseLogging:
		verboseLogging = 1 - verboseLogging
		Draw.Redraw(1)
	if evt == evtAddObjExtension:
		activeObj = bpy.data.scenes.active.objects.active
		slName = "%s.i3d"%activeObj.name
		sl = None
		try:
			sl = Text.Get(slName)
		except:
			sl = None
		if not sl is None:
			guiPopup = Draw.PupMenu("%s already exists. Find it in the Text Editor"%slName)
		else:
			sl = Text.New(slName)
			sl.write("""<!--
this describes some i3d properties of the object it is linked to via Script Links.
the name of this text file must end with ".i3d".
all attributes of the SceneType node are copied to the Object in the final i3d.
"i3dNodeId" is replaced by the id the object gets in the i3d scene.
For the UserAttributes to work the attribute nodeId must be "i3dNodeId".
-->
<i3D>
	<Scene>
		<SceneType static="true" dynamic="false" kinematic="false"/>
	</Scene>
	<UserAttributes>
		<UserAttribute nodeId="i3dNodeId">
			<Attribute name="onCreate" type="scriptCallback" value="print"/>
		</UserAttribute>
	</UserAttributes>
</i3D>""")
			activeObj.addScriptLink(sl.getName(), "FrameChanged")
			guiPopup = Draw.PupMenu("Check ScriptLink panel and Text Editor for %s"%sl.getName())
	if evt == evtAddMatExtension:
		activeObj = bpy.data.scenes.active.objects.active
		activeMat = activeObj.getData().materials[activeObj.activeMaterial-1]
		slName = "%s.i3d"%activeMat.name
		sl = None
		try:
			sl = Text.Get(slName)
		except:
			sl = None
		if not sl is None:
			guiPopup = Draw.PupMenu("%s already exists. Find it in the Text Editor"%slName)
		else:
			sl = Text.New(slName)
			sl.write("""<!--
this describes some i3d properties of the material it is linked to via Script Links.
the name of this text file must end with ".i3d".
all attribute values starting with "assets/" are added to the Files Node and replaced with the id.
in order for file references to work the path must start with "assets/".
-->
<i3D>
	<Materials>
		<Material customShaderId="assets/exampleCustomShader.xml">
			<Custommap name="colorRampTexture" fileId="assets/exampleCustomMap.png"/>
			<CustomParameter name="exampleParameter" value="2 0 0 0"/>	
		</Material>
	</Materials>
</i3D>""")
			activeMat.addScriptLink(sl.getName(), "FrameChanged")
			guiPopup = Draw.PupMenu("Check ScriptLink panel and Text Editor for %s"%sl.getName())
		

def selectExportFile(file):
	global exportPath
	exportPath.val = file
	#print(file)

if __name__ == '__main__':
	Draw.Register(gui, event, buttonEvt)
