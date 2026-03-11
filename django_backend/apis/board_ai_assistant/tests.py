from django.urls import reverse
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from django.test import tag
from apis.projects.models import Project
from apis.boards.models import Board
from apis.columns.models import Column
from apis.tasks.models import Task
from .models import BoardAIChat, BoardAIMessage, BoardMemory, AIProviderSettings
from .services.ai_chat_service import BoardAIChatService, MEMORY_SIMILARITY_THRESHOLD

User = get_user_model()

class BaseBoardAITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(name="Test Project", owner=self.user)
        self.board = Board.objects.create(title="Test Board", project=self.project, owner=self.user)


class BoardAIChatTests(BaseBoardAITest):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('board-ai-chats', kwargs={'board_id': self.board.id})

    def test_create_chat(self):
        data = {'title': 'New Chat'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BoardAIChat.objects.count(), 1)
        self.assertEqual(BoardAIChat.objects.get().title, 'New Chat')

    def test_list_chats(self):
        BoardAIChat.objects.create(board=self.board, title="Chat 1")
        BoardAIChat.objects.create(board=self.board, title="Chat 2")
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_update_delete_chat(self):
        chat = BoardAIChat.objects.create(board=self.board, title="Original")
        url = reverse('ai-chat-detail', kwargs={'pk': chat.id})

        # Retrieve
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update
        response = self.client.patch(url, {'title': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chat.refresh_from_db()
        self.assertEqual(chat.title, 'Updated')
        
        # Delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BoardAIChat.objects.count(), 0)


class BoardAIMessageTests(BaseBoardAITest):
    def setUp(self):
        super().setUp()
        self.chat = BoardAIChat.objects.create(board=self.board, title="Chat")
        self.url = reverse('chat-messages', kwargs={'chat_id': self.chat.id})
        
        # Ensure settings exist for the user (required by view)
        AIProviderSettings.objects.create(user=self.user, model_name="test-model", api_key="test-key")

    def test_list_messages(self):
        BoardAIMessage.objects.create(chat=self.chat, role="user", content="Hello")
        BoardAIMessage.objects.create(chat=self.chat, role="assistant", content="Hi there")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    @patch('apis.board_ai_assistant.views.BoardAIChatService')
    def test_send_message_streaming(self, mock_service_cls):
        # Mock the service instance and the generator method
        mock_service_instance = mock_service_cls.return_value
        
        def stream_generator(message):
            yield "data: chunk1\n\n"
            yield "data: chunk2\n\n"
            yield "event: done\n\n"
            
        mock_service_instance.stream_chat_response.side_effect = stream_generator

        data = {'content': 'Hello AI'}
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if it's a streaming response
        self.assertTrue(response.streaming)
        
        # Consume the stream
        content = b"".join(response.streaming_content).decode('utf-8')
        self.assertIn("data: chunk1", content)
        self.assertIn("data: chunk2", content)
        
        # Verify user message was saved
        self.assertEqual(BoardAIMessage.objects.filter(role='user').count(), 1)
        self.assertEqual(BoardAIMessage.objects.get(role='user').content, 'Hello AI')
    
    def test_retrieve_update_delete_message(self):
        chat = BoardAIChat.objects.create(board=self.board, title="Original")
        message = BoardAIMessage.objects.create(chat=chat, role='user', content='Is python cool?')
        url = reverse('ai-chat-message-detail', kwargs={'pk': message.id})

        # Retrieve
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Update
        response = self.client.patch(url, {'content': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertEqual(message.content, 'Updated')
        
        # Delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(BoardAIMessage.objects.count(), 0)


class BoardMemoryTests(BaseBoardAITest):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('board-ai-memories', kwargs={'board_id': self.board.id})

    @patch('apis.board_ai_assistant.models.embed_text')
    def test_create_manual_memory(self, mock_embed):
        # Mock embedding generation
        mock_embed.return_value = [0.1] * 384
        
        data = {'content': 'Important info'}
        response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BoardMemory.objects.count(), 1)
        memory = BoardMemory.objects.get()
        self.assertEqual(memory.content, 'Important info')
        self.assertTrue(memory.is_pinned) # Manual are pinned by default
        self.assertEqual(memory.memory_type, 'manual')
        self.assertTrue(mock_embed.called)

    def test_toggle_pin(self):
        # Create memory (mock embed to avoid error)
        with patch('apis.board_ai_assistant.models.embed_text') as mock_embed:
            mock_embed.return_value = [0.0] * 384
            memory = BoardMemory.objects.create(board=self.board, content="Test", memory_type="auto", is_pinned=False)
        
        url = reverse('ai-memory-is-pinned-toggle', kwargs={'pk': memory.id})
        
        # Toggle ON
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memory.refresh_from_db()
        self.assertTrue(memory.is_pinned)
        
        # Toggle OFF
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memory.refresh_from_db()
        self.assertFalse(memory.is_pinned)


class AIProviderSettingsTests(BaseBoardAITest):
    def setUp(self):
        super().setUp()
        self.url = reverse('ai-provider-settings')

    def test_get_settings_auto_create(self):
        # Should create default settings if none exist
        self.assertEqual(AIProviderSettings.objects.count(), 0)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AIProviderSettings.objects.count(), 1)
        self.assertNotIn('api_key', response.data) # Should not return API key

    def test_update_settings(self):
        # Ensure created
        self.client.get(self.url)
        
        data = {
            'model_name': 'gpt-4',
            'api_key': 'sk-new-key',
            'base_url': 'https://api.openai.com/v1'
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        settings = AIProviderSettings.objects.get(user=self.user)
        self.assertEqual(settings.model_name, 'gpt-4')
        self.assertEqual(settings.api_key, 'sk-new-key')


class EmbeddingServiceTests(APITestCase):
    @patch('apis.board_ai_assistant.services.embeddings.SentenceTransformer')
    def test_get_model_loads_once(self, mock_transformer):
        from apis.board_ai_assistant.services import embeddings
        
        # Reset the module-level global for a clean test
        embeddings._model = None

        # First call
        embeddings.get_model()
        self.assertEqual(mock_transformer.call_count, 1)

        # Second call
        embeddings.get_model()
        # Should not be called again
        self.assertEqual(mock_transformer.call_count, 1)
        
        # Reset for other tests
        embeddings._model = None

    @patch('apis.board_ai_assistant.services.embeddings.get_model')
    def test_embed_text(self, mock_get_model):
        from apis.board_ai_assistant.services.embeddings import embed_text
        
        mock_model_instance = MagicMock()
        mock_model_instance.encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]
        mock_get_model.return_value = mock_model_instance
        
        text = "hello world"
        embedding = embed_text(text)
        
        mock_get_model.assert_called_once()
        mock_model_instance.encode.assert_called_once_with(text, normalize_embeddings=True)
        self.assertEqual(embedding, [0.1, 0.2, 0.3])


class MemoryServiceTests(BaseBoardAITest):
    @patch('apis.board_ai_assistant.services.memories.embed_text')
    def test_search_similar_memories(self, mock_embed_text):
        from apis.board_ai_assistant.services.memories import search_similar_memories
        
        # This test is limited because CosineDistance requires a real PGVector DB.
        # We will mock the DB call result to test the function's logic.
        
        mock_embed_text.return_value = [0.1] * 384
        
        # We can't execute the query with sqlite, so we'll mock the queryset
        with patch('apis.board_ai_assistant.models.BoardMemory.objects.filter') as mock_filter:
            # Mock the chain of calls
            mock_queryset = MagicMock()
            mock_filter.return_value.annotate.return_value.order_by.return_value = mock_queryset
            
            search_similar_memories(self.board, "query", top_k=5)
            
            mock_embed_text.assert_called_once_with("query")
            mock_filter.assert_called_once_with(board=self.board, is_pinned=False)
            
            # Check that the final slice is called
            mock_queryset.__getitem__.assert_called_once_with(slice(None, 5, None))

    def test_get_pinned_memories(self):
        from apis.board_ai_assistant.services.memories import get_pinned_memories
        
        # Mock embed_text in save to avoid model loading
        with patch('apis.board_ai_assistant.models.embed_text', return_value=[0.0]*384):
            pinned1 = BoardMemory.objects.create(board=self.board, content="pinned 1", is_pinned=True)
            pinned2 = BoardMemory.objects.create(board=self.board, content="pinned 2", is_pinned=True)
            unpinned = BoardMemory.objects.create(board=self.board, content="unpinned", is_pinned=False)
            
        result = get_pinned_memories(self.board)
        
        self.assertEqual(len(result), 2)
        self.assertIn(pinned1, result)
        self.assertIn(pinned2, result)
        self.assertNotIn(unpinned, result)


class LLMServiceTests(APITestCase):
    @patch('apis.board_ai_assistant.services.llm.OpenAI')
    def test_get_llm_stream(self, mock_openai):
        from apis.board_ai_assistant.services.llm import get_llm_stream

        # Mock the response stream from OpenAI
        mock_stream = MagicMock()
        
        # Create mock chunks
        class MockDelta:
            def __init__(self, content=None, tool_calls=None):
                self.content = content
                self.tool_calls = tool_calls
        
        class MockChoice:
            def __init__(self, delta):
                self.delta = delta

        class MockToolCall:
            def __init__(self, index, name, args):
                self.index = index
                self.function = MagicMock()
                self.function.name = name
                self.function.arguments = args

        mock_chunks = [
            MagicMock(choices=[MockChoice(delta=MockDelta(content="Hello"))]),
            MagicMock(choices=[MockChoice(delta=MockDelta(tool_calls=[MockToolCall(0, "func", '{"a":')]))]),
            MagicMock(choices=[MockChoice(delta=MockDelta(tool_calls=[MockToolCall(0, None, '1}')]))]),
        ]
        mock_stream.__iter__.return_value = mock_chunks
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_stream
        mock_openai.return_value = mock_client

        # Call the function
        result_generator = get_llm_stream(
            base_url="test_url",
            api_key="test_key",
            model_name="test_model",
            messages=[{"role": "user", "content": "hi"}],
            tools=[]
        )
        
        results = list(result_generator)
        
        # Verify OpenAI client was initialized correctly
        mock_openai.assert_called_with(api_key="test_key", base_url="test_url")
        
        # Verify chat completion was called correctly
        mock_client.chat.completions.create.assert_called_with(
            model="test_model",
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            stream=True
        )
        
        # Verify the output format
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {"content": "Hello"})
        self.assertEqual(results[1]['tool_calls'][0]['function']['name'], "func")
        self.assertEqual(results[1]['tool_calls'][0]['function']['arguments'], '{"a":')
        self.assertEqual(results[2]['tool_calls'][0]['function']['arguments'], '1}')


class AIChatServiceTests(BaseBoardAITest):
    def setUp(self):
        super().setUp()
        self.chat = BoardAIChat.objects.create(board=self.board, title="Service Test Chat")
        self.llm_settings = AIProviderSettings.objects.create(
            user=self.user, model_name="test-model", api_key="test-key"
        )
        self.service = BoardAIChatService(self.chat, self.llm_settings)

        # Mock embedding for memory creation
        self.embed_patcher = patch('apis.board_ai_assistant.models.embed_text', return_value=[0.0]*384)
        self.mock_embed = self.embed_patcher.start()
        self.addCleanup(self.embed_patcher.stop)

    def test_get_board_state_context(self):
        col1 = Column.objects.create(board=self.board, title="Col 1", order=1, owner=self.user)
        Task.objects.create(board=self.board, column=col1, title="Task 1", order=1, owner=self.user)
        Task.objects.create(board=self.board, title="Unassigned Task", order=1, owner=self.user)
        
        context = self.service._get_board_state_context()
        
        self.assertIn("Current Board Layout:", context)
        self.assertIn("Column: Col 1", context)
        self.assertIn("- Task 1", context)
        self.assertIn("Unassigned Tasks:", context)
        self.assertIn("- Unassigned Task", context)

    @patch('apis.board_ai_assistant.services.ai_chat_service.search_similar_memories')
    @patch('apis.board_ai_assistant.services.ai_chat_service.get_pinned_memories')
    def test_build_llm_messages(self, mock_get_pinned, mock_search_similar):
        BoardAIMessage.objects.create(chat=self.chat, role="user", content="Old message")
        
        # The service assumes the current message is already in the DB (index 0), so we must create it.
        BoardAIMessage.objects.create(chat=self.chat, role="user", content="New message")
        
        mock_search_similar.return_value = [MagicMock(content="similar memory")]
        mock_get_pinned.return_value = [MagicMock(content="pinned memory")]
        
        messages = self.service._build_llm_messages("New message")
        
        self.assertEqual(messages[0]['role'], 'system')
        self.assertIn("similar memory", messages[0]['content'])
        self.assertIn("pinned memory", messages[0]['content'])
        
        self.assertEqual(messages[1]['role'], 'user')
        self.assertEqual(messages[1]['content'], 'Old message')
                
        self.assertEqual(messages[2]['role'], 'user')
        self.assertEqual(messages[2]['content'], 'New message')
        

    @patch('apis.board_ai_assistant.services.ai_chat_service.get_llm_stream')
    def test_stream_chat_response_with_text(self, mock_get_llm_stream):
        # Mock stream to yield only text content
        mock_get_llm_stream.return_value = [
            {"content": "Hello "},
            {"content": "World"},
        ]
        
        response_generator = self.service.stream_chat_response("Hi")
        
        # Consume generator
        responses = list(response_generator)
        
        self.assertIn("data: Hello \n\n", responses)
        self.assertIn("data: World\n\n", responses)
        self.assertIn("event: done\ndata: {}\n\n", responses)
        
        # Check if assistant message was saved
        self.assertTrue(BoardAIMessage.objects.filter(chat=self.chat, role="assistant").exists())
        assistant_msg = BoardAIMessage.objects.get(chat=self.chat, role="assistant")
        self.assertEqual(assistant_msg.content, "Hello World")

    @patch('apis.board_ai_assistant.services.ai_chat_service.get_llm_stream')
    @patch('apis.board_ai_assistant.services.ai_chat_service.BoardAIChatService._create_memory_if_unique')
    def test_stream_chat_response_with_tool_call(self, mock_create_memory, mock_get_llm_stream):
        # Mock stream to yield a tool call
        mock_get_llm_stream.return_value = [
            {
                "tool_calls": [{
                    "index": 0,
                    "function": {"name": "create_memory", "arguments": '{"content": "new fact"}'}
                }]
            }
        ]
        
        response_generator = self.service.stream_chat_response("Remember this")
        list(response_generator) # consume
        
        # Check that the tool handling was called
        mock_create_memory.assert_called_once_with("new fact")
        
        # Check that no assistant message was saved if there's no text content
        self.assertFalse(BoardAIMessage.objects.filter(chat=self.chat, role="assistant").exists())

    @patch('apis.board_ai_assistant.services.ai_chat_service.search_similar_memories')
    def test_create_memory_if_unique(self, mock_search_similar):
        # Case 1: No similar memories, should create
        mock_search_similar.return_value = []
        self.service._create_memory_if_unique("a new memory")
        self.assertEqual(BoardMemory.objects.filter(board=self.board).count(), 1)
        self.assertEqual(BoardMemory.objects.get().content, "a new memory")

        # Case 2: Similar memory below threshold, should NOT create
        mock_search_similar.return_value = [MagicMock(distance=MEMORY_SIMILARITY_THRESHOLD - 0.01)]
        self.service._create_memory_if_unique("a very similar memory")
        self.assertEqual(BoardMemory.objects.filter(board=self.board).count(), 1) # Still 1

        # Case 3: Similar memory above threshold, should create
        mock_search_similar.return_value = [MagicMock(distance=MEMORY_SIMILARITY_THRESHOLD + 0.01)]
        self.service._create_memory_if_unique("a different memory")
        self.assertEqual(BoardMemory.objects.filter(board=self.board).count(), 2) # Now 2


class IntegrationTests(BaseBoardAITest):
    @patch('apis.board_ai_assistant.services.ai_chat_service.get_llm_stream')
    @patch('apis.board_ai_assistant.models.embed_text')
    def test_full_ai_flow(self, mock_embed, mock_get_llm_stream):
        # 1. Setup mocks
        mock_embed.return_value = [0.1] * 384
        
        # Mock the lowest level: the LLM API call.
        # This will make the test run through the actual BoardAIChatService logic.
        def llm_stream_generator(*args, **kwargs):
            # Check if the memory context is in the prompt
            messages = kwargs.get("messages", [])
            system_prompt = next((m['content'] for m in messages if m['role'] == 'system'), "")
            
            if "Project deadline is Friday" in system_prompt:
                yield {"content": "The deadline is Friday."}
            else:
                yield {"content": "I don't know the deadline."}
        
        mock_get_llm_stream.side_effect = llm_stream_generator

        # 2. Configure Settings
        settings_url = reverse('ai-provider-settings')
        self.client.put(settings_url, {
            'model_name': 'gpt-3.5',
            'api_key': 'sk-test',
            'base_url': 'https://openrouter.ai/api/v1'
        })

        # 3. Create Memory
        memories_url = reverse('board-ai-memories', kwargs={'board_id': self.board.id})
        self.client.post(memories_url, {'content': 'Project deadline is Friday'})
        # This memory will be pinned and should be included in context.

        # 4. Create Chat
        chats_url = reverse('board-ai-chats', kwargs={'board_id': self.board.id})
        chat_resp = self.client.post(chats_url, {'title': 'Planning'})
        chat_id = chat_resp.data['id']

        # 5. Send Message
        msg_url = reverse('chat-messages', kwargs={'chat_id': chat_id})
        msg_resp = self.client.post(msg_url, {'content': 'When is the deadline?'})
        
        self.assertEqual(msg_resp.status_code, status.HTTP_200_OK)
        
        # Consume and check the streaming response
        content = b"".join(msg_resp.streaming_content).decode('utf-8')
        self.assertIn("data: The deadline is Friday.", content)
        
        # Verify the service was called (by checking the mock)
        self.assertTrue(mock_get_llm_stream.called)
        
        # Verify the assistant message was saved by the service
        self.assertTrue(
            BoardAIMessage.objects.filter(
                chat_id=chat_id, 
                role='assistant', 
                content='The deadline is Friday.'
            ).exists()
        )

    @tag('live')
    def test_live_ai_chat_flow_with_board_context(self):
        """
        Tests the full, live AI chat flow without mocks.
        This test makes a real API call to an LLM provider.
        It requires TEST_BASE_URL, TEST_MODEL_NAME, and TEST_API_KEY
        environment variables to be set.
        """
        # 1. Check for environment variables for live testing
        base_url = settings.AI_TEST_BASE_URL
        model_name = settings.AI_TEST_MODEL_NAME
        api_key = settings.AI_TEST_API_KEY

        if not all([base_url, model_name, api_key]):
            self.skipTest(
                "Skipping live AI test. Set TEST_BASE_URL, TEST_MODEL_NAME, and TEST_API_KEY environment variables."
            )

        # 2. Create AI settings for the user
        settings_url = reverse('ai-provider-settings')
        self.client.put(settings_url, {
            'model_name': model_name,
            'api_key': api_key,
            'base_url': base_url
        })

        # 3. Create board items to be included in the context
        col1 = Column.objects.create(board=self.board, title="To Do", order=1, owner=self.user)
        Task.objects.create(board=self.board, column=col1, title="My Important Task", order=1, owner=self.user)

        # 4. Create a chat session
        chats_url = reverse('board-ai-chats', kwargs={'board_id': self.board.id})
        chat_resp = self.client.post(chats_url, {'title': 'Live Test Chat'})
        self.assertEqual(chat_resp.status_code, status.HTTP_201_CREATED)
        chat_id = chat_resp.data['id']

        # 5. Send a message and get the streaming response
        msg_url = reverse('chat-messages', kwargs={'chat_id': chat_id})
        user_question = "What is my important task in the 'To Do' column?"
        msg_resp = self.client.post(msg_url, {'content': user_question})

        # 6. Assert streaming response properties
        self.assertEqual(msg_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(msg_resp.streaming)
        self.assertEqual(msg_resp['Content-Type'], 'text/event-stream')

        # 7. Consume the stream and verify the AI's response
        # 7. Consume the stream, parse the SSE data, and verify the AI's response
        content = b"".join(msg_resp.streaming_content).decode('utf-8')
        
        # The AI's response is streamed as Server-Sent Events (SSE).
        # We need to parse the 'data' fields to reconstruct the full message.
        response_text = ''
        for line in content.splitlines():
            if line.startswith('data:'):
                payload = line[5:].strip()
                if payload and payload != '{}':
                    response_text += f' {payload}'

        # The AI's response should mention the task, proving it used the board context.
        # The exact wording will vary, so we check for the key part.
        self.assertIn("My Important Task", response_text, "The AI response did not contain the expected task name.")
        self.assertIn("My Important Task", response_text, "The AI response did not contain the expected task name.")
        self.assertIn("event: done", content)

        # 8. Verify the assistant's message was saved correctly by the service
        self.assertTrue(BoardAIMessage.objects.filter(chat_id=chat_id, role='assistant').exists())
        assistant_message = BoardAIMessage.objects.get(chat_id=chat_id, role='assistant')
        self.assertIn("My Important Task", assistant_message.content, "The saved assistant message did not contain the task name.")
