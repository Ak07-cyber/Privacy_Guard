#!/bin/bash
#===============================================================================
#                    PassiveGuard EXE Build Script
#===============================================================================
# This script builds a single executable file that contains:
# - FastAPI backend server
# - XGBoost ML model
# - Demo HTML frontend
# - All Python dependencies
#
# Usage:
#   ./build.sh           # Build for current platform
#   ./build.sh --clean   # Clean build (remove previous builds)
#   ./build.sh --test    # Build and test the executable
#===============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
STANDALONE_DIR="$SCRIPT_DIR"
BUILD_DIR="$STANDALONE_DIR/build"
DIST_DIR="$STANDALONE_DIR/dist"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║   🛡️  PassiveGuard - Build Executable                            ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
CLEAN=false
TEST=false
for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN=true
            ;;
        --test)
            TEST=true
            ;;
    esac
done

# Clean previous builds if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
    rm -rf "$BUILD_DIR" "$DIST_DIR"
    echo -e "${GREEN}✅ Cleaned!${NC}"
fi

# Check Python
echo -e "${BLUE}📋 Checking requirements...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "   Python: ${GREEN}$PYTHON_VERSION${NC}"

# Create or activate virtual environment
VENV_DIR="$STANDALONE_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install dependencies
echo -e "${BLUE}📥 Installing build dependencies...${NC}"
pip install --upgrade pip --quiet
pip install -r "$STANDALONE_DIR/requirements.txt" --quiet

# Check if ML model exists
if [ ! -f "$BACKEND_DIR/models/bot_detector.joblib" ]; then
    echo -e "${YELLOW}🤖 Training ML model (this may take a moment)...${NC}"
    cd "$BACKEND_DIR"
    pip install -r requirements.txt --quiet
    python -m ml_training.train_model
    cd "$STANDALONE_DIR"
fi

# Verify model exists
if [ ! -f "$BACKEND_DIR/models/bot_detector.joblib" ]; then
    echo -e "${RED}❌ ML model not found! Please run training first.${NC}"
    exit 1
fi
echo -e "   Model: ${GREEN}Found ✓${NC}"

# Verify demo HTML exists
if [ ! -f "$PROJECT_ROOT/demo/index.html" ]; then
    echo -e "${RED}❌ Demo HTML not found!${NC}"
    exit 1
fi
echo -e "   Demo HTML: ${GREEN}Found ✓${NC}"

# Build with PyInstaller
echo -e "${BLUE}🔨 Building executable with PyInstaller...${NC}"
echo -e "   This may take several minutes..."
echo ""

cd "$STANDALONE_DIR"
pyinstaller passiveguard.spec \
    --noconfirm \
    --clean \
    --log-level WARN

# Check if build succeeded
if [ -d "$DIST_DIR" ]; then
    # Find the executable
    if [ "$(uname)" == "Darwin" ]; then
        EXE_PATH="$DIST_DIR/PassiveGuard.app"
        if [ ! -d "$EXE_PATH" ]; then
            EXE_PATH="$DIST_DIR/PassiveGuard"
        fi
    elif [ "$(uname)" == "Linux" ]; then
        EXE_PATH="$DIST_DIR/PassiveGuard"
    else
        EXE_PATH="$DIST_DIR/PassiveGuard.exe"
    fi
    
    if [ -e "$EXE_PATH" ]; then
        # Get file size
        if [ -d "$EXE_PATH" ]; then
            SIZE=$(du -sh "$EXE_PATH" | cut -f1)
        else
            SIZE=$(du -h "$EXE_PATH" | cut -f1)
        fi
        
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                                   ║${NC}"
        echo -e "${GREEN}║   ✅ BUILD SUCCESSFUL!                                           ║${NC}"
        echo -e "${GREEN}║                                                                   ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "   📁 Output: ${BLUE}$EXE_PATH${NC}"
        echo -e "   📦 Size:   ${YELLOW}$SIZE${NC}"
        echo ""
        
        # Test if requested
        if [ "$TEST" = true ]; then
            echo -e "${BLUE}🧪 Testing executable...${NC}"
            if [ -d "$EXE_PATH" ]; then
                open "$EXE_PATH"
            else
                "$EXE_PATH" &
                sleep 3
                curl -s http://127.0.0.1:8000/api/v1/health | python3 -m json.tool
                kill %1 2>/dev/null || true
            fi
        fi
        
        echo -e "${GREEN}🎉 Done! You can now distribute the executable.${NC}"
        echo ""
        echo "To run PassiveGuard:"
        if [ "$(uname)" == "Darwin" ]; then
            echo "   open $DIST_DIR/PassiveGuard.app"
            echo "   # or double-click PassiveGuard.app in Finder"
        else
            echo "   $EXE_PATH"
        fi
    else
        echo -e "${RED}❌ Build failed - executable not found${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Build failed - dist directory not created${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate
