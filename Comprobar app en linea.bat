@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Comprobar Barberia App

set "PATH=%LOCALAPPDATA%\Programs\Python\Python314;%LOCALAPPDATA%\Programs\Python\Python314\Scripts;%PATH%"

python Comprobar_App_En_Linea.py

echo.
pause
