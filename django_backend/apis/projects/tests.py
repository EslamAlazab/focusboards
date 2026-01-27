from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Project
from django.utils.timezone import now


User = get_user_model()
class UserProjectsViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="user@test.com",
            password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@test.com",
            password="password123"
        )

        self.url = reverse("user-projects-list")
    
    def test_authentication_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_only_sees_own_projects(self):
        Project.objects.create(name="User Project", owner=self.user)
        Project.objects.create(name="Other Project", owner=self.other_user)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]["name"], "User Project")
    
    def test_projects_are_ordered_by_created_at(self):
        p1 = Project.objects.create(
            name="Old Project",
            owner=self.user,
        )
        p2 = Project.objects.create(
            name="New Project",
            owner=self.user,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data['results'][0]["id"], str(p1.id))
        self.assertEqual(response.data['results'][1]["id"], str(p2.id))

    def test_search_projects_by_name(self):
        Project.objects.create(name="Django API", owner=self.user)
        Project.objects.create(name="FastAPI App", owner=self.user)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"search": "Django"})

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]["name"], "Django API")

    def test_create_project_sets_owner_automatically(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "name": "My Project"
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        project = Project.objects.get(id=response.data["id"])
        self.assertEqual(project.owner, self.user)
    
    def test_user_cannot_create_project_for_another_user(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "name": "Hacked Project",
            "owner": self.other_user.id
        }

        response = self.client.post(self.url, payload)

        project = Project.objects.get(id=response.data["id"])
        self.assertEqual(project.owner, self.user)

    def test_response_contains_expected_fields(self):
        Project.objects.create(name="Test Project", owner=self.user)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertIn("id", response.data['results'][0])
        self.assertIn("name", response.data['results'][0])
        self.assertIn("description", response.data['results'][0])
        self.assertIn("owner", response.data['results'][0])
        self.assertIn("created_at", response.data['results'][0])
