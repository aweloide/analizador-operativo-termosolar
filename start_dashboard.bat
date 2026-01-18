@echo off
REM Script para iniciar el Thermosolar Dashboard
REM Este archivo activa el entorno virtual e inicia la aplicación

echo.
echo ====================================================================
echo   THERMOSOLAR DASHBOARD - Iniciando...
echo ====================================================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Activar el entorno virtual
echo Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Iniciar el dashboard
echo.
echo ====================================================================
echo   Dashboard disponible en: http://127.0.0.1:8050
echo   Presiona Ctrl+C para detener el servidor
echo ====================================================================
echo.

python app.py

REM Mantener la ventana abierta si hay error
if errorlevel 1 (
    echo.
    echo Error al ejecutar el dashboard
    pause
)
