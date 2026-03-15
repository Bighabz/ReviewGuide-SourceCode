# Testing Patterns

**Analysis Date:** 2026-03-15

## Test Framework

**Frontend Runner:**
- Vitest 4.x
- Config: `frontend/vitest.config.ts`
- Environment: `jsdom` (browser simulation)
- Globals enabled (`globals: true` — no need to import `describe`, `it`, `expect`)

**Backend Runner:**
- pytest with `pytest-asyncio`
- Config: `backend/pytest.ini`
- `asyncio_mode = auto` — all async tests run without explicit `@pytest.mark.asyncio` by default (though the marker is still used for clarity)

**Assertion Libraries:**
- Frontend: Vitest built-in assertions + `@testing-library/jest-dom` (via setup file `frontend/tests/setup.ts`)
- Backend: pytest built-in `assert` statements

**Run Commands:**
```bash
# Frontend
cd frontend && npm run test             # Watch mode
cd frontend && npm run test:run         # Run once (CI)
cd frontend && npm run test:coverage    # Coverage report

# Backend
cd backend && pytest                    # Run all tests
cd backend && pytest tests/test_tiered_router/  # Run specific directory
cd backend && pytest -v                 # Verbose output
cd backend && pytest -k "test_circuit" # Filter by name
```

## Test File Organization

**Frontend:**
- All test files live in `frontend/tests/` (separate directory, not co-located)
- One test file per module/feature — e.g., `chatApi.test.ts` for `frontend/lib/chatApi.ts`
- Naming: `<subject>.test.{ts,tsx}` — TypeScript files for pure logic tests, TSX for component tests
- Skipped test: `ChatContainer.test.tsx.skip` — entire file excluded by renaming (not by `skip` flag)

**Backend:**
- All test files in `backend/tests/`
- Feature-grouped subdirectory: `backend/tests/test_tiered_router/` with its own `__init__.py`
- Naming: `test_<module>.py`
- Shared fixtures in `backend/tests/conftest.py`

**Structure:**
```
frontend/tests/
├── setup.ts                        # Global mocks (router, localStorage, fetch, CSS vars)
├── chatApi.test.ts                 # API client and SSE streaming
├── useStreamReducer.test.ts        # Hook state machine (pure reducer + hook lifecycle)
├── ErrorBoundary.test.tsx          # Component error catching
├── blockSkeleton.test.tsx          # Skeleton loading states
├── designTokens.test.ts            # CSS token presence assertions
├── explainabilityPanel.test.tsx    # Confidence/coverage display
├── messageRecovery.test.tsx        # Interrupted stream recovery UI
├── suggestions.test.tsx            # Suggestion chip sorting + click provenance
└── ChatContainer.test.tsx.skip     # (disabled)

backend/tests/
├── conftest.py                     # Session-scoped startup mock + shared fixtures
├── test_chat_api.py                # Integration tests: HTTP endpoints + rate limiting
├── test_product_compose.py         # Tool-level unit tests
├── test_tiered_router/
│   ├── test_router.py              # Routing table + circuit break filtering
│   ├── test_circuit_breaker.py     # State machine: open/close/reset
│   ├── test_orchestrator.py        # Tier escalation logic
│   ├── test_workflow_integration.py # LangGraph routing gate assertions
│   ├── test_parallel_fetcher.py
│   ├── test_tiered_executor.py
│   ├── test_routing_gate.py
│   ├── test_api_registry.py
│   ├── test_api_logger.py
│   ├── test_data_validator.py
│   └── test_consent_resume.py
├── test_model_service.py
├── test_state_serializer.py
├── test_degradation_policy.py
├── test_qos.py
├── test_sse_events.py
├── test_stage_telemetry.py
├── test_startup_manifest.py
├── test_telemetry.py
├── test_tool_validator.py
├── test_chat_history_efficiency.py
├── test_query_complexity.py
├── test_review_search.py
└── test_cj_provider.py
```

## Test Structure

**Frontend Suite Organization:**
```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

describe('ComponentName', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('does the thing when condition is met', () => {
    // arrange
    // act
    // assert
  })
})
```

**Backend Suite Organization:**
```python
class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check_returns_ok(self):
        """Test that health endpoint returns 200 OK"""
        from app.main import app
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
```

Or flat functions for focused unit tests:
```python
def test_circuit_breaker_starts_closed():
    """New circuit breaker should have all circuits closed"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)
    assert cb.is_open("any_api") is False
```

