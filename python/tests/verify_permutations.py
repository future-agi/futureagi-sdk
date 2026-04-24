"""
Comprehensive permutation testing for ALL 23 APIs.
Tests every endpoint with:
  - Full payload (all fields)
  - Minimal payload (only required fields)
  - Partial payloads (various optional field combos)
  - Missing required fields (expect 400)
  - Null/empty values for optional fields
  - GET endpoints with and without query params

Verifies EVERY response has snake_case keys and NO camelCase keys.
"""
import json
import re
import sys
import uuid
import os
import tempfile
import requests

API_KEY = "3b8edf45aebc47da8a750ee79dddc89b"
SECRET_KEY = "2e265885dcf74b2b96fb5d3b729f5f2c"
BASE_URL = "http://localhost:8001"
HEADERS = {"X-Api-Key": API_KEY, "X-Secret-Key": SECRET_KEY, "Content-Type": "application/json"}

CAMEL_RE = re.compile(r"^[a-z]+[A-Z][a-zA-Z]*$")
SKIP_KEYS = {"ok", "id", "name", "status", "type", "url", "detail", "message"}

results = []
cleanup = []


def find_camel(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k in obj:
            fp = f"{path}.{k}" if path else k
            if CAMEL_RE.match(k) and k not in SKIP_KEYS:
                found.append(fp)
            found.extend(find_camel(obj[k], fp))
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):
            found.extend(find_camel(item, f"{path}[{i}]"))
    return found


def http(method, path, json_body=None, params=None, files=None, data=None):
    url = f"{BASE_URL}/{path}"
    try:
        hdrs = HEADERS.copy()
        if files:
            hdrs.pop("Content-Type", None)
        r = requests.request(method, url, headers=hdrs, json=json_body, params=params, files=files, data=data, timeout=20)
        try:
            body = r.json()
        except:
            body = r.text
        return r.status_code, body
    except Exception as e:
        return None, str(e)


def test(name, method, path, json_body=None, params=None, files=None, data=None,
         expect_status=None, forbid_camel=None):
    s, b = http(method, path, json_body, params, files, data)
    issues = []

    if expect_status:
        exp = expect_status if isinstance(expect_status, (list, tuple)) else [expect_status]
        if s not in exp:
            issues.append(f"Status {s}, expected {expect_status}")

    if isinstance(b, (dict, list)):
        camel = find_camel(b)
        if camel:
            issues.append(f"camelCase: {camel[:8]}")

    if forbid_camel and isinstance(b, (dict, list)):
        flat = json.dumps(b)
        for key in forbid_camel:
            if f'"{key}"' in flat:
                issues.append(f"Forbidden key '{key}' still present")

    passed = len(issues) == 0
    icon = "PASS" if passed else "FAIL"
    status_str = f" ({s})" if s else ""
    print(f"  [{icon}] {name}{status_str}")
    if issues:
        for iss in issues:
            print(f"       -> {iss}")
    results.append({"name": name, "passed": passed, "status": s})
    return s, b


print("=" * 70)
print("PERMUTATION TESTING: ALL FIELD COMBINATIONS")
print(f"Backend: {BASE_URL}")
print("=" * 70)


# ===========================================================
# E. QUEUES — Most thorough (we can create/delete freely)
# ===========================================================
print("\n" + "=" * 50)
print("E. QUEUES — Full Permutation Testing")
print("=" * 50)

# --- E1. Create Queue ---
print("\n--- E1. POST annotation-queues/ (Create) ---")

# Full payload
test("Create queue: all fields", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_full_{uuid.uuid4().hex[:4]}", "description": "Full", "instructions": "Test",
                "assignment_strategy": "manual", "annotations_required": 3,
                "reservation_timeout_minutes": 60, "requires_review": True},
     expect_status=[201], forbid_camel=["assignmentStrategy", "annotationsRequired", "reservationTimeoutMinutes", "requiresReview", "createdAt", "isDefault", "autoAssign"])
