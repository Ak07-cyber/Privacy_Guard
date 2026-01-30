# PassiveGuard - Environment Setup & Deployment

## Development Setup

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- Git

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build the SDK
npm run build

# Run in development mode
npm run dev
```

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Train the ML model
python ml_training/train_model.py

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Settings
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Model Settings
MODEL_PATH=models/bot_detector.joblib
MODEL_THRESHOLD=0.5

# Token Settings
TOKEN_EXPIRE_MINUTES=30

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Redis (optional, for distributed deployment)
REDIS_URL=redis://localhost:6379/0
```

---

## Production Deployment

### Docker Deployment

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY models/ ./models/

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: passiveguard-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: passiveguard-api
  template:
    metadata:
      labels:
        app: passiveguard-api
    spec:
      containers:
      - name: api
        image: passiveguard/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: passiveguard-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: passiveguard-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: passiveguard-api
```

### AWS Deployment

#### Lambda + API Gateway

```python
# lambda_handler.py
from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
```

#### SAM Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 512

Resources:
  PassiveGuardFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_handler.handler
      Runtime: python3.11
      CodeUri: backend/
      Events:
        Api:
          Type: HttpApi
          Properties:
            Path: /{proxy+}
            Method: ANY
      Environment:
        Variables:
          SECRET_KEY: !Ref SecretKey
          MODEL_PATH: /var/task/models/bot_detector.joblib
```

---

## CDN Setup for Frontend SDK

### npm Publishing

```bash
cd frontend
npm login
npm publish --access public
```

### CDN Distribution

After npm publish, the SDK is available via:

```html
<!-- unpkg -->
<script src="https://unpkg.com/passiveguard-sdk@latest/dist/index.js"></script>

<!-- jsDelivr -->
<script src="https://cdn.jsdelivr.net/npm/passiveguard-sdk@latest/dist/index.js"></script>
```

---

## Monitoring & Logging

### Prometheus Metrics

Add to `app/main.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Structured Logging

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info("verification_complete", is_human=True, confidence=0.95)
```

### Health Checks

The API includes a health endpoint at `/api/v1/health`:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true
}
```

---

## Security Considerations

### HTTPS

Always use HTTPS in production. Configure SSL/TLS:

```nginx
server {
    listen 443 ssl http2;
    server_name api.passiveguard.com;

    ssl_certificate /etc/letsencrypt/live/api.passiveguard.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.passiveguard.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Rate Limiting

Configure rate limiting at the reverse proxy level:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

### CORS Configuration

Restrict CORS to your domains:

```python
# In production
settings.CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## Scaling Considerations

### Horizontal Scaling

- The API is stateless and can be horizontally scaled
- Use Redis for distributed token validation
- Load balance across multiple instances

### ML Model Optimization

- The XGBoost model is lightweight (~1MB)
- Inference time is <50ms
- Can be further optimized with ONNX

### Caching

Consider caching for:
- Site key validation
- Token validation (with TTL)
- Feature extraction results
