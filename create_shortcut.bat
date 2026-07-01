@echo off
title Creating B2C Leads Pro Desktop Shortcut...

set BAT_PATH=%~dp0start.bat
set SHORTCUT=%USERPROFILE%\Desktop\B2C Leads Pro.lnk
set ICON=%~dp0start.bat

echo Creating desktop shortcut...

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%BAT_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 1; $s.Description = 'Launch B2C Leads Pro'; $s.Save()"

echo.
echo  ============================================
echo   Shortcut created on your Desktop!
echo   Just double-click 'B2C Leads Pro' to start.
echo  ============================================
echo.
pause