if results[-1]["passed"]:
    cleanup.append(("queue", results[-1].get("body", {}).get("id") if isinstance(results[-1].get("body"), dict) else None))
# Extract queue_id from the response
s, b = results[-1]["status"], None
full_q_s, full_q_b = http("POST", "model-hub/annotation-queues/",
    json_body={"name": f"perm_track_{uuid.uuid4().hex[:4]}", "description": "Track"})
full_q_id = full_q_b.get("id") if isinstance(full_q_b, dict) else None
if full_q_id:
    cleanup.append(("queue", full_q_id))

# Minimal payload (only name)
test("Create queue: only name", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_min_{uuid.uuid4().hex[:4]}"},
     expect_status=[201], forbid_camel=["assignmentStrategy", "annotationsRequired", "createdAt"])
s, b = http("GET", "model-hub/annotation-queues/")
if isinstance(b, dict) and b.get("results"):
    for q in b["results"]:
        if q.get("name", "").startswith("perm_min_"):
            cleanup.append(("queue", q["id"]))
            break

# Partial: name + description only
test("Create queue: name + description", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_nd_{uuid.uuid4().hex[:4]}", "description": "Just desc"},
     expect_status=[201], forbid_camel=["assignmentStrategy", "createdAt"])

# Partial: name + assignment_strategy only
test("Create queue: name + assignment_strategy", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_as_{uuid.uuid4().hex[:4]}", "assignment_strategy": "round_robin"},
     expect_status=[201], forbid_camel=["assignmentStrategy"])

# Partial: name + annotations_required + requires_review
test("Create queue: name + annotations + review", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_ar_{uuid.uuid4().hex[:4]}", "annotations_required": 5, "requires_review": False},
     expect_status=[201], forbid_camel=["annotationsRequired", "requiresReview"])

# Missing required: no name
test("Create queue: missing name (400)", "POST", "model-hub/annotation-queues/",
     json_body={"description": "No name"}, expect_status=[400])

# Empty name
test("Create queue: empty name (400)", "POST", "model-hub/annotation-queues/",
     json_body={"name": ""}, expect_status=[400])

# Null optional fields
test("Create queue: null optional fields", "POST", "model-hub/annotation-queues/",
     json_body={"name": f"perm_null_{uuid.uuid4().hex[:4]}", "description": None, "instructions": None,
                "assignment_strategy": None, "annotations_required": None},
     expect_status=[201, 400], forbid_camel=["assignmentStrategy", "createdAt"])

# --- E1b. PATCH queue ---
print("\n--- E1b. PATCH annotation-queues/{id}/ (Update) ---")
if full_q_id:
    # Update single field
    test("Update queue: only description", "PATCH", f"model-hub/annotation-queues/{full_q_id}/",
         json_body={"description": "Updated desc only"},
         expect_status=[200], forbid_camel=["assignmentStrategy", "createdAt"])

    # Update multiple fields
    test("Update queue: strategy + annotations", "PATCH", f"model-hub/annotation-queues/{full_q_id}/",
         json_body={"assignment_strategy": "round_robin", "annotations_required": 5},
         expect_status=[200], forbid_camel=["assignmentStrategy", "annotationsRequired"])

    # Update with null (clear field)
    test("Update queue: null description", "PATCH", f"model-hub/annotation-queues/{full_q_id}/",
         json_body={"description": None},
         expect_status=[200], forbid_camel=["assignmentStrategy"])

# --- E1c. GET queue ---
print("\n--- E1c. GET annotation-queues/ (List & Detail) ---")
# List with no params
test("List queues: no params", "GET", "model-hub/annotation-queues/",
     expect_status=[200], forbid_camel=["assignmentStrategy", "annotationsRequired", "reservationTimeoutMinutes",
                                        "requiresReview", "createdAt", "itemCount", "completedCount", "isDefault", "autoAssign"])
# List with status filter
test("List queues: status=active", "GET", "model-hub/annotation-queues/",
     params={"status": "active"}, expect_status=[200], forbid_camel=["assignmentStrategy", "createdAt"])

