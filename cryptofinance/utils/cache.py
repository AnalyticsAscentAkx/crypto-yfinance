"""Bounded, expiring cache with isolated copies of mutable results."""
import copy
import inspect
import threading
import time
from collections import OrderedDict
from functools import wraps

_STORE = OrderedDict()
_LOCK = threading.RLock()
_GENERATION = 0
_MAX_ENTRIES = 512


def _freeze(value):
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def ttl_cache(ttl=60):
    """Cache equivalent calls for ttl seconds; never expose the stored object."""
    def decorator(fn):
        signature = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            key = (fn, _freeze(bound.arguments))
            with _LOCK:
                generation = _GENERATION
                cached = _STORE.get(key)
                if cached is not None:
                    value, expires = cached
                    if time.monotonic() < expires:
                        _STORE.move_to_end(key)
                        return copy.deepcopy(value)
                    del _STORE[key]
            value = fn(*args, **kwargs)
            with _LOCK:
                if generation == _GENERATION:
                    _STORE[key] = (copy.deepcopy(value), time.monotonic() + ttl)
                    _STORE.move_to_end(key)
                    while len(_STORE) > _MAX_ENTRIES:
                        _STORE.popitem(last=False)
            return value
        return wrapper
    return decorator


def clear_cache():
    """Clear cached data, including data used by existing Ticker instances."""
    global _GENERATION
    with _LOCK:
        _STORE.clear()
        _GENERATION += 1
