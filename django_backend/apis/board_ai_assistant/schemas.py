from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
)
from drf_spectacular.types import OpenApiTypes


def with_int_path_parameter(description: str):
    """Decorator to add Integer path parameter to schema operations.

    Args:
        description: The resource type name for the ID description

    Returns:
        A dictionary with 'id' parameter configured as Integer
    """
    return {
        'parameters': [
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description=f"{description} unique integer identifier",
            ),
        ]
    }


# ---------------------------------------------------------
# Board AI Chats (List / Create) - Tag: AI Chat > Chats
# ---------------------------------------------------------

board_ai_chats_schema = extend_schema_view(
    get=extend_schema(
        summary="List board AI chats",
        description=(
            "Returns all AI chats associated with a specific board.\n\n"
            "The user must be the owner of the board.\n"
            "Each chat represents a separate conversation context."
        ),
        tags=["AI Chat", "Chats"],
    ),
    post=extend_schema(
        summary="Create a new AI chat for a board",
        description=(
            "Creates a new AI chat attached to a specific board.\n\n"
            "The chat starts empty. Messages are created via the chat messages endpoint."
        ),
        tags=["AI Chat", "Chats"],
    ),
)


# ---------------------------------------------------------
# Single AI Chat (Retrieve / Update / Delete) - Tag: AI Chat > Chats
# ---------------------------------------------------------

board_ai_chat_detail_schema = extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve AI chat",
        description="Retrieve details of a specific AI chat.",
        **with_int_path_parameter("AI Chat"),
        tags=["AI Chat", "Chats"],
    ),
    update=extend_schema(
        summary="Update AI chat",
        description="Update the AI chat (e.g., rename the title).",
        **with_int_path_parameter("AI Chat"),
        tags=["AI Chat", "Chats"],
    ),
    partial_update=extend_schema(
        summary="Partially update AI chat",
        description="Partially update chat fields.",
        **with_int_path_parameter("AI Chat"),
        tags=["AI Chat", "Chats"],
    ),
    destroy=extend_schema(
        summary="Delete AI chat",
        description="Deletes the AI chat and all associated messages.",
        **with_int_path_parameter("AI Chat"),
        tags=["AI Chat", "Chats"],
    ),
)


# ---------------------------------------------------------
# Chat Messages (STREAMING ENDPOINT) - Tag: AI Chat > Messages
# ---------------------------------------------------------

board_ai_chat_messages_schema = extend_schema_view(
    get=extend_schema(
        summary="List chat messages",
        description=(
            "Returns all messages for a specific AI chat.\n\n"
            "Messages include user and assistant roles.\n"
            "Ordered by creation time."
        ),
        tags=["AI Chat", "Messages"],
    ),
    post=extend_schema(
        summary="Send a message to AI (Streaming Response)",
        description=(
            "Sends a user message to the AI assistant and receives a streaming response.\n\n"
            "### ⚠️ Streaming Endpoint\n"
            "This endpoint returns a **Server-Sent Events (SSE) stream** (`text/event-stream`) "
            "instead of a standard JSON response. Clients must be prepared to handle a stream.\n\n"
            "**Note:** The streaming effect is **not visible in Swagger UI**. "
            "Swagger waits for the entire response to complete before displaying it. "
            "To see the streaming effect, use a client that supports SSE (e.g., `curl`, a custom frontend, or Postman with streaming enabled).\n\n"
            "Each chunk of the response is sent as `data: <token>\\n\\n`.\n"
            "The stream is terminated by `event: done\\n\\n`.\n\n"
            "### AI Context\n"
            "To generate a response, the AI is provided with the following context:\n"
            "*   **Chat History:** The last 15 messages.\n"
            "*   **Board Snapshot:**\n"
            "    *   Columns (max 10)\n"
            "    *   Tasks per column (max 10)\n"
            "    *   Unassigned tasks (max 10)\n"
            "*   **Memories:**\n"
            "    *   All pinned memories.\n"
            "    *   Top 3 most similar memories to the new message."
        ),
        tags=["AI Chat", "Messages"],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="Streaming text/event-stream response",
                examples=[
                    OpenApiExample(
                        "Streaming Example",
                        value="""data: Hello
                                data: how
                                data: can I help?
                                event: done
                                """,
                    )
                ],
            )
        },
    ),
)


# ---------------------------------------------------------
# Single Chat Message (Retrieve / Update / Delete) - Tag: AI Chat > Messages
# ---------------------------------------------------------

