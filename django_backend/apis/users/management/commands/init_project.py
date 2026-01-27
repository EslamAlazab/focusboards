import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = "Initialize project: create admin user & celery schedules"

    def handle(self, *args, **options):
        self.create_admin_user()
        self.create_guest_cleanup_task()

    def create_admin_user(self):
        username = settings.DEFAULT_ADMIN_USERNAME
        email = settings.DEFAULT_ADMIN_EMAIL
        password = settings.DEFAULT_ADMIN_PASSWORD

        if User.objects.filter(username=username).exists():
            self.stdout.write("Admin user already exists")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write("Admin user created")

    def create_guest_cleanup_task(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
        )

        task, created = PeriodicTask.objects.get_or_create(
            name="Delete expired guest users",
            defaults={
                "task": "apis.users.tasks.delete_expired_guests",
                "crontab": schedule,
                "args": json.dumps([]),
            },
        )

        if created:
            self.stdout.write("Celery periodic task created")
        else:
            self.stdout.write("Celery periodic task already exists")
