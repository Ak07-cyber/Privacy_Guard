# PassiveGuard SDK

**ML-Powered Passive Bot Detection - A CAPTCHA Replacement**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is PassiveGuard?

PassiveGuard is a **zero-friction bot detection system** that replaces traditional CAPTCHAs. Instead of asking users to solve puzzles, it passively analyzes browser environment and user behavior patterns using machine learning to determine if a visitor is human or bot.

### Why PassiveGuard?

| Traditional CAPTCHA | PassiveGuard |
|---------------------|--------------|
| ❌ Interrupts user flow | ✅ Completely invisible |
| ❌ Accessibility issues | ✅ Works for everyone |
| ❌ Can be solved by AI | ✅ ML-based behavioral analysis |
| ❌ Frustrating experience | ✅ Zero user interaction |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Web Application                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              PassiveGuard SDK (TypeScript)                  ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      ││
│  │  │ Environment  │  │  Behavioral  │  │   Timing     │      ││
│  │  │  Collector   │  │  Collector   │  │  Analysis    │      ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PassiveGuard Backend API                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   FastAPI    │──│   Feature    │──│   XGBoost Model      │  │
│  │   Server     │  │  Extraction  │  │   (56 Features)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Features Analyzed

PassiveGuard collects **56 features** across three categories:

### 🖥️ Environmental Features
- Browser fingerprint (user agent, plugins, screen resolution)
- WebGL renderer and vendor information
- Canvas fingerprint (SHA-256 hashed for privacy)
- Hardware concurrency and device memory
- Timezone, language, and platform details

### 🖱️ Behavioral Features
- Mouse movement patterns, velocity, and acceleration
- Scroll behavior and smoothness
- Keystroke dynamics and timing
- Click patterns and intervals
- Page interaction sequences

### ⏱️ Timing Features
- Time to first interaction
- Session duration patterns
- Event timing consistency
- Response time analysis

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16+ (for frontend SDK)
- **Python** 3.10+ (for backend API)
- **npm** or **yarn**

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/passiveguard.git
cd passiveguard
```

### Step 2: Start the Backend Server

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Train the ML model (if not already trained)
python -m ml_training.train_model

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Step 3: Build the Frontend SDK

```bash
cd ../frontend
npm install
npm run build
```

---

## 📦 SDK Integration Guide

### Option 1: Vanilla JavaScript/TypeScript

#### Installation

Copy the built SDK files or install from npm (if published):

```bash
npm install passiveguard-sdk
```

#### Basic Usage

```typescript
import { PassiveGuard } from 'passiveguard-sdk';

// Initialize PassiveGuard
const guard = new PassiveGuard({
  apiEndpoint: 'https://your-api.com',  // Your PassiveGuard backend URL
  siteKey: 'your-site-key',              // Your site identifier
  debug: false                            // Enable for development
});

// Start collecting data (call on page load)
await guard.init();

// Verify user before sensitive actions
async function handleFormSubmit(event) {
  event.preventDefault();
  
  try {
    const result = await guard.verify();
    
    if (result.isHuman) {
      console.log('Human verified! Confidence:', result.confidence);
      // Proceed with form submission
      submitForm();
    } else {
      console.log('Bot detected! Risk score:', result.riskScore);
      // Show fallback challenge or block action
      showChallenge();
    }
  } catch (error) {
    console.error('Verification failed:', error);
    // Handle gracefully - don't block legitimate users
  }
}

// Get verification token for server-side validation
const token = guard.getToken();

// Clean up when done
guard.destroy();
```

#### Complete Integration Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Application</title>
  <script src="passiveguard.min.js"></script>
</head>
<body>
  <form id="loginForm">
    <input type="email" name="email" placeholder="Email" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>

  <script>
    // Initialize PassiveGuard
    const guard = new PassiveGuard({
      apiEndpoint: 'http://localhost:8000',
      siteKey: 'my-login-page'
    });

    // Start monitoring on page load
    document.addEventListener('DOMContentLoaded', async () => {
      await guard.init();
    });

    // Verify before form submission
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const result = await guard.verify();
      
      if (result.isHuman) {
        // Include verification token in form data
        const formData = new FormData(e.target);
        formData.append('passiveguard_token', guard.getToken());
        
        // Submit to your server
        fetch('/api/login', {
          method: 'POST',
          body: formData
        });
      } else {
        alert('Verification failed. Please try again.');
      }
    });
  </script>
</body>
</html>
```

