@echo off
echo ========================================
echo   CLEANUP TIMETRACKER PROJECT
echo ========================================
echo.

echo This script will delete old files
echo Press Ctrl+C to cancel or any key to continue...
pause >nul

echo.
echo [1/4] Removing old README files...
del /Q COMMANDS_CHEATSHEET.md 2>nul
del /Q DEPLOYMENT_SUMMARY.md 2>nul
del /Q FIX_SESSION_FUNC_ERROR.md 2>nul
del /Q QUICKSTART_DEPLOY.md 2>nul
del /Q QUICK_FIX_FUNC_ERROR.md 2>nul
del /Q README_DEPLOYMENT.md 2>nul
del /Q README_DEPLOY_VPS.md 2>nul
del /Q "TERMI*.md" 2>nul
del /Q "CHECK*.md" 2>nul
echo Done!

echo.
echo [2/4] Removing extra files...
del /Q fmtTime_fix.js 2>nul
del /Q cleanup_old_files.bat 2>nul
del /Q setup_favicon.bat 2>nul
del /Q clear_cache.bat 2>nul
del /Q 4ff09ba5-1d89-46ec-aebb-4eb47660edfb128-128.ico 2>nul
del /Q DejaVuSerif.ttf 2>nul
echo Done!

echo.
echo [3/4] Removing extra HTML files in static...
del /Q app\static\index1.html 2>nul
del /Q app\static\index2.html 2>nul
del /Q app\static\index3.html 2>nul
echo Done!

echo.
echo [4/4] Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
echo Done!

echo.
echo ========================================
echo   CLEANUP COMPLETED!
echo ========================================
echo.
echo Old files removed.
echo Project is ready!
echo.
echo Now run:
echo   uvicorn app.main:app --reload
echo.
pause
