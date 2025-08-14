-- @original author: unknown (someone at GIANTS)
-- @original date: 27.3.2008
-- @author: kippari2 (KLS mods)
-- @date: 17.3.2024
-- @version 1.1
-- @patch date: 11.4.2024

Bizon3 = {};

function Bizon3:new(configFile, positionX, positionY, positionZ, yRot, customMt)

    if Bizon3_mt == nil then
        Bizon3_mt = Class(Bizon3, Vehicle);
    end;

    local mt = customMt;
    if mt == nil then
        mt = Bizon3_mt;
    end;
    local instance = Bizon3:superClass():new(configFile, positionX, positionY, positionZ, yRot, mt);

    local xmlFile = loadXMLFile("TempConfig", configFile);
	
	instance.rundumleuchtenAnz = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.rundumleuchten#count"),0);
    --instance.rundumleuchtenKey = getXMLString(xmlFile, "vehicle.rundumleuchten#key");
    instance.rundumleuchtenAn = false;
    instance.rundumleuchten = {};
    for i=1, instance.rundumleuchtenAnz do
        local objname = string.format("vehicle.rundumleuchten.light" .. "%d",i);
        instance.rundumleuchten[i] = {};
        instance.rundumleuchten[i].rotNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, objname .. "#rotNode"));
        instance.rundumleuchten[i].light = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, objname .. "#light"));
        instance.rundumleuchten[i].source = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, objname .. "#lightsource"));
        instance.rundumleuchten[i].speed = Utils.getNoNil(getXMLInt(xmlFile,  objname .. "#rotSpeed"), 1)/1000;
        instance.rundumleuchten[i].emit = Utils.getNoNil(getXMLBool(xmlFile, objname .. "#emitLight"), true);
        if not instance.rundumleuchten[i].emit and instance.rundumleuchten[i].source ~= nil then
           setVisibility(instance.rundumleuchten[i].source, false);
        end;
    end;
	
	local numCuttingAreas = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.cuttingAreas#count"), 0);
    instance.cuttingAreas = {}
    for i=1, numCuttingAreas do
        instance.cuttingAreas[i] = {};
        local areanamei = string.format("vehicle.cuttingAreas.cuttingArea" .. "%d", i);
        instance.cuttingAreas[i].start = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, areanamei .. "#startIndex"));
        instance.cuttingAreas[i].width = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, areanamei .. "#widthIndex"));
        instance.cuttingAreas[i].height = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, areanamei .. "#heightIndex"));
    end;

    local threshingSound = getXMLString(xmlFile, "vehicle.threshingSound#file");
    if threshingSound ~= nil and threshingSound ~= "" then
        instance.threshingSound = createSample("threshingSound");
        loadSample(instance.threshingSound, threshingSound, false);
        instance.threshingSoundPitchOffset = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.threshingSound#pitchOffset"), 1);
        instance.threshingSoundPitchScale = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.threshingSound#pitchScale"), 0);
        instance.threshingSoundPitchMax = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.threshingSound#pitchMax"), 2.0);
    end;

    instance.attachedCutter = nil;
    --instance.cutterPos = 0;
    _=[[local cutterHolderIndex = getXMLInt(xmlFile, "vehicle.cutterHolder#index");
    if cutterHolderIndex ~= nil then
        instance.cutterHolder = getChildAt(instance.rootNode, cutterHolderIndex);
    end;]]
    local cutterJoint = {};
    cutterJoint.jointTransform = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.cutterAttacherJoint#index"));
    if cutterJoint.jointTransform ~= nil then

        local rotationNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.cutterAttacherJoint#rotationNode"));
        if rotationNode ~= nil then
            cutterJoint.rotationNode = rotationNode;
            local x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.cutterAttacherJoint#maxRot"));
            cutterJoint.maxRot = {};
            cutterJoint.maxRot[1] = Utils.degToRad(Utils.getNoNil(x, 0));
            cutterJoint.maxRot[2] = Utils.degToRad(Utils.getNoNil(y, 0));
            cutterJoint.maxRot[3] = Utils.degToRad(Utils.getNoNil(z, 0));

            x, y, z = getRotation(rotationNode);
            cutterJoint.minRot = {x,y,z};
        end;
        local rotationNode2 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.cutterAttacherJoint#rotationNode2"));
        if rotationNode2 ~= nil then
            cutterJoint.rotationNode2 = rotationNode2;
            local x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.cutterAttacherJoint#maxRot2"));
            cutterJoint.maxRot2 = {};
            cutterJoint.maxRot2[1] = Utils.degToRad(Utils.getNoNil(x, 0));
            cutterJoint.maxRot2[2] = Utils.degToRad(Utils.getNoNil(y, 0));
            cutterJoint.maxRot2[3] = Utils.degToRad(Utils.getNoNil(z, 0));

            x, y, z = getRotation(rotationNode2);
            cutterJoint.minRot2 = {x,y,z};
        end;
        cutterJoint.moveTime = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.cutterAttacherJoint#moveTime"), 0.5)*1000;
        cutterJoint.jointIndex = 0;

        instance.cutterAttacherJoint = cutterJoint;
    end;

    instance.cutterAttacherJointMoveDown = false;

    instance.pipeParticleSystems = {};
    local pipeIndexStr = getXMLString(xmlFile, "vehicle.pipe#index");
    if pipeIndexStr ~= nil then
        instance.pipe = Utils.indexToObject(instance.rootNode, pipeIndexStr);

        local posStr = getXMLString(xmlFile, "vehicle.pipeParticleSystem#position");
        local rotStr = getXMLString(xmlFile, "vehicle.pipeParticleSystem#rotation");
        if posStr ~= nil and rotStr ~= nil then
            local posX, posY, posZ = Utils.getVectorFromString(posStr);
            local rotX, rotY, rotZ = Utils.getVectorFromString(rotStr);
            rotX = Utils.degToRad(rotX);
            rotY = Utils.degToRad(rotY);
            rotZ = Utils.degToRad(rotZ);
            local psFile = getXMLString(xmlFile, "vehicle.pipeParticleSystem#file");
            if psFile == nil then
                psFile = "data/vehicles/particleSystems/wheatParticleSystem.i3d";
            end;
            instance.pipeParticleSystemRoot = loadI3DFile(psFile);
            link(instance.pipe, instance.pipeParticleSystemRoot);
            setTranslation(instance.pipeParticleSystemRoot, posX, posY, posZ);
            setRotation(instance.pipeParticleSystemRoot, rotX, rotY, rotZ);
            for i=0, getNumOfChildren(instance.pipeParticleSystemRoot)-1 do
                local child = getChildAt(instance.pipeParticleSystemRoot, i);
                if getClassName(child) == "Shape" then
                    local geometry = getGeometry(child);
                    if geometry ~= 0 then
                        if getClassName(geometry) == "ParticleSystem" then
                            table.insert(instance.pipeParticleSystems, geometry);
                            setEmittingState(geometry, false);
                        end;
                    end;
                end;
            end;
        end;
    end;

    instance.pipeLight = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.pipeLight#index"));

    instance.grainTankCapacity = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.grainTankCapacity"), 200);
    instance.grainTankUnloadingCapacity = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.grainTankUnloadingCapacity"), 10);
    --instance.grainTankFillLevel = 0.0;
    instance.grainTankCrowded = false;

    instance.grainPlane = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.grainPlane#index"));

    instance.grainPlaneMinY, instance.grainPlaneMaxY = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.grainPlane#minMaxY"));
    if instance.grainPlaneMinY == nil or instance.grainPlaneMaxY == nil then
        instance.grainPlaneMinY = 0;
        instance.grainPlaneMaxY = 0;
    end;

    instance.grainPlaneWindow = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.grainPlane#windowIndex"));

    instance.grainPlaneWindowMinY, instance.grainPlaneWindowMaxY = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.grainPlane#windowMinMaxY"));
    if instance.grainPlaneWindowMinY == nil or instance.grainPlaneWindowMaxY == nil then
        instance.grainPlaneWindowMinY = 0;
        instance.grainPlaneWindowMaxY = 0;
    end;
    instance.grainPlaneWindowStartY = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.grainPlane#windowStartY"), 0.0);

    instance.chopperParticleSystems = {};
    local posStr = getXMLString(xmlFile, "vehicle.chopperParticleSystem#position");
    local rotStr = getXMLString(xmlFile, "vehicle.chopperParticleSystem#rotation");
    if posStr ~= nil and rotStr ~= nil then
        local posX, posY, posZ = Utils.getVectorFromString(posStr);
        local rotX, rotY, rotZ = Utils.getVectorFromString(rotStr);
        rotX = Utils.degToRad(rotX);
        rotY = Utils.degToRad(rotY);
        rotZ = Utils.degToRad(rotZ);
        local psFile = getXMLString(xmlFile, "vehicle.chopperParticleSystem#file");
        if psFile == nil then
            psFile = "data/vehicles/particleSystems/threshingChopperParticleSystem.i3d";
        end;
        instance.chopperParticleSystemRoot = loadI3DFile(psFile);
        link(instance.rootNode, instance.chopperParticleSystemRoot);
        setTranslation(instance.chopperParticleSystemRoot, posX, posY, posZ);
        for i=0, getNumOfChildren(instance.chopperParticleSystemRoot)-1 do
            local child = getChildAt(instance.chopperParticleSystemRoot, i);
            if getClassName(child) == "Shape" then
                local geometry = getGeometry(child);
                if geometry ~= 0 then
                    if getClassName(geometry) == "ParticleSystem" then
                        table.insert(instance.chopperParticleSystems, geometry);
                        setEmittingState(geometry, false);
                    end;
                end;
            end;
        end;
    end;

    instance.combineSize = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.combineSize"), 1);
	
	instance.keys = {};
	instance.keynames = {};
    local i = 0;
    while true do
        local baseName = string.format("vehicle.keys.input(%d)", i);
        local inputName = getXMLString(xmlFile, baseName.. "#name");
        if inputName == nil then
            break;
        end;
        local inputKey = getXMLString(xmlFile, baseName.. "#key");
        if Input[inputKey] == nil then
            print("Error: invalid key '" .. inputKey .. "'  for input event '" .. inputName .. "'");
            break;
        end;
        instance.keys[inputName] = Input[inputKey];
		instance.keynames[inputName] = Input[inputKey];
	    if instance.keynames[inputName] > 32 and instance.keynames[inputName] < 123 then
	    	instance.keynames[inputName] = string.char(instance.keynames[inputName]);
	    elseif instance.keynames[inputName] > 255 and instance.keynames[inputName] < 266 then
	    	instance.keynames[inputName] = "num "..string.char(instance.keynames[inputName]-208);
	    else 
	    	instance.keynames[inputName] = "missig key";
	    end;
		--print(instance.keynames[inputName]);
        i = i + 1;
    end;
	
	instance.strawChopperParticleSystems = {};
    local strawChopperParticleSystemsCount = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.strawChopperParticleSystems#count"), 0);
    for i=1, strawChopperParticleSystemsCount do
        local namei = string.format("vehicle.strawChopperParticleSystems.strawChopperParticleSystem" .. "%d", i);
        Utils.loadParticleSystem(xmlFile, instance.strawChopperParticleSystems, namei, instance.rootNode, false)
    end;
	instance.strawChopperParticleSystems2 = {};
    local strawChopperParticleSystems2Count = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.strawChopperParticleSystems2#count"), 0);
    for i=1, strawChopperParticleSystems2Count do
        local namei = string.format("vehicle.strawChopperParticleSystems2.strawChopperParticleSystem" .. "%d", i);
        Utils.loadParticleSystem(xmlFile, instance.strawChopperParticleSystems2, namei, instance.rootNode, false)
    end;

	local cabinCount = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.cabins#count"))
	instance.cabinNodes = {};
	--instance.showOnLoad = {};
	for i = 0, cabinCount do
		local cabObjectName = string.format("vehicle.cabins.cabin%d", i);
		instance.cabinNodes[i] = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, cabObjectName.."#index"));
		--instance.showOnLoad[i] = getXMLBool(xmlFile, cabObjectName.."#showOnLoad", false);
	end;
	--print(unpack(instance.cabinNodes));

	instance.coversNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.covers#index"));
	instance.engineCoverNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.engineCover#index"));
	instance.railingNode1 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.railing1#index"));
	instance.railingNode2 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.railing2#index"));
	instance.automaticCutterLift = getXMLBool(xmlFile, "vehicle.automaticCutterLift", false);
	instance.strawChopperNode1 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.strawChopper#index1"));
	instance.strawChopperNode2 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.strawChopper#index2"));
	instance.strawChopperNode3 = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.strawChopper#index3"));
	instance.strawChopperRotSpeed1 = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.strawChopper#rotSpeed1")) * 1000;
	instance.strawChopperRotSpeed2 = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.strawChopper#rotSpeed2")) * 1000;
	instance.strawChopperRotSpeed3 = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.strawChopper#rotSpeed3")) * 1000;
	instance.chopperMin1 = {};
	instance.chopperMax1 = {};
	if instance.strawChopperNode1 ~= nil then
		local rx1, rx2 = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.strawChopper#minMaxX1"));
		instance.chopperMin1[1] = Utils.degToRad(Utils.getNoNil(rx1));
		instance.chopperMin1[2] = 0;
		instance.chopperMin1[3] = 0;
		instance.chopperMax1[1] = Utils.degToRad(Utils.getNoNil(rx2));
		instance.chopperMax1[2] = 0;
		instance.chopperMax1[3] = 0;
	else
		print("strawChopper index1 out of range");
	end;
	instance.chopperMin2 = {};
	instance.chopperMax2 = {};
	if instance.strawChopperNode2 ~= nil then
		local rx1, rx2 = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.strawChopper#minMaxX2"));
		instance.chopperMin2[1] = Utils.degToRad(Utils.getNoNil(rx1));
		instance.chopperMin2[2] = 0;
		instance.chopperMin2[3] = 0;
		instance.chopperMax2[1] = Utils.degToRad(Utils.getNoNil(rx2));
		instance.chopperMax2[2] = 0;
		instance.chopperMax2[3] = 0;
	else
		print("strawChopper index2 out of range");
	end;
	instance.chopperMin3 = {};
	instance.chopperMax3 = {};
	if instance.strawChopperNode3 ~= nil then
		local rx1, rx2 = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.strawChopper#minMaxX3"));
		instance.chopperMin3[1] = Utils.degToRad(Utils.getNoNil(rx1));
		instance.chopperMin3[2] = 0;
		instance.chopperMin3[3] = 0;
		instance.chopperMax3[1] = Utils.degToRad(Utils.getNoNil(rx2));
		instance.chopperMax3[2] = 0;
		instance.chopperMax3[3] = 0;
	else
		print("strawChopper index3 out of range");
	end;

    delete(xmlFile);

	instance.coversVisible = false;
	instance.engineCoverVisible = true;
	instance.blindOpen = false;

	self.currentRot1 = {};
	self.currentRot2 = {};

    instance.chopperActivated = false;
    instance.pipeOpening = false;
    instance.pipeOpen = false;
    instance.pipeParticleActivated = false;

    instance.threshingScale = 1;

    instance:setGrainTankFillLevel(0.0);

    instance.drawFillLevel = true;

	instance.hayOn = false;
	
	instance.help = false;

    return instance;