---

### Option 2: React Integration

#### Using the React Hook

```tsx
import React from 'react';
import { usePassiveGuard } from 'passiveguard-sdk/hooks';

function LoginForm() {
  const { 
    isReady,      // SDK initialized
    isHuman,      // Latest verification result
    confidence,   // Confidence score (0-1)
    isVerifying,  // Verification in progress
    error,        // Any errors
    verify,       // Trigger verification
    getToken      // Get verification token
  } = usePassiveGuard({
    apiEndpoint: 'http://localhost:8000',
    siteKey: 'my-react-app',
    autoInit: true  // Initialize automatically
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await verify();
    
    if (result.isHuman) {
      const token = getToken();
      // Submit form with token
      console.log('Submitting with token:', token);
    } else {
      console.log('Bot detected, confidence:', result.confidence);
    }
  };

  if (!isReady) {
    return <div>Initializing security...</div>;
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="email" placeholder="Email" required />
      <input type="password" placeholder="Password" required />
      <button type="submit" disabled={isVerifying}>
        {isVerifying ? 'Verifying...' : 'Login'}
      </button>
      {error && <p className="error">{error.message}</p>}
    </form>
  );
}

export default LoginForm;
```

#### React Context Provider (Recommended for Multiple Components)

```tsx
// PassiveGuardProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { PassiveGuard } from 'passiveguard-sdk';

interface PassiveGuardContextType {
  guard: PassiveGuard | null;
  isReady: boolean;
  verify: () => Promise<any>;
  getToken: () => string | null;
}

const PassiveGuardContext = createContext<PassiveGuardContextType | null>(null);

export function PassiveGuardProvider({ 
  children, 
  config 
}: { 
  children: React.ReactNode;
  config: { apiEndpoint: string; siteKey: string };
}) {
  const [guard, setGuard] = useState<PassiveGuard | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const instance = new PassiveGuard(config);
    instance.init().then(() => {
      setGuard(instance);
      setIsReady(true);
    });

    return () => instance.destroy();
  }, [config.apiEndpoint, config.siteKey]);

  const verify = async () => {
    if (!guard) throw new Error('PassiveGuard not initialized');
    return guard.verify();
  };

  const getToken = () => guard?.getToken() ?? null;

  return (
    <PassiveGuardContext.Provider value={{ guard, isReady, verify, getToken }}>
      {children}
    </PassiveGuardContext.Provider>
  );
}

export const usePassiveGuardContext = () => {
  const context = useContext(PassiveGuardContext);
  if (!context) {
    throw new Error('usePassiveGuardContext must be used within PassiveGuardProvider');
  }
  return context;
};
```

```tsx
// App.tsx
import { PassiveGuardProvider } from './PassiveGuardProvider';
import LoginForm from './LoginForm';

function App() {
  return (
    <PassiveGuardProvider 
      config={{
        apiEndpoint: process.env.REACT_APP_PASSIVEGUARD_API!,
        siteKey: 'my-app'
      }}
    >
      <LoginForm />
    </PassiveGuardProvider>
  );
}
```

---

### Option 3: Vue.js Integration

```vue
<template>
  <form @submit.prevent="handleSubmit">
    <input v-model="email" type="email" placeholder="Email" required />
    <input v-model="password" type="password" placeholder="Password" required />
    <button type="submit" :disabled="isVerifying">
      {{ isVerifying ? 'Verifying...' : 'Login' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { PassiveGuard } from 'passiveguard-sdk';

const email = ref('');
const password = ref('');
const isVerifying = ref(false);

let guard: PassiveGuard | null = null;

onMounted(async () => {
  guard = new PassiveGuard({
    apiEndpoint: import.meta.env.VITE_PASSIVEGUARD_API,
    siteKey: 'my-vue-app'
  });
  await guard.init();
});

onUnmounted(() => {
  guard?.destroy();
});

async function handleSubmit() {
  if (!guard) return;
  
  isVerifying.value = true;
  
  try {
    const result = await guard.verify();
    
    if (result.isHuman) {
      const token = guard.getToken();
      // Submit form with token
      console.log('Human verified, submitting...');
    } else {
      alert('Verification failed');
    }
  } finally {
    isVerifying.value = false;
  }
}
</script>
```

