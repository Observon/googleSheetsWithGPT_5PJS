# API Reference

## FastAPI REST API

Base URL: `http://localhost:8000`

---

## Endpoints

### Health Check

**Check if the API is running**

```http
GET /health
```

**Response (200):**
```json
{
  "status": "ok",
  "timestamp": "2026-03-31T10:30:00Z"
}
```

---

### List Spreadsheets

**List all spreadsheets in the Drive (or a specific folder)**

```http
GET /sheets?folder_id=optional_folder_id
```

**Parameters:**
- `folder_id` (query, optional): Google Drive folder ID to filter

**Response (200):**
```json
{
  "count": 3,
  "sheets": [
    {
      "id": "1a2b3c4d5e6f",
      "name": "Sales Data 2026",
      "mimeType": "application/vnd.google-apps.spreadsheet",
      "modifiedTime": "2026-03-31T09:00:00Z",
      "size": null
    },
    ...
  ]
}
```

**Errors:**
- `401` — Google Drive credentials invalid
- `403` — Insufficient permissions

---

### Analyze Spreadsheet

**Analyze a spreadsheet with GPT**

```http
POST /sheets/{sheet_id}/analyze
Content-Type: application/json

{
  "prompt": "What are the main patterns in this data?",
  "use_cache": true
}
```

**Parameters:**
- `sheet_id` (path, required): Google Sheet ID
- `prompt` (body, required): Analysis prompt
- `use_cache` (body, optional, default: true): Use cached results if available

**Response (200):**
```json
{
  "id": "analysis-uuid",
  "dataset_id": "1a2b3c4d5e6f",
  "dataset_name": "Sales Data 2026",
  "prompt": "What are the main patterns?",
  "result": "The data shows a 15% increase in Q1 sales...",
  "model": "gpt-4o-mini",
  "created_at": "2026-03-31T10:35:20Z",
  "cached": false
}
```

**Errors:**
- `400` — Missing or invalid prompt
- `404` — Sheet not found
- `503` — OpenAI API error or rate limit

---

### Generate Insights

**Automatically generate insights from a spreadsheet**

```http
POST /sheets/{sheet_id}/insights
Content-Type: application/json

{
  "use_cache": true
}
```

**Response (200):**
```json
{
  "id": "analysis-uuid",
  "result": "Key Insights:\n1. 15% growth in Q1\n2. Highest in North region...",
  ...
}
```

---

### Export Analysis

**Export an analysis result**

```http
GET /exports/{analysis_id}/{format}
```

**Parameters:**
- `analysis_id` (path, required): Analysis ID from `/analyze`
- `format` (path, required): `csv`, `pdf`, or `md`

**Response (200):**
```
[File download]
Content-Type: application/pdf (or text/csv, text/markdown)
```

**Example (via curl):**
```bash
curl -o report.pdf http://localhost:8000/exports/abc-123-def/pdf
```

---

### Batch Process Folder

**Process all sheets in a folder**

```http
POST /batch/process
Content-Type: application/json

{
  "folder_id": "1a2b3c4d5e6f",
  "prompt": "Generate insights",
  "export_format": "pdf"
}
```

**Response (200):**
```json
{
  "job_id": "batch-job-uuid",
  "total": 5,
  "processed": [
    {
      "file_id": "sheet-1",
      "file_name": "Q1 Sales",
      "status": "success",
      "analysis_id": "analysis-1",
      "export_path": "output/analysis-1.pdf"
    },
    {
      "file_id": "sheet-2",
      "status": "error",
      "error": "Export failed: reportlab not installed"
    }
  ]
}
```

---

### Clear Cache

**Remove all cached analysis results**

```http
DELETE /cache
```

**Response (200):**
```json
{
  "cleared": 12,
  "message": "Cache cleared successfully"
}
```

---

## Data Models

### FileInfo
```json
{
  "id": "string (Google Sheet ID)",
  "name": "string",
  "mimeType": "application/vnd.google-apps.spreadsheet",
  "modifiedTime": "ISO 8601 datetime",
  "size": "integer or null"
}
```

### Analysis
```json
{
  "id": "UUID",
  "dataset_id": "string",
  "dataset_name": "string",
  "prompt": "string",
  "result": "string (analysis content)",
  "model": "gpt-4o-mini",
  "created_at": "ISO 8601 datetime",
  "cached": "boolean"
}
```

### ExportResult
```json
{
  "analysis_id": "UUID",
  "format": "csv | pdf | md",
  "filepath": "string (full path)",
  "size_bytes": "integer",
  "created_at": "ISO 8601 datetime"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status": 400,
  "timestamp": "2026-03-31T10:45:00Z"
}
```

### Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| `400` | Invalid prompt | Provide non-empty `prompt` field |
| `401` | Unauthorized | Check `GOOGLE_CREDENTIALS_JSON` |
| `403` | Forbidden | Share Google Drive folder with service account |
| `404` | Not found | Verify sheet ID exists |
| `429` | Rate limited | Wait before retrying (OpenAI) |
| `500` | Server error | Check logs, retry |
| `503` | Service unavailable | OpenAI API is down, try later |

---

## Usage Examples

### Python (requests library)

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# List sheets
response = requests.get(f"{BASE_URL}/sheets")
sheets = response.json()["sheets"]

# Analyze a sheet
data = {
    "prompt": "What's the revenue trend?",
    "use_cache": True
}
response = requests.post(
    f"{BASE_URL}/sheets/{sheets[0]['id']}/analyze",
    json=data
)
analysis = response.json()

# Export analysis
response = requests.get(
    f"{BASE_URL}/exports/{analysis['id']}/pdf",
    headers={"Accept": "application/pdf"}
)
with open("report.pdf", "wb") as f:
    f.write(response.content)
```

### cURL

```bash
# List sheets
curl http://localhost:8000/sheets | jq .

# Analyze
curl -X POST http://localhost:8000/sheets/SHEET_ID/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Show me the trends"}'

# Export
curl -o report.pdf http://localhost:8000/exports/ANALYSIS_ID/pdf

# Clear cache
curl -X DELETE http://localhost:8000/cache
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// List sheets
const sheets = await fetch(`${BASE_URL}/sheets`)
  .then(r => r.json())
  .then(d => d.sheets);

// Analyze
const analysis = await fetch(`${BASE_URL}/sheets/${sheets[0].id}/analyze`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "What patterns do you see?",
    use_cache: true
  })
}).then(r => r.json());

console.log(analysis.result);
```

---

## WebHook Support (Future)

```http
POST /sheets/{sheet_id}/analyze?webhook_url=https://...
```

Will POST the analysis result to the webhook URL when complete.

---

## Rate Limiting (Future)

Recommended OpenAI API usage:
- Max 10 requests/min per folder_id
- Cache hits don't count toward limit
- Batch jobs: 1 concurrent limit

---

## Swagger UI

Interactive API documentation available at:

```
http://localhost:8000/docs
```

---

**Last Updated:** March 2026
