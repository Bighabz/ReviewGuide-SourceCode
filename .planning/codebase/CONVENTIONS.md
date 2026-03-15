# Coding Conventions

**Analysis Date:** 2026-03-15

## Naming Patterns

**Files:**
- Frontend components: `PascalCase.tsx` — e.g., `ChatContainer.tsx`, `ProductCards.tsx`, `BlockSkeleton.tsx`
- Frontend hooks: `camelCase.ts` with `use` prefix — e.g., `useStreamReducer.ts`
- Frontend lib utilities: `camelCase.ts` — e.g., `chatApi.ts`, `normalizeBlocks.ts`, `skeletonMap.ts`
- Backend modules: `snake_case.py` — e.g., `product_search.py`, `chat_history_manager.py`
- Backend tests: `test_<module>.py` — e.g., `test_chat_api.py`, `test_circuit_breaker.py`

**Functions/Methods:**
- TypeScript/JS: `camelCase` for functions and variables — e.g., `streamChat`, `formatTimestamp`, `sortSuggestions`
- Python: `snake_case` for functions and methods — e.g., `get_history`, `check_rate_limit`, `log_and_raise_agent_error`
- Python async functions: prefixed with `async def`, no special naming convention beyond that
- Private Python helpers: single underscore prefix — e.g., `_sse_event`, `_load_session_context`, `_run_safety`

**Variables:**
- TypeScript: `camelCase` — e.g., `sessionId`, `uiBlocks`, `streamState`
- Python: `snake_case` — e.g., `session_id`, `ui_blocks`, `mock_redis`
- Constants (both): `UPPER_SNAKE_CASE` — e.g., `MAX_RETRIES`, `SUGGESTION_CLICK_PREFIX`, `TIER_ROUTING_TABLE`, `CATEGORY_SORT_ORDER`

**Types/Classes/Interfaces:**
- TypeScript interfaces: `PascalCase` with descriptive names — e.g., `NextSuggestion`, `StreamAction`, `ResponseMetadata`
- TypeScript types: `PascalCase` — e.g., `StreamState`, `SuggestionCategory`
- Python classes: `PascalCase` — e.g., `BaseAgent`, `ConversationRepository`, `TieredAPIOrchestrator`
- Pydantic models: `PascalCase` ending in `Request`/`Response`/`Model` — e.g., `ClickRequest`, `ClickResponse`, `LivenessResponse`
- Python TypedDict: `PascalCase` — e.g., `GraphState`

**Backend Settings:**
- All settings on `Settings(BaseSettings)` use `UPPER_SNAKE_CASE` — e.g., `OPENAI_API_KEY`, `CORS_ORIGINS`, `MAX_PRODUCTS_RETURN`
- Located at `backend/app/core/config.py`, accessed globally as `settings`

## Code Style

**Formatting:**
- No `.prettierrc` or `biome.json` detected in frontend — relies on Next.js default ESLint
- TypeScript strict mode enabled in `frontend/tsconfig.json` (`"strict": true`)
- Python: no `pyproject.toml` detected; formatting not enforced via config file (manual/editor-based)

**Linting:**
- Frontend: Next.js built-in ESLint (`next lint`), one `eslint-disable-next-line` seen in `HotelCards.tsx` for img element
- Backend: `# noqa: E402` used sparingly for sys.path import ordering exceptions
- `# type: ignore[no-any-return]` used once in `backend/app/lib/toon_python/normalizer.py`

## Import Organization

**TypeScript — Order:**
1. React hooks (`import { useState, useEffect, useRef } from 'react'`)
2. Third-party packages (`import ReactMarkdown from 'react-markdown'`, `import { motion } from 'framer-motion'`)
3. Internal components (`import MessageList from './MessageList'`)
4. Internal lib/hooks (`import { streamChat } from '@/lib/chatApi'`, `import { useStreamReducer } from '@/hooks/useStreamReducer'`)
5. Types (`import type { SkeletonBlockType } from '@/components/BlockSkeleton'`)

**Python — Order:**
1. Standard library (`import json`, `import asyncio`, `from typing import ...`)
2. Third-party (`from fastapi import ...`, `from pydantic import ...`)
3. Internal app (`from app.core.config import settings`, `from app.schemas.graph_state import GraphState`)

**Path Aliases:**
- Frontend uses `@/*` aliased to project root in `frontend/tsconfig.json` — e.g., `@/lib/chatApi`, `@/components/BlockSkeleton`
- Relative imports (`./MessageList`, `'../hooks/useStreamReducer'`) used for same-directory or one-level-up imports

## Module File Headers

**Python:** Every module starts with a docstring describing its purpose:
```python
"""
Chat Endpoints
SSE streaming chat endpoint with LangGraph integration
"""
```

**TypeScript/JS:** JSDoc block comments used for public functions and exported interfaces:
```typescript
/**
 * Chat API Client with SSE Streaming Support
 * Includes auto-reconnect with exponential backoff
 */
```

