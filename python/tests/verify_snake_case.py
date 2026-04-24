"""
Verify that all API responses from the local backend are in snake_case.
Hits each affected endpoint and checks for camelCase keys.
"""
import re
import sys
import requests

API_KEY = "3b8edf45aebc47da8a750ee79dddc89b"
SECRET_KEY = "2e265885dcf74b2b96fb5d3b729f5f2c"
BASE_URL = "http://localhost:8001"

HEADERS = {
    "X-Api-Key": API_KEY,
    "X-Secret-Key": SECRET_KEY,
    "Content-Type": "application/json",
}

CAMEL_CASE_RE = re.compile(r"^[a-z]+[A-Z][a-zA-Z]*$")

# Known exceptions: keys that are intentionally camelCase or single-word
ALLOWED_KEYS = {"ok", "id", "name", "status", "type", "url", "detail", "message"}


def find_camel_case_keys(obj, path=""):
    """Recursively find camelCase keys in a JSON response."""
    found = []
    if isinstance(obj, dict):
        for key in obj:
            full_path = f"{path}.{key}" if path else key
            if CAMEL_CASE_RE.match(key) and key not in ALLOWED_KEYS:
                found.append(full_path)
            found.extend(find_camel_case_keys(obj[key], full_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(find_camel_case_keys(item, f"{path}[{i}]"))
    return found


def api_call(method, path, json=None, params=None):
    """Make an API call and return (status_code, json_body, camel_keys)."""
    url = f"{BASE_URL}/{path}"
    try:
        resp = requests.request(method, url, headers=HEADERS, json=json, params=params, timeout=15)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        camel_keys = find_camel_case_keys(body) if isinstance(body, (dict, list)) else []
        return resp.status_code, body, camel_keys
    except Exception as e:
        return None, str(e), []


results = []


def test_route(name, method, path, json=None, params=None, expected_status=None):
    """Test a single route and report results."""
    status, body, camel_keys = api_call(method, path, json=json, params=params)

    # Determine pass/fail
    reachable = status is not None
    status_ok = expected_status is None or status in (expected_status if isinstance(expected_status, (list, tuple)) else [expected_status])
    no_camel = len(camel_keys) == 0

    passed = reachable and no_camel

    result = {
        "name": name,
        "method": method,
        "path": path,
        "status": status,
        "passed": passed,
        "camel_keys": camel_keys,
    }
    results.append(result)

    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {method:6s} {path}")
    if status:
        print(f"         Status: {status}")
    if camel_keys:
        print(f"         camelCase keys found: {camel_keys[:10]}")
    if not reachable:
        print(f"         ERROR: {body}")

    return result


print("=" * 70)
print("API SNAKE_CASE VERIFICATION")
print(f"Target: {BASE_URL}")
print("=" * 70)

# --- A. Dataset APIs ---
print("\n--- A. Dataset APIs ---")
test_route("List dataset names", "GET", "model-hub/develops/get-datasets-names/")
test_route("Create empty dataset", "POST", "model-hub/develops/create-empty-dataset/",
           json={"dataset_name": "test_snake_case_verify", "dataset_model_type": "text"})

# --- B. Prompt APIs ---
print("\n--- B. Prompt APIs ---")
test_route("List templates", "GET", "model-hub/prompt-templates/")
test_route("Create draft template", "POST", "model-hub/prompt-templates/create-draft/",
           json={"name": "test_snake_verify", "prompt_config": {"model_name": "gpt-4", "messages": [{"role": "user", "content": "test"}]}})

# --- C. Knowledge Base APIs ---
print("\n--- C. Knowledge Base APIs ---")
test_route("List knowledge bases", "GET", "model-hub/knowledge-base/list/")

# --- D. Annotation APIs ---
print("\n--- D. Annotation APIs ---")
test_route("Get annotation labels", "GET", "tracer/get-annotation-labels/")
test_route("List projects", "GET", "tracer/project/list_projects/")

# --- E. Annotation Queue APIs ---
print("\n--- E. Annotation Queue APIs ---")
test_route("List queues", "GET", "model-hub/annotation-queues/")
test_route("Create queue", "POST", "model-hub/annotation-queues/",
           json={"name": "test_snake_case_queue", "description": "Verification test"})

# Check if we got a queue ID to test detail endpoints
queue_id = None
for r in results:
    if r["name"] == "Create queue" and r["status"] in (200, 201):
        try:
            body = api_call("GET", "model-hub/annotation-queues/")[1]
            if isinstance(body, dict):
                items = body.get("result", body).get("results", [])
                if isinstance(body.get("result"), list):
                    items = body["result"]
                for q in items:
                    if isinstance(q, dict) and q.get("name") == "test_snake_case_queue":
                        queue_id = q.get("id")
                        break
        except Exception:
            pass

if queue_id:
    test_route("Get queue detail", "GET", f"model-hub/annotation-queues/{queue_id}/")
    test_route("Get queue progress", "GET", f"model-hub/annotation-queues/{queue_id}/progress/")
    test_route("Get queue analytics", "GET", f"model-hub/annotation-queues/{queue_id}/analytics/")
    test_route("Get queue agreement", "GET", f"model-hub/annotation-queues/{queue_id}/agreement/")
else:
    print("  [SKIP] Queue detail/progress/analytics/agreement (no queue ID)")

# --- F. Annotation Labels CRUD ---
print("\n--- F. Annotation Labels CRUD ---")
test_route("List annotation labels (CRUD)", "GET", "model-hub/annotations-labels/")

# --- G. Scores APIs ---
print("\n--- G. Scores APIs ---")
test_route("List scores", "GET", "model-hub/scores/")

# --- H. Eval APIs ---
print("\n--- H. Eval APIs ---")
test_route("Get eval templates", "GET", "sdk/api/v1/get-evals/")

# --- I. Prompt Labels ---
print("\n--- I. Prompt Labels ---")
test_route("List prompt labels", "GET", "model-hub/prompt-labels/")

# --- J. Model Details ---
print("\n--- J. Model Details ---")
test_route("Get model details", "GET", "model-hub/api/models_list/")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if not r["passed"])

print(f"\nTotal routes tested: {total}")
print(f"Passed (no camelCase): {passed}")
print(f"Failed (camelCase found or error): {failed}")

if failed:
    print("\nFailed routes:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['method']} {r['path']} (status={r['status']})")
            if r["camel_keys"]:
                print(f"    camelCase keys: {r['camel_keys'][:15]}")

# Cleanup: delete test queue if created
if queue_id:
    requests.delete(f"{BASE_URL}/model-hub/annotation-queues/{queue_id}/", headers=HEADERS, timeout=10)
    print(f"\nCleanup: deleted test queue {queue_id}")

sys.exit(0 if failed == 0 else 1)
