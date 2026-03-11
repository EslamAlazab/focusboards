# FocusBoards

FocusBoards backend is an AI-Augmented Kanban-style application designed to help users organize their thoughts and workflows efficiently.

Users can create projects, each containing multiple boards. Boards are composed of columns, and columns contain tasks.

Tasks can be reordered, transferred between columns, or moved across boards. Columns are customizable with colors, and tasks can be created unassigned and linked later.

With the introduction of **AI-powered board assistance**, FocusBoards now includes contextual AI chat capabilities per board.

---

## Architecture Overview

The codebase follows the **Single Responsibility Principle** and is designed to be **loosely coupled**, making it easy to maintain, extend, and review.

The backend follows a modular, domain-driven structure where each core concept  
(**Users, Projects, Boards, Columns, Tasks**) is isolated into its own Django app.

Business logic is kept minimal in views and enforced through:

- Queryset-level filtering
- Explicit permission checks
- Clear ownership rules
- Service-layer abstraction for AI operations

This approach ensures strong separation of concerns, scalability, and predictable behavior.

---

## Board AI Chat

FocusBoards now includes an AI-powered assistant that works at the board level.

Each board has its own contextual AI conversation that understands:

- The board’s columns
- The tasks within the board
- Task descriptions
- Historical chat messages

### AI Capabilities

- Context-aware board discussion
- Task summarization
- Workflow suggestions
- Productivity insights
- Creating memories for future contexts
- Semantic retrieval of relevant memories using embeddings

### AI Configuration & Security

- **Bring Your Own Key:** Users provide their own API key.
- **Universal Compatibility:** Works with any OpenAI-compatible provider (e.g., OpenRouter, LocalAI).
- **Encryption at Rest:** API keys are encrypted in the database to prevent leaks.

### How It Works

Each AI request builds context from three sources:

1. **Board Snapshot** – Current columns and tasks
2. **Chat History** – Last 15 messages for conversation continuity
3. **Memories** – All pinned memories + top 3 semantically similar ones via embeddings

The LLM receives this context plus a `create_memory` tool, allowing it to automatically save insights for future conversations. Responses stream in real-time using Server-Sent Events (SSE).

---

## Database & Vector Search

FocusBoards now uses:

- PostgreSQL as the primary database
- pgvector extension for vector similarity search

### Why pgvector?

- Stores high-dimensional embeddings directly inside PostgreSQL
- Enables fast similarity search using cosine distance
- Keeps AI retrieval tightly integrated with application data
- Eliminates need for external vector databases

### Embedding Use Cases

- Semantic search across memories
- Context retrieval for AI responses

---

## Key Features

- **User Registration**
  - Email / Username / Password
  - Google OAuth
  - Guest access (no email or password required)

- **Authentication**
  - Session-based authentication
  - JWT authentication (access + refresh tokens)
  - HTTP-only refresh tokens with rotation and blacklisting
  - Redis-backed session and token caching for performance

- **Authorization & Permissions**
  - Users can only access resources they own
  - Ownership is enforced at the queryset and permission layer
  - Secure validation when transferring columns or tasks across boards
  - AI chats strictly scoped per board ownership

- **Guest Users**
  - Temporary accounts with limited lifetime
  - Can create projects, boards, columns, and tasks
  - Periodically cleaned up via Celery Beat
  - Can be converted into full accounts while preserving data

- **Email Confirmation**
  - Secure account verification via email

- **Password Reset**
  - Secure reset via email link

- **Background Workers**
  - Celery workers for asynchronous tasks
    - Email sending
    - Automated cleanup of expired guest users

- **Pagination**
  - Efficient pagination across projects, boards, columns, and tasks

- **REST API**
  - Fully RESTful API with filtering, search, pagination, and strict permission enforcement

- **SSE**
  - AI generated response is streamed over a SSE

- **API Documentation**
  - Auto-generated and maintained using DRF-Spectacular

- **Enhanced Security**
  - Refresh token rotation and blacklisting
  - HTTP-only cookie storage
  - Reduced attack surface for token leakage

---

## Testing

The project includes automated test covering:

- Authentication and authorization flows
- Permissions and ownership rules
- CRUD operations for core resources
- Edge cases such as guest user behavior and resource transfers
- AI chat scoping and permissions
- Vector embedding storage and retrieval logic

This ensures correctness, security, and confidence when refactoring or extending features.

---

## Tech Stack

- **Django** – High-level Python web framework
- **Django REST Framework (DRF)** – Web API toolkit
- **PostgreSQL** – Relational database
- **pgvector** – Vector similarity search extension
- **Django ORM** – Optimized database abstraction
- **DRF-Spectacular** – API schema generation
- **Celery** – Asynchronous task processing
- **Celery Beat** – Periodic task scheduling
- **Redis** – Cache, message broker, and token/session storage
- **Gunicorn** – WSGI HTTP server
- **Docker & Docker Compose** – Containerized deployment

---

## Getting Started

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/EslamAlazab/focusboards.git
cd focusboards/django_backend
```

### 2️⃣ Set Up the Environment

Make sure you have Docker and Docker Compose installed.

Create a .env file with the required environment variables (example):

```env
# Security & Debugging
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:3000

# Database (supports standard PostgreSQL URL format)
DATABASE_URL=postgres://user:password@db:5432/dbname
POSTGRES_DB=dbname #(for docker compose)
POSTGRES_USER=user #(for docker compose)
POSTGRES_PASSWORD=password #(for docker compose)

# Redis (used for caching, Celery broker, and session storage)
REDIS_URL=redis://redis:6379/0

# Frontend URL (for email links and CORS)
FRONTEND_URL=http://localhost:3000

# Email Configuration (SMTP credentials)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth (optional, for Google sign-in)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# AI Assistant Configuration (for testing/debugging only)
AI_TEST_BASE_URL=https://api.openai.com/v1
AI_TEST_MODEL_NAME=gpt-4o
AI_TEST_API_KEY=your-api-key
```

```sh
docker-compose -f docker-compose.dev.yaml up
```

Once running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/
