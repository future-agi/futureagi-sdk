import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from threading import BoundedSemaphore
from typing import Optional


# Scoped by callers without changing submit's keyword forwarding contract.
_SUBMIT_DEADLINE: ContextVar[Optional[float]] = ContextVar("executor_submit_deadline", default=None)


class BoundedExecutor:
    """BoundedExecutor behaves as a ThreadPoolExecutor which will block on
    calls to submit() once the limit given as "bound" work items are queued for
    execution.
    :param bound: Integer - the maximum number of items in the work queue
    :param max_workers: Integer - the size of the thread pool
    """

    def __init__(self, bound, max_workers):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = BoundedSemaphore(bound + max_workers)

    """See concurrent.futures.Executor#submit"""

    def submit(self, fn, *args, **kwargs):
        deadline = _SUBMIT_DEADLINE.get()
        if deadline is None:
            self.semaphore.acquire()
        else:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.semaphore.acquire(timeout=remaining):
                raise TimeoutError("Executor submission deadline expired")
        try:
            if deadline is None:
                future = self.executor.submit(fn, *args, **kwargs)
            else:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Executor submission deadline expired")

                def run_before_deadline():
                    # Admission can succeed while the work still has to queue.
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Executor submission deadline expired")
                    return fn(*args, **kwargs)

                future = self.executor.submit(run_before_deadline)
        except Exception:
            self.semaphore.release()
            raise
        else:
            future.add_done_callback(lambda x: self.semaphore.release())
            return future

    """See concurrent.futures.Executor#shutdown"""

    def shutdown(self, wait=True):
        self.executor.shutdown(wait)
