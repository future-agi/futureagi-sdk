# Server contract snapshots

`annotation-queue-create.json` records, from the backend source at the commit named in `source`
(with each file's git blob):

- the fields of `POST /model-hub/annotation-queues/` (the backend's `AnnotationQueueSerializer`):
  which a create accepts (`create.writable`), which it requires (`create.required`) and which it
  ignores as read-only;
- what `AnnotationQueueViewSet.perform_create` saves besides those fields (`view`), which shows
  that a create never scopes a queue to a project, dataset or agent definition;
- which methods on the create path use `project_id`, `dataset_id` or `agent_definition_id`
  (`serializer.scope_ids_read`, `view.scope_ids_read`): only the serializer's `validate_name`,
  which scopes its duplicate-name check with them; nothing applies them to the queue;
- the request of `POST /model-hub/annotation-queues/get-or-create-default/`
  (`get_or_create_default`): its fields and the rule that exactly one of them is given.

Nothing was called or run to make it.

Two contract tests read it and fail when a queue `create()` or `get_or_create_default()`
(TypeScript `getOrCreateDefault()`) drifts from it:

- Python: `python/tests/test_annotation_queue_create_contract.py`
  (`fi.queues.AnnotationQueue` and `FutureAGIClient.annotation_queues`);
- TypeScript: `typescript/futureagi/src/queues/__tests__/create-contract.test.ts`
  (`AnnotationQueue` and `FutureAGIClient.annotationQueues`).

## Refresh

From the repo root, with a checkout of the backend (`future-agi/future-agi`):

```bash
git -C <future-agi checkout> fetch origin dev
python3 scripts/snapshot-annotation-queue-contract.py --backend <future-agi checkout> --ref origin/dev --check
python3 scripts/snapshot-annotation-queue-contract.py --backend <future-agi checkout> --ref origin/dev
```

`--check` exits 1 and prints the difference when the parsed facts changed. When the facts match
but one of the four pinned files changed (its git blob), it prints a WARNING with the `git diff`
command for that file and still exits 0 (`--strict`: exit 2). The script parses only what it
knows, so read that diff for anything that reads or applies a scope id on create before you
refresh. Without `--check`, the script rewrites the snapshot. Commit the new snapshot together with the client changes it calls for:
the contract tests stay red until both clients match it again. When the backend code changes
shape in a way the script does not parse, the script stops with "extend this script" rather than
writing a guess.
