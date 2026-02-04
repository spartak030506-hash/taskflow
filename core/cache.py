from django.core.cache import cache


class CacheTTL:
    PROJECT = 60 * 10  # 10 минут
    MEMBERSHIP = 60 * 5  # 5 минут


class CacheKeys:
    PROJECT_BY_ID = 'projects:by_id:{project_id}'
    MEMBER_ROLE = 'projects:member_role:{project_id}:{user_id}'
    EXISTS_MEMBER = 'projects:exists_member:{project_id}:{user_id}'
    IS_ADMIN_OR_OWNER = 'projects:is_admin_or_owner:{project_id}:{user_id}'


CACHE_NONE_SENTINEL = '__CACHE_NONE__'


def invalidate_project_cache(project_id: int) -> None:
    cache.delete(CacheKeys.PROJECT_BY_ID.format(project_id=project_id))


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
