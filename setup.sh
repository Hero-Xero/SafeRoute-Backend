#!/bin/bash

# Exit on error
set -e

REQUIRED_VERSION="3.12.12"
VENV_DIR=".venv"

echo "🚀 Starting setup for Linux..."

# 1. Try to find the correct Python version
if command -v pyenv &> /dev/null; then
    echo "🔍 Using pyenv to ensure Python $REQUIRED_VERSION is available..."
    pyenv install -s $REQUIRED_VERSION
    PYTHON_CMD=$(pyenv which python)
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
else
    echo "❌ Python 3.12 is not installed."
    echo "Please install it using your package manager or pyenv."
    exit 1
fi

echo "✅ Using Python: $($PYTHON_CMD --version)"

# 2. Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv $VENV_DIR
else
    echo "✅ Virtual environment already exists."
fi

# 3. Activate and Install
echo "🔌 Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "📥 Installing requirements..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
fi

echo "✨ Setup complete! your welcome"
