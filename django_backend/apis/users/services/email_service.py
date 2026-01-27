import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_verification_email(user):
        uid, token = EmailService._generate_user_token(user)
        verify_link = EmailService._gen_verification_link(uid, token)

        EmailService._send_email(
            subject="Verify your email for FocusBoards",
            recipient=user.email,
            template="users/verification_email.html",
            context={"verify_link": verify_link},
            fallback_message=f"Verify your email here: {verify_link}",
            user=user,
        )

    @staticmethod
    def send_password_reset_email(user):
        uid, token = EmailService._generate_user_token(user)
        reset_link = EmailService._gen_password_reset_link(uid, token)

        EmailService._send_email(
            subject="Reset your password",
            recipient=user.email,
            template="users/password_reset_email.html",
            context={"reset_link": reset_link},
            fallback_message=f"Reset your password here: {reset_link}",
            user=user,
        )

    @staticmethod
    def _generate_user_token(user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

    @staticmethod
    def _gen_verification_link(uid, token):
        return f"{settings.VERIFICATION_EMAIL_URL}/?uidb64={uid}&token={token}"

    @staticmethod
    def _gen_password_reset_link(uid, token):
        return f"{settings.PASSWORD_RESET_URL}/?uidb64={uid}&token={token}"    

    @staticmethod
    def _send_email(
        *,
        subject,
        recipient,
        template,
        context,
        fallback_message,
        user,
    ):
        html_message = EmailService._render_template(
            template=template,
            context=context,
            user=user,
        )

        send_mail(
            subject=subject,
            message=fallback_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )

    @staticmethod
    def _render_template(*, template, context, user):
        try:
            return render_to_string(template, context)

        except TemplateDoesNotExist:
            logger.warning(
                "Email template missing: %s | user_id=%s email=%s",
                template,
                user.pk,
                user.email,
            )
            return None

        except Exception as exc:
            logger.exception(
                "Error rendering email template: %s | user_id=%s email=%s "
                "error_type=%s error=%s",
                template,
                user.pk,
                user.email,
                type(exc).__name__,
                str(exc),
            )
            return None
