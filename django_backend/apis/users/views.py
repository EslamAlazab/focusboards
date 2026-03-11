from django.contrib.auth import login, logout as django_logout, get_user_model
from django.db import transaction
from django.conf import settings
from django.middleware.csrf import get_token

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken

from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, VerifyEmailSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer, ChangePasswordSerializer,
    GoogleAuthSerializer, ResendVerificationSerializer
)
from .schemas import (
    register_view_schema, verify_email_view_schema, session_login_view_schema, token_login_view_schema,
    cookie_token_refresh_view_schema, logout_schema, me_view_schema, resend_verification_view_schema,
    password_reset_view_schema, password_reset_confirm_view_schema, password_change_view_schema, 
    google_auth_view_schema, guest_auth_view_schema, guest_register_view_schema
)
from apis.users.services.token_services import (
    generate_tokens_for_user, refresh_access_token, blacklist_refresh_token
    )
from apis.users.services.google_auth_service import GoogleAuthService, GoogleAuthError
from apis.users.services.guest_services import GuestServices
from apis.users.tasks import send_verification_email_task ,send_password_reset_email_task

import logging

User = get_user_model()

logger = logging.getLogger(__name__)

@register_view_schema
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        transaction.on_commit(
            lambda: send_verification_email_task.delay(user.pk)
        )


@resend_verification_view_schema
class ResendVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        if user and not user.is_email_verified:
            transaction.on_commit(
                lambda: send_verification_email_task.delay(user.pk)
            )

        return Response(
            {
                "detail": (
                    "If an account with this email exists and is not verified, "
                    "a verification email has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )
        

@verify_email_view_schema
class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyEmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )


@session_login_view_schema
class SessionLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)

        response = Response({
            "detail": "Logged in successfully"
        })

        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=get_token(request),
            httponly=False,
            secure=not settings.DEBUG,
            samesite="Lax",
        )

        return response
    

@token_login_view_schema
class TokenLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = generate_tokens_for_user(user)

        response = Response({"access": tokens["access"]})

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )

        return response


@cookie_token_refresh_view_schema
class CookieTokenRefreshView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise InvalidToken("No refresh token found")

        tokens = refresh_access_token(refresh_token)

        response = Response({"access": tokens["access"]})

        if "refresh" in tokens:
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )

        return response


@logout_schema
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """handle both session and token based authentication"""
        django_logout(request) #(safe even if no session)

        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            blacklist_refresh_token(refresh_token)

        response = Response(
            {"detail": "Logged out successfully"},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie(
            key="refresh_token",
            samesite="Lax",
        )

        return response


@password_reset_view_schema
class PasswordResetView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class=PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()

        if user:
            transaction.on_commit(
                lambda:send_password_reset_email_task.delay(user.pk)
                )
            
        return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)


@password_reset_confirm_view_schema
class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)


@password_change_view_schema
class PasswordChangeView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    http_method_names= ['patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
    

@google_auth_view_schema
class GoogleAuthView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = GoogleAuthSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user, tokens = GoogleAuthService.authenticate(
                request=request,
                id_token=serializer.validated_data["id_token"],
            )
        except GoogleAuthError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        response = GoogleAuthService.build_DRF_response(user, tokens)

        return response
    

@me_view_schema
class MeView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


@guest_auth_view_schema
class GuestAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = GuestServices.gen_guest_user()
        tokens = generate_tokens_for_user(user)

        response = Response({
            "access": tokens["access"],
            "username": user.username,
            "is_guest": True
        }, status=201)

        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        return response
    

@guest_register_view_schema
class GuestRegisterView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer

    def post(self, request):
        if not request.user.is_guest:
            return Response({"detail": "Not a guest user"}, status=400)
        
        GuestServices.guest_register(self, request)
        
        return Response({
            "message": "Account upgraded successfully"
        })
    
    