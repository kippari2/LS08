#!BPY

"""
Name: 'GIANTS Engine 0.2.5 - 4.0.0 (.i3d)...'
Blender: 248
Group: 'Export'
Tooltip: 'Export to a GIANTS i3D file'
"""

__author__ = "Richard Gracik - Morc, Kippari2 (KLS Mods)"
__url__ = ("biskupovska stranka, http://176.101.178.133:370/, http://themorc.gihub.io/",
"Kippari2 Github, https://github.com/kippari2/")
__version__ = "0.3.3"
__email__ = "r.gracik@gmail.com, kipparizz34@gmail.com"
__bpydoc__ = """\
Exports to Giants .i3d file. Based on Morc's modified 4.1.2 exporter.

Usage:
-Place this script in %appdata%/Blender Foundation/Blender/.blender/scripts directory.
-Open file menu in blender.
-Choose Export -> GIANTS Engine 0.2.5 - 4.0.0 (.i3d)...

Note!
-If your object turns out pink you probably forgot to asign a material.
-If its black you probably forgot to UV unwrap it.
-If youre computer explodes there was probably something wrong with this exporter.
"""

from Blender import Scene, Mesh, Window, sys, Mathutils, Draw, Image, BGL, Get, Material, Text, Texture, Get, ShowHelp, Object
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
			print("LS2009 Mods community i3D 1.5 exporter version 0.3.3")
			print("enabled export options (1=true, 0=false)")
			exportOptionsToPrint = {
				"modifiers": exportModifiers,
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
		exportProgram.setAttribute("version", "0.3.3")
		self.asset.appendChild(exportProgram)
		
		self.files = self.doc.createElement("Files")
		self.root.appendChild(self.files)
		self.materials = self.doc.createElement("Materials")
		self.defaultMat = 0
		self.root.appendChild(self.materials)
		self.shapes = self.doc.createElement("Shapes")
		self.root.appendChild(self.shapes)
		self.lastShapeId = 0
		self.scene = self.doc.createElement("Scene")
		self.root.appendChild(self.scene)
		self.lastNodeId = 0
		#self.texturCount = 0
		self.animation = self.doc.createElement("Animation")
		self.animationSets = self.doc.createElement("AnimationSets")
		self.animation.appendChild(self.animationSets)
		self.root.appendChild(self.animation)
		self.userAttributes = self.doc.createElement("UserAttributes")
		self.root.appendChild(self.userAttributes)
		self.meshesToClear = []
	
	def setTranslation(self, node, pos):
		node.setAttribute("translation", "%f %f %f" %(pos[0], pos[2], -pos[1]))
	#Somethings not right
	#Get mesh first to make testing visual
	def setRotation(self, node, rot, rotX90):
		rot[0], rot[1], rot[2] = math.degrees(rot[0]), math.degrees(rot[2]), math.degrees(-rot[1])
		
		RotationMatrix= Mathutils.RotationMatrix
		MATRIX_IDENTITY_3x3 = Mathutils.Matrix([1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])
		x,y,z = rot[0]%360,rot[1]%360,rot[2]%360 # Clamp all values between 0 and 360, values outside this raise an error
		xmat = RotationMatrix(x,3,'x')
		ymat = RotationMatrix(y,3,'y')
		zmat = RotationMatrix(z,3,'z')
		eRot = (xmat*(zmat * (ymat * MATRIX_IDENTITY_3x3))).toEuler()
		
		if rotX90:
			node.setAttribute("rotation", "%f %f %f" %(eRot.x-90, eRot.y, eRot.z))
		else:
			node.setAttribute("rotation", "%f %f %f" %(eRot.x, eRot.y, eRot.z))
	
	
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
		rotX90=0

		if verboseLogging:
			print("adding object %s with type %s" %(obj.getName(), obj.getType()))
		
		if obj.type == "Mesh":
			me = obj.getData(mesh=1)
			if exportModifiers and len(obj.modifiers) > 0: #TODO: exclude armature option when armature is supported
				me = bpy.data.meshes.new()
				me.getFromObject(obj)
				self.meshesToClear.append(me)
			node = self.doc.createElement("Shape")
			self.addMesh(me)
			node.setAttribute("ref", "%s" %(me.name))

			#print(len(obj.getMaterials()))
			#Materials per object is confusing to implement
			#It's hard to find the variables needed to pull this off
			
			#Shading propertys stored per object in Giants: getting them from first blender material
			if len(me.materials) > 0:
				if me.materials[0]:
					mat = me.materials[0]
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
		elif obj.type == "Camera":
			rotX90=1
			node = self.doc.createElement("Camera")
			node.setAttribute("fov", "%f" %(obj.getData().lens))
			node.setAttribute("nearClip", "%f" %(obj.getData().clipStart))
			node.setAttribute("farClip", "%f" %(obj.getData().clipEnd))
		elif obj.type == "Lamp":
			rotX90=1
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
			node.setAttribute("dropOff", "%f" %(lamp.getSpotBlend()*5))#dropOff seems to be between 0 and 5 right?


		if not node is None:
			node.setAttribute("name", obj.getName())
			
			# getLocation("localspace") seems to be buggy!
			# http://blenderartists.org/forum/showthread.php?t=117421
			localMat = Mathutils.Matrix(obj.matrixLocal)
			#self.setTranslation(node, obj.getLocation("localspace"))
			self.setTranslation(node, localMat.translationPart())			
			#self.setRotation(node, localMat.rotationPart().toEuler(), rotX90)
			self.setRotation(node, obj.getEuler("localspace"), rotX90)
			parentNode.appendChild(node)

			#Parse ScriptLink file and merge xml into i3d
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
		else:
			print("WARNING: cant export %s: %s" %(obj.type, obj.getName()))

	def addMesh(self, mesh):
		faces = self.doc.createElement("Faces")
		ifs = self.doc.createElement("IndexedFaceSet")
		self.lastShapeId = self.lastShapeId + 1
		ifs.setAttribute("name", mesh.name)
		self.shapes.appendChild(ifs)
		verts = self.doc.createElement("Vertices")
		
		faceCount = 0
		vertexCount = 0
		materialCount = 0

		shaderlist = ""

		if verboseLogging:
			print("adding mesh %s with %i vertices" %(mesh.name, len(mesh.verts)))
		
		#print "mesh Mats: ",mesh.materials
		if len(mesh.materials) == 0:
			print("WARNING: mesh %s has no material -> can't export properly" %mesh.name)
		for mat in mesh.materials:
			materialCount = materialCount + 1
			self.addMaterial(mat, materialCount)
			if not mat is None and shaderlist == "":
				shaderlist = mat.name
			elif not mat is None:
				shaderlist = shaderlist + ", %s" %(mat.name)
			else:
				shaderlist = "Default"
			
			for face in mesh.faces:
				
				def createI3dVert(self, vIndex):
					v = self.doc.createElement("v")
					v.setAttribute("c", "%f %f %f" %(face.v[vIndex].co.x, face.v[vIndex].co.z, -face.v[vIndex].co.y))
					return v

				def createTriFace(self, vertexCount):
					i3dt = self.doc.createElement("f")
					i3dt.setAttribute("vi", "%i %i %i" %(vertexCount - 3, vertexCount - 2, vertexCount - 1))
					if exportVertexColors and mesh.vertexColors:
						realColorR = []
						realColorG = []
						realColorB = []
						for vertCol in face.col:
							for i in range(3):
								realColorR.append(vertCol.r/255.0)
								realColorG.append(vertCol.g/255.0)
								realColorB.append(vertCol.b/255.0)
								#print("vertex %i %f %f %f" %(i, realColorR[i], realColorG[i], realColorB[i]))
						i3dt.setAttribute("c", "%f %f %f %f %f %f %f %f %f" %(realColorR[0], realColorG[0], realColorB[0], realColorR[1], realColorG[1], realColorB[1], realColorR[2], realColorG[2], realColorB[2]))
					if evtExportUVMaps and mesh.faceUV:
						#Attempetd multi-UV support, but it only loads one texture (yes the other one was transparent and coords correct)
						#How does it even work????? There are no examples!!!
						#for i in range(self.texturCount):
							#i3dt.setAttribute("t%i" % i, "%f %f %f %f %f %f" % (face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y))
						i3dt.setAttribute("t0", "%f %f %f %f %f %f" %(face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y))
					if exportNormals:
						if face.smooth:
							i3dt.setAttribute("n", "%f %f %f %f %f %f %f %f %f" %(face.v[0].no.x, face.v[0].no.z, -face.v[0].no.y, face.v[1].no.x, face.v[1].no.z, -face.v[1].no.y, face.v[2].no.x, face.v[2].no.z, -face.v[2].no.y))
						else:
							i3dt.setAttribute("n", "%f %f %f %f %f %f %f %f %f" %(face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y))
					i3dt.setAttribute("ci", "%i" %(materialCount-1))
					faces.appendChild(i3dt)

				def createQuadFace(self, vertexCount):
					i3dt = self.doc.createElement("f")
					i3dt.setAttribute("vi", "%i %i %i %i" %(vertexCount - 4, vertexCount - 3, vertexCount - 2, vertexCount - 1))
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
						i3dt.setAttribute("c", "%f %f %f %f %f %f %f %f %f %f %f %f" %(realColorR[0], realColorG[0], realColorB[0], realColorR[1], realColorG[1], realColorB[1], realColorR[2], realColorG[2], realColorB[2], realColorR[3], realColorG[3], realColorB[3]))
					if evtExportUVMaps and mesh.faceUV:
						#for i in range(self.texturCount):
							#i3dt.setAttribute("t%i" % i, "%f %f %f %f %f %f" % (face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y))
						i3dt.setAttribute("t0", "%f %f %f %f %f %f %f %f" %(face.uv[0].x, face.uv[0].y, face.uv[1].x, face.uv[1].y, face.uv[2].x, face.uv[2].y, face.uv[3].x, face.uv[3].y))
					if exportNormals:
						if face.smooth:
							i3dt.setAttribute("n", "%f %f %f %f %f %f %f %f %f %f %f %f" %(face.v[0].no.x, face.v[0].no.z, -face.v[0].no.y, face.v[1].no.x, face.v[1].no.z, -face.v[1].no.y, face.v[2].no.x, face.v[2].no.z, -face.v[2].no.y, face.v[3].no.x, face.v[3].no.z, -face.v[3].no.y))
						else:
							i3dt.setAttribute("n", "%f %f %f %f %f %f %f %f %f %f %f %f" %(face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y, face.no.x, face.no.z, -face.no.y))
					i3dt.setAttribute("ci", "%i" %(materialCount-1))
					faces.appendChild(i3dt)
				
				if face.mat == materialCount-1:
					faceCount = faceCount + 1
					if exportTriangulated and len(face.v) == 4: #It's a quad and user chose to triangulate along shortest edge
						faceCount = faceCount + 1
						if (face.v[0].co - face.v[2].co).length < (face.v[1].co - face.v[3].co).length:
							#print("das")
							verts.appendChild(createI3dVert(self, 0))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 1))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 2))
							vertexCount=vertexCount+1
							createTriFace(self, vertexCount)
							verts.appendChild(createI3dVert(self, 0))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 2))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 3))
							vertexCount=vertexCount+1
							createTriFace(self, vertexCount)
						else:
							#print("asd")
							verts.appendChild(createI3dVert(self, 0))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 1))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 3))
							vertexCount=vertexCount+1
							createTriFace(self, vertexCount)
							verts.appendChild(createI3dVert(self, 1))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 2))
							vertexCount=vertexCount+1
							verts.appendChild(createI3dVert(self, 3))
							vertexCount=vertexCount+1
							createTriFace(self, vertexCount)
					else:
						#print("ads")
						verts.appendChild(createI3dVert(self, 0))
						vertexCount=vertexCount+1
						verts.appendChild(createI3dVert(self, 1))
						vertexCount=vertexCount+1
						verts.appendChild(createI3dVert(self, 2))
						vertexCount=vertexCount+1
						if len(face.v) == 4: #It's a quad and is exported as one
							verts.appendChild(createI3dVert(self, 3))
							vertexCount=vertexCount+1
							createQuadFace(self, vertexCount)
						else: #It should be a triangle since blender doesn't support ngons, or the user chose not to triangulate
							createTriFace(self, vertexCount)

		faces.setAttribute("shaderlist", "%s" %(shaderlist))
				
		ifs.appendChild(verts)
		ifs.appendChild(faces)
		
		return self.lastShapeId
	
	def addMaterial(self, mat, materialCount):
		duplicateMaterial = false
		if mat is None:
			if not self.defaultMat: #Create a nice pink default material
				m = self.doc.createElement("Material")
				m.setAttribute("name", "Default")
				m.setAttribute("diffuseColor", "%f %f %f %f" %(1, 0, 1, 1))
				self.materials.appendChild(m)
				self.defaultMat = 1
				if verboseLogging:
					print("no materials assigned -> added pink default material")
			return self.defaultMat, false
		
		for m in self.materials.getElementsByTagName("Material"):
			if m.getAttribute("name") == mat.getName():
				#print(m.getAttribute("name"))
				duplicateMaterial = true
		if not duplicateMaterial:
			if verboseLogging:
				print("adding material %s" %(mat.name))

			m = self.doc.createElement("Material")
			m.setAttribute("name", mat.name)

			if not mat.getEmit() > 0:
				m.setAttribute("diffuseColor", "%f %f %f %f" %(mat.getRGBCol()[0]*mat.ref, mat.getRGBCol()[1]*mat.ref, mat.getRGBCol()[2]*mat.ref, mat.getAlpha()))
			if mat.getAlpha() < 1:
				m.setAttribute("alphaBlending", "true")
			if mat.getSpec() > 0:
				m.setAttribute("specularColor", "%f %f %f" %(mat.specR*mat.spec/2, mat.specG*mat.spec/2, mat.specB*mat.spec/2))
			if mat.getHardness() > 0:
				m.setAttribute("cosPower", "%i" %(mat.getHardness()))
			if mat.getEmit() > 0:
				m.setAttribute("emissiveColor", "%f %f %f" %(mat.getRGBCol()[0]*mat.emit/2, mat.getRGBCol()[1]*mat.emit/2, mat.getRGBCol()[2]*mat.emit/2))
			if mat.getMode() & Material.Modes['NOMIST']:
				m.setAttribute("allowFog", "false")
			if mat.getAmb() > 0:
				m.setAttribute("ambientColor", "%f %f %f" %(mat.amb, mat.amb, mat.amb)) #mat.getRGBCol()[0]*mat.amb

			texturN = 0
			texturCount = 0
			for textur in mat.getTextures():
				texturEnabled = 0
				for t in mat.enabledTextures:
					if t == texturN:
						texturEnabled = 1
						break
				if texturEnabled and exportUVMaps:
					if textur.tex.getImage() is None or textur.tex.getImage().getFilename() is None:
						print("WARNING: cannot export texture named %s, it's not an image!" %textur.tex.getName())
					else:
						path = textur.tex.getImage().getFilename()
						j, name = os.path.split(path)
						del j #We don't like this variable
						if textur.mtCol:#Map To Col
							if verboseLogging:
								print("adding image texture %s" %name)
							i3dTex = self.doc.createElement("Texture")
							i3dTex.setAttribute("name", "%s" %self.addFile(path))
							m.appendChild(i3dTex)
						if textur.mtNor:#Map To Nor
							if verboseLogging:
								print("adding normal map %s" %name)
							if textur.mtNor == -1:
								print("WARNING: normalmap %s cannot be inverted by the exporter" %textur.tex.getName())
							i3dTex = self.doc.createElement("Normalmap")
							i3dTex.setAttribute("name", "%s" %self.addFile(path))
							if textur.norfac > 0:
								i3dTex.setAttribute("bumpDepth", "%f" %textur.norfac) #Can't test this properly until proper transparent normal maps can be created
							#print(textur.norfac)
							m.appendChild(i3dTex)
						if textur.mtCsp:#Map To Spec
							if verboseLogging:
								print("adding specular map %s" %name)
							if textur.mtSpec == -1:
								print("WARNING: specularmap %s cannot be inverted by the exporter" %textur.tex.getName())
							i3dTex = self.doc.createElement("Glossmap")
							i3dTex.setAttribute("name", "%s" %self.addFile(path))
							m.appendChild(i3dTex)
						if textur.mtEmit:#Map To Emit
							if verboseLogging:
								print("adding emissive map %s" %name)
							if textur.mtEmit == -1:
								print("WARNING: emissivemap %s cannot be inverted by the exporter" %textur.tex.getName())
							i3dTex = self.doc.createElement("Emissivemap")
							i3dTex.setAttribute("name", "%s" %self.addFile(path))
							m.appendChild(i3dTex)
						#self.texturCount = self.texturCount + 1
						#TODO: other maps
				texturN = texturN + 1
		
		#Parse material ScriptLink file and merge xml into i3d (if it ends with .i3d)
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
						while i < n.attributes.length:#Copy attributes
							attr = n.attributes.item(i)
							if attr.nodeValue.startswith(folderName+"/"):
								m.setAttribute(attr.nodeName, "%i" %self.addFile(attr.nodeValue))
							else:
								m.setAttribute(attr.nodeName, attr.nodeValue)
							i = i+1
						for cn in n.childNodes:#Copy child elements
							if cn.nodeType == cn.ELEMENT_NODE:
								#print cn							
								if not cn.attributes is None:
									i = 0
									while i < cn.attributes.length:
										attr = cn.attributes.item(i)
										if attr.nodeValue.startswith(folderName+"/"):
											attr.nodeValue = "%i" %self.addFile(attr.nodeValue)
										i = i+1
								m.appendChild(cn)
		
		self.materials.appendChild(m)

	def copyAssets(self, assetPath):
		j, assetName = os.path.split(assetPath)
		del j #Pure hatrred GRRRR!!!
		head, path = os.path.split(exportPath.val)
		path = os.path.join(head, folderName)
		if not os.path.isdir(path) and folderName is not None:
			os.mkdir(path)
			if verboseLogging:
				print("created texure folder at %s" %path)
		if verboseLogging:
			print("copying asset %s to: %s" %(assetName, path))
		shutil.copy(assetPath, path)

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
#evtExportSkinWeights = 14 Armature and skin weights here we come!!!
evtExportVertexColors = 15
evtExportUVMaps = 16
evtVerboseLogging = 17

