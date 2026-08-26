@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv --system-site-packages .venv || goto :error
)

".venv\Scripts\python.exe" -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('oracledb') or importlib.util.find_spec('cx_Oracle') else 1)" >nul 2>nul
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error

".venv\Scripts\python.exe" cargar_oracle.py %*
exit /b %errorlevel%

:error
echo ERROR: no fue posible preparar o ejecutar Python.
exit /b 1
