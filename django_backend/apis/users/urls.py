from django.urls import path
from . import views


urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth_register'),
    path('auth/verify-email/', views.VerifyEmailView.as_view(), name='auth_verify_email'),
    path('auth/resend-verification-email/', views.ResendVerificationView.as_view(), name='resend_verification_email'),
    path('auth/session/login/', views.SessionLoginView.as_view(), name='session_login'),
    path('auth/token/login/', views.TokenLoginView.as_view(), name='token_login'),
    path('auth/refresh/', views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth_logout'),
    path('auth/password/reset/', views.PasswordResetView.as_view(), name='auth_password_reset'),
    path('auth/password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    path('auth/password/change/', views.PasswordChangeView.as_view(), name='auth_password_change'),
    path('auth/google/', views.GoogleAuthView.as_view(), name='auth_google'),
    path('auth/guest/', views.GuestAuthView.as_view(), name= "auth_guest"),
    path('auth/guest/register/', views.GuestRegisterView.as_view(), name= "auth_guest_register"),
    path('users/me/', views.MeView.as_view(), name='users_me'),
]