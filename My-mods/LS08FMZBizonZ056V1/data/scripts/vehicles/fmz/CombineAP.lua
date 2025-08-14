--
-- Combine Autopilot
--
-- Base Zartask (zartask@yahoo.com)
-- 27.06.2008; v0.1 beta
--
--
-- Autopilot2
--
-- ModAuthor: Headshot XXL (www.team-flash.eu)
-- date: 28.12.2008; AP2beta9
--


CombineAP = {};

source("data/scripts/vehicles/fmz/Bizon1.lua");

function CombineAP:new(configFile, positionX, offsetY, positionZ, rotationY, customMt)
    if CombineAP_mt == nil then
        CombineAP_mt = Class(CombineAP, Bizon1);
    end;

    local mt = customMt;
    if mt == nil then
        mt = CombineAP_mt;
    end;


    local instance = Bizon1:new(configFile, positionX, offsetY, positionZ, rotationY, mt); ---

    local xmlFile = loadXMLFile("TempConfig", configFile); ----  
    
    instance.combinetype = getXMLString(xmlFile, "vehicle.name");


    instance.pipep = {};
    local psName = "vehicle.pipeParticleSystem";
    Utils.loadParticleSystem(xmlFile, instance.pipep, psName, instance.rootNode, false)
	
    instance.autoPilotEnabled = false;
    instance.autoPilotDelayLeft = 0;
    instance.autoPilotDelayRight = 0;

    instance.turnDirection = 0;
    instance.autoRotateBackSpeedBackup = instance.autoRotateBackSpeed;

    instance.stopped = false;

    delete(xmlFile);
    		
    return instance;
end;

function CombineAP:delete()
    CombineAP:superClass().delete(self);
end;

function CombineAP:mouseEvent(posX, posY, isDown, isUp, button)
    CombineAP:superClass().mouseEvent(self, posX, posY, isDown, isUp, button);
end;

function CombineAP:keyEvent(unicode, sym, modifier, isDown)
    CombineAP:superClass().keyEvent(self, unicode, sym, modifier, isDown);

    if self.attachedCutter ~= nil then
        self.attachedCutter:keyEvent(unicode, sym, modifier, isDown);

        if self.attachedCutter.autoPilotPresent then
            if sym == Input.KEY_p and isDown then
                self.autoPilotEnabled = not self.autoPilotEnabled;

                if not self.attachedCutter.autoPilotAreaLeft.active and not self.attachedCutter.autoPilotAreaRight.active then
                    if self.attachedCutter.autoPilotAreaLeft.available then
                        self.attachedCutter.autoPilotAreaLeft.active = true;
                    elseif self.attachedCutter.autoPilotAreaRight.available then
                        self.attachedCutter.autoPilotAreaRight.active = true;
                    end;
                end;

                if self.autoPilotEnabled and self.attachedCutter.reelStarted and self.attachedCutter.hasGroundContact then
                    self.autoRotateBackSpeed = 0;
                else
                    self.autoRotateBackSpeed = self.autoRotateBackSpeedBackup;
                end;
            end;

            if sym == Input.KEY_l and isDown then
                self.attachedCutter.autoPilotAreaLeft.active = self.attachedCutter.autoPilotAreaLeft.available;
                self.attachedCutter.autoPilotAreaRight.active = false;

                self.autoPilotDelayLeft = 0;
                self.autoPilotDelayRight = 0;
            end;

            if sym == Input.KEY_r and isDown then
                self.attachedCutter.autoPilotAreaRight.active = self.attachedCutter.autoPilotAreaRight.available;
                self.attachedCutter.autoPilotAreaLeft.active = false;

                self.autoPilotDelayRight = 0;
                self.autoPilotDelayLeft = 0;
            end;

        end;
   end;

end;

