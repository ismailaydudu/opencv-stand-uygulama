@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/3] Python ortami hazirlaniyor...
python -m venv .venv
if errorlevel 1 goto fail
echo [2/3] Paketler kontrol ediliyor...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo [3/3] Yalnizca kisi ayirma modeli hazirlaniyor (SDXL-Turbo indirilmez)...
.venv\Scripts\python.exe hazirla.py
if errorlevel 1 goto fail
echo Kurulum tamamlandi. 2_BASLAT.bat dosyasini acin.
pause
exit /b 0
:fail
echo Kurulum tamamlanamadi. Yukaridaki hatayi kontrol edin.
echo Python 3.12 64-bit ve internet baglantisi gereklidir.
pause
exit /b 1
