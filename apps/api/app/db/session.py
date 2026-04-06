from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def get_db() -> None:
    yield None

