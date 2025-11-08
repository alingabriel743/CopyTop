@echo off
REM Script pentru pornirea serviciului de backup în fundal pe Windows

echo 🚀 Pornire serviciu backup CopyTop...

REM Creează directorul pentru log-uri dacă nu există
if not exist logs mkdir logs

REM Oprește procesul existent dacă rulează
taskkill /F /IM python.exe /FI "WINDOWTITLE eq backup_scheduler*" >nul 2>&1

REM Pornește serviciul în fundal
start /B python app\backup_scheduler.py > logs\backup_scheduler.log 2>&1

echo ✅ Serviciu backup pornit în fundal
echo 📁 Log-uri în: logs\backup_scheduler.log
echo.
echo Pentru a opri serviciul:
echo   stop_backup_service.bat
echo.
echo Pentru a vedea log-urile:
echo   type logs\backup_scheduler.log
echo.
pause
