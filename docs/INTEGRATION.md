# PassiveGuard Integration Guide

Complete guide for integrating PassiveGuard into your application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Frontend Integration](#frontend-integration)
3. [Backend Integration](#backend-integration)
4. [React/Next.js Integration](#reactnextjs-integration)
5. [API Reference](#api-reference)
6. [Configuration Options](#configuration-options)
7. [Privacy & Compliance](#privacy--compliance)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install the SDK

```bash
# Frontend (npm)
npm install passiveguard-sdk

# Backend (pip)
pip install passiveguard
```

### 2. Initialize on Your Website

```typescript
import { PassiveGuard } from 'passiveguard-sdk';

const guard = new PassiveGuard({
  apiEndpoint: 'https://your-api.com',
  siteKey: 'your-site-key',
});

// Start collecting data
await guard.init();

// Verify before form submission
const result = await guard.verify();
console.log('Is Human:', result.isHuman);
console.log('Token:', result.token);
```

### 3. Validate Token on Backend

```python
import httpx

async def validate_token(token: str, site_key: str):
    response = await httpx.post(
        "https://your-api.com/api/v1/validate",
        json={"token": token, "siteKey": site_key}
    )
    return response.json()["valid"]
```

---

## Frontend Integration

### Vanilla JavaScript

```html
<script src="https://cdn.passiveguard.com/sdk.min.js"></script>
<script>
  const guard = new PassiveGuard({
    apiEndpoint: 'https://api.passiveguard.com',
    siteKey: 'YOUR_SITE_KEY',
  });

  guard.init().then(() => {
    console.log('PassiveGuard initialized');
  });

  document.getElementById('myForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
      const result = await guard.verify();
      
      if (result.isHuman) {
        // Include token in form submission
        document.getElementById('pg_token').value = result.token;
        e.target.submit();
      } else if (result.challengeRequired) {
        // Handle challenge if needed
        handleChallenge(result.challenge);
      }
    } catch (error) {
      console.error('Verification failed:', error);
    }
  });
</script>
```

### TypeScript with Async/Await

```typescript
import PassiveGuard, { 
  PassiveGuardConfig, 
  VerificationResult 
} from 'passiveguard-sdk';

class FormProtection {
  private guard: PassiveGuard;
  
  constructor() {
    const config: PassiveGuardConfig = {
      apiEndpoint: process.env.PASSIVEGUARD_API!,
      siteKey: process.env.PASSIVEGUARD_KEY!,
      debug: process.env.NODE_ENV === 'development',
      enableBehavioral: true,
      enableEnvironmental: true,
    };
    
    this.guard = new PassiveGuard(config);
  }
  
  async initialize(): Promise<void> {
    await this.guard.init();
    
    // Listen to events
    this.guard.on('verifying', () => {
      console.log('Verification in progress...');
    });
    
    this.guard.on('verified', (data) => {
      console.log('Verification complete:', data);
    });
  }
  
  async protectForm(formId: string): Promise<void> {
    const form = document.getElementById(formId) as HTMLFormElement;
    
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const result = await this.guard.verify();
      
      if (result.isHuman && result.confidence > 0.7) {
        // Safe to submit
        const formData = new FormData(form);
        formData.append('pg_token', result.token);
        
        await fetch(form.action, {
          method: 'POST',
          body: formData,
        });
      }
    });
  }
}
```

---

## Backend Integration

### Python FastAPI

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx

app = FastAPI()

PASSIVEGUARD_API = "https://api.passiveguard.com"
SITE_KEY = "your-site-key"

class FormSubmission(BaseModel):
    name: str
    email: str
    pg_token: str

async def verify_passiveguard_token(token: str) -> bool:
    """Verify PassiveGuard token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PASSIVEGUARD_API}/api/v1/validate",
            json={"token": token, "siteKey": SITE_KEY}
        )
        result = response.json()
        return result.get("valid", False) and result.get("isHuman", False)

@app.post("/submit")
async def submit_form(data: FormSubmission):
    # Verify the token
    is_valid = await verify_passiveguard_token(data.pg_token)
    
    if not is_valid:
        raise HTTPException(status_code=403, detail="Bot detected")
    
    # Process the form
    return {"message": "Form submitted successfully"}
```

### Node.js Express

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const PASSIVEGUARD_API = 'https://api.passiveguard.com';
const SITE_KEY = 'your-site-key';

async function verifyToken(token) {
  try {
    const response = await axios.post(`${PASSIVEGUARD_API}/api/v1/validate`, {
      token,
      siteKey: SITE_KEY,
    });
    return response.data.valid && response.data.isHuman;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
}

// Middleware for protected routes
const passiveGuardMiddleware = async (req, res, next) => {
  const token = req.body.pg_token || req.headers['x-passiveguard-token'];
  
  if (!token) {
    return res.status(403).json({ error: 'Missing verification token' });
  }
  
  const isHuman = await verifyToken(token);
  
  if (!isHuman) {
    return res.status(403).json({ error: 'Bot detected' });
  }
  
  next();
};

app.post('/api/contact', passiveGuardMiddleware, (req, res) => {
  // Handle form submission
  res.json({ success: true });
});

app.listen(3000);
```

### Django

```python
# middleware.py
import requests
from django.http import JsonResponse
from django.conf import settings

class PassiveGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_paths = ['/api/contact/', '/api/register/']
    
    def __call__(self, request):
        if request.path in self.protected_paths and request.method == 'POST':
            token = request.POST.get('pg_token') or request.headers.get('X-PassiveGuard-Token')
            
            if not self.verify_token(token):
                return JsonResponse({'error': 'Bot detected'}, status=403)
        
        return self.get_response(request)
    
    def verify_token(self, token):
        if not token:
            return False
        
        try:
            response = requests.post(
                f"{settings.PASSIVEGUARD_API}/api/v1/validate",
                json={"token": token, "siteKey": settings.PASSIVEGUARD_SITE_KEY}
            )
            data = response.json()
            return data.get('valid', False) and data.get('isHuman', False)
        except:
            return False
```

---

## React/Next.js Integration

### React Hook

```tsx
import { usePassiveGuard } from 'passiveguard-sdk';
import { useState } from 'react';

function ContactForm() {
  const {
    verify,
    isLoading,
    isHuman,
    error,
    riskScore,
  } = usePassiveGuard({
    apiEndpoint: process.env.NEXT_PUBLIC_PG_API!,
    siteKey: process.env.NEXT_PUBLIC_PG_KEY!,
    autoInit: true,
  });

  const [formData, setFormData] = useState({ name: '', email: '', message: '' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await verify();
      
      if (result.isHuman) {
        await fetch('/api/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-PassiveGuard-Token': result.token,
          },
          body: JSON.stringify(formData),
        });
        alert('Message sent!');
      } else {
        alert('Verification failed. Please try again.');
      }
    } catch (err) {
      console.error('Error:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Name"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
      />
      <input
        type="email"
        placeholder="Email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
      />
      <textarea
        placeholder="Message"
        value={formData.message}
        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Verifying...' : 'Send Message'}
      </button>
      {error && <p className="error">{error.message}</p>}
    </form>
  );
}
```

### Next.js API Route

```typescript
// pages/api/contact.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const token = req.headers['x-passiveguard-token'] as string;

  // Validate token
  const validationResponse = await fetch(
    `${process.env.PASSIVEGUARD_API}/api/v1/validate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        siteKey: process.env.PASSIVEGUARD_SITE_KEY,
      }),
    }
  );

  const validation = await validationResponse.json();

  if (!validation.valid || !validation.isHuman) {
    return res.status(403).json({ error: 'Bot detected' });
  }

  // Process the request
  const { name, email, message } = req.body;
  
  // ... your business logic

  return res.status(200).json({ success: true });
}
```

---

## API Reference

### POST /api/v1/verify

Verify user data and get verification result.

**Request:**
```json
{
  "siteKey": "your-site-key",
  "environmental": { ... },
  "behavioral": { ... },
  "requestId": "unique-request-id",
  "timestamp": 1706000000000
}
```

**Response:**
```json
{
  "isHuman": true,
  "confidence": 0.95,
  "riskScore": 0.05,
  "token": "eyJ...",
  "expiresAt": 1706000030000,
  "challengeRequired": false,
  "challenge": null
}
```

### POST /api/v1/validate

Validate a verification token.

**Request:**
```json
{
  "token": "eyJ...",
  "siteKey": "your-site-key"
}
```

**Response:**
```json
{
  "valid": true,
  "isHuman": true,
  "riskScore": 0.05,
  "expiresAt": 1706000030000
}
```

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiEndpoint` | string | required | API endpoint URL |
| `siteKey` | string | required | Your site key |
| `debug` | boolean | false | Enable debug logging |
| `collectionTimeout` | number | 30000 | Data collection timeout (ms) |
| `enableBehavioral` | boolean | true | Enable behavioral tracking |
| `enableEnvironmental` | boolean | true | Enable environmental collection |
| `privacyMode` | boolean | false | Enhanced privacy mode |
| `onChallenge` | function | - | Challenge handler callback |
| `onVerify` | function | - | Verification complete callback |

---

## Privacy & Compliance

PassiveGuard is designed with privacy in mind:

### What We Collect
- Browser and device information (hashed)
- Mouse movement patterns (aggregated statistics)
- Keyboard timing patterns (no actual keys)
- Screen dimensions and capabilities
- Hardware capabilities (non-identifying)

### What We DON'T Collect
- Personally Identifiable Information (PII)
- Actual keystrokes or form content
- IP addresses (unless configured)
- Cookies or tracking identifiers
- Cross-site tracking data

### Compliance
- ✅ GDPR compliant
- ✅ UIDAI privacy policy compliant
- ✅ CCPA compliant
- ✅ No third-party data sharing

---

## Troubleshooting

### Common Issues

**1. "Invalid site key" error**
- Ensure your site key is correct
- Check that the domain is registered

**2. Low confidence scores for legitimate users**
- Increase `collectionTimeout` to allow more data collection
- Ensure behavioral tracking is enabled

**3. High false positive rate**
- Adjust the threshold in backend configuration
- Review collected features for anomalies

**4. SDK not initializing**
- Check browser console for errors
- Ensure the API endpoint is accessible
- Verify CORS settings on your server

### Debug Mode

Enable debug mode to see detailed logs:

```typescript
const guard = new PassiveGuard({
  apiEndpoint: 'https://api.example.com',
  siteKey: 'your-key',
  debug: true, // Enable debug logging
});
```

### Support

For issues or questions:
- GitHub Issues: [github.com/passiveguard/sdk](https://github.com/passiveguard/sdk)
- Email: support@passiveguard.com
