# Webhook compatibility fixture

This source-only fixture is not a separate distribution. Webhook verification
ships in the `futureagi` SDK and uses only the Python standard library.

```bash
pip install futureagi
```

```python
import os
from fi.webhooks import verify, WebhookVerificationError

def hook(request):                      # Django; Flask: request.get_data(), FastAPI: await request.body()
    try:
        event = verify(body=request.body, headers=request.headers, secret=os.environ["FI_WEBHOOK_SECRET"])
    except WebhookVerificationError:
        return HttpResponse(status=400)
    if event.get("test"):
        return HttpResponse(status=200)
    # handle event["type"]; dedupe on event["id"] (delivery is at least once)
    return HttpResponse(status=200)
```

- **Verify the raw body.** A body that was parsed and serialized again does not verify.
- **What is checked:** the `webhook-id`, `webhook-timestamp` and `webhook-signature` headers (Standard Webhooks v1):
  `base64(HMAC-SHA256(key, "<id>.<timestamp>.<body>"))` with the decoded `whsec_` secret, any `v1` entry may match
  (two are sent while a secret rotates), and the timestamp must be within 300 s of now. The comparison is constant
  time.
- **Errors.** `WebhookVerificationError.reason` is `missing_headers`, `invalid_timestamp`, `timestamp_too_old`,
  `timestamp_too_new`, `no_matching_signature` or `invalid_body`: answer 4xx. A malformed secret raises
  `WebhookSecretError`: let it be a 5xx, so Future AGI retries the delivery until the secret is fixed.
- The full SDK (`pip install futureagi`) has the same function as `fi.webhooks.verify`, plus the client and the
  `futureagi-py webhooks` CLI. Any Standard Webhooks library also verifies these requests.
