from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
    OpenApiResponse,
)

from .serializers import (
    RegisterSerializer, VerifyEmailSerializer, LoginSerializer, ResendVerificationSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer, ChangePasswordSerializer,
    GoogleAuthSerializer, GoogleAuthResponseSerializer
)

register_view_schema = extend_schema(
    tags=["auth"],
    summary="Register a new user",
    description=(
        "Create a new user account using username, email, and password. "
        "A verification email is sent to the provided email address. "
        "The account remains inactive until the email is verified."
    ),
    request=RegisterSerializer,
    responses={
        201: RegisterSerializer,
        400: OpenApiResponse(
            description="Validation error (e.g. email already exists, weak password)"
        ),
    },
)

verify_email_view_schema = extend_schema(
    tags=["auth"],
    summary="Verify email address",
    description=(
        "Verify a user's email address using the UID and token sent via email. "
        "Once verified, the user's account status is updated."
    ),
    request=VerifyEmailSerializer,
    responses={
        200: OpenApiResponse(description="Email verified successfully"),
        400: OpenApiResponse(description="Invalid UID or token"),
    },
)

resend_verification_view_schema = extend_schema(
    tags=["auth"],
    summary="Resend verification email",
    description=(
        "Resend the verification email to the user's registered email address. "
        "This endpoint is idempotent and secure; it returns the same response "
        "whether the email exists, is already verified, or is not found, "
        "to prevent email enumeration.\n"
        "The URL format used is: VERIFICATION_EMAIL_URL/?uid64=<uid>&token=<token>"
    ),
    request=ResendVerificationSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Request processed successfully",
            examples=[
                OpenApiExample(
                    name="Success Response",
                    value={"detail": "If an account with this email exists and is not verified, a verification email has been sent."}
                )
            ]
        ),
    },
)

session_login_view_schema = extend_schema(
    tags=["auth"],
    summary="Session based login",
    description="Authenticate a user using either a username or email address and establish a session.",
    request= LoginSerializer,
    responses={        
        200: OpenApiResponse(description="Logged in successfully"),
        400: OpenApiResponse(description="Invalid credentials"),
    },
)


token_login_view_schema = extend_schema(
    tags=["auth"],
    summary="Token based login",
    description=("Authenticate a user using either a username or email address and generate an authentication tokens."
                 "sends the access token and put the refresh token as a cookie"),
    request= LoginSerializer,
    responses={        
        200: OpenApiResponse(description="Logged in successfully", 
                             response=OpenApiTypes.OBJECT,
                             examples=[
                                 OpenApiExample(
                                     name="Token Login Success",
                                     summary="Successful token login",
                                     value={
                                         "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                                     })
                             ]),
        400: OpenApiResponse(description="Invalid credentials"),
    },
)

cookie_token_refresh_view_schema = extend_schema(
    tags=['auth'],
    summary="refresh access token",
    description="Refresh the access token using the refresh token stored in an HttpOnly cookie.",
    request=None,
    responses={
        200: OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Access token refreshed successfully",
            examples=[
                OpenApiExample(
                    name="Refresh Success",
                    summary="Successful token refresh",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                )
            ],
        ),
        401: OpenApiResponse(description="Invalid or expired refresh token"),
    },
)

guest_auth_view_schema = extend_schema(
    tags=["auth"],
    summary="Guest Login",
    description="Create a temporary guest account and return authentication tokens.",
    request=None,
    responses={
        201: OpenApiResponse(
            description="Guest account created successfully",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    name="Guest Login Success",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "username": "guest_92af3c1e",
                        "is_guest": True
                    }
                )
            ]
        ),
    },
)

guest_register_view_schema = extend_schema(
    tags=["auth"],
    summary="Register Guest User",
    description="Convert a guest account into a permanent account by providing username, email and password.",
    request=RegisterSerializer,
    responses={
        200: OpenApiResponse(description="Account upgraded successfully"),
        400: OpenApiResponse(description="Validation error or not a guest user"),
    },
)

logout_schema = extend_schema(
    tags=["auth"],
    summary="Logout",
    description="Logs out the user by clearing the session and deleting the refresh token cookie.",
    request=None,
    responses={
        200: OpenApiResponse(description="Logged out successfully"),
    },
)

me_view_schema= extend_schema(tags=['users'])

password_reset_view_schema = extend_schema(
    tags=["auth"],
    summary="Request password reset",
    description=("Send a password reset link to the user's email address. "
                "The URL format used is: PASSWORD_RESET_URL/?uid64=<uid>&token=<token>"),
    request=PasswordResetSerializer,
    responses={
        200: OpenApiResponse(description="Password reset email sent"),
    },
)

password_reset_confirm_view_schema = extend_schema(
    tags=["auth"],
    summary="Confirm password reset",
    description="Set a new password using the token received via email.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: OpenApiResponse(description="Password reset successfully"),
        400: OpenApiResponse(description="Invalid token or password"),
    },
)

password_change_view_schema = extend_schema(
    tags=["auth"],
    summary="Change password",
    description="Change the authenticated user's password.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description="Password updated successfully"),
        400: OpenApiResponse(description="Invalid old password or weak new password"),
    },
)

google_auth_view_schema = extend_schema(
    tags=["auth"],
    summary="Google Login",
    description="Authenticate a user using a Google ID token.",
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(
            response=GoogleAuthResponseSerializer,
            description="Google login successful",
            examples=[
                OpenApiExample(
                    name="Success",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 1,
                            "email": "user@gmail.com",
                            "username": "user_92af3c1e",
                        },
                        "message": "Google login successful",
                    },
                )
            ],
        ),
        400: OpenApiResponse(description="Invalid Google token"),
    },
)
