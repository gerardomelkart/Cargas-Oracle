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

if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul

    if errorlevel 1 goto :sin_python

    set "PYTHON=python"
)

set "VENV_BASE=%LOCALAPPDATA%\Cargas-Oracle"
set "VENV_DIR=%VENV_BASE%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" --version >nul 2>nul

    if errorlevel 1 (
        echo Eliminando entorno virtual incompatible...
        rmdir /s /q "%VENV_DIR%"
    )
)

if not exist "%VENV_PYTHON%" (
    echo Creando entorno virtual para esta computadora...

    if not exist "%VENV_BASE%" (
        mkdir "%VENV_BASE%"
    )

    %PYTHON% -m venv "%VENV_DIR%"

    if errorlevel 1 goto :error
)

"%VENV_PYTHON%" -c "import oracledb" >nul 2>nul

if errorlevel 1 (
    echo Instalando controlador Oracle...

    "%VENV_PYTHON%" -m pip install -r requirements.txt

    if errorlevel 1 goto :error
)

"%VENV_PYTHON%" "%SCRIPT%"

set "CODIGO=%errorlevel%"

echo.

if %CODIGO%==0 (
    echo Proceso terminado correctamente.
) else (
    echo El proceso termino con error.
)

pause
exit /b %CODIGO%

:sin_python
echo.
echo ERROR: Python 3 no esta instalado en esta computadora.
echo Instala Python 3 y vuelve a ejecutar este archivo.
pause
exit /b 1

:error
echo.
echo No fue posible preparar o ejecutar Python.
pause
exit /b 1