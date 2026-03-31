# Setup Guide (Advanced)

This guide covers advanced setup scenarios, troubleshooting, and production deployment.

---

## Table of Contents

1. [Google Cloud Configuration](#google-cloud-configuration)
2. [Advanced Development Setup](#advanced-development-setup)
3. [Troubleshooting](#troubleshooting)
4. [Docker Setup](#docker-setup)
5. [Production Deployment](#production-deployment)

---

## Google Cloud Configuration

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Drive API**:
   - In search bar, search for "Drive API"
   - Click "Enable"

### Step 2: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in details:
   - Service account name: `gpt-sheets-analyzer`
   - Description: `Service account for analyzing Google Sheets`
4. Click **Create and Continue**
5. Grant roles (optional for now):
   - Skip: No special roles needed (Drive API read-only is implicit)
6. Click **Done**

### Step 3: Create and Download JSON Key

1. Go back to **Credentials**
2. Under **Service Accounts**, click the one you just created
3. Go to **Keys** tab
4. Click **Add Key** → **Create new key** → **JSON**
5. A JSON file downloads automatically
6. **Save this file securely** (not in your repository!)

### Step 4: Share Google Drive Folder

1. Locate folder you want to analyze
2. Share it with the Service Account email
   - Email is in JSON file: `"client_email": "...@...iam.gserviceaccount.com"`
3. Permission level: **Viewer** (read-only)

### Step 5: Verify Configuration

```bash
# Test credentials are valid
python -c "
import json
from google.oauth2 import service_account

with open('path/to/credentials.json') as f:
    creds_dict = json.load(f)

creds = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)

print('✅ Credentials valid!')
"
```

---

## Advanced Development Setup

### Using Docker for Development

```bash
# Build image
docker build -t googlesheets-gpt:latest .

# Run container
docker run -it \
  -e GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}' \
  -e OPENAI_API_KEY=sk-... \
  -v $(pwd)/output:/app/output \
  googlesheets-gpt:latest
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  app:
    build: .
    environment:
      GOOGLE_CREDENTIALS_JSON: '${GOOGLE_CREDENTIALS_JSON}'
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LOG_LEVEL: DEBUG
    volumes:
      - ./output:/app/output
      - ./.cache:/app/.cache
    ports:
      - "8000:8000"
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Run:
```bash
# Copy env vars to .env file
docker-compose up
```

### Remote Development (VS Code)

1. Install Remote - Containers extension
2. Open project in container
3. Terminal will automatically use Python inside container

### Python Version Management

Using `pyenv`:

```bash
# Install Python 3.11
pyenv install 3.11.0

# Set local version
pyenv local 3.11.0

# Create venv
python -m venv .venv
```

---

## Troubleshooting

### Authorization Errors

**Error:** `HttpError 403: The user does not have sufficient permissions`

**Solution:**
1. Verify Service Account email
2. Check folder sharing:
   ```
   Right-click folder → Share
   → Add client_email from JSON
   → Set to "Viewer"
   ```
3. Wait 1-2 minutes for permissions to propagate

### Credentials Not Found

**Error:** `GOOGLE_CREDENTIALS_JSON not found`

**Solution Option 1: File Path**
```bash
# .env
GOOGLE_CREDENTIALS_JSON=C:\Users\erickk\credentials.json
```

**Solution Option 2: Inline JSON**
```bash
# Get JSON without line breaks
python -c "
import json
with open('credentials.json') as f:
    print(json.dumps(json.load(f)))
" > inline_creds.txt

# Copy the output and paste into .env
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

**Solution Option 3: Environment Variable**
```bash
# Windows PowerShell
$env:GOOGLE_CREDENTIALS_JSON = Get-Content credentials.json -Raw

# macOS/Linux
export GOOGLE_CREDENTIALS_JSON=$(cat credentials.json)

python __main__.py
```

### OpenAI API Errors

**Error:** `Unauthorized: Invalid authentication credentials`

**Solution:**
1. Verify API key at https://platform.openai.com/account/keys
2. Check key hasn't expired
3. Ensure you have available credits
4. Verify `OPENAI_API_KEY` in `.env`

```bash
# Test API key
python -c "
from openai import OpenAI
client = OpenAI(api_key='sk-...')
print('✅ API key valid!')
"
```

**Error:** `RateLimitError: Rate limit exceeded`

**Solution:**
1. Use cache to avoid duplicate calls:
   ```bash
   # Already enabled by default
   # Cache saves same prompts for same spreadsheet
   ```
2. Wait 1-2 minutes before retrying
3. Upgrade API plan at OpenAI

### Memory Issues

**Error:** `MemoryError` when processing large spreadsheets

**Solution:**
1. Increase Python memory:
   ```bash
   set PYTHONUNBUFFERED=1
   jupyter notebook  # or your script
   ```

2. Process in batches:
   ```python
   # Don't load entire sheet, read in chunks
   chunks = pd.read_excel(file, chunksize=1000)
   ```

3. Increase system swap

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
1. Ensure you're in project root:
   ```bash
   pwd  # should end with gpt-sheets-analyzer
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

3. Or run with `-m` flag:
   ```bash
   python -m src.cli.main
   ```

---

## Docker Setup

### Dockerfile

The repository already includes a production-ready `Dockerfile`.

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
   PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
   && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY __main__.py ./
COPY __init__.py ./

RUN pip install --no-cache-dir --upgrade pip \
   && pip install --no-cache-dir .

COPY .env.example ./.env.example
COPY docs ./docs
COPY examples ./examples

RUN mkdir -p /app/output /app/.cache

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
# Build
docker build -t gpt-sheets-analyzer:latest .

# Run API (compose)
docker compose up api

# Run CLI (compose profile)
docker compose run --rm cli
```

### Docker Compose

The repository includes `docker-compose.yml` with two services:
- `api`: runs `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- `cli`: runs `python __main__.py` for interactive usage

### .dockerignore

```
.git
.gitignore
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.venv
.env
*.json
output/
.cache/
```

---

## Production Deployment

### AWS Lambda

1. Install SAM CLI
2. Create `template.yaml`:
   ```yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Transform: AWS::Serverless-2016-10-31

   Resources:
     AnalyzerFunction:
       Type: AWS::Serverless::Function
       Properties:
         Handler: src.api.handler.lambda_handler
         Runtime: python3.11
         Environment:
           Variables:
             GOOGLE_CREDENTIALS_JSON: !Sub '{{{{SECRETS:google_creds}}}}'
             OPENAI_API_KEY: !Sub '{{{{SECRETS:openai_key}}}}'
   ```

3. Deploy:
   ```bash
   sam deploy --guided
   ```

### Heroku

1. Create `Procfile`:
   ```
   web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

2. Create `runtime.txt`:
   ```
   python-3.11.0
   ```

3. Deploy:
   ```bash
   git push heroku main
   ```

### Google Cloud Run

```bash
# Build container
gcloud builds submit

# Deploy
gcloud run deploy googlesheets-gpt \
  --image gcr.io/PROJECT/googlesheets-gpt \
  --platform managed \
  --region us-central1 \
  --set-env-vars "OPENAI_API_KEY=..." \
  --memory 512Mi
```

### Environment Variables in Production

**Never hardcode secrets!** Use:

- **AWS**: Secrets Manager
- **Heroku**: Config Vars
- **GCP**: Secret Manager
- **Docker**: .env files (not in repo)

Example with AWS:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

creds = get_secret('googlesheets-gpt/credentials')
```

### Monitoring & Logging

Use structured logging:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'extra': record.__dict__.get('extra', {})
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Rate Limiting

Add rate limiting for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post('/sheets/{id}/analyze')
@limiter.limit("10/minute")
async def analyze(...):
    ...
```

---

## Performance Optimization

### Caching

- File cache: Already implemented ✅
- Redis cache: Install `redis` + use RedisCache

### Database

For production, use PostgreSQL:

```python
from sqlalchemy import …

# Add migrations with Alembic
alembic init alembic
```

### Async Support

Convert to async/await:

```python
async def analyze_spreadsheet(...):
    df = await drive_adapter.read_spreadsheet_async(...)
    result = await openai_adapter.process_async(df, prompt)
    return result
```

---

## Health Checks

Implement liveness/readiness probes:

```python
@app.get('/health/live')
async def liveness():
    return {"status": "alive"}

@app.get('/health/ready')
async def readiness():
    # Check dependencies
    try:
        drive.list_spreadsheets()
        return {"status": "ready"}
    except:
        return {"status": "not_ready"}, 503
```

---

## Backup & Recovery

### Cache Backup

```bash
# Backup cache
tar -czf cache_backup.tar.gz .cache/

# Restore
tar -xzf cache_backup.tar.gz
```

### Configuration Backup

```bash
# Store credentials securely
# Option 1: AWS Secrets Manager
# Option 2: HashiCorp Vault
# Option 3: Azure Key Vault
```

---

## Support & Debugging

### Verbose Logging

```python
# In .env
LOG_LEVEL=DEBUG

# Or via environment
export LOG_LEVEL=DEBUG
python __main__.py
```

### Debug Mode

```bash
# Enable Python debugger
python -m pdb -m src.cli.main
```

### Common Issues Checklist

- [ ] `.env` file exists and filled
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Google credentials valid and shared
- [ ] OpenAI API key valid and has credits
- [ ] Python 3.10+ installed
- [ ] Port 8000 not in use (for API)

---

**Last Updated:** March 2026

For issues, open a [GitHub Issue](https://github.com/Observon/gpt-sheets-analyzer/issues)
