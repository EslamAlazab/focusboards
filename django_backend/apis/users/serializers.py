from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers


from .services.auth_services import authenticate_with_username_or_email, UidTokenMixin

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_email_verified', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'is_email_verified', "email")


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate_with_username_or_email(
            data["username_or_email"],
            data["password"]
        )
        data["user"] = user
        return data
    

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user #Used in email verification


class VerifyEmailSerializer(UidTokenMixin, serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        user = self._get_user_from_uid(attrs["uidb64"])
        self._validate_token(user, attrs["token"])

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]

        if user.is_email_verified:
            return user

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return user


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address used during registration"
    )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(UidTokenMixin, serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate(self, attrs):
        user = self._get_user_from_uid(attrs['uidb64'])
        self._validate_token(user, attrs['token'])

        self.user = user
        return attrs

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class GoogleAuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    user = UserSerializer()
    message = serializers.CharField()


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_active', 'is_staff')
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user