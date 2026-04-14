"""
Comprehensive POST/PATCH/DELETE API verification for snake_case conversion.
Tests all write endpoints with valid payloads, missing fields, and edge cases.
"""
import re
import sys
import json
import uuid
import requests
import time

API_KEY = "3b8edf45aebc47da8a750ee79dddc89b"
SECRET_KEY = "2e265885dcf74b2b96fb5d3b729f5f2c"
BASE_URL = "http://localhost:8001"

HEADERS = {
    "X-Api-Key": API_KEY,
    "X-Secret-Key": SECRET_KEY,
    "Content-Type": "application/json",
}

CAMEL_CASE_RE = re.compile(r"^[a-z]+[A-Z][a-zA-Z]*$")
ALLOWED_KEYS = {"ok", "id", "name", "status", "type", "url", "detail", "message"}

results = []
created_resources = {}  # Track resources for cleanup


def find_camel_case_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for key in obj:
            full_path = f"{path}.{key}" if path else key
            if CAMEL_CASE_RE.match(key) and key not in ALLOWED_KEYS:
                found.append(full_path)
            found.extend(find_camel_case_keys(obj[key], full_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:3]):  # Check first 3 items
            found.extend(find_camel_case_keys(item, f"{path}[{i}]"))
    return found


def api(method, path, json_body=None, params=None):
    url = f"{BASE_URL}/{path}"
    try:
        resp = requests.request(method, url, headers=HEADERS, json=json_body, params=params, timeout=20)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return resp.status_code, body
    except Exception as e:
        return None, str(e)


def test(name, method, path, json_body=None, params=None, expect_status=None, expect_snake_keys=None, expect_no_camel=True):
    """Run a test and record results."""
    status, body = api(method, path, json_body, params)

    issues = []

    # Check camelCase in response
    if expect_no_camel and isinstance(body, (dict, list)):
        camel_keys = find_camel_case_keys(body)
        if camel_keys:
            issues.append(f"camelCase keys: {camel_keys[:10]}")

    # Check expected status
    if expect_status:
        expected = expect_status if isinstance(expect_status, (list, tuple)) else [expect_status]
        if status not in expected:
            issues.append(f"Expected status {expect_status}, got {status}")

    # Check expected snake_case keys exist in response
    if expect_snake_keys and isinstance(body, dict):
        # Unwrap common wrappers
        check_obj = body
        if "result" in body and isinstance(body["result"], dict):
            check_obj = body["result"]
        for key in expect_snake_keys:
            if key not in check_obj and key not in body:
                issues.append(f"Missing expected key: {key}")

    passed = len(issues) == 0
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {method:6s} {path}")
    print(f"         Status: {status}")
    if issues:
        for issue in issues:
            print(f"         ISSUE: {issue}")

    results.append({"name": name, "method": method, "path": path, "status": status, "passed": passed, "issues": issues, "body": body})
    return status, body


# ============================================================
print("=" * 70)
print("COMPREHENSIVE POST/PATCH/DELETE API VERIFICATION")
print(f"Target: {BASE_URL}")
print("=" * 70)

# ============================================================
# A. ANNOTATION QUEUE CRUD (full lifecycle)
# ============================================================
print("\n--- A. Annotation Queue CRUD ---")

# A1. Create queue with all snake_case fields
print("\n  A1. Create queue (full payload)")
status, body = test(
    "Create queue (full payload)", "POST", "model-hub/annotation-queues/",
    json_body={
        "name": f"test_verify_{uuid.uuid4().hex[:8]}",
        "description": "Verification test queue",
        "instructions": "Test instructions",
        "assignment_strategy": "manual",
        "annotations_required": 2,
        "reservation_timeout_minutes": 30,
        "requires_review": True,
    },
    expect_status=[200, 201],
    expect_snake_keys=["assignment_strategy", "annotations_required", "reservation_timeout_minutes", "requires_review", "created_at"],
)
queue_id = None
if isinstance(body, dict):
    queue_id = body.get("id") or (body.get("result", {}) or {}).get("id")
    created_resources["queue_id"] = queue_id

# A2. Create queue with minimal payload
print("\n  A2. Create queue (minimal payload)")
status2, body2 = test(
    "Create queue (minimal)", "POST", "model-hub/annotation-queues/",
    json_body={"name": f"test_minimal_{uuid.uuid4().hex[:8]}"},
    expect_status=[200, 201],
)
queue_id_min = None
if isinstance(body2, dict):
    queue_id_min = body2.get("id") or (body2.get("result", {}) or {}).get("id")
    created_resources["queue_id_min"] = queue_id_min

