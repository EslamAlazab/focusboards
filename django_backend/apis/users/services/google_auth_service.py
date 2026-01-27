from django.conf import settings
import uuid
from django.contrib.auth import login

from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests

from apis.users.models import User
from apis.users.serializers import UserSerializer
from apis.users.services.token_services import generate_tokens_for_user


class GoogleAuthService:
    @staticmethod
    def authenticate(request, id_token):
        google_user = GoogleAuthError._verify_google_token(id_token)
        if not google_user:
            raise GoogleAuthError("Invalid Google token")

        user = GoogleAuthService._get_or_create_user(google_user)
        login(request, user)

        tokens = generate_tokens_for_user(user)
        return user, tokens
    
    @staticmethod 
    def build_DRF_response(self, user, tokens):
        response = Response(
            {
                "access": tokens["access"],
                "user": UserSerializer(user).data,
                "message": "Google login successful",
            }
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        # response.set_cookie(
        #     key=settings.CSRF_COOKIE_NAME,
        #     value=get_token(request),
        #     httponly=False,
        #     secure=not settings.DEBUG,
        #     samesite="Lax",
        # )
        return response
    
    @staticmethod
    def _verify_google_token(token: str):
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
            return idinfo
        except Exception:
            return None

    @staticmethod
    def _get_or_create_user(google_user):
        email = google_user["email"]
        google_id = google_user["sub"]

        user = User.objects.filter(google_id=google_id).first()
        if user:
            return GoogleAuthService._ensure_verified(user)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": GoogleAuthService._generate_username(email),
                "first_name": google_user.get("given_name", ""),
                "last_name": google_user.get("family_name", ""),
                "google_id": google_id,
                "is_email_verified": True,
            },
        )

        if not created and not user.google_id:
            user.google_id = google_id
            user.save(update_fields=["google_id"])

        return GoogleAuthService._ensure_verified(user)

    @staticmethod
    def _ensure_verified(user):
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        return user

    @staticmethod
    def _generate_username(email):
        return f"{email.split('@')[0]}_{uuid.uuid4().hex[:8]}"


class GoogleAuthError(Exception):
    """Raised when Google authentication fails."""
