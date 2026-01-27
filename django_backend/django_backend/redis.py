import time

from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


def is_token_blacklisted(jti):
    return cache.get(f"blacklist:{jti}") is not None


def redis_blacklist_refresh_token(jti, exp):
    """
    jti: token unique id
    exp: expiration timestamp (seconds)
    """
    ttl = int(exp - time.time())
    if ttl > 0:
        cache.set(f"blacklist:{jti}", True, timeout=ttl)


#only used if we don't override the refresh token behavior
class RedisJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)

        jti = token.get("jti")
        if jti and is_token_blacklisted(jti):
            raise AuthenticationFailed("Token is blacklisted")

        return token