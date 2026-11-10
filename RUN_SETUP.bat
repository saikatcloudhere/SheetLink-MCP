@echo off
setlocal
title SheetLink-MCP Setup Launcher
cd /d "%~dp0" || goto setup_error

echo =======================================================
echo       SheetLink-MCP 1-Click Installation Setup
echo       Author: Saikat (github.com/saikatcloudhere)
echo =======================================================
echo.

set "SHEETLINK_TOOLS=%CD%\.setup-tools"
set "UV_PYTHON_INSTALL_DIR=%SHEETLINK_TOOLS%\python"
set "UV=%SHEETLINK_TOOLS%\uv.exe"
"%UV%" --version >nul 2>&1
if errorlevel 1 (
    echo [1/3] Downloading the setup tool...
    call :download_setup_tool
    if errorlevel 1 goto setup_error
)

echo [2/3] Preparing Python and SheetLink-MCP...
call :prepare_environment
if errorlevel 1 goto setup_error

echo [3/3] Opening setup in your browser...
".venv\Scripts\python.exe" setup_wizard.py %*
if errorlevel 1 goto setup_error

exit /b 0

:download_setup_tool
set "SHEETLINK_ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "SHEETLINK_ARCH=%PROCESSOR_ARCHITEW6432%"
if /i "%SHEETLINK_ARCH%"=="AMD64" (
    set "SHEETLINK_ASSET=uv-x86_64-pc-windows-msvc.zip"
    set "SHEETLINK_UV_SHA=0cdc5b38fe5a8168ed6a25814f5ba43c21d313dd3187314fccb37b7cec46e021"
) else if /i "%SHEETLINK_ARCH%"=="ARM64" (
    set "SHEETLINK_ASSET=uv-aarch64-pc-windows-msvc.zip"
    set "SHEETLINK_UV_SHA=505d9e65e7692bac3ddf98c66754aa26c5050c409c184af30a881a0a72cc85e3"
) else (
    echo [ERROR] This installer requires 64-bit Windows.
    exit /b 1
)
if not exist "%SHEETLINK_TOOLS%" mkdir "%SHEETLINK_TOOLS%"
set "SHEETLINK_UV_ARCHIVE=%SHEETLINK_TOOLS%\uv-download.zip"
curl.exe --proto =https --tlsv1.2 --fail --silent --show-error --location --retry 2 "https://releases.astral.sh/github/uv/releases/download/0.13.7/%SHEETLINK_ASSET%" -o "%SHEETLINK_UV_ARCHIVE%"
if errorlevel 1 exit /b 1
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -Command "$ErrorActionPreference = 'Stop'; $bytes = [IO.File]::ReadAllBytes($env:SHEETLINK_UV_ARCHIVE); $sha = [Security.Cryptography.SHA256]::Create(); $actual = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', ''); if ($actual -ne $env:SHEETLINK_UV_SHA) { Write-Error 'Setup tool checksum did not match.' }"
if errorlevel 1 exit /b 1
tar.exe -xf "%SHEETLINK_UV_ARCHIVE%" -C "%SHEETLINK_TOOLS%" uv.exe
if errorlevel 1 exit /b 1
del "%SHEETLINK_UV_ARCHIVE%"
exit /b 0

:prepare_environment
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
    if not errorlevel 1 goto install_packages
)
"%UV%" --no-config venv --managed-python --python 3.13 --clear .venv
if errorlevel 1 exit /b 1

:install_packages
"%UV%" --no-config pip install --python ".venv\Scripts\python.exe" -r requirements.txt
exit /b %errorlevel%

:setup_error
echo [ERROR] Setup did not complete. Check your internet connection and reopen this launcher to retry.
pause
exit /b 1
