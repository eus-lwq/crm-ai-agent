# Quick Start Guide

## BigQuery Connection ✅

The BigQuery connection is working! Test results show:
- ✅ Table exists: `ai-hackathon-477617.CRM_DATA.deals`
- ✅ Data available: 5+ rows found
- ✅ Schema correct: All fields accessible

## Starting the Server

### If Port is Already in Use

If you see "Address already in use" error:

**Option 1: Kill the process on port 8000**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use the helper script
./scripts/kill_port.sh 8000
```

**Option 2: Use a different port**
```bash
# Set in .env file
API_PORT=8001

# Or override when running
uv run uvicorn api.main:app --host 0.0.0.0 --port 8001
```

### Normal Start

```bash
cd crm-ai-agent
uv run python main.py
```

Server will start on `http://localhost:8001`

## Frontend Connection

Make sure the frontend API URL matches your backend port:

In `langgraph-crm-insight/src/lib/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";
```

Or set environment variable:
```bash
cd langgraph-crm-insight
VITE_API_URL=http://localhost:8001 npm run dev
```

## Testing the Full Stack

1. **Start Backend:**
   ```bash
   cd crm-ai-agent
   uv run python main.py
   ```

2. **Start Frontend:**
   ```bash
   cd langgraph-crm-insight
   npm run dev
   ```

3. **Verify Connection:**
   - Open browser to `http://localhost:8080` (or your frontend port)
   - Go to "Interactions Data" tab
   - You should see data from BigQuery table

## BigQuery Data

Current data in table:
- 5+ interactions/deals
- Fields: contact_name, company, next_step, deal_value, follow_up_date, notes, interaction_medium
- Data includes both email and phone_call interactions

## Troubleshooting

### Port Already in Use
- Kill existing process: `lsof -ti:8001 | xargs kill -9`
- Or change port in `.env`: `API_PORT=8002`

### Frontend Can't Connect
- Check backend is running: `curl http://localhost:8001/health`
- Check CORS settings in `api/main.py`
- Verify API_BASE_URL in frontend

### No Data Showing
- Check browser console for errors
- Verify BigQuery connection: `uv run python scripts/test_bigquery_connection.py`
- Check backend logs for query errors

