"""``fi.experiments.sandbox``: one sandbox per (row, trial), the results in a Future AGI experiment run.

    from fi.experiments.sandbox import SandboxEval, reward, run_in_sandboxes

    spec = SandboxEval(agent=agent, verifier="python3 /workspace/check.py")
    result = run_in_sandboxes("swe-mini", spec, [reward()], trials=2)

A task for the existing engine, not a second engine: trials, concurrency, timeouts, journal, resume
and upload stay ``fi.experiments``'. Sandboxes come from the environment (``OMEGA_BASE_URL`` and the
sandbox credentials of ``fi.sandbox``), or from ``client_factory=``. See ``README.md`` here.
"""

from fi.experiments.sandbox._runner import arun_in_sandboxes, reward, run_in_sandboxes
from fi.experiments.sandbox._spec import EVAL_DIR, SandboxEval
from fi.experiments.sandbox._task import sandbox_task

__all__ = ["EVAL_DIR", "SandboxEval", "arun_in_sandboxes", "reward", "run_in_sandboxes", "sandbox_task"]
