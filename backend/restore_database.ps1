# ====================================
# Database Restore Script
# ====================================
# Відновлює базу даних з backup файлу

param(
    [string]$BackupFile = ""
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TimeTracker - Database Restore" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Конфігурація
$backupDir = "F:\Вуз\ДИПЛОМ\SYSTEM\backend\backups"

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

# Якщо файл не вказано - показати список
if (!$BackupFile -or !(Test-Path $BackupFile)) {
    Write-Host "Available backups:" -ForegroundColor Yellow
    Write-Host ""
    
    $backups = Get-ChildItem "$backupDir\backup_*.sql*" | 
        Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "✗ No backups found in $backupDir" -ForegroundColor Red
        Write-Host ""
        Write-Host "Create a backup first using:" -ForegroundColor Yellow
        Write-Host "  .\backup_database.ps1" -ForegroundColor White
        exit 1
    }
    
    $index = 1
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
        
        Write-Host "  [$index] $($backup.Name)" -ForegroundColor White
        Write-Host "      Size: $size MB, Created: $ageStr" -ForegroundColor Gray
        Write-Host ""
        
        $index++
    }
    
    Write-Host "Select backup to restore:" -ForegroundColor Yellow
    $selection = Read-Host "Enter number (1-$($backups.Count)) or 'q' to quit"
    
    if ($selection -eq 'q') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    $selectedIndex = [int]$selection - 1
    if ($selectedIndex -lt 0 -or $selectedIndex -ge $backups.Count) {
        Write-Host "✗ Invalid selection!" -ForegroundColor Red
        exit 1
    }
    
    $BackupFile = $backups[$selectedIndex].FullName
}

# Перевірити чи файл існує
if (!(Test-Path $BackupFile)) {
    Write-Host "✗ Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

# Якщо це zip - розпакувати
$tempFile = $null
if ($BackupFile -match "\.zip$") {
    Write-Host "Extracting compressed backup..." -ForegroundColor Yellow
    $tempFile = "$env:TEMP\restore_temp_$(Get-Date -Format 'yyyyMMddHHmmss').sql"
    Expand-Archive -Path $BackupFile -DestinationPath $env:TEMP -Force
    
    $extractedFile = Get-ChildItem "$env:TEMP\backup_*.sql" | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -First 1
    
    if ($extractedFile) {
        Move-Item $extractedFile.FullName $tempFile -Force
        $BackupFile = $tempFile
        Write-Host "✓ Backup extracted" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to extract backup" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Restore Information:" -ForegroundColor Yellow
Write-Host "  Database: $dbName" -ForegroundColor White
Write-Host "  Host: $dbHost" -ForegroundColor White
Write-Host "  Backup: $(Split-Path $BackupFile -Leaf)" -ForegroundColor White
Write-Host ""

# ПОПЕРЕДЖЕННЯ
Write-Host "⚠️  WARNING!" -ForegroundColor Red
Write-Host "This will OVERWRITE all current data in the database!" -ForegroundColor Red
Write-Host ""
Write-Host "Current database will be replaced with backup data." -ForegroundColor Yellow
Write-Host ""

# Показати статистику поточної БД
Write-Host "Current database statistics:" -ForegroundColor Cyan
try {
    $stats = mysql -u $dbUser -p$dbPass -h $dbHost -P $dbPort -D $dbName -e "
        SELECT 'users' as tbl, COUNT(*) as cnt FROM users
        UNION ALL SELECT 'employees', COUNT(*) FROM employees
        UNION ALL SELECT 'terminals', COUNT(*) FROM terminals
        UNION ALL SELECT 'events', COUNT(*) FROM events
        UNION ALL SELECT 'schedules', COUNT(*) FROM schedules
    " 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host $stats -ForegroundColor White
    }
} catch {
    Write-Host "  (Unable to retrieve statistics)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Do you want to continue?" -ForegroundColor Yellow
$confirm = Read-Host "Type 'yes' to proceed"

if ($confirm -ne 'yes') {
    Write-Host "✗ Restore cancelled." -ForegroundColor Yellow
    if ($tempFile) { Remove-Item $tempFile -Force }
    exit 0
}

Write-Host ""

# Створити backup поточної БД перед restore
Write-Host "Creating safety backup of current database..." -ForegroundColor Yellow
$safetyBackup = "$backupDir\before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"

try {
    mysqldump -u $dbUser -p$dbPass -h $dbHost -P $dbPort $dbName > $safetyBackup 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Safety backup created: $(Split-Path $safetyBackup -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Warning: Could not create safety backup" -ForegroundColor Yellow
        $proceed = Read-Host "Continue anyway? (yes/no)"
        if ($proceed -ne 'yes') {
            if ($tempFile) { Remove-Item $tempFile -Force }
            exit 1
        }
    }
} catch {
    Write-Host "⚠️  Warning: Error creating safety backup" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""

# Виконати restore
Write-Host "Restoring database..." -ForegroundColor Yellow
$startTime = Get-Date

try {
    # Відновити з backup файлу
    $restoreCmd = "mysql -u $dbUser -p$dbPass -h $dbHost -P $dbPort $dbName"
    Get-Content $BackupFile | Invoke-Expression -Command $restoreCmd 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Restore failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Your database was not modified." -ForegroundColor Yellow
        Write-Host "Safety backup is available at:" -ForegroundColor Yellow
        Write-Host "  $safetyBackup" -ForegroundColor White
        
        if ($tempFile) { Remove-Item $tempFile -Force }
        exit 1
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "✓ Database restored successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Duration: $([math]::Round($duration.TotalSeconds, 2)) seconds" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "✗ Error during restore!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Safety backup is available at:" -ForegroundColor Yellow
    Write-Host "  $safetyBackup" -ForegroundColor White
    
    if ($tempFile) { Remove-Item $tempFile -Force }
    exit 1
}

# Перевірити відновлену БД
Write-Host "Verifying restored database..." -ForegroundColor Yellow
try {
    $stats = mysql -u $dbUser -p$dbPass -h $dbHost -P $dbPort -D $dbName -e "
        SELECT 'users' as tbl, COUNT(*) as cnt FROM users
        UNION ALL SELECT 'employees', COUNT(*) FROM employees
        UNION ALL SELECT 'terminals', COUNT(*) FROM terminals
        UNION ALL SELECT 'events', COUNT(*) FROM events
        UNION ALL SELECT 'schedules', COUNT(*) FROM schedules
    " 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database verification successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Restored database statistics:" -ForegroundColor Cyan
        Write-Host $stats -ForegroundColor White
    } else {
        Write-Host "⚠️  Warning: Could not verify database" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Warning: Verification failed" -ForegroundColor Yellow
}

# Очистити тимчасові файли
if ($tempFile -and (Test-Path $tempFile)) {
    Remove-Item $tempFile -Force
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Restore completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Important notes:" -ForegroundColor Yellow
Write-Host "  ✓ Database has been restored from backup" -ForegroundColor White
Write-Host "  ✓ Safety backup saved: $(Split-Path $safetyBackup -Leaf)" -ForegroundColor White
Write-Host "  ✓ You may need to restart your application" -ForegroundColor White
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart the FastAPI server if it's running" -ForegroundColor White
Write-Host "  2. Test the application functionality" -ForegroundColor White
Write-Host "  3. If everything works, you can delete the safety backup" -ForegroundColor White
Write-Host ""