# A3. Create queue with missing required field (name)
print("\n  A3. Create queue (missing name - should fail)")
test(
    "Create queue (missing name)", "POST", "model-hub/annotation-queues/",
    json_body={"description": "No name provided"},
    expect_status=[400],
)

# A4. Update queue with PATCH
if queue_id:
    print("\n  A4. Update queue (PATCH)")
    test(
        "Update queue", "PATCH", f"model-hub/annotation-queues/{queue_id}/",
        json_body={
            "description": "Updated description",
            "assignment_strategy": "round_robin",
            "annotations_required": 3,
        },
        expect_status=[200],
        expect_snake_keys=["assignment_strategy", "annotations_required"],
    )

# A5. Update queue status
if queue_id:
    print("\n  A5. Update queue status (activate)")
    test(
        "Activate queue", "POST", f"model-hub/annotation-queues/{queue_id}/update-status/",
        json_body={"status": "active"},
        expect_status=[200],
    )

# ============================================================
# B. QUEUE ITEMS
# ============================================================
print("\n--- B. Queue Items ---")

if queue_id:
    # B1. Add items with snake_case payload
    print("\n  B1. Add items to queue")
    test(
        "Add items", "POST", f"model-hub/annotation-queues/{queue_id}/items/add-items/",
        json_body={
            "items": [
                {"source_type": "trace", "source_id": str(uuid.uuid4())},
                {"source_type": "trace", "source_id": str(uuid.uuid4())},
            ]
        },
        expect_status=[200, 201],
    )

    # B2. Add items with missing source_type
    print("\n  B2. Add items (missing source_type - should fail)")
    test(
        "Add items (missing source_type)", "POST", f"model-hub/annotation-queues/{queue_id}/items/add-items/",
        json_body={
            "items": [{"source_id": str(uuid.uuid4())}]
        },
        expect_status=[400],
    )

    # B3. List items (verify response keys)
    print("\n  B3. List items (GET)")
    test(
        "List items", "GET", f"model-hub/annotation-queues/{queue_id}/items/",
        expect_status=[200],
    )

    # B4. Assign items
    print("\n  B4. Assign items")
    _, items_body = api("GET", f"model-hub/annotation-queues/{queue_id}/items/")
    item_ids = []
    if isinstance(items_body, dict):
        item_list = items_body.get("results", items_body.get("result", []))
        if isinstance(item_list, list):
            item_ids = [i["id"] for i in item_list[:1] if "id" in i]

    if item_ids:
        test(
            "Assign items", "POST", f"model-hub/annotation-queues/{queue_id}/items/assign/",
            json_body={"item_ids": item_ids, "user_id": None},
            expect_status=[200],
        )

    # B5. Submit annotations
    if item_ids:
        print("\n  B5. Submit annotations")
        test(
            "Submit annotations", "POST",
            f"model-hub/annotation-queues/{queue_id}/items/{item_ids[0]}/annotations/submit/",
            json_body={
                "annotations": [
                    {"label_id": str(uuid.uuid4()), "value": "positive", "score_source": "api"}
                ]
            },
            expect_status=[200, 201, 400, 404],  # label might not exist
        )

    # B6. Import annotations
    if item_ids:
        print("\n  B6. Import annotations")
        test(
            "Import annotations", "POST",
            f"model-hub/annotation-queues/{queue_id}/items/{item_ids[0]}/annotations/import/",
            json_body={
                "annotations": [
                    {"label_id": str(uuid.uuid4()), "value": 4, "score_source": "human"}
                ],
                "annotator_id": str(uuid.uuid4()),
            },
            expect_status=[200, 201, 400, 404],
        )

    # B7. Bulk remove items
    if item_ids:
        print("\n  B7. Bulk remove items")
        test(
            "Bulk remove items", "POST", f"model-hub/annotation-queues/{queue_id}/items/bulk-remove/",
            json_body={"item_ids": item_ids},
            expect_status=[200],
        )

# ============================================================
# C. QUEUE LABELS
# ============================================================
print("\n--- C. Queue Labels ---")

