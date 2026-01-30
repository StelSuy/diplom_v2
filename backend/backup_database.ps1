# ====================================
# Automatic Database Backup Script
# ====================================
# Створює backup бази даних з timestamp

param(
    [string]$Comment = "",
    [switch]$Compress = $false
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TimeTracker - Database Backup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Конфігурація
$backupDir = "F:\Вуз\ДИПЛОМ\SYSTEM\backend\backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$maxBackups = 10

# Читання конфігурації з .env
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -match "DATABASE_URL=mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^\?]+)") {
        $dbUser = $matches[1]
        $dbPass = $matches[2]
        $dbHost = $matches[3]
        $dbPort = $matches[4]
        $dbName = $matches[5]
    } else {
        Write-Host "✗ Cannot parse DATABASE_URL from .env" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    exit 1
}

# Створити директорію backups якщо не існує
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "✓ Created backups directory" -ForegroundColor Green
}

# Ім'я файлу backup
if ($Comment) {
    $backupFile = "$backupDir\backup_${timestamp}_$Comment.sql"
} else {
    $backupFile = "$backupDir\backup_$timestamp.sql"
}

# Інформація про backup
Write-Host "Backup Information:" -ForegroundColor Yellow
Write-Host "  Database: $dbName" -ForegroundColor White
Write-Host "  Host: $dbHost" -ForegroundColor White
Write-Host "  File: $(Split-Path $backupFile -Leaf)" -ForegroundColor White
Write-Host ""

# Створити backup
Write-Host "Creating backup..." -ForegroundColor Yellow
$startTime = Get-Date

try {
    # Виконати mysqldump
    $mysqlDumpCmd = "mysqldump -u $dbUser -p$dbPass -h $dbHost -P $dbPort $dbName"
    $output = Invoke-Expression $mysqlDumpCmd 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Backup failed!" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        exit 1
    }
    
    # Записати у файл
    $output | Out-File -FilePath $backupFile -Encoding UTF8
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    $fileSize = (Get-Item $backupFile).Length / 1MB
    
    Write-Host "✓ Backup created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  File: $backupFile" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
    Write-Host "  Duration: $([math]::Round($duration.TotalSeconds, 2)) seconds" -ForegroundColor White
    Write-Host ""
    
    # Стиснути backup якщо потрібно
    if ($Compress) {
        Write-Host "Compressing backup..." -ForegroundColor Yellow
        $zipFile = "$backupFile.zip"
        Compress-Archive -Path $backupFile -DestinationPath $zipFile -Force
        
        $zipSize = (Get-Item $zipFile).Length / 1MB
        $compression = (1 - ($zipSize / $fileSize)) * 100
        
        Write-Host "✓ Backup compressed!" -ForegroundColor Green
        Write-Host "  Compressed size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor White
        Write-Host "  Compression: $([math]::Round($compression, 1))%" -ForegroundColor White
        Write-Host ""
        
        # Видалити незаархівований файл
        Remove-Item $backupFile
        $backupFile = $zipFile
    }
    
} catch {
    Write-Host "✗ Error creating backup!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Очистити старі backups
Write-Host "Cleaning old backups..." -ForegroundColor Yellow

$backups = Get-ChildItem "$backupDir\backup_*.sql*" | 
    Sort-Object LastWriteTime -Descending

$totalBackups = $backups.Count
Write-Host "  Total backups: $totalBackups" -ForegroundColor White

if ($totalBackups -gt $maxBackups) {
    $toDelete = $backups | Select-Object -Skip $maxBackups
    $deletedCount = 0
    
    foreach ($backup in $toDelete) {
        Remove-Item $backup.FullName -Force
        $deletedCount++
    }
    
    Write-Host "✓ Deleted $deletedCount old backups" -ForegroundColor Green
    Write-Host "  Kept: $maxBackups most recent backups" -ForegroundColor White
} else {
    Write-Host "✓ No cleanup needed" -ForegroundColor Green
}

Write-Host ""

# Список існуючих backups
Write-Host "Existing backups:" -ForegroundColor Cyan
$backups = Get-ChildItem "$backupDir\backup_*.sql*" | 
    Sort-Object LastWriteTime -Descending

foreach ($backup in $backups) {
    $size = [math]::Round($backup.Length / 1MB, 2)
    $age = (Get-Date) - $backup.LastWriteTime
    $ageStr = if ($age.TotalDays -ge 1) {
        "$([math]::Floor($age.TotalDays)) days ago"
    } elseif ($age.TotalHours -ge 1) {
        "$([math]::Floor($age.TotalHours)) hours ago"
    } else {
        "$([math]::Floor($age.TotalMinutes)) minutes ago"
    }
    
    Write-Host "  $($backup.Name)" -ForegroundColor White -NoNewline
    Write-Host " ($size MB, $ageStr)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Запропонувати дії
Write-Host "What would you like to do next?" -ForegroundColor Yellow
Write-Host "  1. Continue working" -ForegroundColor White
Write-Host "  2. Open backups folder" -ForegroundColor White
Write-Host "  3. Test restore (on test database)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-3) or press Enter to exit"

switch ($choice) {
    "1" {
        Write-Host "✓ Continuing..." -ForegroundColor Green
    }
    "2" {
        Start-Process explorer.exe -ArgumentList $backupDir
    }
    "3" {
        Write-Host ""
        Write-Host "⚠️  Test restore should be done on a separate test database!" -ForegroundColor Yellow
        Write-Host "Example command:" -ForegroundColor Cyan
        Write-Host "  mysql -u root -p test_db < $backupFile" -ForegroundColor White
        Write-Host ""
    }
    default {
        Write-Host "Exiting..." -ForegroundColor Gray
    }
}
