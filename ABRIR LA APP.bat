@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Barberia App

set PYTHONDONTWRITEBYTECODE=1

set "PATH=%LOCALAPPDATA%\Programs\Python\Python314;%LOCALAPPDATA%\Programs\Python\Python314\Scripts;%PATH%"

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ==========================================================
    echo    Python no esta instalado en este computador.
    echo.
    echo    Ejecuta primero:  1 - Instalar.bat
    echo  ==========================================================
    echo.
    pause
    exit /b 1
)

echo.
echo  Abriendo Barberia App...
echo  (deja esta ventana abierta mientras uses la aplicacion)
echo.

python -m streamlit run Aplicacion.py

echo.
echo  La aplicacion se cerro.
pause
