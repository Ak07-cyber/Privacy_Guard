# PassiveGuard Standalone Executable

Build a **single executable file** that bundles everything needed to run PassiveGuard:
- ✅ FastAPI backend server
- ✅ XGBoost ML model (bot_detector.joblib)
- ✅ Demo HTML frontend
- ✅ All Python dependencies
- ✅ Auto-opens browser on launch

## 📦 What You Get

| Platform | Output | Size |
|----------|--------|------|
| **Windows** | `PassiveGuard.exe` | ~80-100 MB |
| **macOS** | `PassiveGuard.app` | ~80-100 MB |
| **Linux** | `PassiveGuard` | ~80-100 MB |

## 🚀 Quick Build

### macOS / Linux

```bash
cd standalone
chmod +x build.sh
./build.sh
```

### Windows

```cmd
cd standalone
build.bat
```

## 📋 Prerequisites

1. **Python 3.10+** installed and in PATH
2. **pip** package manager
3. **ML Model trained** (will auto-train if missing)

## 🔨 Build Options

```bash
# Standard build
./build.sh

# Clean build (removes previous builds)
./build.sh --clean

# Build and test
./build.sh --test
```

## 📁 Output Location

After successful build:

```
standalone/
├── dist/
│   ├── PassiveGuard          # Linux executable
│   ├── PassiveGuard.exe      # Windows executable
│   └── PassiveGuard.app/     # macOS app bundle
└── build/                     # Intermediate build files (can delete)
```

## 🎯 Running the Executable

### Windows
```
Double-click PassiveGuard.exe
```

### macOS
```bash
open dist/PassiveGuard.app
# or double-click PassiveGuard.app in Finder
```

### Linux
```bash
./dist/PassiveGuard
```

## ✨ What Happens When You Run It

1. 🚀 Server starts on `http://127.0.0.1:8000`
2. 🌐 Browser automatically opens demo page
3. 🛡️ PassiveGuard is ready for bot detection!

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🛡️  PassiveGuard v1.0.0                                        ║
║   ML-Based Passive Bot Detection                                  ║
║                                                                   ║
║   Server: http://127.0.0.1:8000                                   ║
║   Demo:   http://127.0.0.1:8000/demo                              ║
║   API:    http://127.0.0.1:8000/docs                              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## 🔧 Customization

### Change Default Port

Edit `standalone/passiveguard_app.py`:
```python
class Settings:
    PORT = 8000  # Change this
```

### Disable Auto-Open Browser

Edit `standalone/passiveguard_app.py`:
```python
def main():
    # Comment out these lines:
    # browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    # browser_thread.start()
```

### Add Custom Icon

1. Place icon file in `standalone/`:
   - Windows: `icon.ico`
   - macOS: `icon.icns`
   
2. Update `passiveguard.spec`:
```python
icon_file = 'icon.ico'  # or 'icon.icns' for macOS
```

## ❓ Troubleshooting

### "Python not found"
- Install Python 3.10+ from https://python.org
- Make sure Python is added to PATH

### "Model not found"
```bash
cd ../backend
python -m ml_training.train_model
```

### Build fails with missing module
```bash
pip install <module_name>
# Then rebuild
./build.sh --clean
```

### Antivirus blocks the executable
- PyInstaller executables may trigger false positives
- Add exception for the executable or sign it with a code signing certificate

### Port already in use
- PassiveGuard automatically finds an available port
- Or manually kill the process using port 8000

## 📊 Size Optimization

To reduce executable size:

1. **Use UPX compression** (already enabled in spec):
   ```bash
   brew install upx  # macOS
   apt install upx   # Linux
   ```

2. **Exclude unused modules** (edit spec file):
   ```python
   excludes=[
       'tkinter',
       'matplotlib', 
       'PIL',
       # Add more...
   ]
   ```

## 🔐 Code Signing (Optional)

### Windows
```bash
signtool sign /f certificate.pfx /p password PassiveGuard.exe
```

### macOS
```bash
codesign --sign "Developer ID" PassiveGuard.app
```

## 📄 Files in This Directory

| File | Description |
|------|-------------|
| `passiveguard_app.py` | Main application (FastAPI + ML + UI) |
| `passiveguard.spec` | PyInstaller build configuration |
| `build.sh` | Build script for macOS/Linux |
| `build.bat` | Build script for Windows |
| `requirements.txt` | Python dependencies for building |
| `README.md` | This file |

---

**Built with ❤️ using PyInstaller**
