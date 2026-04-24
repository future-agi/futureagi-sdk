# Plan: Verify futureagi-sdk camelCase-to-snake_case API Conversion

## Context

PR #22 in `futureagi-sdk` (`feature/removing-camelcase-middleeware` branch) converts all API payload/response field names from camelCase to snake_case across Python and TypeScript SDKs. We need to verify every affected API endpoint actually works end-to-end against a local core-backend server that has already been updated to return snake_case.

**Note:** The simulate-sdk is unrelated (it's for voice AI agent testing via LiveKit). This plan covers only the futureagi-sdk + core-backend verification.

---

## Step 1: Start the Core-Backend Local Server

```bash
cd /Users/apple/future-agi/core-backend

# Ensure .env exists and is configured
cp .env.example .env   # if not already done

# Start all services (PostgreSQL, ClickHouse, Redis, RabbitMQ, Temporal, etc.)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Verify server is running
curl http://localhost:8000/healthcheck
```

**Key config in .env:**
- `ENV_TYPE=local`
- `BACKEND_PORT=8000`
- `ENABLE_HTTP=true`

Server will be available at `http://localhost:8000`.

---

## Step 2: Set Up the futureagi-sdk Environment

### Python SDK
```bash
cd /Users/apple/future-agi/futureagi-sdk
git checkout feature/removing-camelcase-middleeware

cd python
pip install poetry   # if not installed
poetry install

# Set environment variables pointing to local server
export FI_API_KEY="<local-dev-api-key>"
export FI_SECRET_KEY="<local-dev-secret-key>"
export FI_BASE_URL="http://localhost:8000"
```

### TypeScript SDK
```bash
cd /Users/apple/future-agi/futureagi-sdk/typescript/futureagi
pnpm install
pnpm build

# Same env vars
export FI_API_KEY="<local-dev-api-key>"
export FI_SECRET_KEY="<local-dev-secret-key>"
export FI_BASE_URL="http://localhost:8000"
```

---

## Step 3: Run Existing Unit Tests (Sanity Check)

These use mocks, so they verify the SDK code itself is internally consistent.

### Python
```bash
cd /Users/apple/future-agi/futureagi-sdk/python
pytest tests/ -v
```

### TypeScript
```bash
cd /Users/apple/future-agi/futureagi-sdk/typescript/futureagi
pnpm test
```

**Expected:** All tests pass. If any fail, the snake_case conversion has broken something in the SDK logic before we even hit the server.

---

## Step 4: Run Integration Tests Against Local Server

### TypeScript (has existing integration tests)
```bash
cd /Users/apple/future-agi/futureagi-sdk/typescript/futureagi
FI_API_KEY="<key>" FI_SECRET_KEY="<secret>" FI_BASE_URL="http://localhost:8000" pnpm test -- --testPathPattern="integration"
```

### Python (run example scripts)
```bash
cd /Users/apple/future-agi/futureagi-sdk/python
FI_BASE_URL="http://localhost:8000" python examples/datasets.py
```

---

## Step 5: Write and Run Manual API Verification Script

Create a Python verification script that hits every affected API route and validates the response fields are in snake_case.

**File:** `python/tests/verify_snake_case.py`

### APIs to verify (grouped by module):

#### A. Dataset APIs (6 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 1 | `model-hub/develops/get-datasets-names/` | GET | Response fields: `dataset_id`, `model_type` |
| 2 | `model-hub/develops/create-empty-dataset/` | POST | Response fields: `dataset_id`, `dataset_name`, `dataset_model_type` |
| 3 | `model-hub/develops/{id}/get-dataset-table/` | GET | Response fields: `data_type`, `origin_type`, `source_id`, `is_frozen`, `is_visible`, `eval_tag`, `average_score`, `order_index`, `row_id`, `cell_value`, `value_infos`, `failure_reason`, `column_id`, `total_pages` |
| 4 | `model-hub/develops/{id}/add_user_eval/` | POST | Request: `save_as_template`, `reason_column`. Response: `eval_id`, `required_keys` |
| 5 | `model-hub/dataset/{id}/eval-stats/` | GET | Response: eval config fields in snake_case |
| 6 | `sdk/api/v1/get-evals/` | GET | Response: `eval_id` |

#### B. Prompt APIs (7 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 7 | `model-hub/prompt-templates/create-draft/` | POST | Response: `template_version` / `created_version` |
| 8 | `model-hub/prompt-templates/` | GET | Response: `prompt_config`, `variable_names`, `is_default`, `evaluation_configs`, `error_message` |
| 9 | `model-hub/prompt-templates/{id}/` | GET | Response: `model_name`, `frequency_penalty`, `presence_penalty`, `max_tokens`, `top_p`, `response_format`, `tool_choice` |
| 10 | `model-hub/prompt-templates/{id}/add-new-draft/` | POST | Response: `template_version` |
| 11 | `model-hub/prompt-history-executions/` | GET | Response: `template_version`, `is_draft` |
| 12 | `model-hub/prompt-templates/{id}/commit/` | POST | Response: version fields in snake_case |
| 13 | Error responses on any prompt endpoint | ALL | Error field: `error_code` |

#### C. Prompt Label APIs (3 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 14 | `model-hub/prompt-labels/{t_id}/{l_id}/assign-label-by-id/` | POST | Response: `version_id`, `execution_id` |
| 15 | `model-hub/prompt-labels/remove/` | POST | Response: same as above |
| 16 | `model-hub/prompt-labels/set-default/` | POST | Response: label fields in snake_case |

#### D. Knowledge Base APIs (3 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 17 | `model-hub/knowledge-base/` | POST | Response: `kb_id`, `kb_name`, `file_ids`, `not_uploaded` |
| 18 | `model-hub/knowledge-base/` | PATCH | Response: same as above |
| 19 | `model-hub/knowledge-base/files/` | GET | Response: `table_data` |

#### E. Annotation APIs (1 route)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 20 | `tracer/bulk-annotation/` | POST | Response: `annotations_created`, `annotations_updated`, `notes_created`, `succeeded_count`, `errors_count`, `warnings_count` |

#### F. Annotation Queue APIs (7 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 21 | `model-hub/annotation-queues/` | GET/POST | Response: `assignment_strategy`, `annotations_required`, `reservation_timeout_minutes`, `requires_review`, `created_at`, `item_count`, `completed_count` |
| 22 | `model-hub/annotation-queues/{id}/` | GET/PATCH | Response: same as above |
| 23 | `model-hub/annotation-queues/{id}/progress/` | GET | Response: `in_progress`, `progress_pct`, `annotator_stats` |
| 24 | `model-hub/annotation-queues/{id}/analytics/` | GET | Response: `annotator_performance`, `label_distribution`, `status_breakdown` |
| 25 | `model-hub/annotation-queues/{id}/agreement/` | GET | Response: `overall_agreement`, `per_label`, `annotator_pairs` |
| 26 | `model-hub/annotation-queues/{id}/export-to-dataset/` | POST | Response: `dataset_id`, `dataset_name`, `rows_created` |

#### G. Scores APIs (2 routes)
| # | Route | Method | What to test |
|---|-------|--------|-------------|
| 27 | `model-hub/scores/` | POST | Response: `label_id`, `label_name`, `score_source`, `annotator_id`, `annotator_name`, `source_type`, `source_id`, `created_at` |
| 28 | `model-hub/scores/for-source/` | GET | Response: same as above |

### Verification approach per API:

```python
# Pseudocode for each test
def verify_api(endpoint, method, payload=None):
    response = sdk_client.call(endpoint, method, payload)
    
    # 1. Assert HTTP 200/201
    assert response.status_code in (200, 201)
    
    # 2. Assert NO camelCase keys in response JSON
    response_json = response.json()
    camel_case_keys = find_camel_case_keys(response_json)  # recursive check
    assert len(camel_case_keys) == 0, f"Found camelCase keys: {camel_case_keys}"
    
    # 3. Assert expected snake_case keys ARE present
    for expected_key in expected_keys:
        assert expected_key in response_json
    
    # 4. Assert SDK model deserialization works (Pydantic/TS types)
    model = SdkModel(**response_json)  # Should not throw
```

---

## Step 6: Verify TypeScript SDK Against Same Routes

Run equivalent tests from TypeScript:

```bash
cd /Users/apple/future-agi/futureagi-sdk/typescript/futureagi

# Run all tests including integration
FI_BASE_URL="http://localhost:8000" pnpm test
```

Additionally, create a quick TypeScript verification script if integration tests don't cover all routes.

---

## Step 7: Cleanup and Report

1. Collect pass/fail results for all 28 API routes
2. For any failures:
   - Check if the backend is still returning camelCase for that endpoint
   - Check if the SDK is reading the wrong key
   - Fix and re-test
3. Stop the local server: `docker compose down`

---

## Critical Files

| File | Purpose |
|------|---------|
| `futureagi-sdk/python/fi/datasets/dataset.py` | Dataset API client |
| `futureagi-sdk/python/fi/prompt/client.py` | Prompt API client |
| `futureagi-sdk/python/fi/prompt/label_management.py` | Prompt label API client |
| `futureagi-sdk/python/fi/kb/client.py` | Knowledge Base API client |
| `futureagi-sdk/python/fi/annotations/annotation.py` | Annotation API client |
| `futureagi-sdk/python/fi/annotations/types.py` | Annotation Pydantic models (fixed) |
| `futureagi-sdk/python/fi/queues/types.py` | Queue Pydantic models (fixed) |
| `futureagi-sdk/python/fi/queues/client.py` | Queue API client (Python) |
| `futureagi-sdk/typescript/futureagi/src/queues/client.ts` | Queue API client (TS) |
| `futureagi-sdk/python/fi/utils/routes.py` | All Python API route definitions |
| `futureagi-sdk/typescript/futureagi/src/utils/routes.ts` | All TypeScript API route definitions |
| `core-backend/docker-compose.yml` | Local server setup |
| `core-backend/.env` | Local server config |

---

## Success Criteria

- All 28 API routes return snake_case field names (no camelCase)
- All Python Pydantic models deserialize without errors
- All TypeScript type interfaces match the response shape
- Both Python and TypeScript unit tests pass
- Integration tests pass against local server
- No silent None/undefined values where real data is expected
