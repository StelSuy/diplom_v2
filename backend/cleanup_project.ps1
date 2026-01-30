# ════════════════════════════════════════════════════════════════
# ОЧИЩЕННЯ ПРОЕКТУ - Видалення ненужних файлів
# ════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        ОЧИЩЕННЯ ПРОЕКТУ - Видалення ненужних файлів           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Цей скрипт видалить файли, які не потрібні для локальної розробки:" -ForegroundColor Yellow
Write-Host "  - Docker файли" -ForegroundColor Gray
Write-Host "  - Nginx конфігурації" -ForegroundColor Gray
Write-Host "  - Unix скрипти (.sh)" -ForegroundColor Gray
Write-Host "  - Production конфіги" -ForegroundColor Gray
Write-Host "  - Старі англійські документи" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Продовжити? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host ""
    Write-Host "Операцію скасовано." -ForegroundColor Red
    exit
}

# Лічильники
$deletedCount = 0
$notFoundCount = 0
$totalFiles = 0

# Функція для видалення файлу
function Remove-FileIfExists {
    param([string]$FilePath, [string]$Description)
    
    $global:totalFiles++
    
    if (Test-Path $FilePath) {
        try {
            Remove-Item -Path $FilePath -Force
            Write-Host "  ✓ $Description" -ForegroundColor Green
            $global:deletedCount++
        } catch {
            Write-Host "  ✗ $Description (помилка: $_)" -ForegroundColor Red
        }
    } else {
        Write-Host "  - $Description (не знайдено)" -ForegroundColor DarkGray
        $global:notFoundCount++
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[1/6] Видалення Docker файлів..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Remove-FileIfExists "Dockerfile" "Dockerfile"
Remove-FileIfExists ".dockerignore" ".dockerignore"
Remove-FileIfExists "docker-compose.dev.yml" "docker-compose.dev.yml"
Remove-FileIfExists "docker-compose.prod.yml" "docker-compose.prod.yml"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[2/6] Видалення Nginx конфігурації..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Remove-FileIfExists "nginx.conf" "nginx.conf"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[3/6] Видалення Unix скриптів..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Remove-FileIfExists "cleanup.sh" "cleanup.sh"
Remove-FileIfExists "run_dev.sh" "run_dev.sh"
Remove-FileIfExists "generate-ssl.sh" "generate-ssl.sh"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[4/6] Видалення Production файлів..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Remove-FileIfExists ".env.production.example" ".env.production.example"
Remove-FileIfExists "Makefile" "Makefile"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[5/6] Видалення старих англійських документів..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if (Test-Path "docs") {
    Push-Location "docs"
    
    $oldDocs = @(
        "START_HERE.md",
        "QUICK_START.md",
        "README.md",
        "DATABASE_MANAGEMENT.md",
        "DEPLOYMENT.md",
        "PRODUCTION_CHECKLIST.md",
        "PROJECT_ANALYSIS.md",
        "CHANGELOG.md",
        "CHEATSHEET.md",
        "CHECKLIST.md",
        "CREATED_FILES.md",
        "INDEX.md",
        "README_COMPLETE.md",
        "REFACTORING_SUMMARY.md"
    )
    
    foreach ($doc in $oldDocs) {
        Remove-FileIfExists $doc "docs\$doc"
    }
    
    Pop-Location
} else {
    Write-Host "  ! Директорія docs не знайдена" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[6/6] Очищення Python кешу..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "  Видалення __pycache__ директорій..." -ForegroundColor Gray
$pycacheDirs = Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory -Force
$pycacheCount = 0
foreach ($dir in $pycacheDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force
    $pycacheCount++
}
Write-Host "  ✓ Видалено $pycacheCount директорій __pycache__" -ForegroundColor Green

Write-Host "  Видалення .pyc файлів..." -ForegroundColor Gray
$pycFiles = Get-ChildItem -Path . -Filter *.pyc -Recurse -Force
$pycCount = 0
foreach ($file in $pycFiles) {
    Remove-Item -Path $file.FullName -Force
    $pycCount++
}
Write-Host "  ✓ Видалено $pycCount файлів .pyc" -ForegroundColor Green

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ ЗАВЕРШЕНО!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Статистика:" -ForegroundColor Yellow
Write-Host "  Всього файлів перевірено: $totalFiles" -ForegroundColor Gray
Write-Host "  Видалено: $deletedCount" -ForegroundColor Green
Write-Host "  Не знайдено: $notFoundCount" -ForegroundColor DarkGray
Write-Host "  __pycache__ директорій: $pycacheCount" -ForegroundColor Green
Write-Host "  .pyc файлів: $pycCount" -ForegroundColor Green
Write-Host ""

Write-Host "✓ Залишилися важливі файли:" -ForegroundColor Green
Write-Host "  ✓ run_dev.bat - запуск сервера" -ForegroundColor Gray
Write-Host "  ✓ clear_cache.bat - очищення кешу" -ForegroundColor Gray
Write-Host "  ✓ requirements.txt - залежності" -ForegroundColor Gray
Write-Host "  ✓ .env - налаштування" -ForegroundColor Gray
Write-Host "  ✓ app/ - код застосунку" -ForegroundColor Gray
Write-Host "  ✓ alembic/ - міграції БД" -ForegroundColor Gray
Write-Host "  ✓ docs/ - українська документація" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 Наступні кроки:" -ForegroundColor Yellow
Write-Host "  1. Перевірте .env файл" -ForegroundColor Gray
Write-Host "  2. Запустіть: run_dev.bat" -ForegroundColor Gray
Write-Host "  3. Відкрийте: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

Write-Host "Натисніть будь-яку клавішу для виходу..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
