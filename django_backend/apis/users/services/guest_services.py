import uuid
from datetime import timedelta
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.request import Request

from apis.users.models import User

class GuestServices:
    @staticmethod
    def gen_guest_user()-> User:
        username = f"guest_{uuid.uuid4().hex[:10]}"

        user = User.objects.create(
            username=username,
            is_guest=True,
            expires_at=timezone.now() + timedelta(days=1),
        )
        user.set_unusable_password()
        user.save()
        return user
    
    @staticmethod
    def guest_register(self, request: Request)-> None | Response:
        user: User = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.email = serializer.validated_data["email"]
        user.username = serializer.validated_data["username"]
        user.set_password(serializer.validated_data["password"])
        user.is_guest = False
        user.expires_at = None
        user.save()