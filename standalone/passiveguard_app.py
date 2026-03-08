#!/usr/bin/env python3
"""
PassiveGuard Standalone Application
===================================
Single executable that bundles:
- FastAPI backend server
- React/HTML demo frontend
- XGBoost ML model
- Auto-opens browser

Build with: pyinstaller passiveguard.spec
"""

import os
import sys
import json
import signal
import socket
import hashlib
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Determine if running as frozen exe or script
if getattr(sys, 'frozen', False):
    # Running as compiled exe - files are bundled inside
    BASE_DIR = Path(sys._MEIPASS)
    IS_FROZEN = True
else:
    # Running as script - look for files in project structure
    BASE_DIR = Path(__file__).parent.parent / "backend"
    IS_FROZEN = False

# ============================================================================
# CONFIGURATION
# ============================================================================

class Settings:
    PROJECT_NAME = "PassiveGuard"
    VERSION = "1.0.0"
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = not IS_FROZEN
    SECRET_KEY = "passiveguard-standalone-secret-key-2024"
    CONFIDENCE_THRESHOLD = 0.7
    
    # Paths - for frozen exe, files are in BASE_DIR/models and BASE_DIR/static
    # For script, files are in backend/models and demo/
    if IS_FROZEN:
        STATIC_DIR = BASE_DIR / "static"
        MODEL_PATH = BASE_DIR / "models" / "bot_detector.joblib"
        FEATURE_IMPORTANCE_PATH = BASE_DIR / "models" / "feature_importance.json"
    else:
        STATIC_DIR = Path(__file__).parent.parent / "demo"
        MODEL_PATH = BASE_DIR / "models" / "bot_detector.joblib"
        FEATURE_IMPORTANCE_PATH = BASE_DIR / "models" / "feature_importance.json"

settings = Settings()

# ============================================================================
# ML MODEL LOADER
# ============================================================================

