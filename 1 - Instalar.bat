@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Instalar Barberia App

set PYTHONDONTWRITEBYTECODE=1

echo ==========================================================
echo    INSTALAR BARBERIA APP EN ESTE COMPUTADOR
echo ==========================================================
echo.
echo  Esto solo se hace UNA VEZ.
echo.
echo ----------------------------------------------------------
echo.

rem ---------- 1. Python ----------
echo [1/3] Buscando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ^> NO se encontro Python en este computador.
    echo.
    echo   Descargalo de:  https://www.python.org/downloads/
    echo.
    echo   IMPORTANTE: en la primera pantalla del instalador, MARCA la casilla
    echo   "Add Python to PATH" antes de darle a Install.
    echo.
    echo   Cuando termine, vuelve a abrir este archivo.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo       Encontrado: %%v

rem ---------- 2. Librerias ----------
echo.
echo [2/3] Instalando las librerias que necesita la app...
echo.
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo   ^> Fallo la instalacion de librerias. Copia el mensaje de arriba
    echo     y enviaselo a quien te comparte la aplicacion.
    echo.
    pause
    exit /b 1
)
echo       Librerias instaladas.

rem ---------- 3. Supabase ----------
echo.
echo [3/3] Revisando la conexion con Supabase...
python Conectar_Supabase.py

echo.
echo ==========================================================
echo    LISTO.
echo.
echo    Para abrirla: doble clic en  ▶ ABRIR LA APP.bat
echo ==========================================================
echo.
pause
