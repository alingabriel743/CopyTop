@echo off
REM Script pentru oprirea serviciului de backup pe Windows

echo ⏹️ Oprire serviciu backup CopyTop...

REM Caută și oprește procesul Python care rulează backup_scheduler.py
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"backup_scheduler.py" >nul
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
        if not errorlevel 1 (
            echo ✅ Serviciu backup oprit (PID: %%a)
            goto :done
        )
    )
)

echo ℹ️ Serviciul de backup nu rulează

:done
echo.
pause
