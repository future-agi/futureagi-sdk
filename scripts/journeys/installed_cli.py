"""Execute the console script installed in the consumer environment rather than invoking a module."""
from pathlib import Path
import subprocess
import sysconfig


def futureagi(*args):
    # Pin to this interpreter's installed scripts, not an unrelated PATH binary.
    # This child inherits the supervisor's process-tree network observer.
    executable = Path(sysconfig.get_path('scripts')) / 'futureagi-py'
    return subprocess.run([str(executable), *args], capture_output=True, text=True, timeout=30, cwd='/')
