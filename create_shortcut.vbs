' Create Port Manager Shortcut with Icon
Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

Set oShortcut = WshShell.CreateShortcut(strDesktop & "\Port Manager.lnk")
oShortcut.TargetPath = "d:\Extra\Test\port-manager\PortManager.bat"
oShortcut.WorkingDirectory = "d:\Extra\Test\port-manager"
oShortcut.Description = "Port Manager - Process Monitor"
' Using Windows network icon
oShortcut.IconLocation = "%SystemRoot%\System32\netcenter.dll,0"
oShortcut.Save

WScript.Echo "Shortcut created successfully!"