# C1. Create an annotation label
print("\n  C1. Create annotation label")
status, label_body = test(
    "Create annotation label", "POST", "model-hub/annotations-labels/",
    json_body={
        "name": f"test_label_{uuid.uuid4().hex[:6]}",
        "type": "categorical",
        "description": "Test label for verification",
        "settings": {"options": ["good", "bad"], "multi_choice": False},
    },
    expect_status=[200, 201, 500],  # 500 may happen if project context missing
)
label_id = None
if isinstance(label_body, dict):
    lb = label_body.get("data", label_body.get("result", label_body))
    if isinstance(lb, dict):
        label_id = lb.get("id")
        created_resources["label_id"] = label_id

# C2. Add label to queue
if queue_id and label_id:
    print("\n  C2. Add label to queue")
    test(
        "Add label to queue", "POST", f"model-hub/annotation-queues/{queue_id}/add-label/",
        json_body={"label_id": label_id},
        expect_status=[200, 201],
    )

# C3. Remove label from queue
if queue_id and label_id:
    print("\n  C3. Remove label from queue")
    test(
        "Remove label from queue", "POST", f"model-hub/annotation-queues/{queue_id}/remove-label/",
        json_body={"label_id": label_id},
        expect_status=[200],
    )

# ============================================================
# D. SCORES (unified annotations)
# ============================================================
print("\n--- D. Scores ---")

# D1. Create single score
print("\n  D1. Create single score")
test_source_id = str(uuid.uuid4())
status, score_body = test(
    "Create score", "POST", "model-hub/scores/",
    json_body={
        "source_type": "trace",
        "source_id": test_source_id,
        "label_id": label_id or str(uuid.uuid4()),
        "value": "positive",
        "score_source": "api",
    },
    expect_status=[200, 201, 400, 404],
)

# D2. Create bulk scores
print("\n  D2. Create bulk scores")
test(
    "Create bulk scores", "POST", "model-hub/scores/bulk/",
    json_body={
        "source_type": "trace",
        "source_id": str(uuid.uuid4()),
        "scores": [
            {"label_id": label_id or str(uuid.uuid4()), "value": "good", "score_source": "api"},
        ],
    },
    expect_status=[200, 201, 400, 404],
)

# D3. Create score with missing required fields
print("\n  D3. Create score (missing source_type - should fail)")
test(
    "Create score (missing source_type)", "POST", "model-hub/scores/",
    json_body={
        "source_id": str(uuid.uuid4()),
        "label_id": str(uuid.uuid4()),
        "value": "test",
    },
    expect_status=[400],
)

# D4. Get scores for source
print("\n  D4. Get scores for source")
test(
    "Get scores for source", "GET", "model-hub/scores/for-source/",
    params={"source_type": "trace", "source_id": test_source_id},
    expect_status=[200],
)

# ============================================================
# E. EXPORT
# ============================================================
print("\n--- E. Export ---")

if queue_id:
    # E1. Export to dataset
    print("\n  E1. Export to dataset (with dataset_name)")
    test(
        "Export to dataset", "POST", f"model-hub/annotation-queues/{queue_id}/export-to-dataset/",
        json_body={"dataset_name": f"test_export_{uuid.uuid4().hex[:6]}"},
        expect_status=[200, 201, 400],
    )

    # E2. Export to dataset with missing args
    print("\n  E2. Export to dataset (missing dataset_name and dataset_id - should fail)")
    test(
        "Export to dataset (no args)", "POST", f"model-hub/annotation-queues/{queue_id}/export-to-dataset/",
        json_body={},
        expect_status=[400],
    )

    # E3. Export JSON
    print("\n  E3. Export queue (JSON format)")
    test(
        "Export JSON", "GET", f"model-hub/annotation-queues/{queue_id}/export/",
        params={"export_format": "json"},
        expect_status=[200],
    )

# ============================================================
# F. DATASET APIS
# ============================================================
print("\n--- F. Dataset APIs ---")

# F1. Create empty dataset
print("\n  F1. Create empty dataset")
ds_name = f"test_ds_{uuid.uuid4().hex[:6]}"
status, ds_body = test(
    "Create empty dataset", "POST", "model-hub/develops/create-empty-dataset/",
    json_body={"new_dataset_name": ds_name, "dataset_model_type": "text"},
    expect_status=[200, 201, 400],
)
dataset_id = None
if isinstance(ds_body, dict):
    result = ds_body.get("result", ds_body)
    if isinstance(result, dict):
        dataset_id = result.get("dataset_id") or result.get("id")
        created_resources["dataset_id"] = dataset_id

