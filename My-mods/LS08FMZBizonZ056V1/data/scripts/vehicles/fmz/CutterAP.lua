--
-- Cutter Autopilot
--
-- Zartask (zartask@yahoo.com)
-- 27.06.2008; v0.1 beta
--

CutterAP = {};

source("data/scripts/vehicles/fmz/BizonCutter.lua");

function CutterAP:new(configFile, positionX, offsetY, positionZ, rotationY, customMt)
    if CutterAP_mt == nil then
        CutterAP_mt = Class(CutterAP, BizonCutter);
    end;

    local mt = customMt;
    if mt == nil then
        mt = CutterAP_mt;
    end;

    local instance = BizonCutter:new(configFile, positionX, offsetY, positionZ, rotationY, mt);

    local xmlFile = loadXMLFile("TempConfig", configFile);


    local rotationPartNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.rotationPart#index"));
    if rotationPartNode ~= nil then
        instance.rotationPart = {};
        instance.rotationPart.node = rotationPartNode;
        local x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.rotationPart#minRot"));
        instance.rotationPart.minRot = {};
        instance.rotationPart.minRot[1] = Utils.degToRad(Utils.getNoNil(x, 0));
        instance.rotationPart.minRot[2] = Utils.degToRad(Utils.getNoNil(y, 0));
        instance.rotationPart.minRot[3] = Utils.degToRad(Utils.getNoNil(z, 0));

        x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.rotationPart#maxRot"));
        instance.rotationPart.maxRot = {};
        instance.rotationPart.maxRot[1] = Utils.degToRad(Utils.getNoNil(x, 0));
        instance.rotationPart.maxRot[2] = Utils.degToRad(Utils.getNoNil(y, 0));
        instance.rotationPart.maxRot[3] = Utils.degToRad(Utils.getNoNil(z, 0));

        instance.rotationPart.rotTime = Utils.getNoNil(getXMLString(xmlFile, "vehicle.rotationPart#rotTime"), 2)*1000;
        instance.rotationPart.touchRotLimit = Utils.degToRad(Utils.getNoNil(getXMLString(xmlFile, "vehicle.rotationPart#touchRotLimit"), 10));
    end;

    local csigaNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.csiga#index"));	
    if csigaNode ~= nil then
        instance.csiga = {};
        instance.csiga.node = csigaNode;
    end;


    local translationPartNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.translationPart#index"));
    if translationPartNode ~= nil then
        instance.translationPart = {};
        instance.translationPart.node = translationPartNode;
        local x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.translationPart#minTrans"));
        instance.translationPart.minTrans = {};
        instance.translationPart.minTrans[1] = Utils.getNoNil(x, 0);
        instance.translationPart.minTrans[2] = Utils.getNoNil(y, 0);
        instance.translationPart.minTrans[3] = Utils.getNoNil(z, 0);
	print ("load doTranslate and transMax")
        x, y, z = Utils.getVectorFromString(getXMLString(xmlFile, "vehicle.translationPart#maxTrans"));
        instance.translationPart.maxTrans = {};
        instance.translationPart.maxTrans[1] = Utils.getNoNil(x, 0);
        instance.translationPart.maxTrans[2] = Utils.getNoNil(y, 0);
        instance.translationPart.maxTrans[3] = Utils.getNoNil(z, 0);

        instance.translationPart.transTime = Utils.getNoNil(getXMLString(xmlFile, "vehicle.translationPart#transTime"), 2)*1000;
        instance.translationPart.touchTransLimit = Utils.getNoNil(getXMLString(xmlFile, "vehicle.translationPart#touchTransLimit"), 10);
    end;



    instance.autoPilotAreaLeft = {};
    instance.autoPilotAreaLeft.available = getXMLBool(xmlFile, "vehicle.autoPilotAreas#left");
    instance.autoPilotAreaLeft.startOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#startOutside"));
    instance.autoPilotAreaLeft.widthOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#widthOutside"));
    instance.autoPilotAreaLeft.heightOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#heightOutside"));
    instance.autoPilotAreaLeft.startInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#startInside"));
    instance.autoPilotAreaLeft.widthInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#widthInside"));
    instance.autoPilotAreaLeft.heightInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaLeft#heightInside"));
    instance.autoPilotAreaLeft.active = false;

    instance.autoPilotAreaRight = {};
    instance.autoPilotAreaRight.available = getXMLBool(xmlFile, "vehicle.autoPilotAreas#right");
    instance.autoPilotAreaRight.startOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#startOutside"));
    instance.autoPilotAreaRight.widthOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#widthOutside"));
    instance.autoPilotAreaRight.heightOutside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#heightOutside"));
    instance.autoPilotAreaRight.startInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#startInside"));
    instance.autoPilotAreaRight.widthInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#widthInside"));
    instance.autoPilotAreaRight.heightInside = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.autoPilotAreas.autoPilotAreaRight#heightInside"));
    instance.autoPilotAreaRight.active = false;

    if instance.autoPilotAreaLeft.available or instance.autoPilotAreaRight.available then
        instance.autoPilotPresent = true;
    else
        instance.autoPilotPresent = false;
    end;
    instance.hasGroundContact = false;

    delete(xmlFile);

    return instance;
end;

function CutterAP:keyEvent(unicode, sym, modifier, isDown)
    Implement.keyEvent(self, unicode, sym, modifier, isDown);
	if sym == Input.KEY_u then
                self.rotationMax = isDown;
	end;
	if sym == Input.KEY_j then
		self.rotationMin = isDown;
	end;

       if sym == Input.KEY_k then
		self.translationMax = isDown;
	end;
	if sym == Input.KEY_h then
		self.translationMin = isDown;
	end;

end;

function CutterAP:update(dt)
    CutterAP:superClass().update(self, dt);

     --if self.translationPart ~= nil and self.attachedCutter then
	--g_currentMission:addExtraPrintText("Taste P; J,U,H,K: Motolla le,fel,elore,vissza ");	
     --end;

     if self.reelStarted and self.rotationPart ~= nil then
	rotate(self.csiga.node,-0.5,0,0);
     end;

    if self.rotationPart ~= nil and (self.rotationMax or self.rotationMin) then
          local x, y, z = getRotation(self.rotationPart.node);
          local rot = {x,y,z};
          local newRot = Utils.getMovedLimitedValues(rot, self.rotationPart.maxRot, self.rotationPart.minRot, 3, self.rotationPart.rotTime, dt, not self.rotationMax);
          setRotation(self.rotationPart.node, unpack(newRot));
    end;


    if self.translationPart ~= nil and (self.translationMax or self.translationMin) then
        local x, y, z = getTranslation(self.translationPart.node);
        local trans = {x,y,z};
        local newTrans = Utils.getMovedLimitedValues(trans, self.translationPart.maxTrans, self.translationPart.minTrans, 3, self.translationPart.transTime, dt, not self.translationMax);
        setTranslation(self.translationPart.node, unpack(newTrans));
    end;

    if InputBinding.hasEvent(InputBinding.ATTACH) then
        self.hasGroundContact = false;
    end;

    if InputBinding.hasEvent(InputBinding.ACTIVATE_THRESHING) then
        if (self.hasGroundContact and self.reelStarted) or (not self.hasGroundContact and not self.reelStarted) then
            self.hasGroundContact = not self.hasGroundContact;
        end;
    end;

    if InputBinding.hasEvent(InputBinding.LOWER_IMPLEMENT) then
        self.hasGroundContact = not self.hasGroundContact;
    end;
end;
