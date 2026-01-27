from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def authenticate_with_username_or_email(identifier: str, password: str):
    """
    Authenticate a user using username OR email.
    Executes a single DB query.
    """
    user = _get_user_by_identifier(identifier)

    if not user.check_password(password):
        raise AuthenticationFailed("Invalid credentials")
    
    if not user.is_active:
        raise AuthenticationFailed("User is disabled")

    return user


def _get_user_by_identifier(identifier):
    try:
        return User.objects.get(
            Q(username__iexact=identifier) |
            Q(email__iexact=identifier)
        )
    except User.DoesNotExist:
        raise AuthenticationFailed("Invalid credentials")
    

class UidTokenMixin:
    @staticmethod
    def _get_user_from_uid(uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "Invalid uid"})

    @staticmethod
    def _validate_token(user, token):
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired token"})