ai_chat_message_detail_schema = extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve chat message",
        description="Retrieve a single chat message.",
        **with_int_path_parameter("Chat message"),
        tags=["AI Chat", "Messages"],
    ),
    update=extend_schema(
        summary="Update chat message",
        description="Update the content of a chat message. Note: only 'user' messages are typically editable.",
        **with_int_path_parameter("Chat message"),
        tags=["AI Chat", "Messages"],
    ),
    partial_update=extend_schema(
        summary="Partially update chat message",
        description="Partially update the content of a chat message. Note: only 'user' messages are typically editable.",
        **with_int_path_parameter("Chat message"),
        tags=["AI Chat", "Messages"],
    ),
    destroy=extend_schema(
        summary="Delete chat message",
        description="Deletes a single chat message.",
        **with_int_path_parameter("Chat message"),
        tags=["AI Chat", "Messages"],
    ),
)


# ---------------------------------------------------------
# Board Memories - Tag: AI Chat > Memories
# ---------------------------------------------------------

board_memories_schema = extend_schema_view(
    get=extend_schema(
        summary="List board memories",
        description=(
            "Returns all AI memories associated with the board.\n\n"
            "Includes both manual and auto-generated memories."
        ),
        tags=["AI Chat", "Memories"],
    ),
    post=extend_schema(
        summary="Create manual pinned memory",
        description=(
            "Creates a manually pinned memory.\n\n"
            "Manual memories are always pinned by default.\n"
            "Embeddings are automatically generated."
        ),
        tags=["AI Chat", "Memories"],
    ),
)


memory_detail_schema = extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve memory",
        description="Retrieve a single memory object.",
        **with_int_path_parameter("Memory"),
        tags=["AI Chat", "Memories"],
    ),
    update=extend_schema(
        summary="Update memory",
        description="Update memory content or pin status.",
        **with_int_path_parameter("Memory"),
        tags=["AI Chat", "Memories"],
    ),
    partial_update=extend_schema(
        summary="Partially update memory",
        description="Partially update memory content or pin status.",
        **with_int_path_parameter("Memory"),
        tags=["AI Chat", "Memories"],
    ),
    destroy=extend_schema(
        summary="Delete memory",
        description="Delete memory permanently.",
        **with_int_path_parameter("Memory"),
        tags=["AI Chat", "Memories"],
    ),
    is_pinned_toggle=extend_schema(
        summary="Toggle pinned state",
        description=(
            "Toggles the `is_pinned` flag for a specific memory.\n\n"
            "If pinned → unpins.\n"
            "If unpinned → pins."
        ),
        **with_int_path_parameter("Memory"),
        tags=["AI Chat", "Memories"],
    ),
)


# ---------------------------------------------------------
# AI Provider Settings - Tag: AI Chat > LLM Settings
# ---------------------------------------------------------

ai_provider_settings_schema = extend_schema_view(
    get=extend_schema(
        summary="Retrieve AI provider settings",
        description=(
            "Returns the user's AI provider configuration.\n\n"
            "Users must provide their own API key from any provider compatible with OpenAI APIs.\n\n"
            "⚠️ **Security Note:** The API key is **encrypted at rest** to protect against database leaks "
            "and is never returned in the response.\n\n"
            "### Auto-Creation\n"
            "If settings do not exist (e.g., first access or after deletion), "
            "default settings are automatically created:\n"
            "*   **Base URL:** `https://openrouter.ai/api/v1`\n"
            "*   **API Key:** Empty (must be set via Update/Patch)"
        ),
        tags=["AI Chat", "LLM Settings"],
    ),
    put=extend_schema(
        summary="Update AI provider settings",
        description=(
            "Updates the AI provider configuration (Model, API Key, Base URL).\n\n"
            "*   **Provider:** Any provider compatible with OpenAI APIs.\n"
            "*   **API Key:** Stored securely (encrypted at rest).\n"
            "*   **Auto-Creation:** If settings don't exist, they are created with defaults before applying updates."
        ),
        tags=["AI Chat", "LLM Settings"],
    ),
    patch=extend_schema(
        summary="Partially update AI provider settings",
        description="Partially updates the AI provider configuration.",
        tags=["AI Chat", "LLM Settings"],
    ),
    delete=extend_schema(
        summary="Delete AI provider settings",
        description=(
            "Deletes the stored AI provider configuration.\n\n"
            "**Note:** Accessing settings after deletion will trigger auto-creation of defaults."
        ),
        tags=["AI Chat", "LLM Settings"],
    ),
)