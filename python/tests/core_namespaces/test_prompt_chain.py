"""A prompt's life on one client: create with its first version, commit, label, fetch by label, compile."""

import json

import httpx
import pytest

from fi.errors import BadRequestError

pytestmark = pytest.mark.asyncio

GREETING = {
    "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello {{name}}"}]}],
    "configuration": {"model": "test-model"},
}


def ok(result):
    return httpx.Response(200, json={"status": True, "result": result})


def refused(message):
    return httpx.Response(400, json={"status": False, "result": message})


class PromptRoutes:
    """Loopback stand-in for the prompt routes, keeping templates, versions and labels in memory."""

    def __init__(self):
        self.templates, self.labels = {}, {}

    def __call__(self, request):
        route = request.url.path.removeprefix("/model-hub/").strip("/").split("/")
        body = json.loads(request.content) if request.content else {}
        if route == ["prompt-templates", "create-draft"]:
            template_id = f"t{len(self.templates) + 1}"
            first = {"config": body["prompt_config"][0], "draft": True, "labels": set()}
            self.templates[template_id] = {"name": body["name"], "versions": {"v1": first}}
            return ok({"id": template_id, "name": body["name"], "created_version": "v1",
                       "template_version": "v1", "is_draft": True})
        if route[0] == "prompt-templates" and route[-1] == "add-new-draft":
            versions, made = self.templates[route[1]]["versions"], []
            for prompt in body["new_prompts"]:
                name = f"v{len(versions) + 1}"
                versions[name] = {"config": prompt["prompt_config"][0], "draft": True, "labels": set()}
                made.append({"template_version": name, "is_draft": True})
            return ok(made)
        if route[0] == "prompt-templates" and route[-1] == "commit":
            version = self.templates[route[1]]["versions"].get(body["version_name"])
            if version is None:
                return refused("Prompt Version Not Found")
            version["draft"] = body["is_draft"]
            return ok(f"Commit for {body['version_name']} has been added")
        if route == ["prompt-labels"]:
            label_id = f"l{len(self.labels) + 1}"
            self.labels[label_id] = body["name"]
            return httpx.Response(201, json={"id": label_id, **body})
        if route[0] == "prompt-labels" and route[-1] == "assign-label-by-id":
            template_id, label_id = route[1], route[2]
            versions = self.templates[template_id]["versions"]
            if body["version"] not in versions:
                return refused(f"No version '{body['version']}' found")
            for version in versions.values():
                version["labels"].discard(label_id)
            versions[body["version"]]["labels"].add(label_id)
            return ok({"template_id": template_id, "version": body["version"], "label_id": label_id,
                       "label_name": self.labels[label_id], "moved_from_versions": []})
        if route == ["prompt-labels", "get-by-name"]:
            name, label = request.url.params["name"], request.url.params["label"].lower()
            template_id, template = next((k, v) for k, v in self.templates.items() if v["name"] == name)
            for version_name, version in template["versions"].items():
                if any(self.labels[item].lower() == label for item in version["labels"]):
                    return ok({"id": template_id, "name": name, "version": version_name,
                               "is_draft": version["draft"], "prompt_config": [version["config"]]})
            return refused(f"No version found for label '{label}'")
        return httpx.Response(404, json={"detail": f"no route for {request.method} {request.url.path}"})


async def test_create_commit_label_fetch_and_compile(resources):
    resources.server = routes = PromptRoutes()
    prompts = resources.prompts
    created = await resources.call(prompts.create, {"name": "greeting", "prompt_config": [GREETING]})
    template_id, first = created["id"], created["created_version"]
    assert routes.templates[template_id]["versions"][first]["config"] == GREETING
    await resources.call(prompts.versions.commit, template_id, first, message="first")
    label = await resources.call(prompts.labels.create, {"name": "production", "type": "custom"})
    assigned = await resources.call(prompts.labels.assign, template_id, label["id"], version=first)
    assert assigned["version"] == first
    fetched = await resources.call(prompts.get_by_label, "greeting", "production")
    assert (fetched["version"], fetched["is_draft"]) == (first, False)
    rendered = prompts.compile(fetched, {"name": "reader"})
    assert rendered == [{"role": "user", "content": [{"type": "text", "text": "Hello reader"}]}]
    assert [(r.method, r.url.path.removeprefix("/model-hub/")) for r in resources.requests] == [
        ("POST", "prompt-templates/create-draft/"),
        ("POST", f"prompt-templates/{template_id}/commit/"),
        ("POST", "prompt-labels/"),
        ("POST", f"prompt-labels/{template_id}/{label['id']}/assign-label-by-id/"),
        ("GET", "prompt-labels/get-by-name/"),
    ]


async def test_a_later_version_is_drafted_committed_and_takes_the_label(resources):
    resources.server = PromptRoutes()
    prompts = resources.prompts
    created = await resources.call(prompts.create, {"name": "greeting", "prompt_config": [GREETING]})
    template_id = created["id"]
    revised = {**GREETING, "messages": [{"role": "user", "content": "Hi {{name}}"}]}
    drafts = await resources.call(prompts.versions.create, template_id, {"new_prompts": [{"prompt_config": [revised]}]})
    later = drafts[0]["template_version"]
    assert later != created["created_version"]
    label = await resources.call(prompts.labels.create, {"name": "production", "type": "custom"})
    await resources.call(prompts.labels.assign, template_id, label["id"], version=created["created_version"])
    await resources.call(prompts.versions.commit, template_id, later)
    await resources.call(prompts.labels.assign, template_id, label["id"], version=later)
    fetched = await resources.call(prompts.get_by_label, "greeting", "production")
    assert fetched["version"] == later
    assert prompts.compile(fetched, {"name": "reader"}) == [{"role": "user", "content": "Hi reader"}]
    with pytest.raises(BadRequestError):
        await resources.call(prompts.versions.commit, template_id, "v9")
