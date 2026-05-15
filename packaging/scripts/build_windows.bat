@echo off
setlocal

cd /d "%~dp0\..\.."

REM Generar iconos antes de compilar
call "%~dp0\convert_icons.sh"
call venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -r requirements-build.txt

set ICON_ARG=
if exist "packaging\assets\app-icon-win.ico" set ICON_ARG=--icon packaging\assets\app-icon-win.ico

pyinstaller --noconfirm --clean --windowed ^
  --name "JORGE-Books-to-Woocommerce" ^
  --add-data "book_uploader;book_uploader" ^
  %ICON_ARG% ^
  "%CD%\main.py"

echo Build Windows finalizado. Revisa dist\JORGE-Books-to-Woocommerce
endlocal