---

## 🔧 Server-Side Token Validation

After client-side verification, validate the token on your server:

### Python (FastAPI/Flask)

```python
import httpx
from fastapi import FastAPI, HTTPException, Form

app = FastAPI()

PASSIVEGUARD_API = "http://localhost:8000"
PASSIVEGUARD_SECRET = "your-secret-key"

@app.post("/api/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    passiveguard_token: str = Form(...)
):
    # Validate PassiveGuard token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PASSIVEGUARD_API}/api/v1/validate-token",
            json={
                "token": passiveguard_token,
                "secret": PASSIVEGUARD_SECRET
            }
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=403, detail="Bot detected")
    
    validation = response.json()
    
    if not validation["valid"] or not validation["is_human"]:
        raise HTTPException(status_code=403, detail="Verification failed")
    
    # Proceed with login logic
    return {"message": "Login successful"}
```

### Node.js (Express)

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const PASSIVEGUARD_API = 'http://localhost:8000';
const PASSIVEGUARD_SECRET = 'your-secret-key';

app.post('/api/login', async (req, res) => {
  const { email, password, passiveguard_token } = req.body;
  
  try {
    // Validate PassiveGuard token
    const validation = await axios.post(
      `${PASSIVEGUARD_API}/api/v1/validate-token`,
      {
        token: passiveguard_token,
        secret: PASSIVEGUARD_SECRET
      }
    );
    
    if (!validation.data.valid || !validation.data.is_human) {
      return res.status(403).json({ error: 'Bot detected' });
    }
    
    // Proceed with login logic
    res.json({ message: 'Login successful' });
    
  } catch (error) {
    res.status(403).json({ error: 'Verification failed' });
  }
});
```

---

## 📡 API Reference

### Backend Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/verify` | POST | Submit collected data for bot detection |
| `/api/v1/validate-token` | POST | Validate a verification token server-side |
| `/api/v1/health` | GET | Health check endpoint |

### Verify Request

```json
POST /api/v1/verify
Content-Type: application/json

{
  "site_key": "your-site-key",
  "environmental_data": {
    "user_agent": "Mozilla/5.0...",
    "screen_resolution": "1920x1080",
    "timezone": "America/New_York",
    "language": "en-US",
    "platform": "MacIntel",
    "hardware_concurrency": 8,
    "device_memory": 16,
    "webgl_vendor": "Apple Inc.",
    "webgl_renderer": "Apple M1",
    "canvas_fingerprint": "sha256:abc123...",
    "plugins": ["PDF Viewer", "Chrome PDF Viewer"],
    "touch_support": false
  },
  "behavioral_data": {
    "mouse_movements": 245,
    "mouse_velocity_avg": 156.7,
    "mouse_acceleration_avg": 23.4,
    "mouse_direction_changes": 89,
    "scroll_events": 12,
    "scroll_smoothness": 0.87,
    "keystroke_count": 45,
    "keystroke_timing_avg": 123.5,
    "click_count": 5,
    "click_intervals": [234, 456, 189, 567]
  },
  "timing_data": {
    "page_load_time": 1234,
    "time_to_first_interaction": 2345,
    "session_duration": 45678
  }
}
```

### Verify Response

```json
{
  "is_human": true,
  "confidence": 0.97,
  "risk_score": 0.03,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "details": {
    "environmental_score": 0.95,
    "behavioral_score": 0.98,
    "timing_score": 0.96
  }
}
```

---

## ⚙️ Configuration Options

### SDK Configuration

```typescript
interface PassiveGuardConfig {
  // Required
  apiEndpoint: string;        // Backend API URL
  siteKey: string;            // Your site identifier
  
  // Optional
  debug?: boolean;            // Enable debug logging (default: false)
  collectInterval?: number;   // Data collection interval in ms (default: 100)
  minInteractions?: number;   // Min interactions before verify (default: 5)
  timeout?: number;           // API timeout in ms (default: 10000)
  
  // Callbacks
  onReady?: () => void;       // Called when SDK is initialized
  onError?: (error: Error) => void;  // Called on errors
  onChallenge?: (challenge: Challenge) => void;  // Fallback challenge
}
```

