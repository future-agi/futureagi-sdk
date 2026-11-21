"""Check every Python example in the generated reference against the installed SDK.

    python docs_examples.py <path to docs/sdk-reference>

For each ```python fence: the code must parse, every `client.<...>` attribute chain
must resolve on a real `fi.Client`, and the call's arguments must bind to the real
method signature (`inspect.signature(...).bind`), so an example that names a
missing method, a wrong keyword or a wrong arity fails here before it reaches a
reader. Nothing is called and no network is touched. The overview's error import
is executed as written. Runs in the SDK test suite (from the sources) and in CI's
"Packages as installed" job (from the wheel, in an empty virtualenv).
"""

from __future__ import annotations

import ast
import inspect
import re
import sys
from pathlib import Path

# Only the fences inside <CodeGroup> are examples a reader copies; the fences inside the
# "Signature" expander are declarations (`dataset_id: str, *, ...`), not runnable code.
GROUP = re.compile(r"<CodeGroup>(.*?)</CodeGroup>", re.S)
FENCE = re.compile(r"```python[^\n]*\n(.*?)```", re.S)


def examples(reference: Path) -> list[tuple[str, str]]:
    """[(page, code)] for every Python example fence in the reference."""
    out = []
    for page in sorted(reference.glob("*.mdx")):
        for group in GROUP.findall(page.read_text()):
            for code in FENCE.findall(group):
                out.append((page.name, code.strip()))
    return out


def _calls(tree: ast.AST):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and _chain(node.func)
            and _chain(node.func)[0] == "client"
        ):
            yield node


def _chain(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


def _literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except ValueError:
        return (
            object()
        )  # a non-literal argument (a variable) still binds by position/keyword


def check(reference: Path) -> list[str]:
    """Problems found; empty when every example is sound against this SDK."""
    import fi

    client = fi.Client(api_key="docs", secret_key="docs", base_url="http://127.0.0.1:9")
    problems: list[str] = []
    seen_calls = 0
    for page, code in examples(reference):
        imports = "\n".join(
            line for line in code.splitlines() if line.startswith(("from ", "import "))
        )
        if imports:
            # The documented import lines must resolve as written (the error classes, the client).
            try:
                exec(compile(imports, page, "exec"), {})
            except Exception as error:  # noqa: BLE001 - report, keep checking
                problems.append(f"{page}: import example fails: {error!r}")
            if code.startswith(("from ", "import ")) and "client." not in code:
                continue
        try:
            tree = ast.parse(code)
        except SyntaxError as error:
            problems.append(f"{page}: does not parse: {error}")
            continue
        for call in _calls(tree):
            chain = _chain(call.func) or []
            target = client
            for attr in chain[1:]:
                target = getattr(target, attr, None)
                if target is None:
                    problems.append(
                        f"{page}: `{'.'.join(chain)}` does not exist on fi.Client"
                    )
                    break
            else:
                args = [_literal(a) for a in call.args]
                kwargs = {k.arg: _literal(k.value) for k in call.keywords if k.arg}
                try:
                    inspect.signature(target).bind(*args, **kwargs)
                except TypeError as error:
                    problems.append(f"{page}: `{'.'.join(chain)}(...)`: {error}")
                seen_calls += 1
    if seen_calls < 100:
        problems.append(
            f"only {seen_calls} client calls found in {reference}; is this the generated reference?"
        )
    return problems


def main(argv: list[str]) -> int:
    reference = Path(argv[1]) if len(argv) > 1 else Path("docs/sdk-reference")
    problems = check(reference)
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print(
            f"docs examples: every Python example in {reference} binds to the installed SDK"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
