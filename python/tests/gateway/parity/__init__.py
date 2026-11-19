"""AgentCC parity suite (the AgentCC fold plan, section 5.3): recorder, goldens and comparator.

The recorder runs one case catalog against a target module root: ``agentcc``
(E-OLD, the published 1.0.0 wheel; E-SHIM, the 2.0 shim) or ``fi.gateway``
(E-NEW). It records what each call sends on the wire and what the caller sees.
Goldens live in ``tests/fixtures/gateway/golden/``; ``compare.py`` diffs a new
recording against them under ``tests/fixtures/gateway/intended-differences.json``.

Nothing here imports a target at module import time, so the fixed CI install
line (futureagi plus pytest only) collects this package without agentcc.
"""
