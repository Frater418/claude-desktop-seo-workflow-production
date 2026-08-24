from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock


class DeliveryAdmission:
    def __init__(self) -> None:
        self._lock = Lock()

    @contextmanager
    def lock(self) -> Iterator[None]:
        with self._lock:
            yield
