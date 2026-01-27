from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from .services.email_service import EmailService
from .models import User

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_verification_email_task(user):
    EmailService.send_verification_email(user)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_password_reset_email_task(user):
    EmailService.send_password_reset_email(user)


@shared_task
def delete_expired_guests():
    cutoff = timezone.now() - timedelta(days=1)
    User.objects.filter(
        is_guest=True,
        expires_at__lt=cutoff
    ).delete()