@echo off
REM Script de instalación para JORGE - Books to Woocommerce en Windows

echo.
echo 🚀 JORGE - Books to Woocommerce - Instalacion
echo ==============================
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Windows PowerShell
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ❌ Python no esta instalado. Por favor instala Python 3 primero.
        echo Descargalo desde: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

for /f "tokens=*" %%i in ('%PYTHON% --version') do set PYTHON_VERSION=%%i
echo   %PYTHON_VERSION% encontrado ✓
echo.

REM Crear entorno virtual
echo Creando entorno virtual...
if not exist "venv" (
    %PYTHON% -m venv venv
    echo   Entorno virtual creado ✓
) else (
    echo   Entorno virtual ya existe ✓
)
echo.

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo   Entorno virtual activado ✓
echo.

REM Instalar dependencias
echo Instalando dependencias...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
echo   Dependencias instaladas ✓
echo.

echo ==============================
echo ✅ ¡Instalacion completada!
echo ==============================
echo.
echo Para ejecutar la aplicacion, usa:
echo   venv\Scripts\activate
echo   python main.py
echo.
pause
