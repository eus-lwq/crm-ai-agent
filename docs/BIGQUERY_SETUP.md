# BigQuery Integration Setup

## Table Configuration

The interactive table in the frontend is connected to BigQuery table:
```
ai-hackathon-477617.CRM_DATA.deals
```

## Configuration

### Backend Configuration

The backend uses the following configuration (from `config.py`):
- **Project ID**: `ai-hackathon-477617` (default, can be overridden via `.env`)
- **Dataset**: `CRM_DATA` (uppercase)
- **Table**: `deals`

### Environment Variables

Set in `.env` file:
```bash
GCP_PROJECT_ID=ai-hackathon-477617
BIGQUERY_DATASET=CRM_DATA
GCP_SERVICE_ACCOUNT_PATH=/path/to/gcp-service-account.json
```

## API Endpoint

The frontend fetches data from:
```
GET /api/interactions?limit=50
```

This endpoint:
1. Connects to BigQuery using the configured credentials
2. Queries the `ai-hackathon-477617.CRM_DATA.deals` table
3. Returns interaction data in JSON format

## Table Schema

The BigQuery table should have the following columns:
- `contact_name` (STRING, nullable)
- `company` (STRING, nullable)
- `next_step` (STRING, nullable)
- `deal_value` (FLOAT, nullable)
- `follow_up_date` (DATE, nullable)
- `notes` (STRING, nullable)
- `interaction_medium` (STRING, nullable)

## Frontend Integration

The frontend (`langgraph-crm-insight`) automatically:
1. Fetches data from `/api/interactions` endpoint
2. Displays data in the interactive table
3. Auto-refreshes every 30 seconds
4. Shows loading and error states

## Testing the Connection

Run the test script to verify BigQuery connection:
```bash
cd crm-ai-agent
uv run python scripts/test_bigquery_connection.py
```

This will:
- Test BigQuery client connection
- Verify dataset and table exist
- Query sample data
- Display results

## Troubleshooting

### Error: "Table not found"
- Verify the table exists in BigQuery console
- Check that `GCP_PROJECT_ID` and `BIGQUERY_DATASET` are correct
- Ensure the service account has BigQuery read permissions

### Error: "Permission denied"
- Verify the service account JSON file path is correct
- Ensure the service account has `BigQuery Data Viewer` role
- Check that the service account has access to the dataset

### No data showing in frontend
- Check browser console for API errors
- Verify backend is running on port 8001
- Check backend logs for BigQuery query errors
- Verify CORS is configured correctly

## Data Flow

```
BigQuery Table (ai-hackathon-477617.CRM_DATA.deals)
    ↓
Backend API (/api/interactions)
    ↓
Frontend API Client (getInteractions)
    ↓
React Component (Index.tsx)
    ↓
Interactive Table Display
```