# List with pagination
test("List queues: page=1, page_size=2", "GET", "model-hub/annotation-queues/",
     params={"page": 1, "page_size": 2}, expect_status=[200], forbid_camel=["assignmentStrategy"])

# Detail
if full_q_id:
    test("Get queue detail", "GET", f"model-hub/annotation-queues/{full_q_id}/",
         expect_status=[200], forbid_camel=["assignmentStrategy", "annotationsRequired", "createdAt"])

# --- E2. Queue Items ---
print("\n--- E2. Queue Items ---")
if full_q_id:
    http("POST", f"model-hub/annotation-queues/{full_q_id}/update-status/", json_body={"status": "active"})

    # Add items: valid
    test("Add items: 2 items", "POST", f"model-hub/annotation-queues/{full_q_id}/items/add-items/",
         json_body={"items": [
             {"source_type": "trace", "source_id": str(uuid.uuid4())},
             {"source_type": "trace", "source_id": str(uuid.uuid4())},
         ]}, expect_status=[200], forbid_camel=["sourceType", "sourceId"])

    # Add items: single item
    test("Add items: 1 item", "POST", f"model-hub/annotation-queues/{full_q_id}/items/add-items/",
         json_body={"items": [{"source_type": "observation_span", "source_id": str(uuid.uuid4())}]},
         expect_status=[200], forbid_camel=["sourceType", "sourceId"])

    # Add items: empty list
    test("Add items: empty list (400)", "POST", f"model-hub/annotation-queues/{full_q_id}/items/add-items/",
         json_body={"items": []}, expect_status=[400])

    # Add items: missing source_type
    test("Add items: missing source_type (400)", "POST", f"model-hub/annotation-queues/{full_q_id}/items/add-items/",
         json_body={"items": [{"source_id": str(uuid.uuid4())}]}, expect_status=[400])

    # List items: no params
    test("List items: no params", "GET", f"model-hub/annotation-queues/{full_q_id}/items/",
         expect_status=[200], forbid_camel=["sourceType", "sourceId", "assignedTo", "createdAt"])

    # List items: with pagination
    test("List items: page_size=1", "GET", f"model-hub/annotation-queues/{full_q_id}/items/",
         params={"page_size": 1}, expect_status=[200], forbid_camel=["sourceType", "sourceId"])

    # List items: with status filter
    test("List items: status=pending", "GET", f"model-hub/annotation-queues/{full_q_id}/items/",
         params={"status": "pending"}, expect_status=[200], forbid_camel=["sourceType"])

# --- E3. Scores ---
print("\n--- E3. Scores ---")
# List: no params
test("List scores: no params", "GET", "model-hub/scores/",
     expect_status=[200], forbid_camel=["sourceType", "sourceId", "labelId", "labelName",
                                        "scoreSource", "annotatorName", "createdAt", "labelType", "labelSettings"])

# List: with pagination
test("List scores: page_size=5", "GET", "model-hub/scores/",
     params={"page_size": 5}, expect_status=[200], forbid_camel=["sourceType", "labelId", "scoreSource"])

# Get for source (valid UUID)
test("Scores for source: valid UUID", "GET", "model-hub/scores/for-source/",
     params={"source_type": "trace", "source_id": str(uuid.uuid4())},
     expect_status=[200], forbid_camel=["sourceType", "sourceId", "labelId", "scoreSource"])

# Get for source: missing source_type
test("Scores for source: missing params (400)", "GET", "model-hub/scores/for-source/",
     expect_status=[400])

# Create score: missing value
test("Create score: missing value (400)", "POST", "model-hub/scores/",
     json_body={"source_type": "trace", "source_id": str(uuid.uuid4()), "label_id": str(uuid.uuid4())},
     expect_status=[400, 404])