**Patterns:**
- Descriptive `it`/`test_` names that state the expected behavior: `'calls onError on 4xx response without retry'`
- One assertion per `it` block preferred, but related assertions grouped when they logically belong together
- `beforeEach`/`afterEach` in frontend for timer mocking and spy cleanup
- Backend imports of `app.main` done inside test functions to avoid module-level import order issues

## Mocking

**Frontend Framework:** Vitest `vi` — `vi.fn()`, `vi.mock()`, `vi.spyOn()`, `vi.useFakeTimers()`

**Global Mocks (in `frontend/tests/setup.ts`):**
```typescript
// Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn(), back: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// localStorage
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// fetch
global.fetch = vi.fn()

// DOM methods missing from jsdom
Element.prototype.scrollIntoView = vi.fn()
```

**Frontend Per-Test Mocking:**
```typescript
// Mock fetch per test
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  body: createMockReadableStream([...]),
})

// Spy and suppress console noise
vi.spyOn(console, 'error').mockImplementation(() => {})

// Timer control for async/timeout tests
vi.useFakeTimers()
await vi.runAllTimersAsync()
vi.advanceTimersByTime(120_000)
vi.useRealTimers() // in afterEach
vi.restoreAllMocks() // in afterEach
```

**Backend Framework:** `unittest.mock` — `AsyncMock`, `MagicMock`, `patch`

**Backend Session-Scoped Startup Mock (in `backend/tests/conftest.py`):**
All I/O-triggering lifespan startup functions are patched at session scope so tests run without real PostgreSQL or Redis:
```python
with patch("app.main.init_db", new_callable=AsyncMock), \
     patch("app.main.init_redis", new_callable=AsyncMock), \
     patch("app.core.redis_client.redis_client", mock_redis), \
     patch("app.core.database.AsyncSessionLocal", mock_session_local):
    yield
```

**Backend Per-Test Mocking:**
```python
# Patch module-level dependency
with patch('app.api.v1.admin_auth.AdminUserRepository') as mock_repo:
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_by_username = AsyncMock(return_value=None)
    mock_repo.return_value = mock_repo_instance
    ...

# Patch object method
with patch.object(orchestrator.fetcher, "fetch_tier", new_callable=AsyncMock) as mock_fetch:
    mock_fetch.return_value = {...}
    result = await orchestrator.execute(...)

# monkeypatch (pytest fixture) for patching module attributes directly
monkeypatch.setattr("app.api.v1.chat.HaltStateManager.get_halt_state", fake_halt)
```

**What to Mock:**
- All external I/O: OpenAI API calls, database sessions, Redis connections
- Time-dependent operations: `datetime.now`, timers
- Network requests: `fetch`, `httpx.AsyncClient` connections

**What NOT to Mock:**
- Business logic being tested (the subject under test)
- Pure functions (sort logic, state reducers) — test these without any mocking

## Fixtures and Factories

**Backend Shared Fixtures (`backend/tests/conftest.py`):**
```python
@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.ping = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def sample_chat_request():
    return {
        "message": "What are the best wireless headphones?",
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }

@pytest.fixture
def auth_headers(sample_user):
    from app.utils.auth import create_access_token
    token = create_access_token({"sub": str(sample_user["id"]), ...})
    return {"Authorization": f"Bearer {token}"}
```

**Backend Local Fixtures:**
Fixtures defined in the test file itself when they are specific to one test module:
```python
@pytest.fixture
def orchestrator():
    return TieredAPIOrchestrator()

@pytest.fixture
def mock_state():
    return {"user_id": "test-user", "session_id": "test-session", ...}
```

**Frontend Test Data:**
No shared factory files — test data is inline within each test:
```typescript
const suggestions: NextSuggestion[] = [
  { id: 's1', question: 'Question one?', category: 'clarify' },
  { id: 's2', question: 'Question two?', category: 'compare' },
]
```

**Frontend Render Helper Pattern:**
Small `renderUI()` helper functions defined inside test files to reduce prop boilerplate:
```typescript
function renderUI(overrides: Partial<MessageRecoveryUIProps> = {}) {
  const defaults: MessageRecoveryUIProps = {
    completeness: 'partial',
    onShowPartial: vi.fn(),
    onRetryFull: vi.fn(),
  }
  return { ...render(<MessageRecoveryUI {...{ ...defaults, ...overrides }} />), props: { ...defaults, ...overrides } }
}
```

**Location:**
- Frontend: All fixtures inline in test files (no separate fixtures directory)
- Backend: Shared in `backend/tests/conftest.py`; module-specific fixtures in the test file itself

## Coverage

**Requirements:** No enforced coverage threshold. Coverage configured but not gated.

