Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("Wscript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run "pythonw """ & dir & "\window_opacity.py""", 0, False