class BotDetector:
    """XGBoost-based bot detection with ML model"""
    
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.feature_importance = {}
        self._load_model()
    
    def _load_model(self):
        """Load the trained XGBoost model"""
        try:
            import joblib
            if settings.MODEL_PATH.exists():
                self.model = joblib.load(settings.MODEL_PATH)
                print(f"✅ ML Model loaded from {settings.MODEL_PATH}")
            else:
                print(f"⚠️ Model not found at {settings.MODEL_PATH}, using rule-based detection")
            
            if settings.FEATURE_IMPORTANCE_PATH.exists():
                with open(settings.FEATURE_IMPORTANCE_PATH) as f:
                    self.feature_importance = json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            self.model = None
    
    def extract_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract 56 features from request data"""
        features = []
        
        env = data.get("environmental_data", {})
        beh = data.get("behavioral_data", {})
        tim = data.get("timing_data", {})
        
        # Environmental features (20)
        features.append(env.get("hardware_concurrency", 4))
        features.append(env.get("device_memory", 8))
        features.append(self._parse_resolution(env.get("screen_resolution", "1920x1080")))
        features.append(env.get("color_depth", 24))
        features.append(env.get("pixel_ratio", 1.0))
        features.append(env.get("timezone_offset", 0))
        features.append(len(env.get("plugins", [])))
        features.append(1 if env.get("touch_support", False) else 0)
        features.append(env.get("max_touch_points", 0))
        features.append(1 if env.get("cookie_enabled", True) else 0)
        features.append(1 if env.get("do_not_track", False) else 0)
        features.append(len(env.get("languages", ["en"])))
        features.append(self._hash_to_float(env.get("canvas_fingerprint", "")))
        features.append(self._hash_to_float(env.get("webgl_vendor", "")))
        features.append(self._hash_to_float(env.get("webgl_renderer", "")))
        features.append(self._hash_to_float(env.get("audio_fingerprint", "")))
        features.append(self._hash_to_float(env.get("user_agent", "")))
        features.append(self._hash_to_float(env.get("platform", "")))
        features.append(env.get("screen_width", 1920))
        features.append(env.get("screen_height", 1080))
        
        # Behavioral features (26)
        features.append(beh.get("mouse_movements", 0))
        features.append(beh.get("mouse_velocity_avg", 0))
        features.append(beh.get("mouse_velocity_std", 0))
        features.append(beh.get("mouse_acceleration_avg", 0))
        features.append(beh.get("mouse_acceleration_std", 0))
        features.append(beh.get("mouse_direction_changes", 0))
        features.append(beh.get("mouse_pause_count", 0))
        features.append(beh.get("mouse_distance_total", 0))
        features.append(beh.get("mouse_straightness", 0))
        features.append(beh.get("scroll_events", 0))
        features.append(beh.get("scroll_velocity_avg", 0))
        features.append(beh.get("scroll_velocity_std", 0))
        features.append(beh.get("scroll_direction_changes", 0))
        features.append(beh.get("scroll_smoothness", 0))
        features.append(beh.get("keystroke_count", 0))
        features.append(beh.get("keystroke_timing_avg", 0))
        features.append(beh.get("keystroke_timing_std", 0))
        features.append(beh.get("keyhold_duration_avg", 0))
        features.append(beh.get("keyhold_duration_std", 0))
        features.append(beh.get("click_count", 0))
        features.append(beh.get("click_interval_avg", 0))
        features.append(beh.get("click_interval_std", 0))
        features.append(beh.get("double_click_count", 0))
        features.append(beh.get("right_click_count", 0))
        features.append(beh.get("focus_blur_count", 0))
        features.append(beh.get("visibility_changes", 0))
        
        # Timing features (10)
        features.append(tim.get("page_load_time", 0))
        features.append(tim.get("dom_ready_time", 0))
        features.append(tim.get("time_to_first_interaction", 0))
        features.append(tim.get("session_duration", 0))
        features.append(tim.get("interaction_density", 0))
        features.append(tim.get("idle_time_total", 0))
        features.append(tim.get("idle_time_avg", 0))
        features.append(tim.get("active_time_ratio", 0))
        features.append(tim.get("event_timing_consistency", 0))
        features.append(tim.get("response_time_avg", 0))
        
        return features
    
    def _parse_resolution(self, res: str) -> float:
        """Parse resolution string to total pixels"""
        try:
            w, h = res.lower().split('x')
            return float(int(w) * int(h))
        except:
            return 2073600.0  # 1920x1080
    
    def _hash_to_float(self, s: str) -> float:
        """Convert string to consistent float via hash"""
        if not s:
            return 0.0
        hash_val = hashlib.md5(s.encode()).hexdigest()[:8]
        return int(hash_val, 16) / 0xFFFFFFFF
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run bot detection prediction"""
        features = self.extract_features(data)
        
        if self.model is not None:
            try:
                import numpy as np
                X = np.array([features])
                prob = self.model.predict_proba(X)[0]
                is_human = bool(prob[1] > settings.CONFIDENCE_THRESHOLD)
                confidence = float(prob[1])
                risk_score = float(prob[0])
            except Exception as e:
                print(f"ML prediction error: {e}")
                is_human, confidence, risk_score = self._rule_based_detection(data)
        else:
            is_human, confidence, risk_score = self._rule_based_detection(data)
        
        return {
            "is_human": is_human,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 4),
            "model_type": "xgboost" if self.model else "rule_based"
        }
    
    def _rule_based_detection(self, data: Dict[str, Any]) -> tuple:
        """Fallback rule-based bot detection"""
        beh = data.get("behavioral_data", {})
        tim = data.get("timing_data", {})
        
        score = 0.5
        
        # Behavioral signals
        if beh.get("mouse_movements", 0) > 10:
            score += 0.15
        if beh.get("mouse_direction_changes", 0) > 5:
            score += 0.1
        if beh.get("scroll_smoothness", 0) > 0.5:
            score += 0.1
        if beh.get("keystroke_count", 0) > 0:
            score += 0.05
        
        # Timing signals
        if tim.get("time_to_first_interaction", 0) > 500:
            score += 0.05
        if tim.get("session_duration", 0) > 3000:
            score += 0.05
        
        score = min(max(score, 0), 1)
        is_human = score > settings.CONFIDENCE_THRESHOLD
        
        return is_human, score, 1 - score

# Global detector instance
detector = BotDetector()

# ============================================================================
# JWT TOKEN HANDLING
# ============================================================================