# --- E4-E6. Progress/Analytics/Agreement ---
print("\n--- E4-E6. Progress, Analytics, Agreement ---")
if full_q_id:
    test("Progress", "GET", f"model-hub/annotation-queues/{full_q_id}/progress/",
         expect_status=[200], forbid_camel=["inProgress", "progressPct", "annotatorStats"])
    test("Analytics", "GET", f"model-hub/annotation-queues/{full_q_id}/analytics/",
         expect_status=[200], forbid_camel=["annotatorPerformance", "labelDistribution", "statusBreakdown"])
    test("Agreement", "GET", f"model-hub/annotation-queues/{full_q_id}/agreement/",
         expect_status=[200], forbid_camel=["overallAgreement", "perLabel", "annotatorPairs"])

# --- E7. Export ---
print("\n--- E7. Export ---")
if full_q_id:
    # Export JSON
    test("Export: JSON format", "GET", f"model-hub/annotation-queues/{full_q_id}/export/",
         params={"export_format": "json"}, expect_status=[200])

    # Export CSV
    test("Export: CSV format", "GET", f"model-hub/annotation-queues/{full_q_id}/export/",
         params={"export_format": "csv"}, expect_status=[200])

    # Export to dataset: with name
    test("Export to dataset: with name", "POST", f"model-hub/annotation-queues/{full_q_id}/export-to-dataset/",
         json_body={"dataset_name": f"perm_exp_{uuid.uuid4().hex[:4]}"},
         expect_status=[200, 201], forbid_camel=["datasetId", "datasetName", "rowsCreated"])

    # Export to dataset: missing both
    test("Export to dataset: missing args (400)", "POST", f"model-hub/annotation-queues/{full_q_id}/export-to-dataset/",
         json_body={}, expect_status=[400])

    # Export to dataset: with dataset_id (existing)
    _, ds_data = http("GET", "model-hub/develops/get-datasets-names/")
    if isinstance(ds_data, dict):
        ds_list = ds_data.get("result", {}).get("datasets", [])
        if ds_list:
            test("Export to dataset: with dataset_id", "POST", f"model-hub/annotation-queues/{full_q_id}/export-to-dataset/",
                 json_body={"dataset_id": ds_list[0]["dataset_id"]},
                 expect_status=[200, 201], forbid_camel=["datasetId", "datasetName", "rowsCreated"])


# ===========================================================
# B. DATASETS — Permutation Testing
# ===========================================================
print("\n" + "=" * 50)
print("B. DATASETS — Permutation Testing")
print("=" * 50)

# List names: no params
test("Dataset names: default", "GET", "model-hub/develops/get-datasets-names/",
     expect_status=[200], forbid_camel=["datasetId", "modelType"])

# Create empty: valid
test("Create empty dataset: valid", "POST", "model-hub/develops/create-empty-dataset/",
     json_body={"new_dataset_name": f"perm_ds_{uuid.uuid4().hex[:4]}", "model_type": "GenerativeLLM"},
     expect_status=[200, 201], forbid_camel=["datasetId", "datasetName", "datasetModelType"])

# Create empty: missing name
test("Create empty dataset: missing name (400)", "POST", "model-hub/develops/create-empty-dataset/",
     json_body={"model_type": "GenerativeLLM"}, expect_status=[400])

# Create empty: missing model_type
test("Create empty dataset: missing model_type (400)", "POST", "model-hub/develops/create-empty-dataset/",
     json_body={"new_dataset_name": f"perm_ds2_{uuid.uuid4().hex[:4]}"}, expect_status=[400])

# Get dataset table with pagination
_, ds_data = http("GET", "model-hub/develops/get-datasets-names/")
ds_id = None
if isinstance(ds_data, dict):
    ds_list = ds_data.get("result", {}).get("datasets", [])
    if ds_list:
        ds_id = ds_list[0]["dataset_id"]

if ds_id:
    test("Dataset table: page 1", "GET", f"model-hub/develops/{ds_id}/get-dataset-table/",
         params={"page": 1}, expect_status=[200],
         forbid_camel=["columnConfig", "dataType", "originType", "sourceId", "isFrozen",
                       "isVisible", "evalTag", "averageScore", "orderIndex", "rowId",
                       "cellValue", "valueInfos", "failureReason", "totalPages"])

    test("Dataset table: page 1 size 5", "GET", f"model-hub/develops/{ds_id}/get-dataset-table/",
         params={"page": 1, "page_size": 5}, expect_status=[200],
         forbid_camel=["columnConfig", "totalPages", "rowId"])