**Frontend Coverage Config (`frontend/vitest.config.ts`):**
```typescript
coverage: {
  reporter: ['text', 'json', 'html'],
  exclude: ['node_modules/', '.next/', 'tests/'],
}
```

**View Coverage:**
```bash
cd frontend && npm run test:coverage   # Generates text + JSON + HTML reports
```

**Backend Coverage:** Not configured in `pytest.ini`. No `pytest-cov` plugin invocation detected.

## Test Types

**Unit Tests:**
- Backend: Pure business logic — routing table lookups, circuit breaker state transitions, sort functions. No I/O, no HTTP client. Fast.
- Frontend: Pure reducer functions (`streamReducer` state transitions), utility functions (`sortSuggestions`), CSS token presence checks. No component rendering.

**Integration Tests:**
- Backend: HTTP endpoint tests using `httpx.AsyncClient` with `ASGITransport(app=app)`. Tests the full request/response cycle with mocked downstream services (DB, Redis, LangGraph graph).
- Backend: Concurrency tests — verifying `asyncio.gather` runs calls in parallel (`test_startup_io_calls_are_concurrent` in `backend/tests/test_chat_api.py`).
- Backend: LangGraph node tests — calling routing gate nodes with mock state dicts and asserting state updates.

**Component Tests (Frontend):**
- Uses `@testing-library/react` `render`, `screen`, `fireEvent`
- Tests rendered output via accessible queries (`screen.getByText`, `screen.getByTestId`)
- Tests user interactions via `fireEvent.click`
- Tests that callbacks are called with correct arguments

**E2E Tests:** Not detected.

## Environment Bootstrap (Backend)

Environment variables must be set before any app import. This is done at the top of `conftest.py`:
```python
os.environ["ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["LOG_ENABLED"] = "false"
```

For test files that do NOT use `conftest.py` (standalone tool tests like `test_product_compose.py`), they set env vars locally at the module level using `os.environ.setdefault(...)`.

## Common Patterns

**Async Testing (Backend):**
```python
@pytest.mark.asyncio
async def test_execute_returns_success_when_sufficient(orchestrator, mock_state):
    with patch.object(orchestrator.fetcher, "fetch_tier", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"amazon": {"status": "success", "data": {"products": [...]}}}
        result = await orchestrator.execute("product", "best vacuum", mock_state)
    assert result["status"] == "success"
```

**Async Testing with Fake HTTP Client (Backend):**
```python
async with AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test"
) as client:
    response = await client.post("/v1/chat/stream", json={"message": "Hello"})
    assert response.status_code in [200, 500]
```

**SSE Stream Mocking (Frontend):**
```typescript
function createMockReadableStream(chunks: string[]) {
  let index = 0
  const encoder = new TextEncoder()
  return {
    getReader: () => ({
      read: async () => {
        if (index < chunks.length) {
          return { done: false, value: encoder.encode(chunks[index++]) }
        }
        return { done: true, value: undefined }
      },
    }),
  }
}

global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  body: createMockReadableStream(['data: {"token":"Hello"}\n', 'data: {"done":true}\n']),
})
```

**Timer-Based Testing (Frontend):**
```typescript
beforeEach(() => { vi.useFakeTimers() })
afterEach(() => { vi.useRealTimers() })

it('dispatches STREAM_INTERRUPTED after 120s', () => {
  const { result } = renderHook(() => useStreamReducer())
  act(() => { result.current.dispatch({ type: 'SEND_MESSAGE' }) })
  act(() => { vi.advanceTimersByTime(120_000) })
  expect(result.current.streamState).toBe('interrupted')
})
```

**Error Testing (Backend):**
```python
with pytest.raises(HTTPException) as exc_info:
    await limiter.check_rate_limit("test-key", is_authenticated=False)
assert exc_info.value.status_code == 429
```

**Error Testing (Frontend):**
```typescript
await expect(login('admin', 'wrong')).rejects.toThrow('Invalid credentials')
```

**Pure Reducer Testing (Frontend):**
Test all state transitions directly, without rendering:
```typescript
it('transitions idle → placeholder on SEND_MESSAGE', () => {
  const next = streamReducer('idle', { type: 'SEND_MESSAGE' })
  expect(next).toBe('placeholder')
})
```

**CSS/Token Testing (Frontend):**
Read source files directly and assert string presence:
```typescript
const globals = fs.readFileSync(path.resolve(__dirname, '../app/globals.css'), 'utf-8')
it('defines --stream-status-size token', () => {
  expect(globals).toContain('--stream-status-size')
})
```

---

*Testing analysis: 2026-03-15*