def create_token(data: Dict[str, Any]) -> str:
    """Create a simple JWT-like token"""
    import base64
    payload = {
        **data,
        "iat": datetime.utcnow().isoformat(),
        "exp": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    token_data = json.dumps(payload)
    encoded = base64.urlsafe_b64encode(token_data.encode()).decode()
    signature = hashlib.sha256(f"{encoded}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
    return f"{encoded}.{signature}"

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode token"""
    import base64
    try:
        encoded, signature = token.rsplit('.', 1)
        expected_sig = hashlib.sha256(f"{encoded}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return None
        
        payload = json.loads(base64.urlsafe_b64decode(encoded).decode())
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.utcnow() > exp:
            return None
        
        return payload
    except:
        return None

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

class VerifyRequest(BaseModel):
    site_key: str = "default"
    environmental_data: Dict[str, Any] = {}
    behavioral_data: Dict[str, Any] = {}
    timing_data: Dict[str, Any] = {}

class ValidateRequest(BaseModel):
    token: str
    secret: str = ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🛡️  PassiveGuard v{settings.VERSION}                               ║
║   ML-Based Passive Bot Detection                                  ║
║                                                                   ║
║   Server: http://{settings.HOST}:{settings.PORT}                         ║
║   Demo:   http://{settings.HOST}:{settings.PORT}/demo                    ║
║   API:    http://{settings.HOST}:{settings.PORT}/docs                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    yield
    print("\n👋 PassiveGuard shutting down...")

app = FastAPI(
    title="PassiveGuard",
    description="ML-Based Passive Bot Detection - CAPTCHA Replacement",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to demo page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/demo">
        <title>PassiveGuard</title>
    </head>
    <body>
        <p>Redirecting to <a href="/demo">PassiveGuard Demo</a>...</p>
    </body>
    </html>
    """

@app.get("/demo", response_class=HTMLResponse)
async def demo():
    """Serve demo page"""
    demo_path = settings.STATIC_DIR / "index.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    else:
        return HTMLResponse(get_embedded_demo_html())

@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "model_loaded": detector.model is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/verify")
async def verify(request: VerifyRequest):
    """Main bot detection endpoint"""
    data = {
        "site_key": request.site_key,
        "environmental_data": request.environmental_data,
        "behavioral_data": request.behavioral_data,
        "timing_data": request.timing_data
    }
    
    result = detector.predict(data)
    
    # Generate token
    token = create_token({
        "is_human": result["is_human"],
        "confidence": result["confidence"],
        "site_key": request.site_key
    })
    
    return {
        **result,
        "token": token,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/validate-token")
async def validate_token(request: ValidateRequest):
    """Validate a verification token"""
    payload = verify_token(request.token)
    
    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "is_human": payload.get("is_human", False),
        "confidence": payload.get("confidence", 0),
        "site_key": payload.get("site_key", ""),
        "issued_at": payload.get("iat")
    }

@app.get("/api/v1/stats")
async def stats():
    """Get model statistics"""
    return {
        "model_type": "xgboost" if detector.model else "rule_based",
        "feature_count": 56,
        "feature_importance": detector.feature_importance,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD
    }

# ============================================================================
# EMBEDDED DEMO HTML (Fallback)
# ============================================================================

def get_embedded_demo_html():
    """Return embedded demo HTML if static file not found"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PassiveGuard Demo</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; border-radius: 20px; padding: 40px; max-width: 500px; 
                     width: 90%; box-shadow: 0 25px 50px rgba(0,0,0,0.2); }
        h1 { color: #4f46e5; margin-bottom: 10px; font-size: 28px; }
        p { color: #6b7280; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #374151; font-weight: 500; margin-bottom: 8px; }
        input { width: 100%; padding: 12px 16px; border: 2px solid #e5e7eb; border-radius: 10px; 
                font-size: 16px; transition: border-color 0.2s; }
        input:focus { outline: none; border-color: #4f46e5; }
        button { width: 100%; padding: 14px; background: #4f46e5; color: white; border: none; 
                 border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; 
                 transition: background 0.2s; }
        button:hover { background: #4338ca; }
        button:disabled { background: #9ca3af; cursor: not-allowed; }
        .result { margin-top: 20px; padding: 20px; border-radius: 10px; display: none; }
        .result.success { background: #d1fae5; border: 2px solid #10b981; }
        .result.danger { background: #fee2e2; border: 2px solid #ef4444; }
        .result h3 { margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
        .stat { background: rgba(255,255,255,0.5); padding: 10px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #4f46e5; }
        .stat-label { font-size: 12px; color: #6b7280; }
        #status { text-align: center; padding: 10px; margin-bottom: 20px; border-radius: 8px; 
                  background: #fef3c7; color: #92400e; font-size: 14px; }
        #status.ready { background: #d1fae5; color: #065f46; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ PassiveGuard Demo</h1>
        <p>ML-powered bot detection without CAPTCHAs</p>
        
        <div id="status">Initializing...</div>
        
        <form id="demoForm">
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="email" placeholder="your@email.com" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" placeholder="••••••••" required>
            </div>
            <button type="submit" id="submitBtn">Verify & Submit</button>
        </form>
        
        <div id="result" class="result">
            <h3 id="resultTitle"></h3>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="confidence">-</div>
                    <div class="stat-label">Confidence</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="riskScore">-</div>
                    <div class="stat-label">Risk Score</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Behavioral data collection
        const behavioralData = {
            mouse_movements: 0,
            mouse_velocity_avg: 0,
            mouse_direction_changes: 0,
            scroll_events: 0,
            scroll_smoothness: 0,
            keystroke_count: 0,
            click_count: 0
        };
        
        let lastMouseX = 0, lastMouseY = 0, lastMouseTime = 0;
        let velocities = [];
        let lastScrollTime = 0;
        const startTime = Date.now();
        
        // Mouse tracking
        document.addEventListener('mousemove', (e) => {
            const now = Date.now();
            if (lastMouseTime > 0) {
                const dx = e.clientX - lastMouseX;
                const dy = e.clientY - lastMouseY;
                const dt = now - lastMouseTime;
                if (dt > 0) {
                    const velocity = Math.sqrt(dx*dx + dy*dy) / dt;
                    velocities.push(velocity);
                    if (velocities.length > 100) velocities.shift();
                    behavioralData.mouse_velocity_avg = velocities.reduce((a,b) => a+b, 0) / velocities.length;
                }
                if (Math.abs(dx) > 5 && Math.abs(dy) > 5) {
                    behavioralData.mouse_direction_changes++;
                }
            }
            behavioralData.mouse_movements++;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
            lastMouseTime = now;
        });
        
        // Scroll tracking
        document.addEventListener('scroll', () => {
            behavioralData.scroll_events++;
            const now = Date.now();
            if (lastScrollTime > 0) {
                const dt = now - lastScrollTime;
                behavioralData.scroll_smoothness = Math.min(1, dt / 100);
            }
            lastScrollTime = now;
        });
        
        // Keystroke tracking
        document.addEventListener('keydown', () => {
            behavioralData.keystroke_count++;
        });
        
        // Click tracking
        document.addEventListener('click', () => {
            behavioralData.click_count++;
        });
        
        // Update status
        setTimeout(() => {
            document.getElementById('status').textContent = '✅ PassiveGuard Active - Collecting behavioral data...';
            document.getElementById('status').classList.add('ready');
        }, 1000);
        
        // Form submission
        document.getElementById('demoForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.textContent = 'Verifying...';
            
            try {
                const response = await fetch('/api/v1/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        site_key: 'demo',
                        environmental_data: {
                            screen_resolution: `${screen.width}x${screen.height}`,
                            user_agent: navigator.userAgent,
                            language: navigator.language,
                            platform: navigator.platform,
                            hardware_concurrency: navigator.hardwareConcurrency || 4,
                            device_memory: navigator.deviceMemory || 8,
                            timezone_offset: new Date().getTimezoneOffset(),
                            cookie_enabled: navigator.cookieEnabled,
                            touch_support: 'ontouchstart' in window
                        },
                        behavioral_data: behavioralData,
                        timing_data: {
                            session_duration: Date.now() - startTime,
                            time_to_first_interaction: behavioralData.mouse_movements > 0 ? 
                                (Date.now() - startTime) / behavioralData.mouse_movements * 10 : 5000
                        }
                    })
                });
                
                const result = await response.json();
                
                const resultDiv = document.getElementById('result');
                const resultTitle = document.getElementById('resultTitle');
                
                if (result.is_human) {
                    resultDiv.className = 'result success';
                    resultTitle.textContent = '✅ Human Verified!';
                } else {
                    resultDiv.className = 'result danger';
                    resultTitle.textContent = '🤖 Bot Detected!';
                }
                
                document.getElementById('confidence').textContent = (result.confidence * 100).toFixed(1) + '%';
                document.getElementById('riskScore').textContent = (result.risk_score * 100).toFixed(1) + '%';
                resultDiv.style.display = 'block';
                
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Verify & Submit';
            }
        });
    </script>
</body>
</html>'''

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def find_free_port(start_port: int = 8000) -> int:
    """Find a free port starting from start_port"""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((settings.HOST, port))
                return port
        except OSError:
            port += 1
    return start_port

def open_browser(port: int):
    """Open browser after a short delay"""
    import time
    time.sleep(1.5)  # Wait for server to start
    url = f"http://{settings.HOST}:{port}/demo"
    print(f"🌐 Opening browser: {url}")
    webbrowser.open(url)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n👋 Shutting down PassiveGuard...")
    sys.exit(0)

def main():
    """Main entry point"""
    signal.signal(signal.SIGINT, signal_handler)
    
    # Find available port
    port = find_free_port(settings.PORT)
    settings.PORT = port
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🛡️  PassiveGuard - ML Bot Detection                            ║
    ║   Starting standalone application...                             ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()
    
    # Run server
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=port,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG
    )

if __name__ == "__main__":
    main()
