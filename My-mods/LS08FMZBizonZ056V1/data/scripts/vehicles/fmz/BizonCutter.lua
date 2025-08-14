--
-- BizonCutter
-- Modified base cutter script
--
-- @original author: Stefan Geiger (mailto:sgeiger@giants.ch)
-- @original date: 08.04.07
-- @author: kippari2 (KLS mods)
-- @date: 19.3.2024


BizonCutter = {};

function BizonCutter:new(configFile, positionX, offsetY, positionZ, rotationY, customMt)

    if BizonCutter_mt == nil then
        BizonCutter_mt = Class(BizonCutter);
    end;

    local instance = {};
    if customMt ~= nil then
        setmetatable(instance, customMt);
    else
        setmetatable(instance, BizonCutter_mt);
    end;

    local xmlFile = loadXMLFile("TempConfig", configFile);

    local rootNode = loadI3DFile(getXMLString(xmlFile, "vehicle.filename"));
    instance.rootNode = getChildAt(rootNode, 0);
    link(getRootNode(), instance.rootNode);
    delete(rootNode);

    --placementCallback = VehiclePlacementCallback:new();
    --raycastClosest(positionX, 250, positionZ, 0, -1, 0, "placementCallback.callback", 300);

    local terrainHeight = getTerrainHeightAtWorldPos(g_currentMission.terrainRootNode, positionX, 300, positionZ);

    setTranslation(instance.rootNode, positionX, terrainHeight+offsetY, positionZ);
    rotate(instance.rootNode, 0, rotationY, 0);
    --setRigidBodyType(instance.rootNode, "Dynamic");

    local indexStr = getXMLString(xmlFile, "vehicle.reel#index");
    --print(Utils.indexToObject(instance.rootNode, indexStr));
    instance.reelNode = Utils.indexToObject(instance.rootNode, indexStr);
    local numCuttingAreas = getXMLInt(xmlFile, "vehicle.cuttingAreas#count");
    instance.cuttingAreas = {}
    for i=1, numCuttingAreas do
        instance.cuttingAreas[i] = {};
        local areanamei = string.format("vehicle.cuttingAreas.cuttingArea" .. "%d", i);
        local x,y,z = getTranslation(getChildAt(instance.rootNode, getXMLInt(xmlFile, areanamei .. "#startIndex")));
        local widthX, widthY, widthZ = getTranslation(getChildAt(instance.rootNode, getXMLInt(xmlFile, areanamei .. "#widthIndex")));
        local heightX, heightY, heightZ = getTranslation(getChildAt(instance.rootNode, getXMLInt(xmlFile, areanamei .. "#heightIndex")));
        instance.cuttingAreas[i].startX = x;
        instance.cuttingAreas[i].startZ = z;
        instance.cuttingAreas[i].width = widthX-x;
        instance.cuttingAreas[i].height = heightZ-z;
    end;

    instance.attacherJoint = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.attacherJoint#index"));

    instance.threshingParticleSystems = {};
    local psName = "vehicle.threshingParticleSystem";
    Utils.loadParticleSystem(xmlFile, instance.threshingParticleSystems, psName, instance.rootNode, false)

    instance.preferedCombineSize = Utils.getNoNil(getXMLInt(xmlFile, "vehicle.preferedCombineSize"), 1);
	
	instance.rollNode = Utils.indexToObject(instance.rootNode, getXMLString(xmlFile, "vehicle.roll#index"));
	instance.rollSpeed = Utils.getNoNil(getXMLFloat(xmlFile, "vehicle.roll#speed"));
	--print("index ", instance.rollNode, " speed ", instance.rollSpeed);

    delete(xmlFile);

    instance.isAttached = false;
    instance.reelStarted = false;

    instance.speedViolationMaxTime = 50;
    instance.speedViolationTimer = instance.speedViolationMaxTime;
    instance.printRainWarning = false;

    instance.lastArea = 0;

    return instance;
end;

function BizonCutter:delete()
    delete(self.rootNode);
end;

function BizonCutter:mouseEvent(posX, posY, isDown, isUp, button)
end;

function BizonCutter:keyEvent(unicode, sym, modifier, isDown)
end;


