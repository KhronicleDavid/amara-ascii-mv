@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title AMARA - ASCII Music Film
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 "%~dp0amara.py" %*
goto finish
:use_python
python "%~dp0amara.py" %*
:finish
if not errorlevel 1 goto done
echo.
echo Playback could not start. See the error above.
pause
:done
endlocal
