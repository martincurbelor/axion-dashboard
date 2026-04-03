@echo off
:: ejecutar.bat
:: Este archivo corre el script Python y sube los datos a GitHub.
:: El Programador de tareas de Windows lo llama automaticamente cada dia.

cd /d "%~dp0"

echo [%date% %time%] Iniciando actualizacion de datos...

:: Correr el script Python
python procesar_datos.py

if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: el script fallo con codigo %errorlevel%
    exit /b %errorlevel%
)

echo [%date% %time%] Actualizacion completada exitosamente