end;

function Bizon3:delete()

    self:detachCurrentCutter();

    if self.threshingSound ~= nil then
        delete(self.threshingSound);
    end;
    Bizon3:superClass().delete(self);

end;

function Bizon3:keyEvent(unicode, sym, modifier, isDown)
    Bizon3:superClass().keyEvent(self, unicode, sym, modifier, isDown);
	if self.isEntered then
		if isDown and sym == self.keys.stroh and self.currentRot1[1] == self.chopperMin1[1] then
			self.hayOn = not self.hayOn;
		end;
		if isDown and sym == self.keys.chopperblind then
			self.blindOpen = not self.blindOpen;
		end;
		if isDown and sym == self.keys.beacon then
			self.rundumleuchtenAn = not self.rundumleuchtenAn;
			for i=1, self.rundumleuchtenAnz do
				setVisibility(self.rundumleuchten[i].light, self.rundumleuchtenAn);
			end;
		end;
		if isDown and sym == self.keys.covers then
			self.coversVisible = not self.coversVisible;
			if self.coversNode ~= nil then
				setVisibility(self.coversNode, self.coversVisible);
			end;
		end;
		if isDown and sym == self.keys.enginecover then
			self.engineCoverVisible = not self.engineCoverVisible;
			if self.engineCoverNode ~= nil then
				setVisibility(self.engineCoverNode, self.engineCoverVisible);
			end;
		end;
		if isDown and sym == self.keys.help then
			self.help = not self.help;
		end;
		if isDown and sym == self.keys.railing then
			setVisibility(self.railingNode1, true);
			setVisibility(self.cabinNodes[1], false);
			setVisibility(self.cabinNodes[2], false);
			setVisibility(self.cabinNodes[3], false);
		end;
		if isDown and sym == self.keys.cabin1 then
			setVisibility(self.railingNode1, false);
			setVisibility(self.cabinNodes[1], true);
			setVisibility(self.cabinNodes[2], false);
			setVisibility(self.cabinNodes[3], false);
		end;
		if isDown and sym == self.keys.cabin2 then
			setVisibility(self.railingNode1, false);
			setVisibility(self.cabinNodes[1], false);
			setVisibility(self.cabinNodes[2], true);
			setVisibility(self.cabinNodes[3], false);
		end;
		if isDown and sym == self.keys.cabin3 then
			setVisibility(self.railingNode1, false);
			setVisibility(self.cabinNodes[1], false);
			setVisibility(self.cabinNodes[2], false);
			setVisibility(self.cabinNodes[3], true);
		end;
	end;
