' Create Port Manager Desktop GUI Shortcut with Icon
Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

Set oShortcut = WshShell.CreateShortcut(strDesktop & "\Port Manager GUI.lnk")
oShortcut.TargetPath = "pythonw"
oShortcut.Arguments = """d:\Extra\Test\port-manager\port_manager_gui.py"""
oShortcut.WorkingDirectory = "d:\Extra\Test\port-manager"
oShortcut.Description = "Port Manager - Desktop GUI"
' Using Windows network icon
oShortcut.IconLocation = "%SystemRoot%\System32\netcenter.dll,0"
oShortcut.Save

WScript.Echo "Desktop GUI shortcut created!"
