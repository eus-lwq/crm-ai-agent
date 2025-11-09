# Troubleshooting Guide

## Frontend Shows No Data (All Zeros)

### Problem
The frontend dashboard shows:
- 0 customers
- $0 deal value
- 0 companies
- Empty charts and tables

### Solution Steps

#### 1. Check if Backend Server is Running

```bash
# Test if backend is responding
curl http://localhost:8001/health

# Should return: {"status":"healthy","service":"crm-ai-agent"}
```

If it doesn't respond, the server is not running.

#### 2. Start the Backend Server

**Option A: Use the helper script (recommended)**
```bash
cd crm-ai-agent
./scripts/start_server.sh
```

**Option B: Manual start**
```bash
cd crm-ai-agent

# Kill any existing process on port 8001
lsof -ti:8001 | xargs kill -9

# Start server
uv run python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### 3. Verify Frontend Can Connect

Open browser console (F12) and check for errors:
- `Failed to fetch` = Backend not running or CORS issue
- `404 Not Found` = Wrong API URL
- `Network Error` = Backend not accessible

#### 4. Check API Endpoint Directly

```bash
# Test the interactions endpoint
curl http://localhost:8001/api/interactions?limit=5

# Should return JSON array of interactions
```

#### 5. Verify BigQuery Connection

```bash
cd crm-ai-agent
uv run python scripts/test_bigquery_connection.py
```

Should show:
- ✅ Dataset exists
- ✅ Table exists
- ✅ Data retrieved

#### 6. Check Frontend API URL

In `langgraph-crm-insight/src/lib/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

Make sure this matches your backend port.

#### 7. Check CORS Configuration

In `api/main.py`, make sure your frontend URL is in the allowed origins:
```python
allow_origins=[
    "http://localhost:8080",  # Your frontend port
    "http://localhost:5173",  # Vite default
    ...
]
```

## Common Issues

### Port Already in Use

**Error:** `[Errno 48] Address already in use`

**Solution:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
# Edit .env: API_PORT=8001
```

### CORS Errors

**Error in browser console:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
1. Check `api/main.py` CORS configuration
2. Make sure your frontend URL is in `allow_origins`
3. Restart the backend server
4. Verify backend is running on port 8001

### BigQuery Connection Errors

**Error:** `DefaultCredentialsError` or `Permission denied`

**Solution:**
1. Verify service account JSON path in `.env`:
   ```
   GCP_SERVICE_ACCOUNT_PATH=/path/to/gcp-service-account.json
   ```
2. Check service account has BigQuery permissions
3. Run test script: `uv run python scripts/test_bigquery_connection.py`

### Frontend Shows Loading Forever

**Possible causes:**
1. Backend not running
2. API endpoint returning error
3. Network/CORS issue

**Solution:**
1. Check browser console for errors
2. Test API directly: `curl http://localhost:8000/api/interactions`
3. Check backend logs for errors

## Quick Diagnostic Commands

```bash
# 1. Check if backend is running
curl http://localhost:8001/health

# 2. Check what's using port 8001
lsof -i :8001

# 3. Test BigQuery connection
cd crm-ai-agent
uv run python scripts/test_bigquery_connection.py

# 4. Test API endpoint
curl http://localhost:8001/api/interactions?limit=5

# 5. Check frontend can reach backend
# Open browser console and check Network tab
```

## Still Not Working?

1. **Check all logs:**
   - Backend terminal output
   - Browser console (F12)
   - Network tab in browser dev tools

2. **Verify environment:**
   - `.env` file exists and has correct values
   - Service account JSON file exists
   - GCP project ID is correct

3. **Test each component:**
   - BigQuery connection (test script)
   - Backend API (curl commands)
   - Frontend API client (browser console)