end;

function Bizon3:update(dt, isActive)
    Bizon3:superClass().update(self, dt, isActive);

    if self.attachedCutter ~= nil then
        self.attachedCutter:update(dt);
    end;

    if self.isEntered then
		if self.rundumleuchtenAnz > 0 then
			if self.rundumleuchtenAn then
				for i=1, self.rundumleuchtenAnz do
					rotate(self.rundumleuchten[i].rotNode, 0, dt*self.rundumleuchten[i].speed, 0);
				end;
			end;
		end;
		if getVisibility(self.cabinNodes[1]) or getVisibility(self.cabinNodes[2]) or getVisibility(self.cabinNodes[3]) then
			setVisibility(self.railingNode2, true);
		else
			setVisibility(self.railingNode2, false);
		end;
		--if isDown and sym == Input.KEY_x then
        if InputBinding.hasEvent(InputBinding.ATTACH) then
            if self.attachedCutter == nil then

                local cutter = g_currentMission.cutterInMountRange;
                if cutter ~= nil then
                    self:playAttachSound();
                    self:attachCutter(cutter);
                end;
            else
                self:playAttachSound();
                self:detachCurrentCutter();
            end;
        end;

        if self.grainTankFillLevel < self.grainTankCapacity then
            if InputBinding.hasEvent(InputBinding.ACTIVATE_THRESHING) then
                if self.attachedCutter ~= nil then
                    if self.attachedCutter:isReelStarted() then
                        self:stopThreshing();
                    else
                        self:startThreshing();
                    end;
                end;
            end;
        end;

        if InputBinding.hasEvent(InputBinding.LOWER_IMPLEMENT) then
            if self.attachedCutter ~= nil then
                self.cutterAttacherJointMoveDown = not self.cutterAttacherJointMoveDown;
            end;
        end;

        --if isDown and sym == Input.KEY_3 then
        --    self.chopperActivated = not self.chopperActivated;
        --end;

        --if isDown and sym == Input.KEY_r then
        _=[[if InputBinding.hasEvent(InputBinding.OPEN_PIPE) then
            self.pipeOpening = not self.pipeOpening;
            self.pipeParticleActivated = self.pipeParticleActivated and self.pipeOpening;
        end;]]

        --if isDown and sym == Input.KEY_t then
        if InputBinding.hasEvent(InputBinding.EMPTY_GRAIN) then
            self.pipeOpening = not self.pipeOpening;
            _=[[if self.pipeOpening then
                if not self.pipeParticleActivated then
                    if self.grainTankFillLevel > 0.0 then
                        self.pipeParticleActivated = true;
                    end;
                else
                    self.pipeParticleActivated = false;
                end;
            end;]]
        end;

        if self.grainTankFillLevel == self.grainTankCapacity and self.attachedCutter ~= nil then
            self.attachedCutter:onStopReel();
			if self.automaticCutterLift then
				self.cutterAttacherJointMoveDown = false; 
			end;
			stopSample(self.threshingSound);
			self.pipeOpening = true;
        end;
    end;

	if self.strawChopperNode1 ~= nil and self.strawChopperNode2 ~= nil and self.strawChopperNode3 ~= nil then
		self.currentRot1[1], self.currentRot1[2], self.currentRot1[3] = getRotation(self.strawChopperNode1);
		self.currentRot2[1], self.currentRot2[2], self.currentRot2[3] = getRotation(self.strawChopperNode2);
		local currentRot = {};
		currentRot[1], currentRot[2], currentRot[3] = getRotation(self.strawChopperNode3);
		
		if self.currentRot1[1] == self.chopperMin1[1] and self.currentRot2[1] ~= self.chopperMin2[1] then
			self.blindOpen = false;
		end;
		if self.currentRot2[1] ~= self.chopperMin2[1] then
			self.blindOpen = false;
		end;

		local newRot = Utils.getMovedLimitedValues(self.currentRot1, self.chopperMax1, self.chopperMin1, 3, self.strawChopperRotSpeed1, dt, not self.blindOpen);
		setRotation(self.strawChopperNode1, unpack(newRot));
		local newRot = Utils.getMovedLimitedValues(self.currentRot2, self.chopperMax2, self.chopperMin2, 3, self.strawChopperRotSpeed2, dt, not self.hayOn);
		setRotation(self.strawChopperNode2, unpack(newRot));
		local newRot = Utils.getMovedLimitedValues(currentRot, self.chopperMax3, self.chopperMin3, 3, self.strawChopperRotSpeed3, dt, not self.hayOn);
		setRotation(self.strawChopperNode3, unpack(newRot));
	end;

	if self.hayOn and g_currentMission.strawId ~= nil then					
		if self.attachedCutter ~= nil and self.attachedCutter.reelStarted and self.attachedCutter.lastArea > 0 then
			for i=1, table.getn(self.cuttingAreas) do
				local x,y,z = getWorldTranslation(self.cuttingAreas[i].start);
				local x1,y1,z1 = getWorldTranslation(self.cuttingAreas[i].width);
				local x2,y2,z2 = getWorldTranslation(self.cuttingAreas[i].height);				
				Utils.makeStrawArea(x, z, x1, z1, x2, z2);
			end;	
		end;
	end;
	
	if self.currentRot2[1] ~= self.chopperMin2[1] and self.attachedCutter ~= nil and self.attachedCutter.reelStarted and self.attachedCutter.lastArea > 0 then
		Utils.setEmittingState(self.chopperParticleSystems, true)
	else
		Utils.setEmittingState(self.chopperParticleSystems, false)
	end;
	if not self.hayOn and self.currentRot2[1] == self.chopperMin2[1] and self.currentRot1[1] == self.chopperMin1[1] and self.attachedCutter ~= nil and self.attachedCutter.reelStarted and self.attachedCutter.lastArea > 0 then
		Utils.setEmittingState(self.strawChopperParticleSystems2, true)
	else
		Utils.setEmittingState(self.strawChopperParticleSystems2, false)
	end;
	if not self.hayOn and self.currentRot1[1] ~= self.chopperMin1[1] and self.attachedCutter ~= nil and self.attachedCutter.reelStarted and self.attachedCutter.lastArea > 0 then
		Utils.setEmittingState(self.strawChopperParticleSystems, true)
	else
		Utils.setEmittingState(self.strawChopperParticleSystems, false)
	end;

    self.pipeParticleActivated = false;
    if self.pipeOpen then
        self.pipeParticleActivated = true;
        -- test if we should drain the grain tank
        self.trailerFound = 0;
        local x,y,z = getWorldTranslation(self.pipeParticleSystemRoot);
        raycastClosest(x, y, z, 0, -1, 0, "findTrailerRaycastCallback", 10, self);
        
        local trailer = g_currentMission.objectToTrailer[self.trailerFound];
        if self.trailerFound == 0 or not trailer:allowFillType(Trailer.FILLTYPE_WHEAT) then
            --self.noTrailerWarning = true;
            self.pipeParticleActivated = false;
        else
            --self.noTrailerWarning = false;

            local deltaLevel = self.grainTankUnloadingCapacity*dt/1000.0;
            deltaLevel = math.min(deltaLevel, trailer.capacity - trailer.fillLevel);

            self.grainTankFillLevel = self.grainTankFillLevel-deltaLevel;
            if self.grainTankFillLevel <= 0.0 then
                deltaLevel = deltaLevel+self.grainTankFillLevel;
                self.grainTankFillLevel = 0.0;
                self.pipeParticleActivated = false;
            end;
            if deltaLevel == 0 then
                self.pipeParticleActivated = false;
				self.pipeOpening = false;
            end;
            self:setGrainTankFillLevel(self.grainTankFillLevel);
            trailer:setFillLevel(trailer.fillLevel+deltaLevel, Trailer.FILLTYPE_WHEAT);
        end;
    end;
    Utils.setEmittingState(self.pipeParticleSystems, self.pipeParticleActivated);

    _=[[for i=1, table.getn(self.pipeParticleSystems) do
        setEmittingState(self.pipeParticleSystems[i], self.pipeParticleActivated);
    end;]]

    --local chopperEmitState = false;
    if self.isEntered then

        local jointDesc = self.cutterAttacherJoint;
        if jointDesc.jointIndex ~= 0 then
            if jointDesc.rotationNode ~= nil then
                local x, y, z = getRotation(jointDesc.rotationNode);
                local rot = {x,y,z};
                local newRot = Utils.getMovedLimitedValues(rot, jointDesc.maxRot, jointDesc.minRot, 3, jointDesc.moveTime, dt, not self.cutterAttacherJointMoveDown);
                setRotation(jointDesc.rotationNode, unpack(newRot));
                for i=1, 3 do
                    if math.abs(newRot[i] - rot[i]) > 0.001 then
                        jointFrameInvalid = true;
                    end;
                end;
            end;
            if jointDesc.rotationNode2 ~= nil then
                local x, y, z = getRotation(jointDesc.rotationNode2);
                local rot = {x,y,z};
                local newRot = Utils.getMovedLimitedValues(rot, jointDesc.maxRot2, jointDesc.minRot2, 3, jointDesc.moveTime, dt, not self.cutterAttacherJointMoveDown);
                setRotation(jointDesc.rotationNode2, unpack(newRot));
                for i=1, 3 do
                    if math.abs(newRot[i] - rot[i]) > 0.001 then
                        jointFrameInvalid = true;
                    end;
                end;
            end;
            if jointFrameInvalid then
                setJointFrame(jointDesc.jointIndex, 0, jointDesc.jointTransform);
            end;
        end;

        local pipeRotationSpeed = 0.0006;
        local pipeMinRotY = -90*3.1415/180.0;
        if self.pipe ~= nil then
            local x,y,z = getRotation(self.pipe);
            if self.pipeOpening then
                y = y-dt*pipeRotationSpeed;
                if y < pipeMinRotY then
                    y = pipeMinRotY;
                end;
            else
                y = y+dt*pipeRotationSpeed;
                if y > 0.0 then
                    y = 0.0;
                end;
            end;
            setRotation(self.pipe, x, y, z);
            self.pipeOpen = (math.abs(pipeMinRotY-y) < 0.01);
        end;

        _=[[if self.pipeLight ~= nil then
            local pipeLightActive = self.lightsActive and self.pipeOpening;
            setVisibility(self.pipeLight, pipeLightActive);
        end;]]

        if self.motor.speedLevel == 1 then
            self.speedDisplayScale = 0.5;
        elseif self.motor.speedLevel == 2 then
            self.speedDisplayScale = 0.6;
        else
            self.speedDisplayScale = 1.0;
        end;
    end;
    --Utils.setEmittingState(self.chopperParticleSystems, chopperEmitState)
	if self.chopperActivated and self.attachedCutter ~= nil and self.attachedCutter.reelStarted and self.attachedCutter.lastArea > 0 then
		--chopperEmitState = true;

		-- 8000/1200 = 6.66 liter/meter
		-- 8000/1200 / 6 = 1.111 liter/m^2
		-- 8000/1200 / 6 / 2^2 = 0.277777 liter / density pixel (density is 4096^2, on a area of 2048m^2
		local literPerPixel = 8000/1200 / 6 / (2*2);

		literPerPixel = literPerPixel*1.5;

		self.grainTankFillLevel = self.grainTankFillLevel+self.attachedCutter.lastArea*literPerPixel*self.threshingScale;
		self:setGrainTankFillLevel(self.grainTankFillLevel);
	end;
end;

function Bizon3:attachCutter(cutter)
    if self.attachedCutter == nil then
        -- attach
        local jointDesc = self.cutterAttacherJoint;

        if jointDesc.rotationNode ~= nil then
            setRotation(jointDesc.rotationNode, unpack(jointDesc.maxRot));
        end;
        if jointDesc.rotationNode2 ~= nil then
            setRotation(jointDesc.rotationNode2, unpack(jointDesc.maxRot2));
        end;
        self.cutterAttacherJointMoveDown = false;

        self.attachedCutter = cutter;

        local constr = JointConstructor:new();
        constr:setActors(self.rootNode, cutter.rootNode);
        constr:setJointTransforms(jointDesc.jointTransform, cutter.attacherJoint);
        --constr:setBreakable(20, 10);

        for i=1, 3 do
            constr:setRotationLimit(i-1, 0, 0);
            constr:setTranslationLimit(i-1, true, 0, 0);
        end;

        jointDesc.jointIndex = constr:finalize();

        self.attachedCutter:onAttach(self);
    end;
end;

function Bizon3:detachCurrentCutter()
    self.chopperActivated = false;
    if self.attachedCutter ~= nil then
        _=[[local cx, cy, cz = localToWorld(self.cutterHolder, 0, 0, 0.4);
        setTranslation(self.attachedCutter.rootNode, cx, cy, cz);
        setRotation(self.attachedCutter.rootNode, getWorldRotation(self.attachedCutter.rootNode));
        link(getRootNode(), self.attachedCutter.rootNode);
        setRigidBodyType(self.attachedCutter.rootNode, "Dynamic");
        self.attachedCutter:onDetach();
        self.attachedCutter = nil;]]

        local jointDesc = self.cutterAttacherJoint;
        removeJoint(jointDesc.jointIndex);
        jointDesc.jointIndex = 0;

        self.attachedCutter:onDetach();
        self.attachedCutter = nil;

        if self.threshingSound ~= nil then
            stopSample(self.threshingSound);
        end;
    end;
end;

function Bizon3:setGrainTankFillLevel(fillLevel)
    self.grainTankFillLevel = fillLevel;
    if self.grainTankFillLevel > self.grainTankCapacity then
        self.grainTankFillLevel = self.grainTankCapacity;
    end;
    if self.grainTankFillLevel < 0 then
        self.grainTankFillLevel = 0;
    end;
    if self.grainPlane ~= nil then
        local m = (self.grainPlaneMaxY - self.grainPlaneMinY) / self.grainTankCapacity;
        local xPos, yPos, zPos = getTranslation(self.grainPlane);
        setTranslation(self.grainPlane, xPos, m*self.grainTankFillLevel + self.grainPlaneMinY, zPos);
        setVisibility(self.grainPlane, self.grainTankFillLevel ~= 0);
        if self.grainPlaneWindow ~= nil then
            local startFillLevel = (self.grainPlaneWindowStartY-self.grainPlaneMinY)/m;
            local windowXPos, windowYPos, windowZPos = getTranslation(self.grainPlaneWindow);
            local yTranslation = math.min(m*(self.grainTankFillLevel-startFillLevel)+self.grainPlaneWindowMinY, self.grainPlaneWindowMaxY);
            setTranslation(self.grainPlaneWindow, windowXPos, yTranslation, windowZPos);
            setVisibility(self.grainPlaneWindow, self.grainTankFillLevel >= startFillLevel);
        end;
    end;
end;

function Bizon3:findTrailerRaycastCallback(transformId, x, y, z, distance)

    self.trailerFound = 0;
    if getUserAttribute(transformId, "vehicleType") == 2 then
        self.trailerFound = transformId;
    end;

    return false;

end;

function Bizon3:onLeave()
    Bizon3:superClass().onLeave(self);
    _=[[if self.pipeLight ~= nil then
        setVisibility(self.pipeLight, false);
    end;]]
    if self.threshingSound ~= nil then
        stopSample(self.threshingSound);
    end;
	self.rundumleuchtenAn = false;
    for i=1, self.rundumleuchtenAnz do
       setVisibility(self.rundumleuchten[i].light, self.rundumleuchtenAn);
    end;
end;

function Bizon3:draw()
    Bizon3:superClass().draw(self);
    local percent = self.grainTankFillLevel/self.grainTankCapacity*100;
    if self.drawFillLevel then
        --if percent > 95 then
        --    setTextColor(1.0, 0.0, 0.0, 1.0);
        --else
        --    setTextColor(1.0, 1.0, 1.0, 1.0);
        --end;
        --renderText(0.015, 0.95, 0.03, string.format("Füllstand: %.0f (%d%%)", self.grainTankFillLevel, percent));
        Bizon3:superClass().drawGrainLevel(self, self.grainTankFillLevel, self.grainTankCapacity, 95);
    end;
    if self.pipeOpen and not self.pipeParticleActivated and self.grainTankFillLevel > 0 then
        g_currentMission:addExtraPrintText(g_i18n:getText("Move_the_pipe_over_a_trailer"));
    elseif self.grainTankFillLevel == self.grainTankCapacity then
        g_currentMission:addExtraPrintText(g_i18n:getText("Dump_corn_to_continue_threshing"));
    end;
    if self.attachedCutter ~= nil then
        if self.attachedCutter:isReelStarted() then
            g_currentMission:addHelpButtonText(g_i18n:getText("Turn_off_cutter"), InputBinding.ACTIVATE_THRESHING);
        else
            g_currentMission:addHelpButtonText(g_i18n:getText("Turn_on_cutter"), InputBinding.ACTIVATE_THRESHING);
        end;
    end;
    if self.pipeOpening then
        g_currentMission:addHelpButtonText(g_i18n:getText("Pipe_in"), InputBinding.EMPTY_GRAIN);
    else
        if percent > 80 then
            g_currentMission:addHelpButtonText(g_i18n:getText("Dump_corn"), InputBinding.EMPTY_GRAIN);
        end;
    end;

    if self.attachedCutter ~= nil then
        self.attachedCutter:draw();
    end;

	g_currentMission:addExtraPrintText(string.format("Help panel: %s", string.char(self.keys.help)));

	if self.help then
		renderText(0.05, 0.28, 0.025, string.format("Straw on/off: %s", self.keynames.stroh));
		if self.strawChopperNode1 ~= nil then
			renderText(0.05, 0.26, 0.025, string.format("Chopper blind open/close: %s", self.keynames.chopperblind));
		end;
		if self.rundumleuchten ~= nil then
			renderText(0.05, 0.24, 0.025, string.format("Beacon on/off: %s", self.keynames.beacon));
		end;
		if self.coversNode ~= nil then
			renderText(0.05, 0.22, 0.025, string.format("Covers on/off: %s", self.keynames.covers));
		end;
		if self.engineCoverNode ~= nil then
			renderText(0.05, 0.2, 0.025, string.format("Engine cover on/off: %s", self.keynames.enginecover));
		end;
		if self.coversNode ~= nil then
			renderText(0.05, 0.18, 0.025, string.format("Configurations (railing/cabins) %s, %s, %s, %s", self.keynames.railing, self.keynames.cabin1, self.keynames.cabin2, self.keynames.cabin3));
		end;
	end;
end;

function Bizon3:startThreshing()
    if self.attachedCutter ~= nil then
        self.attachedCutter:setReelSpeed(0.003);
        self.attachedCutter:onStartReel();
        self.chopperActivated = true;
        self.cutterAttacherJointMoveDown = true;
        if self.threshingSound ~= nil then
            setSamplePitch(self.threshingSound, math.min(self.threshingSoundPitchOffset + self.threshingSoundPitchScale*math.abs(self.lastSoundSpeed), self.threshingSoundPitchMax));
            playSample(self.threshingSound, 0, 1, 0);
        end;
    end;
end;

function Bizon3:stopThreshing()
    if self.attachedCutter ~= nil then
        self.attachedCutter:onStopReel();
        self.chopperActivated = false;
        self.cutterAttacherJointMoveDown = false;
        if self.threshingSound ~= nil then
            stopSample(self.threshingSound);
        end;
    end;
end;