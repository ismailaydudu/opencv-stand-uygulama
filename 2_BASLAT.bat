@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Once 1_KUR.bat dosyasini calistirin.
 pause
 exit /b 1
)
.venv\Scripts\python.exe app.py --camera 0
if errorlevel 1 pause
