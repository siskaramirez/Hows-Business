from copy import deepcopy
from threading import RLock
from time import monotonic


_cache = {}
_lock = RLock()


def get_cached_result(key):
    now = monotonic()
    with _lock:
        cached = _cache.get(key)
        if not cached:
            return None
        expires_at, value = cached
        if expires_at <= now:
            _cache.pop(key, None)
            return None
        return deepcopy(value)


def set_cached_result(key, value, ttl_seconds=60):
    with _lock:
        _cache[key] = (monotonic() + ttl_seconds, deepcopy(value))
    return value


def invalidate_user_cache(user_no):
    with _lock:
        stale_keys = [key for key in _cache if len(key) > 1 and key[1] == user_no]
        for key in stale_keys:
            _cache.pop(key, None)