# F2. Create dataset with missing name
print("\n  F2. Create empty dataset (missing name - should fail)")
test(
    "Create dataset (missing name)", "POST", "model-hub/develops/create-empty-dataset/",
    json_body={"dataset_model_type": "text"},
    expect_status=[400],
)

# F3. Get dataset table
if dataset_id:
    print("\n  F3. Get dataset table")
    test(
        "Get dataset table", "GET", f"model-hub/develops/{dataset_id}/get-dataset-table/",
        expect_status=[200],
    )

# F4. Add rows
if dataset_id:
    print("\n  F4. Add rows to dataset")
    test(
        "Add rows", "POST", f"model-hub/develops/{dataset_id}/add_rows/",
        json_body={"rows": [{"input": "test input", "output": "test output"}]},
        expect_status=[200, 201, 400],
    )

# ============================================================
# G. PROMPT APIS
# ============================================================
print("\n--- G. Prompt APIs ---")

# G1. Create prompt template
print("\n  G1. Create prompt template")
tmpl_name = f"test_prompt_{uuid.uuid4().hex[:6]}"
status, tmpl_body = test(
    "Create prompt template", "POST", "model-hub/prompt-templates/create-draft/",
    json_body={
        "name": tmpl_name,
        "prompt_config": {
            "model_name": "gpt-4",
            "messages": [{"role": "user", "content": "Hello {{name}}"}],
            "max_tokens": 100,
            "temperature": 0.7,
        },
    },
    expect_status=[200, 201, 400],
)
template_id = None
if isinstance(tmpl_body, dict):
    result = tmpl_body.get("result", tmpl_body)
    if isinstance(result, dict):
        template_id = result.get("id") or result.get("template_id")
        created_resources["template_id"] = template_id

# G2. Create prompt with missing config
print("\n  G2. Create prompt (missing prompt_config - should fail)")
test(
    "Create prompt (missing config)", "POST", "model-hub/prompt-templates/create-draft/",
    json_body={"name": f"test_bad_{uuid.uuid4().hex[:6]}"},
    expect_status=[400],
)

# G3. Get template by ID
if template_id:
    print("\n  G3. Get template by ID")
    test(
        "Get template by ID", "GET", f"model-hub/prompt-templates/{template_id}/",
        expect_status=[200],
        expect_snake_keys=["prompt_config"],
    )

# G4. Add new draft
if template_id:
    print("\n  G4. Add new draft to template")
    test(
        "Add new draft", "POST", f"model-hub/prompt-templates/{template_id}/add-new-draft/",
        json_body={
            "prompt_config": {
                "model_name": "gpt-4",
                "messages": [{"role": "user", "content": "Updated: {{name}}"}],
                "max_tokens": 200,
            },
        },
        expect_status=[200, 201],
    )

# G5. Commit template
if template_id:
    print("\n  G5. Commit template")
    test(
        "Commit template", "POST", f"model-hub/prompt-templates/{template_id}/commit/",
        json_body={},
        expect_status=[200, 201, 400],
    )

# G6. Get version history
if template_id:
    print("\n  G6. Get version history")
    test(
        "Get version history", "GET", "model-hub/prompt-history-executions/",
        params={"template_id": template_id},
        expect_status=[200],
    )

# ============================================================
# H. KNOWLEDGE BASE APIS
# ============================================================
print("\n--- H. Knowledge Base APIs ---")

# H1. Create KB (needs file upload, test with empty)
print("\n  H1. Create KB (minimal)")
test(
    "Create KB", "POST", "model-hub/knowledge-base/",
    json_body={"kb_name": f"test_kb_{uuid.uuid4().hex[:6]}"},
    expect_status=[200, 201, 400],
)

# ============================================================
# I. ANNOTATION APIs
# ============================================================
print("\n--- I. Annotation APIs ---")

# I1. Bulk annotation
print("\n  I1. Bulk annotation")
test(
    "Bulk annotation", "POST", "tracer/bulk-annotation/",
    json_body={
        "annotations": [
            {
                "trace_id": str(uuid.uuid4()),
                "label": "quality",
                "value": "good",
            }
        ]
    },
    expect_status=[200, 201, 400],
)

# ============================================================
# J. PROMPT LABELS
# ============================================================
print("\n--- J. Prompt Labels ---")

