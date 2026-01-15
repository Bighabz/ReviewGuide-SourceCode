# 1. Source Code Overview

## Repository Structure

```
ReviewGuide/
├── backend/                     # FastAPI Python backend
│   ├── app/                     # Main application code
│   │   ├── agents/              # LangGraph AI agents
│   │   ├── api/                 # API routes/endpoints
│   │   ├── core/                # Core utilities (config, auth, db)
│   │   ├── executors/           # Task executors
│   │   ├── middleware/          # Request middleware
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── repositories/        # Database repositories
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic services
│   │   │   └── langgraph/       # LangGraph workflow orchestration
│   │   ├── utils/               # Utility functions
│   │   └── main.py              # FastAPI app entry point
│   ├── alembic/                 # Database migrations
│   ├── config/                  # YAML configuration files
│   ├── data/                    # Static data files
│   ├── mcp_server/              # MCP server implementation
│   ├── scripts/                 # Utility scripts
│   ├── tests/                   # Backend tests
│   ├── Dockerfile               # Backend Docker image
│   ├── .env                     # Backend environment (gitignored)
│   ├── .env.example             # Example environment file
│   ├── .env.ecs.example         # ECS-specific environment template
│   └── alembic.ini              # Alembic configuration
│
├── frontend/                    # Next.js React frontend
│   ├── app/                     # Next.js App Router pages
│   │   ├── admin/               # Admin dashboard pages
│   │   ├── chat/                # Chat interface
│   │   └── page.tsx             # Home/login page
│   ├── components/              # React components
│   ├── contexts/                # React context providers
│   ├── lib/                     # Utility libraries
│   ├── public/                  # Static assets
│   ├── Dockerfile               # Frontend Docker image
│   ├── .env.local.example       # Local environment example
│   ├── .env.ecs.example         # ECS environment template
│   ├── package.json             # NPM dependencies
│   ├── next.config.js           # Next.js configuration
│   ├── tailwind.config.ts       # TailwindCSS configuration
│   └── tsconfig.json            # TypeScript configuration
│
├── docs/                        # Documentation
│   ├── HANDOVER.md              # This handover package index
│   ├── aws-secrets-setup.md     # AWS Secrets Manager guide
│   ├── backend.env              # Production backend env reference
│   └── frontend.env             # Production frontend env reference
│
├── docker-compose.yml           # Local Docker development
├── .dockerignore                # Docker ignore patterns
├── run.sh                       # Local development startup
├── setup.sh                     # Database setup script
├── kill.sh                      # Process kill script
├── requirements.txt             # Root Python dependencies
│
└── Existing Documentation:
    ├── README.md                # Basic readme
    ├── ARCHITECTURE_DIAGRAM.md  # Detailed architecture diagrams
    ├── COMPLETED_FEATURES.md    # List of completed features
    ├── DETAILED_FLOW_DIAGRAM.md # Request flow documentation
    ├── PHASE_1_DEVELOPMENT_PLAN.md
    └── REMAINING_TASKS.md       # Pending tasks
```

---

## Backend Structure Details

### `/backend/app/agents/`
LangGraph AI agents for different tasks:
- **SafetyAgent**: Content moderation, PII detection, jailbreak prevention
- **IntentAgent**: Intent classification and slot extraction
- **ClarifierAgent**: Follow-up question generation
- **PlannerAgent**: Search query planning
- **SearchAgent**: Product/service/travel search
- **ComposerAgent**: Response composition and formatting

### `/backend/app/api/`
FastAPI route definitions:
- `v1/auth/` - Authentication endpoints (login, logout)
- `v1/chat/` - Chat streaming endpoint (SSE)
- `v1/admin/` - Admin dashboard APIs
- `health` - Health check endpoint

### `/backend/app/core/`
Core utilities:
- `config.py` - Application configuration (loads from env/database)
- `auth.py` - JWT authentication
- `database.py` - SQLAlchemy async database connection
- `redis.py` - Redis connection and utilities
- `security.py` - Password hashing, encryption

### `/backend/app/models/`
SQLAlchemy ORM models:
- `user.py` - User accounts
- `session.py` - User sessions
- `conversation.py` - Chat conversations
- `affiliate_link.py` - Affiliate link tracking
- `core_config.py` - Dynamic configuration storage
- Various travel-related models

### `/backend/app/services/langgraph/`
LangGraph workflow orchestration:
- `workflow.py` - Main StateGraph workflow definition
- `state.py` - GraphState dataclass
- Agent integration and routing logic

### `/backend/alembic/`
Database migration files:
- Version-controlled schema migrations
- Run with: `alembic upgrade head`

### `/backend/config/`
YAML configuration files:
- `search.yaml` - Search provider configurations
- `travel.yaml` - Travel API configurations

---

## Frontend Structure Details

### `/frontend/app/`
Next.js App Router pages:
- `page.tsx` - Login/landing page
- `chat/page.tsx` - Main chat interface
- `admin/Dashboard.tsx` - Admin dashboard

### `/frontend/components/`
React components:
- `ChatInterface.tsx` - Main chat UI
- `ChatInput.tsx` - Message input component
- `MessageList.tsx` - Message display
- `ProductCard.tsx` - Product result cards
- `TravelResults.tsx` - Travel booking results
- Various UI components

### `/frontend/lib/`
Utility libraries:
- `api.ts` - API client functions
- `streamChat.ts` - SSE streaming utilities

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI application entry point |
| `backend/app/core/config.py` | All configuration loading |
| `backend/app/services/langgraph/workflow.py` | LangGraph agent workflow |
| `frontend/app/chat/page.tsx` | Main chat page |
| `frontend/components/ChatInterface.tsx` | Chat UI component |
| `docker-compose.yml` | Local development orchestration |
| `backend/Dockerfile` | Backend container build |
| `frontend/Dockerfile` | Frontend container build |

---

## Build Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
cd backend
alembic upgrade head
```

### Frontend
```bash
# Install dependencies
cd frontend
npm install

# Run locally
npm run dev

# Build for production
npm run build
```

### Docker
```bash
# Build and run all services locally
docker-compose up --build

# Build individual images
docker build -t reviewguide-backend -f backend/Dockerfile .
docker build -t reviewguide-frontend -f frontend/Dockerfile frontend/
```

---

## Database Migrations

Migrations are managed with Alembic:

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

---

## Code Quality Notes

- Backend uses async/await throughout for non-blocking I/O
- Frontend uses TypeScript for type safety
- SSE (Server-Sent Events) for real-time chat streaming
- LangGraph for AI agent orchestration
- SQLAlchemy 2.0 async ORM pattern