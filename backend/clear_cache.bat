@echo off
echo ========================================
echo   ОЧИСТКА PYTHON CACHE
echo ========================================
echo.

cd /d "%~dp0"

echo Видалення __pycache__ папок...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo Видаляю: %%d
    rd /s /q "%%d"
)

echo.
echo Видалення .pyc файлів...
del /s /q *.pyc 2>nul

echo.
echo ========================================
echo   CACHE ОЧИЩЕНО!
echo ========================================
echo.
echo Тепер перезапустіть сервер:
echo   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.

pause
