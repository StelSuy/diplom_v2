# ====================================
# Database Setup Script
# ====================================
# Створює базу даних та користувача для TimeTracker API

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TimeTracker API - Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Читання конфігурації з .env
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -match "DATABASE_URL=mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^\?]+)") {
        $dbUser = $matches[1]
        $dbPass = $matches[2]
        $dbHost = $matches[3]
        $dbPort = $matches[4]
        $dbName = $matches[5]
        
        Write-Host "Configuration from .env:" -ForegroundColor Yellow
        Write-Host "  Database: $dbName" -ForegroundColor White
        Write-Host "  User: $dbUser" -ForegroundColor White
        Write-Host "  Host: $dbHost" -ForegroundColor White
        Write-Host "  Port: $dbPort" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "✗ Cannot parse DATABASE_URL from .env" -ForegroundColor Red
        Write-Host "Please check your .env file" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Copy .env.example to .env first" -ForegroundColor Yellow
    exit 1
}

# Запит root пароля
Write-Host "Enter MySQL root password:" -ForegroundColor Yellow
$rootPassword = Read-Host -AsSecureString
$rootPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($rootPassword)
)

Write-Host ""
Write-Host "Creating database and user..." -ForegroundColor Yellow
Write-Host ""

# SQL команди
$sqlCommands = @"
-- Create database
CREATE DATABASE IF NOT EXISTS $dbName 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Create user (if not exists)
CREATE USER IF NOT EXISTS '$dbUser'@'localhost' 
IDENTIFIED BY '$dbPass';

-- Grant privileges
GRANT ALL PRIVILEGES ON ${dbName}.* TO '$dbUser'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Show databases
SHOW DATABASES LIKE '$dbName';

-- Show user grants
SHOW GRANTS FOR '$dbUser'@'localhost';
"@

# Виконання SQL команд
try {
    $sqlCommands | mysql -u root -p$rootPasswordPlain -h $dbHost -P $dbPort 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Details:" -ForegroundColor Cyan
        Write-Host "  Database: $dbName" -ForegroundColor White
        Write-Host "  User: $dbUser" -ForegroundColor White
        Write-Host "  Charset: utf8mb4" -ForegroundColor White
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Run: alembic upgrade head" -ForegroundColor White
        Write-Host "  2. Run: uvicorn app.main:app --reload" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "✗ Error creating database" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Error executing SQL commands" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Тестування підключення
Write-Host "Testing connection with new user..." -ForegroundColor Yellow
try {
    $testResult = mysql -u $dbUser -p$dbPass -h $dbHost -P $dbPort -e "SELECT 1" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Connection test successful!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "✗ Connection test failed" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Cannot test connection" -ForegroundColor Red
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