function CombineAP:update(dt)
    CombineAP:superClass().update(self, dt);

    if InputBinding.hasEvent(InputBinding.ATTACH) or InputBinding.hasEvent(InputBinding.ACTIVATE_THRESHING) or InputBinding.hasEvent(InputBinding.LOWER_IMPLEMENT) then
        if self.attachedCutter ~= nil and self.attachedCutter.autoPilotPresent then
            if self.autoPilotEnabled and self.attachedCutter.reelStarted and self.attachedCutter.hasGroundContact then
                self.autoRotateBackSpeed = 0;
            else
                self.autoRotateBackSpeed = self.autoRotateBackSpeedBackup;
            end;
        end;
    end;
	
    if self.stopped then	
		g_currentMission:addExtraPrintText("Mähdrescher STOPP");		
		if self.isEntered then
			self.stopped=false;
		end;
    end;	
	
	
        if self.pipeLight ~= nil then
            local pipeLightActive = self.lightsActive and self.pipeOpening;
            setVisibility(self.pipeLight, pipeLightActive);
        end;

        if self.attachedCutter ~= nil and self.attachedCutter.autoPilotPresent then
            if self.autoPilotEnabled and self.attachedCutter.reelStarted then --and self.attachedCutter.hasGroundContact then | and self.movingDirection > 0
                self.turnDirection = 0;

                if self.attachedCutter.autoPilotAreaLeft.available and self.attachedCutter.autoPilotAreaLeft.active then
                    local x,y,z = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.startOutside);
                    local x1,y1,z1 = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.widthOutside);
                    local x2,y2,z2 = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.heightOutside);
                    local left = Utils.getDensity(g_currentMission.wheatId, 0, x, z, x1, z1, x2, z2);
					--print("left-", left)

                    local x,y,z = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.startInside);
                    local x1,y1,z1 = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.widthInside);
                    local x2,y2,z2 = getWorldTranslation(self.attachedCutter.autoPilotAreaLeft.heightInside);
                    local right = Utils.getDensity(g_currentMission.wheatId, 0, x, z, x1, z1, x2, z2);
					--print("right-", right)

                    self.turnDirection = (9 -right) -left;
                    
                    if (left < 1 and right < 1) or (left > 8 and right > 8) then
                        self.autoPilotDelayLeft = self.autoPilotDelayLeft +1;
                    else
                        self.autoPilotDelayLeft = 0;
                    end;
                end;

                if self.attachedCutter.autoPilotAreaRight.available and self.attachedCutter.autoPilotAreaRight.active then
                    local x,y,z = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.startOutside);
                    local x1,y1,z1 = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.widthOutside);
                    local x2,y2,z2 = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.heightOutside);
                    local right = Utils.getDensity(g_currentMission.wheatId, 0, x, z, x1, z1, x2, z2);

                    local x,y,z = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.startInside);
                    local x1,y1,z1 = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.widthInside);
                    local x2,y2,z2 = getWorldTranslation(self.attachedCutter.autoPilotAreaRight.heightInside);
                    local left = Utils.getDensity(g_currentMission.wheatId, 0, x, z, x1, z1, x2, z2);

                    self.turnDirection = right -(9 -left);

                    if (left < 1 and right < 1) or (left > 8 and right > 8) then
                        self.autoPilotDelayRight = self.autoPilotDelayRight +1;
                    else
                        self.autoPilotDelayRight = 0;
                    end;
                end;

                local acceleration = 0;
                if g_currentMission.allowSteerableMoving and not self.playMotorSound then
                    if self.motor.speedLevel ~= 0 then
                        acceleration = 1.0;
                    end;
                end;
                if self.fuelFillLevel == 0 then
                    acceleration = 0;
                end;

                local rotScale = math.min(1.0/(self.lastSpeed*50+1), 1);
				if self.attachedCutter.autoPilotAreaLeft.active and self.turnDirection < -8 then
                    self.rotatedTime = math.max(self.rotatedTime - dt/1000*self.turnDirection*rotScale, 0.90);-----self.minRotTime
                elseif self.turnDirection < -4 then
                    self.rotatedTime = math.min(self.rotatedTime - dt/1000*self.turnDirection*100, 0.20);----self.maxRotTime
				elseif self.attachedCutter.autoPilotAreaLeft.active and self.turnDirection > 8 then
                    self.rotatedTime = math.max(self.rotatedTime - dt/1000*self.turnDirection*rotScale, -0.90);-----self.minRotTime				
                elseif self.turnDirection > 4 then
                    self.rotatedTime = math.max(self.rotatedTime - dt/1000*self.turnDirection*100, -0.20);-----self.minRotTime
                else
                    self.rotatedTime = 0;
                end;

                if self.firstTimeRun then
                    WheelsUtil.updateWheels(self, dt, self.lastSpeed, acceleration, false, 0)
                end;
            
                if self.steering ~= nil then
                    setRotation(self.steering, 0, self.rotatedTime*self.steeringSpeed, 0);
                end;

                if self.autoPilotDelayLeft > 300 or self.autoPilotDelayRight > 300 then
                    self.autoRotateBackSpeed = self.autoRotateBackSpeedBackup;
					
					if not self.isEntered then

						self.motor.speedLevel = 0;
						self.stopped=true;
					end;
                end;
		
            else
                self.autoPilotDelayLeft = 0;
                self.autoPilotDelayRight = 0;

                if not self.attachedCutter.reelStarted then
                    self.autoPilotEnabled = false;
                    self.autoRotateBackSpeed = self.autoRotateBackSpeedBackup;
					
					--if self.autoPilotEnabled then 
						--self.motor.speedLevel = 0;
					--end;
                end;
            end;	
        end;	
  
end;

function CombineAP:draw()
    CombineAP:superClass().draw(self);

  if self.attachedCutter ~= nil and self.attachedCutter.autoPilotPresent then

    if self.attachedCutter ~= nil then
        if not self.autoPilotEnabled then
            if self.attachedCutter.autoPilotAreaLeft.active then
                g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot links einschalten");
            elseif self.attachedCutter.autoPilotAreaRight.active then
                g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot rechts einschalten");	

            else
                g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot einschalten");
            end;
        else
            if self.attachedCutter.autoPilotAreaLeft.active then
                if self.movingDirection > 0 and self.attachedCutter.reelStarted then 
                    g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot links (aktiv) ausschalten");
                else
                    g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot links (inaktiv) ausschalten");
                end;
            elseif self.attachedCutter.autoPilotAreaRight.active then
                if self.movingDirection > 0 and self.attachedCutter.reelStarted then 
                    g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot rechts (aktiv) ausschalten");
                else
                    g_currentMission:addExtraPrintText("Taste P; L,R: Autopilot rechts (inaktiv) ausschalten");
                end;
            end;
        end;
    end;
  end;
end;

function CombineAP:onEnter()
    CombineAP:superClass().onEnter(self);
    stopSample(self.fulledSound);
end;

function CombineAP:onLeave()
    CombineAP:superClass().onLeave(self);
    
    if self.pipeLight ~= nil then
        setVisibility(self.pipeLight, false);
    end;
end;
function CombineAP:onDetach()
    CombineAP.onDetach(self);
    ---stopSample(self.fulledSound);

end;