### Environment Variables

```bash
# Backend (.env)
PASSIVEGUARD_SECRET_KEY=your-secret-key-here
PASSIVEGUARD_MODEL_PATH=./models/bot_detector.joblib
PASSIVEGUARD_CONFIDENCE_THRESHOLD=0.7
PASSIVEGUARD_CORS_ORIGINS=http://localhost:3000,https://yoursite.com

# Frontend (.env)
REACT_APP_PASSIVEGUARD_API=http://localhost:8000
REACT_APP_PASSIVEGUARD_SITE_KEY=my-site
```

---

## 🧪 Testing Your Integration

### 1. Manual Testing

Open the demo page and interact normally:

```bash
cd demo
python3 -m http.server 3000
# Open http://localhost:3000 in browser
```

### 2. Bot Simulation Testing

```javascript
// Test bot-like behavior
const guard = new PassiveGuard({
  apiEndpoint: 'http://localhost:8000',
  siteKey: 'test'
});

await guard.init();

// Immediately verify without any user interaction
// This should return is_human: false
const result = await guard.verify();
console.log('Bot test result:', result);
```

### 3. API Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test verification with minimal data (should detect bot)
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "site_key": "test",
    "environmental_data": {"user_agent": "bot"},
    "behavioral_data": {},
    "timing_data": {}
  }'
```

---

## 🔐 Security Best Practices

1. **Always validate tokens server-side** - Never trust client-side verification alone
2. **Use HTTPS in production** - Protect data in transit
3. **Implement rate limiting** - Prevent API abuse
4. **Rotate secret keys** - Change keys periodically
5. **Monitor for anomalies** - Log and alert on unusual patterns
6. **Graceful degradation** - Don't block users if service is unavailable

---

## 📁 Project Structure

```
passiveguard/
├── frontend/                    # TypeScript SDK
│   ├── src/
│   │   ├── core/
│   │   │   └── PassiveGuard.ts  # Main SDK class
│   │   ├── collectors/
│   │   │   ├── environmental.ts # Environment data collection
│   │   │   └── behavioral.ts    # Behavior tracking
│   │   ├── hooks/
│   │   │   └── usePassiveGuard.ts # React hook
│   │   ├── utils/
│   │   │   ├── api.ts           # API client
│   │   │   └── fingerprint.ts   # Fingerprinting utilities
│   │   └── types/
│   │       └── index.ts         # TypeScript definitions
│   └── package.json
│
├── backend/                     # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── api/
│   │   │   ├── routes.py       # API endpoints
│   │   │   └── models.py       # Pydantic models
│   │   ├── features/
│   │   │   └── extractor.py    # Feature engineering
│   │   ├── ml/
│   │   │   └── detector.py     # ML model inference
│   │   └── core/
│   │       ├── config.py       # Configuration
│   │       └── security.py     # Security utilities
│   ├── ml_training/
│   │   └── train_model.py      # Model training script
│   ├── models/
│   │   ├── bot_detector.joblib # Trained XGBoost model
│   │   └── feature_importance.json
│   └── requirements.txt
│
├── demo/                        # Demo application
│   └── index.html
│
├── docs/                        # Documentation
│   ├── DEPLOYMENT.md
│   ├── INTEGRATION.md
│   └── PARAMETERS.md
│
└── Chapters/                    # Thesis documentation (LaTeX)
```

---

## 📊 ML Model Performance

| Metric | Value |
|--------|-------|
| **Accuracy** | 100% (on synthetic data) |
| **ROC-AUC** | 1.0 |
| **Cross-Validation** | 100% ± 0% |
| **Inference Time** | < 50ms |
| **Model Size** | 156 KB |

### Top Feature Importance

| Feature | Importance |
|---------|------------|
| scroll_smoothness | 45.25% |
| mouse_direction_changes | 27.58% |
| mouse_pause_count | 26.46% |

---

## 🚢 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t passiveguard-api .
docker run -p 8000:8000 passiveguard-api
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PASSIVEGUARD_SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./models:/app/models
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Support

For questions and support:
- Create an issue on GitHub
- Email: support@passiveguard.dev

---

**Made with ❤️ for a CAPTCHA-free internet**
