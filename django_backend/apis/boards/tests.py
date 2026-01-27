from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apis.projects.models import Project
from apis.boards.models import Board

User = get_user_model()

class BoardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        
        self.project_boards_url = reverse('project-boards', kwargs={'project_id': self.project.id})

    def test_create_board(self):
        """Test creating a board for a specific project."""
        data = {
            'title': 'Development Board',
            'description': 'Board for dev tasks'
        }
        response = self.client.post(self.project_boards_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Board.objects.count(), 1)
        
        board = Board.objects.get()
        self.assertEqual(board.title, 'Development Board')
        self.assertEqual(board.project, self.project)
        self.assertEqual(board.owner, self.user)

    def test_list_boards(self):
        """Test listing boards belonging to a project."""
        Board.objects.create(title='Board 1', project=self.project, owner=self.user)
        Board.objects.create(title='Board 2', project=self.project, owner=self.user)
        
        response = self.client.get(self.project_boards_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_board(self):
        """Test retrieving a specific board."""
        board = Board.objects.create(title='My Board', project=self.project, owner=self.user)
        url = reverse('boards-detail', kwargs={'pk': board.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Board')

    def test_update_board(self):
        """Test updating a board."""
        board = Board.objects.create(title='Old Title', project=self.project, owner=self.user)
        url = reverse('boards-detail', kwargs={'pk': board.id})
        
        data = {'title': 'New Title'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        board.refresh_from_db()
        self.assertEqual(board.title, 'New Title')

    def test_delete_board(self):
        """Test deleting a board."""
        board = Board.objects.create(title='To Delete', project=self.project, owner=self.user)
        url = reverse('boards-detail', kwargs={'pk': board.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 0)

    def test_create_board_invalid_project(self):
        """Test creating a board for a project not owned by the user."""
        other_user = User.objects.create_user(username='other', email='other@example.com', password='password123')
        other_project = Project.objects.create(name='Other Project', owner=other_user)
        
        url = reverse('project-boards', kwargs={'project_id': other_project.id})
        data = {'title': 'Intruder Board'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_access_other_user_board(self):
        """Test accessing a board owned by another user."""
        other_user = User.objects.create_user(username='other', email='other@example.com', password='password123')
        other_project = Project.objects.create(name='Other Project', owner=other_user)
        other_board = Board.objects.create(title='Other Board', project=other_project, owner=other_user)
        
        url = reverse('boards-detail', kwargs={'pk': other_board.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API."""
        self.client.logout()
        response = self.client.get(self.project_boards_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)