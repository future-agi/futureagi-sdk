# Future AGI SDK Compliance Adapter

Thin HTTP adapter used by `futureagi-sdk-test-harness`.

It wraps the Python `futureagi` SDK and exposes the adapter contract expected by
the shared harness:

- `GET /health`
- `POST /init`
- `POST /reset`
- `GET /state`
- `POST /raw-request`
- `POST /annotation/log`
- `POST /annotation-queue/lifecycle`
- `POST /annotation-score/lifecycle`
- `POST /dataset/lifecycle`
- `POST /model/log`

## Local Run

From the `futureagi-sdk` repo root:

```bash
uv venv --python 3.11 .venv-compliance
. .venv-compliance/bin/activate
uv pip install -e python
PYTHONPATH=python PORT=8080 python tests/compliance/python/adapter.py
```

Then run the harness from `../futureagi-sdk-test-harness`:

```bash
futureagi-sdk-test-harness run --adapter-url http://127.0.0.1:8080
```

Current passing suites:

- `auth_raw_request`
- `annotation_bulk_log`
- `annotation_queue_lifecycle_e2e`
- `annotation_score_lifecycle_e2e`
- `dataset_lifecycle_e2e`
- `model_log_lifecycle_e2e`

## Docker

```bash
docker build -f tests/compliance/python/Dockerfile -t futureagi-sdk-python-adapter .
docker run --rm -p 8080:8080 futureagi-sdk-python-adapter
```
