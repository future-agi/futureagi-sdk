"""Fail-closed workflow checks with exact, byte-bound release exceptions.

Reviewed trigger/action/source exceptions do not authorize credentials or
publication. W2/W3 blockers stay blocked, including in released workflows.
This is a static regression gate, not a sandbox for arbitrary application code.
New actions and reusable workflows need review. Runtime permissions must remain
read-only even when a step is disabled or a workflow is manually triggered.

Command rules are a blocklist for the usual publish, tag and deploy tools; a
raw HTTP client is not matched. The backstop is credentials: read-only token
permissions, no `secrets` or GitHub token in any expression, no credential-named
workflow input, and no credential-named variable, action input or shell
assignment taken from an expression. A person who runs a script with their own
registry credential is outside what a static check of this tree can decide.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import yaml


class WorkflowLoader(yaml.BaseLoader):
    """Preserve YAML keys such as `on`; reject ambiguous mapping overrides."""

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key == "<<" or key in result:
                raise ValueError("duplicate, merged or non-string mapping key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


# Repository selectors may precede `release`/`api` or the release subcommand.
# Match split, equals and attached short forms without treating option values
# (or read-only commands' arguments) as mutation subcommands.
GH_REPOSITORY_OPTIONS = r"(?:\s+(?:--repo(?:=|\s+)|-R\s*)(?:\$\{\{[^}\n]*\}\}|[^\s;|&]+))*"

# Scan parsed scalars, not source lines: this includes folded strings, aliases,
# JSON/flow-style YAML, action inputs, environment variables and matrix entries.
COMMAND_RULES = {
    "package publication": r"\b(?:npm|pnpm|yarn|bun|poetry|uv|lerna|changeset|changesets)\b[^;|&\n]*\b(?:publish|release|deploy)\b",
    "PyPI upload": r"\btwine\b[^;|&\n]*\bupload\b|\bflit\b[^;|&\n]*\bpublish\b",
    "Maven deployment": r"\b(?:mvn|mvnw)\b[^;|&\n]*\b(?:deploy|deploy-file|release:perform)\b",
    "Gradle publication": r"\b(?:gradle|gradlew)\b[^;|&\n]*\b(?:publish\w*|uploadArchives|release)\b",
    "Git mutation": r"\bgit\b[^;|&\n]*\b(?:push|tag)\b",
    # `new` is the CLI's alias of `create`; `delete` also matches `delete-asset`.
    "GitHub release": rf"\bgh{GH_REPOSITORY_OPTIONS}\s+release{GH_REPOSITORY_OPTIONS}\s+(?:create|new|upload|edit|delete)\b",
    # Fields and --input bodies make the request a POST. Short flags may carry
    # attached values (-XPOST, -fkey=value) or follow the boolean -i.
    "GitHub API mutation": rf"\bgh{GH_REPOSITORY_OPTIONS}\s+api\b[^;|&\n]*\s(?:--(?:method|field|raw-field|input)(?![\w-])|-i*[XfF])",
    "GitHub CLI alias": rf"\bgh{GH_REPOSITORY_OPTIONS}\s+alias\s+(?:set|import)\b",
    "release automation": r"\b(?:semantic-release|release-please|goreleaser)\b",
    "container publication": r"\b(?:docker|podman|buildah)\b[^;|&\n]*(?:\bpush\b|--push\b)|\bskopeo\s+copy\b",
    "deployment": r"\b(?:vercel|netlify|firebase|serverless|sls|wrangler|flyctl)\b[^;|&\n]*\b(?:deploy|publish)\b|\bkubectl\s+(?:apply|create|replace|set)\b|\bhelm\s+(?:install|upgrade|push)\b|\bterraform\s+apply\b|\bgcloud\b[^;|&\n]*\bdeploy\b",
}
RULES = {name: re.compile(pattern, re.I) for name, pattern in COMMAND_RULES.items()}
# Inside an expression body: `secrets` anywhere, and the `github` context except
# as `github.<property>` for a property other than `token`. A step id or output
# named `github` (`steps.github.outputs.x`) is not the context.
CREDENTIAL_CONTEXTS = re.compile(r"\bsecrets\b|(?<![\w.-])github\b(?!\s*\.\s*(?!token\b)[a-z_][\w-]*)", re.I)
# Credential-shaped names; `auth(?!or)` keeps GIT_AUTHOR_NAME and similar out.
CREDENTIAL_NAME = re.compile(r"token|passw(?:or)?d|passphrase|secret|credential|auth(?!or)|^twine_", re.I)
SHELL_ASSIGNMENT = re.compile(r"([A-Za-z_][\w-]*)\s*=\s*\$\{\{")
SAFE_EVENTS = {"pull_request", "push", "workflow_call", "workflow_dispatch"}
RELEASE_BRANCHES = {"main", "master", "release/**", "releases/**"}


def normalized(value):
    # Shell quote splitting and line continuations must not hide a command.
    return re.sub(r"\\\r?\n", "", value).translate(str.maketrans("", "", "'\"\\"))


def expression_bodies(value):
    """Yield each `${{ ... }}` body with string-literal contents blanked.

    The body ends at the first `}}` outside a single-quoted literal (`''` is an
    escaped quote and toggles twice). An unterminated body runs to the end.
    A literal cannot dereference a context, so blanking it is safe.
    """
    start = value.find("${{")
    while start != -1:
        body, quoted, index = [], False, start + 3
        while index < len(value) and (quoted or not value.startswith("}}", index)):
            if value[index] == "'":
                quoted = not quoted
            body.append(" " if quoted and value[index] != "'" else value[index])
            index += 1
        yield "".join(body)
        start = value.find("${{", index)


RELEASED_WORKFLOWS = {
    ".github/workflows/ci.yml", ".github/workflows/e2e.yml",
    ".github/workflows/publish.yml", ".github/workflows/promote.yml",
    ".github/workflows/release-please.yml", ".github/workflows/pr-title-lint.yml",
}
EXCEPTION_KINDS = {"trigger", "action", "checkout_ref", "workflow_name"}
# No credential, permission, command, workflow_run or checkout-persistence
# escape hatch. Blocked released workflows must be fixed before admission.
EXCEPTABLE_EVENTS = {"push", "schedule", "repository_dispatch"}
ACTION_REF = re.compile(r"(?:[0-9a-f]{40}|v[0-9]+(?:\.[0-9]+)*(?:-[A-Za-z0-9.-]+)?)")


def git_blob_id(raw):
    """Hash original bytes, including CRLF/BOM, without a Git subprocess."""
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class ReleasedExceptions:
    """Consume exact, byte-bound constructs, never suppress arbitrary errors."""

    def __init__(self, entries, filename, raw, fail):
        self.entries, self.used, self.fail = [], set(), fail
        if not isinstance(entries, (list, tuple)):
            fail("exceptions", "exceptions must be a list")
            return
        ids, selectors = set(), set()
        for entry in entries:
            fields = {"id", "record", "workflow", "blob", "kind", "location", "value"}
            if (not isinstance(entry, dict) or set(entry) != fields
                    or any(not isinstance(entry[k], str) or not entry[k]
                           for k in fields - {"value"})
                    or entry["workflow"] not in RELEASED_WORKFLOWS
                    or entry["kind"] not in EXCEPTION_KINDS
                    or not re.fullmatch(r"[0-9a-f]{40}", entry["blob"])):
                fail("exceptions", "invalid exact released-workflow exception")
                continue
            selector = (entry["workflow"], entry["kind"], entry["location"])
            if entry["id"] in ids or selector in selectors:
                fail("exceptions", "duplicate released-workflow exception")
                continue
            ids.add(entry["id"])
            selectors.add(selector)
            if entry["workflow"] != filename:
                continue
            if entry["blob"] != git_blob_id(raw):
                fail("exceptions", f"blob mismatch for {entry['id']}; review and re-pin required")
                continue
            self.entries.append(entry)

    def allows(self, kind, location, value):
        for entry in self.entries:
            if (entry["kind"], entry["location"], entry["value"]) == (kind, location, value):
                self.used.add(entry["id"])
                return True
        return False

    def finish(self):
        for entry in self.entries:
            if entry["id"] not in self.used:
                self.fail("exceptions", f"unused exact exception {entry['id']}")


def trusted_checkout_source(document, job, step):
    """Resolve one workflow env hop; accept only dispatch inputs/vars/constants.

    The exception also pins the entire file, repository, ref and source text.
    Shadowed env values are refused, even after a blob-only re-pin.
    """
    options = step.get("with", {})
    ref = options.get("ref", "")
    match = re.fullmatch(r"\$\{\{ env\.([A-Za-z_][A-Za-z0-9_]*) \}\}", ref) if isinstance(ref, str) else None
    if not match:
        return None
    name = match[1]
    env = document.get("env", {})
    if not isinstance(env, dict) or not isinstance(env.get(name), str):
        return None
    for scope in [job, *job.get("steps", [])]:
        scoped = scope.get("env", {}) if isinstance(scope, dict) else None
        if not isinstance(scoped, dict) or name in scoped:
            return None
    source = env[name]
    expression = re.fullmatch(
        r"\$\{\{ (inputs|vars)\.([A-Za-z_][\w-]*)(?: \|\| '[A-Za-z0-9_./-]+')? \}\}", source
    )
    if expression and expression[1] == "inputs":
        events = document.get("on", {})
        dispatch = events.get("workflow_dispatch", {}) if isinstance(events, dict) else {}
        inputs = dispatch.get("inputs", {}) if isinstance(dispatch, dict) else {}
        if not isinstance(inputs, dict) or expression[2] not in inputs:
            return None
    elif not expression and not re.fullmatch(r"[A-Za-z0-9_./-]+", source):
        return None
    return {"repository": options.get("repository"), "ref": ref, "source": source}


def check_workflow(text, filename, actions, local_workflows, exceptions=()):
    errors = []

    def fail(where, message):
        errors.append(f"{filename}:{where}: {message}")

    raw = text.encode("utf-8") if isinstance(text, str) else text
    grants = ReleasedExceptions(exceptions, filename, raw, fail)
    try:
        document = yaml.load(raw.decode("utf-8"), Loader=WorkflowLoader)
    except (yaml.YAMLError, ValueError, UnicodeError, RecursionError) as error:
        return [f"{filename}: invalid YAML ({type(error).__name__})"]
    if not isinstance(document, dict):
        return [f"{filename}: workflow must be a mapping"]
    if not isinstance(document.get("permissions"), dict):
        fail("permissions", "explicit read-only permissions mapping required")
    if not isinstance(document.get("jobs"), dict) or not document["jobs"]:
        fail("jobs", "at least one job required")
    events = document.get("on")
    if isinstance(events, str):
        events = {events: None}
    elif isinstance(events, list):
        events = dict.fromkeys(events)
    if not isinstance(events, dict) or not events:
        fail("on", "explicit CI events required")
    else:
        for event, settings in events.items():
            excepted = event in EXCEPTABLE_EVENTS and grants.allows("trigger", f"on.{event}", settings)
            if event not in SAFE_EVENTS and not excepted:
                fail("on", f"event {event!r} is not a test-only trigger")
            if event == "push" and not excepted:
                settings = settings if isinstance(settings, dict) else {}
                if not RELEASE_BRANCHES.issubset(settings.get("branches-ignore", [])):
                    fail("on.push", "exclude main, master, release/** and releases/**")
                if settings.get("tags-ignore") != ["**"] or "tags" in settings:
                    fail("on.push", "all tag pushes must be excluded")
            inputs = settings.get("inputs") if isinstance(settings, dict) else None
            for name in inputs if isinstance(inputs, dict) else ():
                if CREDENTIAL_NAME.search(name):
                    fail(f"on.{event}.inputs.{name}", "credential-named workflow input is forbidden")
    seen = set()

    def walk(value, where):
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                fail(where, "recursive YAML alias is not allowed")
                return
            seen.add(id(value))
        if isinstance(value, dict):
            for key, item in value.items():
                here = f"{where}.{key}"
                if key == "permissions":
                    if not isinstance(item, dict) or any(v not in ("read", "none") for v in item.values()):
                        fail(here, "write or dynamic permissions are forbidden")
                if key == "secrets":
                    fail(here, "workflow secrets may not be passed or inherited")
                if key in ("env", "with") and isinstance(item, str) and "${{" in item:
                    fail(here, "dynamic env or with mapping is forbidden")
                if key in ("env", "with") and isinstance(item, dict):
                    for name, entry in item.items():
                        if CREDENTIAL_NAME.search(name) and isinstance(entry, str) and "${{" in entry:
                            fail(f"{here}.{name}", "credential-named value may not come from an expression")
                if key == "uses":
                    if not isinstance(item, str):
                        fail(here, "action must be a literal reviewed reference")
                    elif item.startswith("./.github/workflows/"):
                        if item not in local_workflows:
                            fail(here, "local reusable workflow does not exist")
                    else:
                        # W2: neither global actions nor per-file exceptions can
                        # authorize a branch reference (including release/v1).
                        if not ACTION_REF.fullmatch(item.rpartition("@")[2]):
                            fail(here, "W2_BLOCKER: action requires a full SHA or a release-version tag")
                        if item not in actions and not grants.allows("action", here, item):
                            fail(here, f"unreviewed action or remote reusable workflow: {item}")
                    if item == "actions/checkout@v4":
                        options = value.get("with", {})
                        if not isinstance(options, dict) or options.get("persist-credentials") != "false":
                            fail(here, "checkout must disable persist-credentials")
                        ref = options.get("ref", "") if isinstance(options, dict) else ""
                        if isinstance(options, dict) and "repository" in options and not (isinstance(ref, str) and re.fullmatch(r"[0-9a-f]{40}", ref)):
                            job_name = re.fullmatch(r"workflow\.jobs\.([\w-]+)\.steps\[[0-9]+\]\.uses", here)
                            job = document.get("jobs", {}).get(job_name[1], {}) if job_name else {}
                            source = trusted_checkout_source(document, job, value)
                            if source is None or not grants.allows("checkout_ref", here, source):
                                fail(here, "external source checkout must use a full commit pin")
                walk(item, here)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{where}[{index}]")
        elif isinstance(value, str):
            if any(CREDENTIAL_CONTEXTS.search(body) for body in expression_bodies(value)):
                fail(where, "explicit token or secret access is forbidden")
            command = normalized(value)
            if any(CREDENTIAL_NAME.search(m.group(1)) for m in SHELL_ASSIGNMENT.finditer(command)):
                fail(where, "credential-named value may not come from an expression")
            for name, pattern in RULES.items():
                if pattern.search(command):
                    if (where == "workflow.name" and name == "release automation"
                            and grants.allows("workflow_name", where, value)):
                        continue
                    fail(where, f"{name} is forbidden")
        if isinstance(value, (dict, list)):
            seen.remove(id(value))

    try:
        walk(document, "workflow")
    except RecursionError:
        fail("workflow", "YAML nesting exceeds the policy limit")
    grants.finish()
    return errors


def repository_path_violation(root, path):
    """Check lexical components first; resolving early would erase aliases.

    The repository root itself is included. Its external parents may have OS
    aliases (for example a temporary-directory prefix); compare within the
    resolved root only after checking every component at or below that root.
    """
    try:
        relative = path.relative_to(root)
        if ".." in root.parts or ".." in relative.parts:
            return f"{path}: parent traversal is not a lexical repository path"
        component = root
        for part in (None, *relative.parts):
            if part is not None:
                component = component / part
            if component.is_symlink():
                return f"{path}: symlink path component is forbidden ({component})"
        if path.resolve(strict=True) != root.resolve(strict=True) / relative:
            return f"{path}: resolved path differs from lexical repository path"
    except (OSError, RuntimeError, ValueError) as error:
        return f"{path}: unreadable repository path ({type(error).__name__})"
    return None


def check_repository(root):
    # Normalize only lexical ".." in the selected root (e.g. `--root ..`); never resolve
    # symlinks here, so every component at or below the root is still checked.
    root = Path(os.path.normpath(Path(root).absolute()))
    folder = root / ".github" / "workflows"
    # Configuration stays anchored to this checker, not the candidate root.
    policy_path = Path(os.path.normpath(Path(__file__).absolute())).with_name("workflow-policy.json")
    for boundary, path in ((root, folder), (policy_path.parents[2], policy_path)):
        violation = repository_path_violation(boundary, path)
        if violation:
            return [violation]
    if not folder.is_dir() or not policy_path.is_file():
        return ["workflow directory and regular policy file required"]
    try:
        policy = json.loads(policy_path.read_text())
        paths = sorted(p for p in folder.rglob("*") if p.suffix.lower() in {".yml", ".yaml"})
    except (OSError, UnicodeError, ValueError) as error:
        return [f"workflow policy inputs are unreadable ({type(error).__name__})"]
    if not paths:
        return [".github/workflows: no workflows found"]
    errors = []
    for path in paths:
        violation = repository_path_violation(root, path)
        if violation:
            errors.append(violation)
        elif path.parent != folder or path.suffix not in {".yml", ".yaml"} or not path.is_file():
            errors.append(f"{path}: workflows must be regular top-level .yml or .yaml files")
    if errors:
        return errors
    # No workflow bytes, blob matching or grant lookups precede path validation.
    locals_ = {f"./.github/workflows/{p.name}" for p in paths}
    for path in paths:
        try:
            errors.extend(check_workflow(
                path.read_bytes(), path.relative_to(root).as_posix(), policy["actions"], locals_,
                policy.get("released_workflow_exceptions", []),
            ))
        except (OSError, UnicodeError) as error:
            errors.append(f"{path}: unreadable workflow ({type(error).__name__})")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[2])
    args = parser.parse_args()
    errors = check_repository(args.root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Workflow policy: all workflows are test-only or satisfy exact released-workflow exceptions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
