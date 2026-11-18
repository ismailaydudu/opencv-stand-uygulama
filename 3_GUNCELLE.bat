@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Once 1_KUR.bat dosyasini calistirin.
 pause
 exit /b 1
)
echo Kisi ayirma modeli hazirlaniyor. Ilk seferde yaklasik 176 MB indirilir.
echo SDXL-Turbo veya uretken gorsel modeli indirilmez.
.venv\Scripts\python.exe hazirla.py
if errorlevel 1 (
 echo Model hazirlanamadi. Yukaridaki hatayi kontrol edin.
 pause
 exit /b 1
)
echo Guncelleme tamamlandi. 2_BASLAT.bat dosyasini acin.
pause