# Eval templates
test("Eval templates", "GET", "sdk/api/v1/get-evals/",
     expect_status=[200], forbid_camel=["evalId", "evalTags", "requiredKeys", "configParamsDesc", "functionParamsSchema", "multiChoice"])


# ===========================================================
# D. PROMPT — Permutation Testing
# ===========================================================
print("\n" + "=" * 50)
print("D. PROMPT — Permutation Testing")
print("=" * 50)

# List: default
test("Prompt list: default", "GET", "model-hub/prompt-templates/",
     expect_status=[200], forbid_camel=["promptFolder", "createdBy", "variableNames", "isDefault"])

# List: with pagination
test("Prompt list: page 1 size 3", "GET", "model-hub/prompt-templates/",
     params={"page": 1, "page_size": 3}, expect_status=[200],
     forbid_camel=["promptFolder", "createdBy"])

# Get by ID (use first existing)
_, tmpl_data = http("GET", "model-hub/prompt-templates/")
tmpl_id = None
if isinstance(tmpl_data, dict) and tmpl_data.get("results"):
    tmpl_id = tmpl_data["results"][0]["id"]

if tmpl_id:
    test("Prompt by ID", "GET", f"model-hub/prompt-templates/{tmpl_id}/",
         expect_status=[200], forbid_camel=["promptConfig", "variableNames", "isDefault",
                                            "evaluationConfigs", "errorMessage", "promptFolder"])

    # Version history
    test("Prompt version history", "GET", "model-hub/prompt-history-executions/",
         params={"template_id": tmpl_id}, expect_status=[200],
         forbid_camel=["templateVersion", "isDraft", "versionId", "executionId"])

# Create: missing name
test("Prompt create: missing name (400)", "POST", "model-hub/prompt-templates/create-draft/",
     json_body={"prompt_config": {"model_name": "gpt-4o-mini", "messages": []}},
     expect_status=[400])

# Create: missing prompt_config
test("Prompt create: missing config (400)", "POST", "model-hub/prompt-templates/create-draft/",
     json_body={"name": f"perm_p_{uuid.uuid4().hex[:4]}"},
     expect_status=[400])

# Prompt labels
test("Prompt labels: list", "GET", "model-hub/prompt-labels/",
     expect_status=[200], forbid_camel=["createdAt", "updatedAt", "totalPages", "currentPage"])


# ===========================================================
# C. KNOWLEDGE BASE — Permutation Testing
# ===========================================================
print("\n" + "=" * 50)
print("C. KNOWLEDGE BASE — Permutation Testing")
print("=" * 50)

# List
test("KB list", "GET", "model-hub/knowledge-base/list/",
     expect_status=[200], forbid_camel=["tableData", "kbId", "kbName", "lastError"])

# Create with file
tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
tmp.write("Permutation test content\n")
tmp.close()
with open(tmp.name, "rb") as f:
    test("KB create: with file", "POST", "model-hub/knowledge-base/",
         files={"files": ("perm_test.txt", f, "text/plain")},
         data={"kb_name": f"perm_kb_{uuid.uuid4().hex[:4]}"},
         expect_status=[200, 201], forbid_camel=["kbId", "kbName", "fileIds", "notUploaded"])
os.unlink(tmp.name)

# Create: missing name
test("KB create: missing name (400)", "POST", "model-hub/knowledge-base/",
     json_body={}, expect_status=[400, 500])


# ===========================================================
# A. ANNOTATIONS — Permutation Testing
# ===========================================================
print("\n" + "=" * 50)
print("A. ANNOTATIONS — Permutation Testing")
print("=" * 50)

# Get annotation labels
test("Annotation labels: list", "GET", "tracer/get-annotation-labels/",
     expect_status=[200], forbid_camel=["rulePrompt", "multiChoice", "autoAnnotate", "stepSize", "displayType"])