**RFC References:** RFC section markers (`RFC §2.4`, `RFC §2.3`) used as inline comments to mark implementation of specific design decisions — e.g., `// RFC §2.4 — Category sort priority`.

## Error Handling

**Backend Patterns:**

Agents use the `log_and_raise_agent_error` helper from `backend/app/core/error_manager.py`:
```python
except Exception as e:
    log_and_raise_agent_error(
        logger=self.logger,
        source=self.agent_name,
        message=f"Model generation failed: {str(e)}",
        original_error=e,
        session_id=session_id,
        extra_context={"operation": "generate", "model": model}
    )
```

Tools use the `@tool_error_handler` decorator from `backend/app/core/error_manager.py`:
```python
@tool_error_handler(tool_name="product_search", error_message="Failed to search products")
async def product_search(state: Dict[str, Any]) -> Dict[str, Any]:
    ...
```

FastAPI endpoints raise `HTTPException` directly:
```python
raise HTTPException(status_code=503, detail=health_status)
```

Error classes: `AgentError(BaseError)` and `ToolError(BaseError)` in `backend/app/core/error_manager.py`. Both carry `source`, `message`, `original_error`, and `context`.

**Frontend Patterns:**

Callbacks-based error propagation in streaming — callers pass `onError` callback:
```typescript
const promise = streamChat({ message: 'test', onToken, onComplete, onError })
```

`ErrorBoundary` component (`frontend/components/ErrorBoundary.tsx`) wraps subtrees. The `useStreamReducer` hook tracks `errored` and `interrupted` terminal states.

## Logging

**Backend:**
- `get_logger(__name__)` from `backend/app/core/centralized_logger.py` used in every module
- `get_colored_logger(__name__)` from `backend/app/core/colored_logging.py` used for agent/tool debug output
- Both loggers respect `LOG_ENABLED` env flag (disabled in test environment)
- F-string interpolation used in log messages: `logger.error(f"Database health check failed: {e}")`
- `logger.info`, `logger.error`, `logger.debug` — standard Python log levels
- Structured logging optionally JSON-formatted (`LOG_FORMAT=json`)

**Frontend:**
- `console.error` and `console.warn` preserved in production build (others stripped via `removeConsole` in `frontend/next.config.js`)
- No frontend logging framework — plain `console.*` calls
- Tests mock `console.error` with `vi.spyOn(console, 'error').mockImplementation(() => {})` to suppress noise

## Comments

**When to Comment:**
- Docstrings required on all Python classes, public methods, and module headers
- JSDoc blocks used on exported TypeScript functions and interfaces
- Inline comments on non-obvious logic — especially RFC section compliance markers
- Descriptive comments on complex `mock` setups in tests (explain why async vs sync mock)

**Inline Style:**
- Python: `# Comment text` — space after `#`
- TypeScript: `// Comment` for single-line, `/* */` for multi-line blocks in non-JSDoc contexts

## Function Design

**Python async functions:**
- All agent and tool entry points are `async def`
- Inner coroutines nested inside workflow nodes to enable budget/cancellation wrapping
- State dict (`Dict[str, Any]`) is the standard tool interface: read from `state.get(...)`, return dict of updates

**TypeScript functions:**
- Arrow functions for callbacks and closures
- Named `function` declarations for exported utilities and reducers
- Custom render helpers in tests (e.g., `function renderUI(overrides)`) to reduce boilerplate

**Parameters:**
- Python: keyword args with `Optional` type hints and defaults, documented in Google-style docstrings
- TypeScript: destructured object params for component props with explicit `interface` definitions

**Return Values:**
- Python tools: always return `Dict[str, Any]` — partial state updates to merge into GraphState
- Python agents: `async def run(self, state: Any) -> Any` — returns updated state dict
- TypeScript hooks: return named object with state and dispatch (`{ streamState, isStreaming, dispatch }`)

## Component Design (Frontend)

**'use client' directive:** Applied at top of every interactive component file.

**Props interfaces:** Defined inline above the component function using `interface ComponentNameProps`.

**State initialization:** Use deterministic values based on IDs, never `Math.random()` (causes hydration errors in SSR).

**Tailwind class composition:** Use `cn()` from `frontend/lib/utils.ts` to merge conditional classes:
```typescript
import { cn } from '@/lib/utils'
cn('base-class', condition && 'conditional-class')
```

**Re-export pattern:** Types canonical in one module, re-exported from consumers:
```typescript
// In ChatContainer.tsx
export type { SuggestionCategory, NextSuggestion } from '@/lib/chatApi'
```

## Module Design

**Barrel Files:** Not used. Direct imports from specific files.

**Exports:**
- Python: no `__all__` defined; all public symbols importable
- TypeScript: named exports preferred (`export function`, `export interface`); default export for React components

**Singleton Pattern (Python):**
- Module-level instances used for services — e.g., `chat_history_manager` in `backend/app/services/chat_history_manager.py`, `model_service` in `backend/app/services/model_service.py`
- Settings loaded as `settings = Settings()` at module level in `backend/app/core/config.py`

---

*Convention analysis: 2026-03-15*
