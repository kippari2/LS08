Authors: Kippari2 (KLS Mods), Morc
Date: 25.7.2025
Uploaded to https://komeo.xyz/ls2009mods/
Additional sources:
https://github.com/TheMorc/LS08-things

Playercam controls:
Pageup = ascend
Pagedown = descend
Home = reset camera
Space = zoom
Numpad + = increase walking speed
Numpad - = decrease walking speed
Numpad * = reset walking speed

Installing Morc's screenshot lua snippet:
1. Open the main.lua file (you need to unpack it from the scripts.zip using password 411S6R5772V673kT if it isn't already in the scripts folder).
2. Find function keyEvent(unicode, sym, modifier, isDown) in it (around line 290/or use CTRL + F).
3. Add this snippet of code to the function (check the image example if you are unsure where to paste it).

if sym == 316 and isDown then
	createFolder(getUserProfileAppPath().."screenshots/")
	screenFilename = os.date(getUserProfileAppPath().."screenshots/LS2008_%d.%m.%Y_%H.%M.%S.png")
	saveScreenshot(screenFilename)
	print("saved screenshot " .. screenFilename)
end;

4. Open the game and test it with the printscreen key on your keyboard.

Screenshot locations:
Windows: AppData/Roaming/FarmingSimulator2008/ (use %appdata% to get there)
Linux: /home/username/.wine/dosdevices/c:/users/username/AppData/Roaming/FarmingSimulator2008/ (the .wine folder is hidden, so enable hidden files)
