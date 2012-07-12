; Script for AutoHotKeys, http://autohotkey.com/
; Inverts the mouse along the y axis. Works great, but not in games or other
; apps that use DirectInput. :/

#SingleInstance
#Persistent

SetBatchLines, 10ms
;CoordMode, Mouse, Screen
BlockInput, Mouse
SetMouseDelay, -1  ; Makes movement smoother.

oldy = 0  ; initial value
SetTimer, WatchMouse, 1
return

WatchMouse:
IfWinNotActive, Beyond Good & Evil - Ubisoft
	return

MouseGetPos, x, y,

delta = %y%
delta -= %oldy%
if delta <> 0
{
	delta *= -2
	MouseMove, 0, %delta%, 0, R
	MouseGetPos, x, oldy
}
return