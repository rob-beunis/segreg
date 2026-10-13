@echo off
cd /d "%~dp0"
python segreg.py %*
if errorlevel 1 pause
