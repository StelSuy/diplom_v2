@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================================
echo           CLEANUP PROJECT - Remove Unnecessary Files           
echo ================================================================
echo.
echo This script will remove files not needed for local development:
echo   - Docker files
echo   - Nginx configs
echo   - Unix scripts (.sh)
echo   - Production configs
echo   - Old English docs
echo.

set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo Operation cancelled.
    pause
    exit /b
)

set deleted=0
set notfound=0

echo.
echo ================================================================
echo [1/6] Removing Docker files...
echo ================================================================

if exist "Dockerfile" (
    del /f /q "Dockerfile" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] Dockerfile
        set /a deleted+=1
    )
) else (
    echo   [-] Dockerfile not found
    set /a notfound+=1
)

if exist ".dockerignore" (
    del /f /q ".dockerignore" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] .dockerignore
        set /a deleted+=1
    )
) else (
    echo   [-] .dockerignore not found
    set /a notfound+=1
)

if exist "docker-compose.dev.yml" (
    del /f /q "docker-compose.dev.yml" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] docker-compose.dev.yml
        set /a deleted+=1
    )
) else (
    echo   [-] docker-compose.dev.yml not found
    set /a notfound+=1
)

if exist "docker-compose.prod.yml" (
    del /f /q "docker-compose.prod.yml" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] docker-compose.prod.yml
        set /a deleted+=1
    )
) else (
    echo   [-] docker-compose.prod.yml not found
    set /a notfound+=1
)

echo.
echo ================================================================
echo [2/6] Removing Nginx config...
echo ================================================================

if exist "nginx.conf" (
    del /f /q "nginx.conf" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] nginx.conf
        set /a deleted+=1
    )
) else (
    echo   [-] nginx.conf not found
    set /a notfound+=1
)

echo.
echo ================================================================
echo [3/6] Removing Unix scripts...
echo ================================================================

if exist "cleanup.sh" (
    del /f /q "cleanup.sh" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] cleanup.sh
        set /a deleted+=1
    )
) else (
    echo   [-] cleanup.sh not found
    set /a notfound+=1
)

if exist "run_dev.sh" (
    del /f /q "run_dev.sh" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] run_dev.sh
        set /a deleted+=1
    )
) else (
    echo   [-] run_dev.sh not found
    set /a notfound+=1
)

if exist "generate-ssl.sh" (
    del /f /q "generate-ssl.sh" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] generate-ssl.sh
        set /a deleted+=1
    )
) else (
    echo   [-] generate-ssl.sh not found
    set /a notfound+=1
)

echo.
echo ================================================================
echo [4/6] Removing Production files...
echo ================================================================

if exist ".env.production.example" (
    del /f /q ".env.production.example" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] .env.production.example
        set /a deleted+=1
    )
) else (
    echo   [-] .env.production.example not found
    set /a notfound+=1
)

if exist "Makefile" (
    del /f /q "Makefile" 2>nul
    if !errorlevel! equ 0 (
        echo   [OK] Makefile
        set /a deleted+=1
    )
) else (
    echo   [-] Makefile not found
    set /a notfound+=1
)

echo.
echo ================================================================
echo [5/6] Removing old English docs...
echo ================================================================

cd docs 2>nul
if errorlevel 1 (
    echo   [!] docs directory not found, skipping...
) else (
    if exist "START_HERE.md" (
        del /f /q "START_HERE.md" 2>nul && echo   [OK] START_HERE.md && set /a deleted+=1
    )
    if exist "QUICK_START.md" (
        del /f /q "QUICK_START.md" 2>nul && echo   [OK] QUICK_START.md && set /a deleted+=1
    )
    if exist "README.md" (
        del /f /q "README.md" 2>nul && echo   [OK] README.md && set /a deleted+=1
    )
    if exist "DATABASE_MANAGEMENT.md" (
        del /f /q "DATABASE_MANAGEMENT.md" 2>nul && echo   [OK] DATABASE_MANAGEMENT.md && set /a deleted+=1
    )
    if exist "DEPLOYMENT.md" (
        del /f /q "DEPLOYMENT.md" 2>nul && echo   [OK] DEPLOYMENT.md && set /a deleted+=1
    )
    if exist "PRODUCTION_CHECKLIST.md" (
        del /f /q "PRODUCTION_CHECKLIST.md" 2>nul && echo   [OK] PRODUCTION_CHECKLIST.md && set /a deleted+=1
    )
    if exist "PROJECT_ANALYSIS.md" (
        del /f /q "PROJECT_ANALYSIS.md" 2>nul && echo   [OK] PROJECT_ANALYSIS.md && set /a deleted+=1
    )
    if exist "CHANGELOG.md" (
        del /f /q "CHANGELOG.md" 2>nul && echo   [OK] CHANGELOG.md && set /a deleted+=1
    )
    if exist "CHEATSHEET.md" (
        del /f /q "CHEATSHEET.md" 2>nul && echo   [OK] CHEATSHEET.md && set /a deleted+=1
    )
    if exist "CHECKLIST.md" (
        del /f /q "CHECKLIST.md" 2>nul && echo   [OK] CHECKLIST.md && set /a deleted+=1
    )
    if exist "CREATED_FILES.md" (
        del /f /q "CREATED_FILES.md" 2>nul && echo   [OK] CREATED_FILES.md && set /a deleted+=1
    )
    if exist "INDEX.md" (
        del /f /q "INDEX.md" 2>nul && echo   [OK] INDEX.md && set /a deleted+=1
    )
    if exist "README_COMPLETE.md" (
        del /f /q "README_COMPLETE.md" 2>nul && echo   [OK] README_COMPLETE.md && set /a deleted+=1
    )
    if exist "REFACTORING_SUMMARY.md" (
        del /f /q "REFACTORING_SUMMARY.md" 2>nul && echo   [OK] REFACTORING_SUMMARY.md && set /a deleted+=1
    )
    cd ..
)

echo.
echo ================================================================
echo [6/6] Cleaning Python cache...
echo ================================================================

echo   Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rd /s /q "%%d" 2>nul && echo   [OK] %%d
)

echo.
echo   Removing .pyc files...
del /s /q *.pyc >nul 2>&1
echo   [OK] All .pyc files removed

echo.
echo ================================================================
echo COMPLETED!
echo ================================================================
echo.
echo Statistics:
echo   Deleted: %deleted% files
echo   Not found: %notfound% files
echo.
echo Project cleaned for local development.
echo.
echo Important files remain:
echo   [OK] run_dev.bat - start server
echo   [OK] clear_cache.bat - clear cache
echo   [OK] requirements.txt - dependencies
echo   [OK] .env - settings
echo   [OK] app/ - application code
echo   [OK] alembic/ - DB migrations
echo   [OK] docs/ - Ukrainian documentation
echo.
echo Next steps:
echo   1. Check .env file
echo   2. Run: run_dev.bat
echo   3. Open: http://localhost:8000/docs
echo.
pause
