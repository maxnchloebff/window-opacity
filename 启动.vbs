Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("Wscript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run "pythonw """ & dir & "\window_opacity.py""", 0, False

ahk = "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
If Not fso.FileExists(ahk) Then
  ahk = "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe"
End If
script = dir & "\wallpaper_click_passthrough.ahk"
If fso.FileExists(ahk) And fso.FileExists(script) Then
  sh.Run """" & ahk & """ """ & script & """", 0, False
End If
