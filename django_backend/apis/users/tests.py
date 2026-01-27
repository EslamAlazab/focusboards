from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from django.template import TemplateDoesNotExist
from django.core.cache import cache
from unittest.mock import patch
import uuid

from apis.users.services.auth_services import authenticate_with_username_or_email, UidTokenMixin
from apis.users.services.token_services import generate_tokens_for_user, refresh_access_token, blacklist_refresh_token
from apis.users.services.email_service import EmailService
from apis.projects.models import Project
from apis.boards.models import Board
from apis.columns.models import Column
from apis.tasks.models import Task

User = get_user_model()

class BaseUserTest(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123!'
        }

    def tearDown(self):
        cache.clear()


class RegistrationTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.register_url = reverse('auth_register')
        self.verify_email_url = reverse('auth_verify_email')
        self.resend_verification_url = reverse('resend_verification_email')

    def test_register_user(self):
        """Test user registration"""
        with patch('apis.users.views.send_verification_email_task') as mock_task:
            with patch('apis.users.views.transaction.on_commit') as mock_on_commit:
                mock_on_commit.side_effect = lambda func: func() # force it to run as there is no commit here
                
                response = self.client.post(self.register_url, self.user_data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(User.objects.count(), 1)
                self.assertEqual(User.objects.get().email, 'test@example.com')
                mock_task.delay.assert_called_once()

    def test_verify_email(self):
        """Test email verification logic"""
        user = User.objects.create_user(**self.user_data)
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        data = {
            'uidb64': uid,
            'token': token
        }
        
        response = self.client.post(self.verify_email_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_resend_verification_email(self):
        """Test resending verification email"""
        user = User.objects.create_user(**self.user_data)
        # is_email_verified is False by default
        
        with patch('apis.users.views.send_verification_email_task') as mock_task:
            with patch('apis.users.views.transaction.on_commit') as mock_on_commit:
                mock_on_commit.side_effect = lambda func: func()
                
                response = self.client.post(self.resend_verification_url, {'email': self.user_data['email']}, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                mock_task.delay.assert_called_once()


class AuthenticationTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.login_url = reverse('token_login')
        self.logout_url = reverse('auth_logout')
        self.user = User.objects.create_user(
            **self.user_data
        )

    def test_login_by_email(self):
        """Test user login by email and token generation"""

        response = self.client.post(self.login_url, {
            'username_or_email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh_token', response.cookies)
    
    def test_login_by_username(self):
        """Test user login by username and token generation"""

        response = self.client.post(self.login_url, {
            'username_or_email': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh_token', response.cookies)

    def test_refresh_token(self):
        """Test refreshing access token using cookie"""
        
        # Login to get refresh token
        login_resp = self.client.post(self.login_url, {
            'username_or_email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        refresh_token = login_resp.cookies['refresh_token'].value
        
        # Set cookie for refresh request
        self.client.cookies['refresh_token'] = refresh_token
        refresh_url = reverse('token_refresh')
        
        response = self.client.post(refresh_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout(self):
        """Test logout clears cookies"""
        login_resp = self.client.post(self.login_url, {
            'username_or_email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        self.client.cookies['refresh_token'] = login_resp.cookies['refresh_token'].value
        
        response = self.client.post(self.logout_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['refresh_token'].value, '')


class UserProfileTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.me_url = reverse('users_me')

    def test_me_view_authenticated(self):
        """Test retrieving user profile"""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_me_view_unauthenticated(self):
        """Test retrieving user profile without auth"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PasswordTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.password_reset_url = reverse('auth_password_reset')
        self.password_change_url = reverse('auth_password_change')
        self.login_url = reverse('token_login')
        self.user = User.objects.create_user(
            **self.user_data
        )

    def test_password_reset_request(self):
        """Test password reset email request"""        
        with patch('apis.users.views.send_password_reset_email_task') as mock_task:
            with patch('apis.users.views.transaction.on_commit') as mock_on_commit:
                mock_on_commit.side_effect = lambda func: func()
                
                response = self.client.post(self.password_reset_url, {'email': self.user_data['email']}, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                mock_task.delay.assert_called_once()

    def test_change_password(self):
        """Test password change"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': self.user_data['password'],
            'new_password': 'NewPassword123!'
        }
        
        response = self.client.patch(self.password_change_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.client.logout()
        login_resp = self.client.post(self.login_url, {
            'username_or_email': self.user_data['email'],
            'password': 'NewPassword123!'
        }, format='json')
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)


class AuthServicesTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(**self.user_data)

    def test_authenticate_with_username_or_email(self):
        """Test authentication with valid credentials"""
        # Test with username
        user = authenticate_with_username_or_email(
            self.user_data['username'], 
            self.user_data['password']
        )
        self.assertEqual(user, self.user)

        # Test with email
        user = authenticate_with_username_or_email(
            self.user_data['email'], 
            self.user_data['password']
        )
        self.assertEqual(user, self.user)

    def test_authenticate_failures(self):
        """Test authentication failures"""
        # Invalid password
        with self.assertRaises(AuthenticationFailed):
            authenticate_with_username_or_email(self.user_data['username'], 'WrongPass')
            
        # Invalid user
        with self.assertRaises(AuthenticationFailed):
            authenticate_with_username_or_email('nonexistent', self.user_data['password'])
            
        # Inactive user
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(AuthenticationFailed):
            authenticate_with_username_or_email(self.user_data['username'], self.user_data['password'])

    def test_uid_token_mixin(self):
        """Test UidTokenMixin helper methods"""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Test valid uid retrieval
        retrieved_user = UidTokenMixin._get_user_from_uid(uid)
        self.assertEqual(retrieved_user, self.user)
        
        # Test valid token validation (should not raise)
        UidTokenMixin._validate_token(self.user, token)
        
        # Test invalid uid
        with self.assertRaises(serializers.ValidationError):
            UidTokenMixin._get_user_from_uid("invalid_base64")
            
        # Test non-existent user uid
        fake_uid = urlsafe_base64_encode(force_bytes(uuid.uuid4()))
        with self.assertRaises(serializers.ValidationError):
            UidTokenMixin._get_user_from_uid(fake_uid)
            
        # Test invalid token
        with self.assertRaises(serializers.ValidationError):
            UidTokenMixin._validate_token(self.user, "invalid_token")


class TokenServicesTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(**self.user_data)

    def test_generate_tokens(self):
        tokens = generate_tokens_for_user(self.user)
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)

    def test_refresh_access_token(self):
        tokens = generate_tokens_for_user(self.user)
        refresh_token = tokens['refresh']
        
        new_tokens = refresh_access_token(refresh_token)
        self.assertIn('access', new_tokens)
        
        # Test invalid token
        with self.assertRaises(InvalidToken):
            refresh_access_token("invalid_token")

    def test_blacklist_refresh_token(self):
        tokens = generate_tokens_for_user(self.user)
        refresh_token = tokens['refresh']
        
        blacklist_refresh_token(refresh_token)
        
        # Verify it's blacklisted by trying to use it
        with self.assertRaises(InvalidToken) as exc:
            refresh_access_token(refresh_token)
        self.assertIn("Token is blacklisted", str(exc.exception))

    def test_refresh_token_rotation_and_blacklisting(self):
        """
        Test that after refreshing, the old refresh token is blacklisted
        and cannot be used again.
        """
        # This test relies on SIMPLE_JWT settings for rotation and blacklisting
        # being enabled, which they are in settings.py.

        # 1. Generate initial tokens
        tokens = generate_tokens_for_user(self.user)
        old_refresh_token = tokens["refresh"]

        # 2. Refresh the token, which should rotate it and blacklist the old one
        new_tokens = refresh_access_token(old_refresh_token)
        self.assertIn("access", new_tokens)
        self.assertIn("refresh", new_tokens)
        self.assertNotEqual(old_refresh_token, new_tokens["refresh"])

        # 3. Try to use the old refresh token again
        # This should fail because it's now blacklisted.
        with self.assertRaises(InvalidToken) as exc:
            refresh_access_token(old_refresh_token)
        self.assertIn("Token is blacklisted", str(exc.exception))


class EmailServiceTests(BaseUserTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(**self.user_data)

    @patch('apis.users.services.email_service.send_mail')
    def test_send_verification_email(self, mock_send_mail):
        EmailService.send_verification_email(self.user)
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn(self.user.email, kwargs['recipient_list'])
        self.assertIn('Verify your email', kwargs['subject'])

    @patch('apis.users.services.email_service.send_mail')
    def test_send_password_reset_email(self, mock_send_mail):
        EmailService.send_password_reset_email(self.user)
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn(self.user.email, kwargs['recipient_list'])
        self.assertIn('Reset your password', kwargs['subject'])

    @patch('apis.users.services.email_service.render_to_string')
    @patch('apis.users.services.email_service.logger')
    def test_render_template_errors(self, mock_logger, mock_render):
        # Test TemplateDoesNotExist
        mock_render.side_effect = TemplateDoesNotExist("missing.html")
        result = EmailService._render_template(
            template="missing.html", 
            context={}, 
            user=self.user
        )
        self.assertIsNone(result)
        mock_logger.warning.assert_called()

        # Test other Exception
        mock_render.side_effect = Exception("Random error")
        result = EmailService._render_template(
            template="error.html", 
            context={}, 
            user=self.user
        )
        self.assertIsNone(result)
        mock_logger.exception.assert_called()


class GuestIntegrationTests(APITestCase):
    def setUp(self):
        self.guest_auth_url = reverse('auth_guest')
        self.guest_register_url = reverse('auth_guest_register')

    def test_guest_lifecycle_and_data_transfer(self):
        """
        Test the full lifecycle of a guest user:
        1. Login as guest
        2. Create resources (Project, Board, Column, Task)
        3. Register (upgrade) account
        4. Verify resources still belong to user
        """
        # 1. Login as guest
        response = self.client.post(self.guest_auth_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_guest'])
        access_token = response.data['access']
        
        # Authenticate client with guest token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        user = User.objects.get(username=response.data['username'])
        self.assertTrue(user.is_guest)

        # 2. Create resources
        project = Project.objects.create(name="Guest Project", owner=user)
        
        board = Board.objects.create(title="Guest Board", project=project, owner=user)
        
        column = Column.objects.create(title="Guest Column", order=1, board=board, owner=user)
        
        task = Task.objects.create(
            title="Guest Task", 
            order=1, 
            board=board, 
            column=column, 
            owner=user
        )

        # Verify ownership before registration
        self.assertEqual(project.owner, user)
        self.assertEqual(task.owner, user)

        # 3. Register (upgrade) guest
        register_data = {
            'username': 'new_username', 
            'email': 'realuser@example.com',
            'password': 'StrongPassword123!'
        }
        
        response = self.client.post(self.guest_register_url, register_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh user from DB
        user.refresh_from_db()
        
        # Verify user attributes updated
        self.assertFalse(user.is_guest)
        self.assertEqual(user.email, 'realuser@example.com')
        self.assertTrue(user.check_password('StrongPassword123!'))
        self.assertIsNone(user.expires_at)

        # 4. Verify data transfer (ownership should remain)
        project.refresh_from_db()
        task.refresh_from_db()
        
        self.assertEqual(project.owner, user)
        self.assertEqual(task.owner, user)
        self.assertEqual(task.board.owner, user)
    
    def test_register_normal_user(self):
        user = User.objects.create_user(
            username='testuser',
            email = 'test@example.com',
            password = 'StrongPassword123!')
        self.client.force_authenticate(user=user)
        response = self.client.post(self.guest_register_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
