# LegalEase AI - API Gateway & Endpoints Specification

## Overview
The LegalEase AI backend exposes RESTful endpoints for health monitoring, service diagnostics, and legal document drafting. Interactive Swagger documentation is available at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## Endpoint Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root verification endpoint | No |
| `GET` | `/health` | Service health & AI configuration status | No |
| `POST` | `/generate` | Generate AI legal agreement draft | No (Server API Key) |

---

## 1. Root Verification Endpoint

### `GET /`
Used by load balancers, uptime monitors, or developers to verify that the backend API is live and serving traffic.

#### Request Example
```http
GET / HTTP/1.1
Host: localhost:8000
Accept: application/json
```

#### Response Example
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "LegalEase AI API is running"
}
```

---

## 2. Health & Diagnostics Endpoint

### `GET /health`
Returns the status of the service, the active Gemini model configuration, and verifies whether the Gemini API key has been configured.

#### Request Example
```http
GET /health HTTP/1.1
Host: localhost:8000
Accept: application/json
```

#### Response Example
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "model_configured": "gemini-2.5-flash",
  "api_key_configured": true
}
```

---

## 3. Generate Legal Document Endpoint

### `POST /generate`
Accepts contract parameters, performs semantic validation, calls Google Gemini, and returns sanitized legal text.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Payload Specification
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `document_type` | `string` | **Yes** | Category of agreement (e.g. Employment Contract, Non-Disclosure Agreement). |
| `parties` | `string` | **Yes** | Description of all parties, including roles, legal capacity, and addresses. |
| `terms` | `array` or `string` | **Yes** | List of terms or semicolon-separated clauses defining obligations and payments. |
| `agreement_date` | `string` | **Yes** | Date of agreement signing (YYYY-MM-DD or human-readable format). |
| `effective_date` | `string` | **Yes** | Date when terms become active (YYYY-MM-DD or human-readable format). |
| `start_date` | `string` | No | Optional beginning date of term. |
| `end_date` | `string` | No | Optional end date of term. Must be on or after `start_date`. |

#### Request Example
```json
POST /generate HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "document_type": "Employment Contract",
  "parties": "Employer: ABC Technologies Pvt. Ltd.\nEmployee: Jane Doe",
  "terms": [
    "Monthly compensation: ₹50,000",
    "Working hours: 9 AM to 6 PM Monday through Friday",
    "Notice period: 30 calendar days written notice",
    "Confidentiality: Strict non-disclosure of proprietary software code"
  ],
  "agreement_date": "2026-10-03",
  "effective_date": "2026-10-05",
  "start_date": "2026-10-05",
  "end_date": "2027-10-04"
}
```

#### Successful Response Example (`HTTP 200 OK`)
```json
{
  "success": true,
  "document_type": "Employment Contract",
  "content": "# EMPLOYMENT CONTRACT\n\nThis Employment Agreement is made and entered into as of October 03, 2026...\n\n1. APPOINTMENT AND DUTIES\nThe Employer agrees to employ Jane Doe in the capacity of Senior Software Engineer...\n\n2. COMPENSATION AND BENEFITS\nThe Employee shall receive a monthly gross compensation of ₹50,000...\n\n3. NOTICE AND TERMINATION\nEither party may terminate employment by providing thirty (30) calendar days prior written notice...\n\nIN WITNESS WHEREOF, the parties have executed this Agreement.",
  "error": null,
  "terms_count": 4
}
```

#### Validation Error Example (`HTTP 422 Unprocessable Entity`)
Returned when required fields are missing or date constraints are violated (e.g. `end_date` before `start_date`):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, End date (2026-05-01) cannot be before start date (2026-10-05).",
      "input": { ... }
    }
  ]
}
```

#### Upstream Error Example (`HTTP 502 Bad Gateway` / `HTTP 500`)
Returned when the Gemini API key is missing or invalid:
```json
{
  "success": false,
  "error": "Google Gemini API key is missing. Please set GEMINI_API_KEY in your .env file.",
  "document_type": ""
}
```
