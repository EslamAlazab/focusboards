# FocusBoards

FocusBoards backend is a Kanban-style application designed to help users organize their thoughts and workflows efficiently.  
Users can create projects, each containing multiple boards. Boards are composed of columns, and columns contain tasks.

Tasks can be reordered, transferred between columns, or moved across boards. Columns are customizable with colors, and tasks can be created unassigned and linked later.

---

## Architecture Overview

The codebase follows the **Single Responsibility Principle** and is designed to be **loosely coupled**, making it easy to maintain, extend, and review.

The backend follows a modular, domain-driven structure where each core concept  
(**Users, Projects, Boards, Columns, Tasks**) is isolated into its own Django app.

Business logic is kept minimal in views and enforced through:

- Queryset-level filtering
- Explicit permission checks
- Clear ownership rules

This approach ensures strong separation of concerns, scalability, and predictable behavior.

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

- **API Documentation**
  - Auto-generated and maintained using DRF-Spectacular

- **Enhanced Security**
  - Refresh token rotation and blacklisting
  - HTTP-only cookie storage
  - Reduced attack surface for token leakage

---

## Testing

The project includes **51 automated tests** covering:

- Authentication and authorization flows
- Permissions and ownership rules
- CRUD operations for core resources
- Edge cases such as guest user behavior and resource transfers

This ensures correctness, security, and confidence when refactoring or extending features.

---

## Tech Stack

- **Django** – High-level Python web framework
- **Django REST Framework (DRF)** – Web API toolkit
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
git clone https://github.com/eslamalazab/focusboards/django_backend.git
```

### 2️⃣ Set Up the Environment

Make sure you have Docker and Docker Compose installed.

Create a .env file with the required environment variables (example):

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://...
REDIS_URL=redis://redis:6379/0
FRONTEND_URL=http://localhost:3000
```

```sh
docker-compose up
```

Once running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/
