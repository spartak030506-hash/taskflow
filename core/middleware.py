from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = self._get_token_from_scope(scope)
        get_user = database_sync_to_async(self._get_user_from_token, thread_sensitive=True)
        scope['user'] = await get_user(token)
        return await super().__call__(scope, receive, send)

    def _get_token_from_scope(self, scope):
        query_string = scope.get('query_string', b'').decode()
        params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
        return params.get('token')

    def _get_user_from_token(self, token_string):
        if not token_string:
            logger.debug('JWT auth: no token provided')
            return AnonymousUser()

        try:
            token = AccessToken(token_string)
            user_id = token['user_id']
            user = User.objects.get(id=user_id, is_active=True)

            logger.debug(
                f'JWT auth success: user_id={user_id}',
                extra={'user_id': user_id, 'email': user.email}
            )

            return user

        except User.DoesNotExist:
            logger.warning(
                f'JWT auth failed: user not found or inactive',
                extra={'user_id': user_id}
            )
            return AnonymousUser()

        except Exception as e:
            logger.warning(
                f'JWT auth failed: {type(e).__name__}: {e}',
                extra={'token_preview': token_string[:20] if token_string else None}
            )
            return AnonymousUser()
