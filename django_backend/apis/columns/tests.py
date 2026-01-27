from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apis.projects.models import Project
from apis.boards.models import Board
from apis.columns.models import Column

User = get_user_model()

class ColumnTests(APITestCase):
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
        
        self.board = Board.objects.create(
            title='Test Board',
            project=self.project,
            owner=self.user
        )
        
        self.board_columns_url = reverse('board_column', kwargs={'board_id': self.board.id})

    def test_create_column(self):
        """Test creating a column on a board."""
        data = {
            'title': 'To Do',
            'order': 1
        }
        response = self.client.post(self.board_columns_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Column.objects.count(), 1)
        
        column = Column.objects.get()
        self.assertEqual(column.title, 'To Do')
        self.assertEqual(column.board, self.board)
        self.assertEqual(column.owner, self.user)

    def test_create_column_on_other_user_board(self):
        """Test that a user cannot create a column on someone else's board."""
        other_user = User.objects.create_user(username='other', email='other@example.com', password='password123')
        other_project = Project.objects.create(name='Other Project', owner=other_user)
        other_board = Board.objects.create(title='Other Board', project=other_project, owner=other_user)
        
        url = reverse('board_column', kwargs={'board_id': other_board.id})
        data = {'title': 'Intruder Column', 'order': 1}
        
        response = self.client.post(url, data)
        
        # Should return 404 because the view filters board by owner=request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_move_column_to_other_user_board(self):
        """Test that a user cannot move a column to someone else's board."""
        column = Column.objects.create(title='My Column', order=1, board=self.board, owner=self.user)
        
        other_user = User.objects.create_user(username='other', email='other@example.com', password='password123')
        other_project = Project.objects.create(name='Other Project', owner=other_user)
        other_board = Board.objects.create(title='Other Board', project=other_project, owner=other_user)
        
        url = reverse('columns-detail', kwargs={'pk': column.id})
        data = {'board': other_board.id}
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You can only create or move columns to your own boards.", str(response.data))
