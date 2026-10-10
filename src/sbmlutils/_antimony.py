"""Serialize access to libAntimony's process-wide model registry."""

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock
from types import ModuleType

_lock = RLock()


@contextmanager
def antimony_session() -> Iterator[ModuleType]:
    """Load Antimony on demand and release loaded models after conversion.

    Loading and extracting a model must share a lock: another load changes
    the active model. Applications using Antimony directly must coordinate
    that access themselves or use separate processes.
    """
    with _lock:
        import antimony

        antimony.clearPreviousLoads()
        try:
            yield antimony
        finally:
            antimony.clearPreviousLoads()
