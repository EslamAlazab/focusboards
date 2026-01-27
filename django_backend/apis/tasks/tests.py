from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apis.projects.models import Project
from apis.boards.models import Board
from apis.columns.models import Column
from apis.tasks.models import Task

User = get_user_model()

class TaskTests(APITestCase):
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
        
        self.column = Column.objects.create(
            title='To Do',
            order=1,
            board=self.board,
            owner=self.user
        )
        
        self.column_tasks_url = reverse('column_tasks', kwargs={'column_id': self.column.id})
        self.unassigned_tasks_url = reverse('unassigned_tasks', kwargs={'board_id': self.board.id})

    def test_create_task_in_column(self):
        """Test creating a task in a specific column."""
        data = {
            'title': 'New Task',
            'order': 1,
            'content': 'Task content',
            'column_id': self.column.id
        }
        response = self.client.post(self.column_tasks_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        
        task = Task.objects.get()
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.column, self.column)
        self.assertEqual(task.board, self.board)
        self.assertEqual(task.owner, self.user)

    def test_list_column_tasks(self):
        """Test listing tasks for a specific column."""
        Task.objects.create(
            title='Existing Task',
            order=1,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        
        response = self.client.get(self.column_tasks_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Task')

    def test_update_task(self):
        """Test updating a task via tasksView."""
        task = Task.objects.create(
            title='Original Title',
            order=1,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        
        url = reverse('tasks-detail', kwargs={'pk': task.id})
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')

    def test_delete_task(self):
        """Test deleting a task via tasksView."""
        task = Task.objects.create(
            title='To Delete',
            order=1,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        
        url = reverse('tasks-detail', kwargs={'pk': task.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_create_unassigned_task(self):
        """Test creating a task that is not assigned to any column."""
        data = {
            'title': 'Unassigned Task',
            'order': 1,
            'content': 'Content'
        }
        response = self.client.post(self.unassigned_tasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(id=response.data['id'])
        self.assertIsNone(task.column)
        self.assertEqual(task.board, self.board)

    def test_list_unassigned_tasks(self):
        """Test listing unassigned tasks for a board."""
        Task.objects.create(
            title='Unassigned',
            order=1,
            board=self.board,
            column=None,
            owner=self.user
        )
        # Create a task in a column to ensure it's not returned
        Task.objects.create(
            title='Assigned',
            order=2,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        
        response = self.client.get(self.unassigned_tasks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Unassigned')

    def test_transfer_unassigned_task_to_column(self):
        """Test moving an unassigned task to a column."""
        task = Task.objects.create(
            title='Unassigned',
            order=1,
            board=self.board,
            column=None,
            owner=self.user
        )
        
        url = reverse('tasks-detail', kwargs={'pk': task.id})
        data = {'column': self.column.id}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        task.refresh_from_db()
        self.assertEqual(task.column, self.column)

    def test_transfer_task_between_columns(self):
        """Test moving a task from one column to another."""
        column2 = Column.objects.create(
            title='Done',
            order=2,
            board=self.board,
            owner=self.user
        )
        
        task = Task.objects.create(
            title='Moving Task',
            order=1,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        
        url = reverse('tasks-detail', kwargs={'pk': task.id})
        data = {'column': column2.id}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        task.refresh_from_db()
        self.assertEqual(task.column, column2)

    def test_retrieve_task(self):
        """Test retrieving a single task details."""
        task = Task.objects.create(
            title='Detail Task',
            order=1,
            board=self.board,
            column=self.column,
            owner=self.user
        )
        url = reverse('tasks-detail', kwargs={'pk': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')