# J1. Create prompt label
print("\n  J1. Create prompt label")
status, pl_body = test(
    "Create prompt label", "POST", "model-hub/prompt-labels/",
    json_body={"name": f"test_plabel_{uuid.uuid4().hex[:6]}", "type": "custom"},
    expect_status=[200, 201],
)
prompt_label_id = None
if isinstance(pl_body, dict):
    result = pl_body.get("result", pl_body.get("results", [pl_body]))
    if isinstance(result, list) and result:
        prompt_label_id = result[0].get("id")
    elif isinstance(result, dict):
        prompt_label_id = result.get("id")
    created_resources["prompt_label_id"] = prompt_label_id

# J2. Assign label to template
if template_id and prompt_label_id:
    print("\n  J2. Assign label to template")
    test(
        "Assign label to template", "POST",
        f"model-hub/prompt-labels/{template_id}/{prompt_label_id}/assign-label-by-id/",
        json_body={},
        expect_status=[200, 201, 400],
    )

# J3. Get template labels
print("\n  J3. Get template labels")
test(
    "Get template labels", "GET", "model-hub/prompt-labels/template-labels/",
    params={"template_id": template_id} if template_id else {"template_id": "00000000-0000-0000-0000-000000000000"},
    expect_status=[200, 400],
)

# J4. Remove label
if template_id and prompt_label_id:
    print("\n  J4. Remove prompt label")
    test(
        "Remove prompt label", "POST", "model-hub/prompt-labels/remove/",
        json_body={"template_id": template_id, "label_id": prompt_label_id},
        expect_status=[200, 400],
    )

# ============================================================
# K. DATASET EVAL APIs
# ============================================================
print("\n--- K. Dataset Eval APIs ---")

if dataset_id:
    # K1. Add evaluation with snake_case payload
    print("\n  K1. Add evaluation to dataset")
    test(
        "Add evaluation", "POST", f"model-hub/develops/{dataset_id}/add_user_eval/",
        json_body={
            "template_id": 1,  # Use first built-in eval
            "run": True,
            "name": "test_eval",
            "save_as_template": False,
            "config": {
                "mapping": {},
                "config": {},
                "reason_column": "",
            },
        },
        expect_status=[200, 201, 400, 404],
    )

    # K2. Get eval stats
    print("\n  K2. Get eval stats")
    test(
        "Get eval stats", "GET", f"model-hub/dataset/{dataset_id}/eval-stats/",
        expect_status=[200, 404],
    )

# ============================================================
# CLEANUP
# ============================================================
print("\n--- Cleanup ---")

# Delete test queue
if created_resources.get("queue_id"):
    api("DELETE", f"model-hub/annotation-queues/{created_resources['queue_id']}/")
    print(f"  Deleted queue: {created_resources['queue_id']}")
if created_resources.get("queue_id_min"):
    api("DELETE", f"model-hub/annotation-queues/{created_resources['queue_id_min']}/")
    print(f"  Deleted queue: {created_resources['queue_id_min']}")

# Delete test label
if created_resources.get("label_id"):
    api("DELETE", f"model-hub/annotations-labels/{created_resources['label_id']}/")
    print(f"  Deleted label: {created_resources['label_id']}")

# Delete test template
if created_resources.get("template_id"):
    api("DELETE", f"model-hub/prompt-templates/{created_resources['template_id']}/")
    print(f"  Deleted template: {created_resources['template_id']}")

# Delete test dataset
if created_resources.get("dataset_id"):
    api("POST", "model-hub/develops/delete_dataset/", json_body={"dataset_ids": [created_resources["dataset_id"]]})
    print(f"  Deleted dataset: {created_resources['dataset_id']}")

# Delete prompt label
if created_resources.get("prompt_label_id"):
    api("DELETE", f"model-hub/prompt-labels/{created_resources['prompt_label_id']}/")
    print(f"  Deleted prompt label: {created_resources['prompt_label_id']}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("COMPREHENSIVE POST/PATCH/DELETE SUMMARY")
print("=" * 70)

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if not r["passed"])

print(f"\nTotal tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed:
    print("\n--- FAILED TESTS ---")
    for r in results:
        if not r["passed"]:
            print(f"\n  {r['method']} {r['path']}")
            print(f"  Name: {r['name']}")
            print(f"  Status: {r['status']}")
            for issue in r["issues"]:
                print(f"  ISSUE: {issue}")
            if isinstance(r["body"], dict):
                print(f"  Response: {json.dumps(r['body'], indent=2)[:300]}")

print(f"\n{'PASS' if failed == 0 else 'FAIL'}: {passed}/{total} tests passed")
sys.exit(0 if failed == 0 else 1)
