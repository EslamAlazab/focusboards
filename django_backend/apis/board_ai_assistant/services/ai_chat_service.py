import json
from typing import Generator
from django.db import transaction
from ..models import BoardAIMessage, BoardMemory
from .memories import search_similar_memories, get_pinned_memories
from .llm import get_llm_stream


MEMORY_SIMILARITY_THRESHOLD = 0.15

class BoardAIChatService:
    def __init__(self, chat, llm_settings):
        self.chat = chat
        self.board = chat.board
        self.base_url = llm_settings.base_url
        self.model_name = llm_settings.model_name
        self.api_key = llm_settings.api_key

    # -------------------------
    # Public Entry Point
    # -------------------------

    def stream_chat_response(self, user_message: str) -> Generator[str, None, None]:
        llm_messages = self._build_llm_messages(user_message)

        tool_calls_buffer = {}
        assistant_text_buffer = ""

        try:
            for chunk in get_llm_stream(
                base_url=self.base_url,
                api_key=self.api_key,
                model_name=self.model_name,
                messages=llm_messages,
                tools=self._tools_schema(),
            ):
                # Handle tool call deltas
                if chunk.get("tool_calls"):
                    for tc in chunk["tool_calls"]:
                        idx = tc["index"]
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {"name": "", "arguments": ""}
                        
                        if tc["function"]["name"]:
                            tool_calls_buffer[idx]["name"] = tc["function"]["name"]
                        if tc["function"]["arguments"]:
                            tool_calls_buffer[idx]["arguments"] += tc["function"]["arguments"]
                    

                # Handle assistant content
                if chunk.get("content"):
                    content_piece = chunk["content"]
                    assistant_text_buffer += content_piece
                    yield f"data: {content_piece}\n\n"
            
            # After streaming ends:
            final_tool_calls = []

            for _, call in sorted(tool_calls_buffer.items()):
                if call["name"] and call["arguments"]:
                    final_tool_calls.append({"function": call})

            self._handle_tool_calls(final_tool_calls)

            if assistant_text_buffer.strip():
                BoardAIMessage.objects.create(
                    chat=self.chat,
                    role="assistant",
                    content=assistant_text_buffer.strip(),
                )

            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"data: [ERROR]:Provider error occurred. {e}\n\n"
            yield "event: done\n\n"
            return

    # -------------------------
    # Build Context
    # -------------------------

    def _build_llm_messages(self, user_message: str):
        similar_memories = search_similar_memories(
            self.board, user_message, top_k=3
        )
        pinned_memories = get_pinned_memories(self.board)

        all_memories = [*similar_memories, *pinned_memories]

        if all_memories:
            memory_context = "\n".join(f"- {mem.content}" for mem in all_memories)
        else:
            memory_context = "No relevant memories."

        board_state = self._get_board_state_context()

        system_prompt = (
            "You are a helpful assistant for a project management board.\n"
            f"{board_state}\n\n"
            "Use the provided memory context when relevant.\n"
            "If new long-term information should be remembered, "
            "call the `create_memory` function.\n\n"
            f"Memory context:\n{memory_context}"
        )

        history = self.chat.messages.order_by("-created_at")[1:16]
        
        history = reversed(history)

        messages = [{"role": "system", "content": system_prompt}]

        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    # -------------------------
    # Board Context
    # -------------------------

    def _get_board_state_context(self) -> str:
        """
        Builds a text representation of the board (Columns & Tasks).
        Limits tasks per column to avoid exceeding context window.
        """
        lines = ["Current Board Layout:"]
        
        columns = self.board.columns.all().order_by('order')
        
        for col in columns:
            lines.append(f"\nColumn: {col.title}")
            
            tasks = col.tasks.all().order_by('order')
            
            for task in tasks[:10]:
                lines.append(f"- {task.title}")
            
            count = tasks.count()
            if count > 10:
                lines.append(f"  ... ({count - 10} more)")
        
        # Add unassigned tasks
        unassigned_tasks = self.board.tasks.filter(column=None).order_by('order')
        unassigned_count = unassigned_tasks.count()

        if unassigned_count > 0:
            lines.append("\nUnassigned Tasks:")
            for task in unassigned_tasks[:10]:
                lines.append(f"- {task.title}")
            if unassigned_count > 10:
                lines.append(f"  ... ({unassigned_count - 10} more)")
        
        return "\n".join(lines)

    # -------------------------
    # Tool Schema
    # -------------------------

    def _tools_schema(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_memory",
                    "description": "Store a new long-term memory for this board.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Concise memory fact to store."
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]

    # -------------------------
    # Tool Execution
    # -------------------------

    @transaction.atomic
    def _handle_tool_calls(self, tool_calls):
        for call in tool_calls:
            if call["function"]["name"] == "create_memory":
                try:
                    arguments = json.loads(call["function"]["arguments"])
                except Exception:
                    continue  # ignore corrupted tool call
                
                content = arguments.get("content")

                if content:
                    self._create_memory_if_unique(content)

    def _create_memory_if_unique(self, content: str):
        similar_memories = search_similar_memories(self.board, content, top_k=1)

        if similar_memories and similar_memories[0].distance < MEMORY_SIMILARITY_THRESHOLD:
            return

        BoardMemory.objects.create(
            board=self.board,
            content=content.strip(),
            memory_type="auto",
        )