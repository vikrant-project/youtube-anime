#!/bin/bash
# Setup script for Anime Automation System

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎬 ANIME AUTOMATION SYSTEM SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Some commands require sudo. You may be prompted for password."
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✅ Detected: Linux"
    PKG_MANAGER="apt"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ Detected: macOS"
    PKG_MANAGER="brew"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo ""
echo "📦 Installing system dependencies..."

# Install FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    if [ "$PKG_MANAGER" == "apt" ]; then
        sudo apt update
        sudo apt install -y ffmpeg
    else
        brew install ffmpeg
    fi
else
    echo "✅ FFmpeg already installed"
fi

# Install Python3 and pip
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    if [ "$PKG_MANAGER" == "apt" ]; then
        sudo apt install -y python3 python3-pip
    else
        brew install python3
    fi
else
    echo "✅ Python3 already installed"
fi

# Install ani-cli
if ! command -v ani-cli &> /dev/null; then
    echo "Installing ani-cli..."
    sudo curl -sL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli \
        -o /usr/local/bin/ani-cli && sudo chmod +x /usr/local/bin/ani-cli
    echo "✅ ani-cli installed"
else
    echo "✅ ani-cli already installed"
fi

# Install yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp..."
    sudo curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
        -o /usr/local/bin/yt-dlp && sudo chmod +x /usr/local/bin/yt-dlp
    echo "✅ yt-dlp installed"
else
    echo "✅ yt-dlp already installed"
fi

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p ~/anime_downloads
mkdir -p processed_videos
mkdir -p thumbnails

# Check .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file with your API keys."
    echo "Use .env as a template."
else
    echo "✅ .env file found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Configure .env with your API keys"
echo "2. Start anime API: python3 anime_api.py"
echo "3. Test system: python3 main.py --mode test"
echo "4. Start auto mode: python3 main.py --mode auto"
echo ""
echo "For help, see README.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
