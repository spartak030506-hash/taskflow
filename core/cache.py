import logging
import time
import random

from django.core.cache import cache
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)

CACHE_VERSION = 'v1'


class CacheTTL:
    PROJECT = 60 * 10  # 10 минут
    MEMBERSHIP = 60 * 5  # 5 минут
    NOT_FOUND = 60  # 1 минута для негативного кэширования


class CacheKeys:
    PROJECT_DETAIL = f'{CACHE_VERSION}:projects:detail:{{project_id}}'
    MEMBER_ROLE = f'{CACHE_VERSION}:projects:member_role:{{project_id}}:{{user_id}}'
    EXISTS_MEMBER = f'{CACHE_VERSION}:projects:exists_member:{{project_id}}:{{user_id}}'
    IS_ADMIN_OR_OWNER = f'{CACHE_VERSION}:projects:is_admin_or_owner:{{project_id}}:{{user_id}}'


CACHE_NONE_SENTINEL = '__CACHE_NONE__'
CACHE_FALSE_SENTINEL = '__CACHE_FALSE__'


def safe_cache_get(key: str, default=None):
    try:
        return cache.get(key, default=default)
    except ConnectionError:
        logger.warning('Redis unavailable on get', extra={'key': key})
        return default


def safe_cache_set(key: str, value, ttl: int) -> bool:
    try:
        cache.set(key, value, ttl)
        return True
    except ConnectionError:
        logger.warning('Redis unavailable on set', extra={'key': key})
        return False


def cache_with_lock(key: str, ttl: int, fetch_func, lock_ttl: int = 10):
    cached = safe_cache_get(key)

    if cached in (CACHE_NONE_SENTINEL, CACHE_FALSE_SENTINEL):
        return cached
    if cached is not None:
        return cached

    lock_key = f"{key}:lock"

    try:
        lock_acquired = cache.add(lock_key, "locked", lock_ttl)
    except Exception:
        lock_acquired = False

    jitter_max = max(1, ttl // 10)

    if lock_acquired:
        try:
            value = fetch_func()
            jitter = random.randint(0, jitter_max)
            safe_cache_set(key, value, ttl + jitter)
            return value
        finally:
            try:
                cache.delete(lock_key)
            except Exception:
                pass

    for _ in range(20):
        time.sleep(0.05)
        cached = safe_cache_get(key)

        if cached in (CACHE_NONE_SENTINEL, CACHE_FALSE_SENTINEL):
            return cached
        if cached is not None:
            return cached

    # не дождались — сами генерим и всё равно кэшируем
    value = fetch_func()
    jitter = random.randint(0, jitter_max)
    safe_cache_set(key, value, ttl + jitter)
    return value


def invalidate_project_cache(project_id: int) -> None:
    cache.delete(CacheKeys.PROJECT_DETAIL.format(project_id=project_id))


def invalidate_membership_cache(project_id: int, user_id: int) -> None:
    keys = [
        CacheKeys.MEMBER_ROLE.format(project_id=project_id, user_id=user_id),
        CacheKeys.EXISTS_MEMBER.format(project_id=project_id, user_id=user_id),
        CacheKeys.IS_ADMIN_OR_OWNER.format(project_id=project_id, user_id=user_id),
    ]
    cache.delete_many(keys)


def invalidate_all_project_caches(project_id: int, user_ids: list[int]) -> None:
    invalidate_project_cache(project_id)
    for user_id in user_ids:
        invalidate_membership_cache(project_id, user_id)