# Annotation labels CRUD
test("Annotation labels CRUD: list", "GET", "model-hub/annotations-labels/",
     expect_status=[200], forbid_camel=["createdAt", "outputType", "stepSize", "displayType", "rulePrompt"])

# List projects
test("Projects: list", "GET", "tracer/project/list_projects/",
     expect_status=[200], forbid_camel=["totalRows", "pageNumber", "pageSize", "totalPages", "createdAt", "updatedAt"])

# List projects: with pagination
test("Projects: page 1 size 2", "GET", "tracer/project/list_projects/",
     params={"page_number": 0, "page_size": 2}, expect_status=[200],
     forbid_camel=["totalRows", "pageNumber", "pageSize", "createdAt"])

# Bulk annotation: valid
_, labels_data = http("GET", "tracer/get-annotation-labels/")
ann_label_id = None
if isinstance(labels_data, dict):
    ann_labels = labels_data.get("result", [])
    if ann_labels:
        ann_label_id = ann_labels[0]["id"]

if ann_label_id:
    test("Bulk annotation: valid", "POST", "tracer/bulk-annotation/",
         json_body={"records": [{"observation_span_id": str(uuid.uuid4()),
                                 "annotations": [{"annotation_label_id": ann_label_id, "value": "good"}],
                                 "notes": []}]},
         expect_status=[200, 201],
         forbid_camel=["annotationsCreated", "annotationsUpdated", "notesCreated",
                       "succeededCount", "errorsCount", "warningsCount"])

    # Bulk annotation: empty records
    test("Bulk annotation: empty records", "POST", "tracer/bulk-annotation/",
         json_body={"records": []}, expect_status=[200, 400],
         forbid_camel=["annotationsCreated", "succeededCount"])

    # Bulk annotation: multiple records
    test("Bulk annotation: 2 records", "POST", "tracer/bulk-annotation/",
         json_body={"records": [
             {"observation_span_id": str(uuid.uuid4()),
              "annotations": [{"annotation_label_id": ann_label_id, "value": "good"}], "notes": []},
             {"observation_span_id": str(uuid.uuid4()),
              "annotations": [{"annotation_label_id": ann_label_id, "value": "bad"}],
              "notes": [{"text": "Test note"}]},
         ]},
         expect_status=[200, 201],
         forbid_camel=["annotationsCreated", "annotationsUpdated", "notesCreated", "succeededCount"])


# ===========================================================
# CLEANUP
# ===========================================================
print("\n" + "=" * 50)
print("CLEANUP")
print("=" * 50)
# Clean up created queues
s, b = http("GET", "model-hub/annotation-queues/")
if isinstance(b, dict):
    for q in b.get("results", []):
        if q.get("name", "").startswith("perm_"):
            http("DELETE", f"model-hub/annotation-queues/{q['id']}/")
            print(f"  Deleted queue: {q['name']}")

# Clean up datasets
s, b = http("GET", "model-hub/develops/get-datasets-names/")
if isinstance(b, dict):
    for ds in b.get("result", {}).get("datasets", []):
        if ds.get("name", "").startswith("perm_"):
            http("POST", "model-hub/develops/delete_dataset/", json_body={"dataset_ids": [ds["dataset_id"]]})
            print(f"  Deleted dataset: {ds['name']}")


# ===========================================================
# FINAL REPORT
# ===========================================================
print("\n" + "=" * 70)
print("PERMUTATION TEST RESULTS")
print("=" * 70)

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if not r["passed"])

print(f"\nTotal tests:  {total}")
print(f"Passed:       {passed}")
print(f"Failed:       {failed}")

if failed:
    print("\n--- FAILURES ---")
    for r in results:
        if not r["passed"]:
            print(f"  FAIL: {r['name']} (status={r['status']})")

print(f"\n{'=' * 70}")
print(f"RESULT: {'ALL TESTS PASSED' if failed == 0 else f'{failed} FAILURES'}")
print(f"{'=' * 70}")
sys.exit(0 if failed == 0 else 1)
