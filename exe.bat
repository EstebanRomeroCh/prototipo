@echo off
title Banco de Alimentos - Servidor

cd /d "%~dp0"

echo ==========================================
echo   Iniciando Banco de Alimentos (Flask)
echo   Carpeta: %cd%
echo ==========================================

REM 1) Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python no esta instalado.
        pause
        exit /b
    )
    set PY=py
) else (
    set PY=python
)

REM 2) Crear entorno virtual solo si no existe
if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    %PY% -m venv venv

    echo Instalando dependencias...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM 3) Ejecutar Flask sin reinstalar paquetes
echo Iniciando servidor Flask...
cd backend
python app.py

pause