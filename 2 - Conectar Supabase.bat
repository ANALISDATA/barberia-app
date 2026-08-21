@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Conectar Supabase

set "PATH=%LOCALAPPDATA%\Programs\Python\Python314;%LOCALAPPDATA%\Programs\Python\Python314\Scripts;%PATH%"

python Conectar_Supabase.py

echo.
pause
