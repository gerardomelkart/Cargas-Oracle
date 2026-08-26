@echo off
setlocal
cd /d "%~dp0"

set "SCRIPT=%~1"

if "%SCRIPT%"=="" (
    echo No se indico el script.
    pause
    exit /b 1
)

where py >nul 2>nul

if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv

    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -c "import oracledb" >nul 2>nul

if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt

    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" "%SCRIPT%"

set "CODIGO=%errorlevel%"

echo.

if %CODIGO%==0 (
    echo Proceso terminado correctamente.
) else (
    echo El proceso termino con error.
)

pause
exit /b %CODIGO%

:error
echo.
echo No fue posible preparar o ejecutar Python.
pause
exit /b 1