from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


_COUNTERS = defaultdict(float)


def reset() -> None:
    _COUNTERS.clear()


def incr(name: str, value: float = 1.0) -> None:
    _COUNTERS[name] += value


def snapshot() -> dict[str, float]:
    return deepcopy(dict(_COUNTERS))
