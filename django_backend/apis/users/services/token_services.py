from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from django_backend.redis import redis_blacklist_refresh_token, is_token_blacklisted


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    if api_settings.UPDATE_LAST_LOGIN:
        update_last_login(None, user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def refresh_access_token(refresh_token: str):
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError:
        raise InvalidToken("Invalid refresh token")
    
    if is_token_blacklisted(refresh["jti"]):
        raise InvalidToken("Token is blacklisted")

    data = {"access": str(refresh.access_token)}

    # Replication the logic found in SimpleJWT's TokenRefreshSerializer 
    # (because I bypassed it so I could put the refresh token as a cookie and backed it up with redis😁)
    if api_settings.ROTATE_REFRESH_TOKENS:
        if api_settings.BLACKLIST_AFTER_ROTATION:
            redis_blacklist_refresh_token(
                jti=refresh["jti"],
                exp=refresh["exp"]
            )
            
            # try:
            #     refresh.blacklist() # this is the default DB-backed blacklist
            # except AttributeError:
            #     pass

        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

        data["refresh"] = str(refresh)

    return data


def blacklist_refresh_token(refresh_token):
    """Called when a user logs out."""
    try:
        token = RefreshToken(refresh_token)
        redis_blacklist_refresh_token(
            jti=token["jti"],
            exp=token["exp"]
        )
        # token.blacklist()  # this is the default DB-backed blacklist
    except TokenError:
        pass  # token already invalid or expired → ignore