#Toggle button states
exportModifiers = true
#exportSkinWeights = true
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
#guiExportSkinWeights = 0
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
	global guiExport, guiBrows, guiRelativePath, guiExportModifiers, guiExportVertexColors, guiExportUVMaps, guiExportTriangulated, guiExportNormals, guiExportSelection, guiVeboseLogging, guiAddObjExtension, guiAddMatExtension, guiLogo
	
	guiAddObjExtension = Draw.PushButton("Add obj script link", evtAddObjExtension, 10, 250, 150, 25, "Add a text file for more i3d object properties and link it to the active object via script links")
	guiAddMatExtension = Draw.PushButton("Add mat script link", evtAddMatExtension, 175, 250, 155, 25, "Add a text file for more i3d material properties and link it to the active material via script links")
	guiExportModifiers = Draw.Toggle("Apply modifiers", evtExportModifiers, 10, 215, 100, 25, exportModifiers, "Apply modifiers to exported objects")
	guiExportVertexColors = Draw.Toggle("Vertex colors", evtExportVertexColors, 120, 215, 100, 25, exportVertexColors, "Export vertex colors")
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
			ShowHelp("i3dExporter.py")

def buttonEvt(evt):
	global evtExport, evtNameChanged, evtBrows, evtExportSelection, evtDoNothing, exportModifiers, exportVertexColors, exportUVMaps, exportTriangulated, exportNormals, exportSelection, verboseLogging, exportProjectPath, relative, folderName
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
