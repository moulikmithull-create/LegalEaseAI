# LegalEase AI - Quality Assurance & Testing Guide

## Overview
LegalEase AI includes a comprehensive test suite (`tests/`) containing 19 automated test cases covering API routing, schema validation, domain business logic, Gemini AI mocking, sanitization, and multi-format document exporting (TXT, DOCX, and PDF).

---

## 1. Running the Automated Test Suite

To run all automated unit and integration tests:
```powershell
pytest -v
```

### Verified Test Results Summary:
```text
tests/test_document_generation.py::test_sanitize_text PASSED             [  5%]
tests/test_document_generation.py::test_parse_terms_to_table_data PASSED [ 10%]
tests/test_document_generation.py::test_txt_export PASSED                [ 15%]
tests/test_document_generation.py::test_docx_export PASSED               [ 21%]
tests/test_document_generation.py::test_pdf_export PASSED                [ 26%]
tests/test_document_generation.py::test_html_preview_formatting PASSED   [ 31%]
tests/test_generate.py::test_generate_endpoint_success PASSED            [ 36%]
tests/test_generate.py::test_generate_endpoint_missing_fields PASSED     [ 42%]
tests/test_generate.py::test_generate_endpoint_ai_failure PASSED         [ 47%]
tests/test_generate.py::test_generate_endpoint_missing_api_key PASSED    [ 52%]
tests/test_health.py::test_root_endpoint PASSED                          [ 57%]
tests/test_health.py::test_health_endpoint PASSED                        [ 63%]
tests/test_validation.py::test_valid_document_request PASSED             [ 68%]
tests/test_validation.py::test_semicolon_string_terms_parsing PASSED     [ 73%]
tests/test_validation.py::test_missing_document_type PASSED              [ 78%]
tests/test_validation.py::test_missing_parties PASSED                    [ 84%]
tests/test_validation.py::test_invalid_date_order PASSED                 [ 89%]
tests/test_validation.py::test_validate_document_input_helper PASSED     [ 94%]
tests/test_validation.py::test_validate_logo_file PASSED                 [100%]

======================== 19 passed, 1 warning in 1.21s ========================
```

---

## 2. Test Cases Specification

### API Gateway Tests (`tests/test_health.py` & `tests/test_generate.py`)
| Test ID | Test Name | Purpose | Expected Result |
| :--- | :--- | :--- | :--- |
| `TC-API-01` | `test_root_endpoint` | Verifies `GET /` connectivity | Status 200, message `"LegalEase AI API is running"` |
| `TC-API-02` | `test_health_endpoint` | Verifies `GET /health` diagnostics | Status 200, status `"healthy"`, model & API key flags |
| `TC-API-03` | `test_generate_endpoint_success` | Valid `POST /generate` payload with mocked AI | Status 200, `"success": true`, document content returned |
| `TC-API-04` | `test_generate_endpoint_missing_fields` | Payload with missing required fields | Status 422 Unprocessable Entity |
| `TC-API-05` | `test_generate_endpoint_ai_failure` | Simulates upstream Gemini failure | Status 502, friendly error message, no stack trace |
| `TC-API-06` | `test_generate_endpoint_missing_api_key` | Simulates absent `GEMINI_API_KEY` | Status 500, prompt to configure API key in `.env` |

### Validation Tests (`tests/test_validation.py`)
| Test ID | Test Name | Purpose | Expected Result |
| :--- | :--- | :--- | :--- |
| `TC-VAL-01` | `test_valid_document_request` | Standard full payload validation | Passes Pydantic validation cleanly |
| `TC-VAL-02` | `test_semicolon_string_terms_parsing` | Semicolon string parsed into list | List of 3 strings generated |
| `TC-VAL-03` | `test_missing_document_type` | Empty `document_type` | `ValidationError` raised |
| `TC-VAL-04` | `test_missing_parties` | Empty `parties` | `ValidationError` raised |
| `TC-VAL-05` | `test_invalid_date_order` | `end_date` set earlier than `start_date` | `ValidationError` raised with explicit message |
| `TC-VAL-06` | `test_validate_logo_file` | Corrupted / non-image bytes | Validation fails gracefully |

### Document Formatting & Export Tests (`tests/test_document_generation.py`)
| Test ID | Test Name | Purpose | Expected Result |
| :--- | :--- | :--- | :--- |
| `TC-DOC-01` | `test_sanitize_text` | Strips markdown fences & normalizes quotes | Clean ASCII text, quotes normalized |
| `TC-DOC-02` | `test_parse_terms_to_table_data` | Parses clauses into table pairs | Generates 4 `(Term, Details)` tuples |
| `TC-DOC-03` | `test_txt_export` | Exports UTF-8 plain text bytes | Valid bytes, contains title, terms, disclaimer |
| `TC-DOC-04` | `test_docx_export` | Exports Word `.docx` binary | Valid `.docx` binary starting with `PK\x03\x04` |
| `TC-DOC-05` | `test_pdf_export` | Exports ReportLab `.pdf` binary | Valid `.pdf` binary starting with `%PDF-` |
| `TC-DOC-06` | `test_html_preview_formatting` | Renders styled HTML card & table | Contains container div and Schedule A table |

---

## 3. Manual End-to-End Test Plan

To manually test the complete user experience:
1. Start the backend: `uvicorn backend.main:app --port 8000`
2. Start the frontend: `streamlit run frontend/app.py`
3. In your browser at `http://localhost:8501`:
   - Verify sidebar displays **● Backend Connected**
   - Select **Employment Contract**
   - Verify default parties and terms
   - Select dates and click **Generate Legal Document**
   - Confirm generated text renders in the dark-themed preview card
   - Click **Click to Edit Document**, modify a term, and click **Save Changes**
   - Click **Download as .TXT**, **Download as .DOCX**, and **Download as .PDF**
   - Open downloaded files and verify formatting, logos, terms table, and footers
