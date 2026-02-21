# Setup script for Windows PowerShell
$RequiredVersion = "3.12"
$VenvDir = ".venv"

Write-Host "🚀 Starting setup for Windows..." -ForegroundColor Cyan

# 1. Find the best Python executable
$PythonCmd = ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "🔍 Using Python Launcher (py)..."
    $PythonCmd = "py -$RequiredVersion"
} elseif (Get-Command pyenv -ErrorAction SilentlyContinue) {
    Write-Host "🔍 Using pyenv-win..."
    pyenv install -s $RequiredVersion
    $PythonCmd = "python"
} elseif (Get-Command python3.12 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3.12"
} else {
    Write-Host "❌ Python $RequiredVersion not found." -ForegroundColor Red
    Write-Host "Please install it from python.org or use 'pyenv-win install $RequiredVersion'"
    exit
}

# 2. Create virtual environment
if (-not (Test-Path -Path $VenvDir)) {
    Write-Host "📦 Creating virtual environment in $VenvDir..." -ForegroundColor Yellow
    Invoke-Expression "$PythonCmd -m venv $VenvDir"
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

# 3. Activate and Install
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& ".\$VenvDir\Scripts\Activate.ps1"

Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

if (Test-Path -Path "requirements.txt") {
    Write-Host "📥 Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    Write-Host "⚠️ requirements.txt not found!" -ForegroundColor Red
}

Write-Host "✨ Setup complete! To activate, run: .\$VenvDir\Scripts\Activate.ps1" -ForegroundColor Green