function BizonCutter:update(dt)

    self.lastArea = 0;
    if self.isAttached then
        if self.reelStarted and self.attacherVehicle.movingDirection >= 0 then
            local speedLimit = 14;
            if self.preferedCombineSize > self.attacherVehicle.combineSize then
                speedLimit = 8;
            end
            if self.attacherVehicle.lastSpeed*3600 > speedLimit then
                self.speedViolationTimer = self.speedViolationTimer - dt;
                if self.speedViolationTimer < 0 then
                    self.attacherVehicle:detachImplementByObject(self);
                end;
            else
                self.speedViolationTimer = self.speedViolationMaxTime;
            end;
            if self.speedViolationTimer > 0 then
                if g_currentMission.environment.lastRainScale <= 0.1 and g_currentMission.environment.timeSinceLastRain > 30 then
                    self.printRainWarning = false;
                    local realArea = 0;
                    for i=1, table.getn(self.cuttingAreas) do
                        local worldX, worldY, worldZ = localToWorld(self.rootNode, self.cuttingAreas[i].startX, 0, self.cuttingAreas[i].startZ);
                        local worldX2, worldY2, worldZ2 = localToWorld(self.rootNode, self.cuttingAreas[i].startX+self.cuttingAreas[i].width, 0, self.cuttingAreas[i].startZ);
                        local worldX3, worldY3, worldZ3 = localToWorld(self.rootNode, self.cuttingAreas[i].startX, 0, self.cuttingAreas[i].startZ+self.cuttingAreas[i].height);
                        local spray = Utils.getDensity(g_currentMission.terrainDetailId, g_currentMission.sprayChannel, worldX, worldZ, worldX2, worldZ2, worldX3, worldZ3);
                        local multi = 1;
                        if spray > 0 then
                            multi = 2;
                        end;
						Utils.updateCuttedWheatArea(worldX, worldZ, worldX2, worldZ2, worldX3, worldZ3);
						if self.attacherVehicle.cutterAttacherJointMoveDown then
							local area = Utils.updateWheatArea(worldX, worldZ, worldX2, worldZ2, worldX3, worldZ3, 0.0);
							self.lastArea = self.lastArea + area*multi;
							realArea = realArea + area;
						end;
                    end;
                    local pixelToQm = 2048 / 4096 * 2048 / 4096; -- 4096px are mapped to 2048m
                    local qm = realArea*pixelToQm;
                    local ha = qm/10000;

                    g_currentMission.missionStats.hectaresThreshedTotal = g_currentMission.missionStats.hectaresThreshedTotal + ha;
                    g_currentMission.missionStats.hectaresThreshedSession = g_currentMission.missionStats.hectaresThreshedSession + ha;

                    g_currentMission.missionStats.threshingDurationTotal = g_currentMission.missionStats.threshingDurationTotal + dt/(1000*60);
                    g_currentMission.missionStats.threshingDurationSession= g_currentMission.missionStats.threshingDurationSession + dt/(1000*60);
                else
                    self.printRainWarning = true;
                end;
            end;
        else
            self.speedViolationTimer = self.speedViolationMaxTime;
        end;

        Utils.setEmittingState(self.threshingParticleSystems, (self.reelStarted and self.lastArea > 0.0));

        if self.reelStarted then
            rotate(self.reelNode, -dt*self.reelSpeed, 0, 0);
			rotate(self.rollNode, -dt*self.rollSpeed, 0, 0);
        end;
    end;
end


function BizonCutter:draw()

    if math.abs(self.speedViolationTimer - self.speedViolationMaxTime) > 2 then
        str = "2";
        if self.isAttached and self.preferedCombineSize > self.attacherVehicle.combineSize then
            str = "1";
        end;
        g_currentMission:addWarning(string.format("Fahren Sie nicht zu schnell\nTempomat Stufe %s: Taste %s", str, str), 0.07+0.022, 0.019+0.029);
    end;

    if self.printRainWarning then
        g_currentMission:addWarning("Dreschen Sie nicht bei Regen oder Hagel", 0.018, 0.033);
    end;

end;

function BizonCutter:onAttach(attacherVehicle)
    self.isAttached = true;
    self.attacherVehicle = attacherVehicle;
end;

function BizonCutter:onDetach()
    self.isAttached = false;
    self:onStopReel();
    self.attacherVehicle = nil;
    Utils.setEmittingState(self.threshingParticleSystems, false);
    self.speedViolationTimer = self.speedViolationMaxTime;
end;

function BizonCutter:setReelSpeed(speed)
    self.reelSpeed = speed;
end;

function BizonCutter:onStartReel()
    self.reelStarted = true;
end;

function BizonCutter:onStopReel()
    self.reelStarted = false;
    Utils.setEmittingState(self.threshingParticleSystems, false);
    self.speedViolationTimer = self.speedViolationMaxTime;
end;

function BizonCutter:isReelStarted()
    return self.reelStarted;
end;

_=[[function BizonCutter:attachTriggerCallback(triggerId, otherId, onEnter, onLeave, onStay)

    if onEnter then
        if g_currentMission.currentVehicle ~= nil and g_currentMission.currentVehicle.rootNode == otherId then
            table.insert(g_currentMission.triggeredCutters, self);
        end;
    elseif onLeave then
        if g_currentMission.currentVehicle ~= nil and g_currentMission.currentVehicle.rootNode == otherId then
            for i=1, table.getn(g_currentMission.triggeredCutters) do
                if g_currentMission.triggeredCutters[i] == self.rootNode then
                    table.remove(g_currentMission.triggeredCutters, i);
                    break;
                end;
            end;
        end;
    end;
end;]]