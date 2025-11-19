#!/bin/bash

# Chatbot Safety Testbed Platform - Setup Script

echo "=========================================="
echo "Chatbot Safety Testbed Platform"
echo "Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"

# Check Node.js version
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "   Please install Node.js 16 or higher"
    exit 1
fi

node_version=$(node --version | grep -oP '\d+\.\d+' | head -1)
required_node="16.0"

if [ "$(printf '%s\n' "$required_node" "$node_version" | sort -V | head -n1)" != "$required_node" ]; then
    echo "❌ Error: Node.js 16 or higher is required"
    echo "   Current version: $node_version"
    exit 1
fi
echo "✓ Node.js $node_version detected"

# Setup Backend
echo ""
echo "=========================================="
echo "Setting up Backend..."
echo "=========================================="

cd backend || exit

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✓ Python dependencies installed"

echo "Installing Playwright browsers..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Playwright browsers"
    exit 1
fi
echo "✓ Playwright browsers installed"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your API key!"
    echo "   For Anthropic: Set ANTHROPIC_API_KEY=your-key-here"
    echo "   For OpenAI: Set OPENAI_API_KEY=your-key-here"
    echo ""
else
    echo "✓ .env file already exists"
fi

cd ..

# Setup Frontend
echo ""
echo "=========================================="
echo "Setting up Frontend..."
echo "=========================================="

cd frontend || exit

echo "Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
echo "✓ Node.js dependencies installed"

cd ..

# Done
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your API key in backend/.env"
echo ""
echo "2. Start the backend server:"
echo "   cd backend"
echo "   python3 main.py"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "For more information, see QUICKSTART.md"
echo ""
