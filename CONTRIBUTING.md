# Contributing to futureagi-sdk

Thanks for your interest in contributing. `futureagi-sdk` is part of the [Future AGI](https://github.com/future-agi/future-agi) open-source ecosystem, and we welcome bug fixes, new datasets, prompts, knowledge base features, docs improvements, and examples.

---

## Quick links

- 🐛 [Report a bug](https://github.com/future-agi/futureagi-sdk/issues/new)
- ✨ [Request a feature](https://github.com/future-agi/futureagi-sdk/issues/new)
- 🔖 [Good first issues](https://github.com/future-agi/futureagi-sdk/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- 💬 [Join Discord](https://discord.gg/UjZ2gRT5p)
- 📖 [SDK docs](https://docs.futureagi.com/docs/sdk)

---

## Code of Conduct & CLA

This project follows the [main repo's Contributing Guide](https://github.com/future-agi/future-agi/blob/main/CONTRIBUTING.md): same Code of Conduct, same Contributor License Agreement. The CLA signs automatically on your first PR.

---

## Development setup

```bash
git clone https://github.com/future-agi/futureagi-sdk
cd futureagi-sdk
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Run the tests:

```bash
pytest tests/
```

---

## Pull request checklist

- [ ] Tests pass locally (`pytest tests/`)
- [ ] New dataset feature? Add it under the appropriate module, register it, and add at least one end-to-end test.
- [ ] New prompt workbench feature? Include usage examples and tests.
- [ ] New knowledge base or guardrail feature? Add tests and update relevant docs.
- [ ] Docstrings on public classes and methods.
- [ ] README updated if the public API changed.

---

## Adding a new feature — guidelines

Follow the existing module conventions for datasets, prompt workbench, knowledge base, and guardrails. Keep the public API surface small and consistent with existing patterns.

Questions about feature fit, API boundaries, or design — open a Discussion or ping `@future-agi/sdk-maintainers` on Discord before writing the code.
