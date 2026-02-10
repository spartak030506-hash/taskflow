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
        scope['user'] = await self._get_user_from_token(token)
        return await super().__call__(scope, receive, send)

    def _get_token_from_scope(self, scope):
        query_string = scope.get('query_string', b'').decode()
        params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
        return params.get('token')

    @database_sync_to_async
    def _get_user_from_token(self, token_string):
        if not token_string:
            return AnonymousUser()

        try:
            token = AccessToken(token_string)
            user_id = token['user_id']
            return User.objects.get(id=user_id, is_active=True)
        except Exception as e:
            logger.warning(f'JWT auth failed: {e}')
            return AnonymousUser()
