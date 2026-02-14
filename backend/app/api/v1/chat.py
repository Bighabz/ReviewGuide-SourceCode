"""
Chat Endpoints
SSE streaming chat endpoint with LangGraph integration
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Optional
import json
from app.core.centralized_logger import get_logger
import uuid
import asyncio
from datetime import datetime, date

from app.schemas.graph_state import GraphState
from app.services.langgraph.workflow import graph, AGENT_NAME_TO_INSTANCE
from app.core.redis_client import get_redis
from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, check_rate_limit
from app.repositories.conversation_repository import ConversationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.colored_logging import get_colored_logger


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

logger = get_logger(__name__)
colored_logger = get_colored_logger(__name__)

router = APIRouter()

# Initialize Langfuse with CallbackHandler but disable unwanted OpenTelemetry instrumentation
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

# Initialize Langfuse client with blocked instrumentation scopes to prevent HTTP export errors
langfuse_client = None
langfuse_handler = None

if settings.ENABLE_TRACING and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    # Configure Langfuse client to block OpenTelemetry HTTP exporter instrumentation
    # This prevents "opentelemetry.exporter.otlp.proto.http" errors
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        blocked_instrumentation_scopes=[
            "opentelemetry.exporter.otlp.proto.http._internal",
            "opentelemetry.instrumentation.httpx",
            "opentelemetry.instrumentation.requests"
        ]
    )

    # Create CallbackHandler - data will be truncated by Langfuse automatically
    # If traces are too large and crash browser, consider:
    # 1. Reducing prompt sizes in tools
    # 2. Using Langfuse sampling (only trace % of requests)
    # 3. Disabling tracing for specific tools
    langfuse_handler = CallbackHandler()

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    user_id: Optional[int] = None  # For anonymous users to reuse existing user
    country_code: Optional[str] = None  # User's country code for regional affiliate links
    action: Optional[str] = None  # Optional action for button clicks (e.g., "consent_confirm")


def is_consent_confirmation(request) -> bool:
    """Detect consent confirmations vs new queries.

    Used for two-layer consent flow when user needs to approve
    extended search (Tier 3-4) that may incur additional API costs.

    Args:
        request: ChatRequest with message and optional action

    Returns:
        True if this is a consent confirmation
    """
    # Structured payload from button click
    if getattr(request, "action", None) == "consent_confirm":
        return True

    # Text-based confirmation
    message = getattr(request, "message", None)
    if message:
        consent_patterns = {"yes", "search deeper", "continue", "ok", "proceed", "go ahead"}
        normalized = message.strip().lower()
        return normalized in consent_patterns or normalized.startswith("yes")

    return False



async def generate_chat_stream(
    message: str,
    session_id: str,
    user_id: int,
    country_code: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for chat responses with Langfuse tracking
    Uses CallbackHandler for comprehensive LLM observability

    Args:
        message: User's message
        session_id: Session UUID (string)
        user_id: User ID (integer) to return to frontend for persistence
        country_code: User's country code for regional affiliate links
    """
    # Generate conversation_id for this query
    conversation_id = str(uuid.uuid4())

    # Save original user message BEFORE it gets overwritten by status updates
    original_user_message = message

    # Note: Langfuse tracking is now handled by CallbackHandler
    # Token usage and cost are sent once per search via langfuse_handler

    try:
        # Send initial placeholder message IMMEDIATELY
        placeholder_chunk = {
            "token": "Thinking...",
            "done": False,
            "placeholder": True,
        }
        yield f"data: {json.dumps(placeholder_chunk)}\n\n"

        # Check if we're resuming from a halt state first (before loading history)
        # to avoid unnecessary database/Redis queries for new queries
        from app.services.halt_state_manager import HaltStateManager

        halt_exists = await HaltStateManager.check_halt_exists(session_id)

        # Load halt state if resuming
        halt_state_data = None
        conversation_history = []
        extended_search_confirmed = False  # Flag for consent resume flow

        if halt_exists:
            # Load halt state from Redis using HaltStateManager
            halt_state_data = await HaltStateManager.load_halt_state(session_id)

            # Check for consent_required halt (Tier 3-4 extended search)
            halt_reason = halt_state_data.get("halt_reason") if halt_state_data else None
            if halt_reason == "consent_required":
                # Create a mock request object for consent detection
                class MockRequest:
                    def __init__(self, msg):
                        self.message = msg
                        self.action = None

                if is_consent_confirmation(MockRequest(message)):
                    # User confirmed extended search
                    logger.info(f"[ChatEndpoint] User confirmed extended search for session {session_id}")
                    extended_search_confirmed = True
                    # Keep halt_state_data to restore partial results
                else:
                    # User sent a different message - clear halt and treat as new query
                    logger.info(f"[ChatEndpoint] User declined extended search, treating as new query")
                    await HaltStateManager.delete_halt_state(session_id)
                    halt_state_data = None
                    halt_exists = False

            # Check if this is actually a halted state (has followup questions)
            # vs just stored slots from previous request
            elif halt_state_data:
                followups = halt_state_data.get("followups", [])
                if not followups:
                    # No followups = not a halted state, just stored slots - treat as new query
                    logger.info(f"Halt state exists but no followups - treating as new query, clearing stale state")
                    await HaltStateManager.delete_halt_state(session_id)
                    halt_state_data = None
                    halt_exists = False

        # Load conversation history BEFORE workflow starts
        # Note: User message is saved at end of safety_agent, not here
        # ChatHistoryManager handles MAX_HISTORY_MESSAGES limit internally
        from app.services.chat_history_manager import chat_history_manager
        logger.info(f"[ChatEndpoint] Loading conversation history for session {session_id}...")
        conversation_history = await chat_history_manager.get_history(session_id)

        if conversation_history:
            logger.info(f"[ChatEndpoint] ✅ Loaded {len(conversation_history)} messages from conversation history for session {session_id}")
            # Log first and last message for debugging
            if len(conversation_history) > 0:
                first_msg = conversation_history[0]
                last_msg = conversation_history[-1]
                logger.info(f"[ChatEndpoint] First message: role={first_msg.get('role')}, content_preview={first_msg.get('content', '')[:50]}...")
                logger.info(f"[ChatEndpoint] Last message: role={last_msg.get('role')}, content_preview={last_msg.get('content', '')[:50]}...")
        else:
            logger.info(f"[ChatEndpoint] ❌ No conversation history found for session {session_id} (new conversation or empty history)")

        # Initialize graph state (TypedDict)
        from datetime import datetime, timezone

        # Initialize slots with country_code from request (if provided)
        initial_slots = halt_state_data.get("slots", {}) if halt_state_data else {}
        if not initial_slots.get("country_code"):
            # Set country_code from request or default to settings
            initial_slots["country_code"] = country_code or settings.AMAZON_DEFAULT_COUNTRY

        # Set next_agent for consent resume flow
        resume_next_agent = None
        if extended_search_confirmed and halt_state_data:
            # Resume at tiered_executor with consent confirmed
            resume_next_agent = "tiered_executor"
            logger.info(f"[ChatEndpoint] Setting resume flow to tiered_executor with consent confirmed")

        initial_state: GraphState = {
            "user_message": message,
            "session_id": session_id,
            "conversation_history": conversation_history,
            "status": "running",
            "current_agent": None,
            "next_agent": resume_next_agent,  # Set for consent resume, None otherwise
            "halt": False,  # Required field - reset to False so workflow can continue
            "plan": None,
            "slots": initial_slots,  # Initialize with country_code
            "followups": halt_state_data.get("followups", []) if halt_state_data else [],
            "policy_status": "allow",
            "extended_search_confirmed": extended_search_confirmed,  # Flag for tiered executor
            "sanitized_text": None,
            "redaction_map": {},
            "intent": halt_state_data.get("intent") if halt_state_data else None,
            "intro_text": None,
            # Restore partial_items if resuming from consent halt
            "search_results": halt_state_data.get("partial_items", []) if extended_search_confirmed else [],
            "search_query": None,
            "product_names": [],
            "review_aspects": [],
            "evidence_citations": [],
            "confidence_score": 0.0,
            "review_data": {},
            "entity": None,
            "entity_key": None,
            "normalized_products": [],
            "affiliate_products": {},
            "link_health": {},
            "comparison_table": None,
            "travel_info": halt_state_data.get("travel_info", {}) if halt_state_data else {},
            "hotels": halt_state_data.get("hotels", []) if halt_state_data else [],
            "flights": halt_state_data.get("flights", []) if halt_state_data else [],
            "itinerary": halt_state_data.get("itinerary", []) if halt_state_data else [],
            "travel_results": halt_state_data.get("travel_results") if halt_state_data else None,
            "stream_chunk_data": None,
            "ranked_items": [],
            "assistant_text": None,
            "ui_blocks": [],
            "citations": [],
            "next_suggestions": [],  # Follow-up questions from next_step_suggestion tool
            "agent_statuses": [],
            "tool_citations": [],  # Initialize tool citations list
            "last_search_context": halt_state_data.get("last_search_context", {}) if halt_state_data else {},
            "search_history": halt_state_data.get("search_history", []) if halt_state_data else [],
            "errors": [],
            "metadata": {
                # NOTE: Do NOT add langfuse_handler or callbacks here!
                # CallbackHandler is passed via LangGraph config, not state
                # Adding it to state causes massive JSON serialization that crashes browser
            },
            "created_at": datetime.now(timezone.utc),
        }

        # Log restored state (state was already restored during initialization above)
        if halt_state_data:
            logger.info("🔄 Resumed from HALT state")
            # Log slots from halt_state_data (not from initial_state, as they're removed from GraphState)
            slots = halt_state_data.get("slots", {})
            followups = halt_state_data.get("followups", [])
            logger.info(f"✅ Restored state: intent={initial_state['intent']}, slots={list(slots.keys())}, followups_remaining={len(followups)}")

        # Execute the workflow and stream intermediate states
        # Cost tracking is handled by langfuse_handler passed to graph.astream_events()
        # Create a shared list for citations (mutable, accessible from both tasks)
        citation_buffer = []
        workflow_running = True

        # Create a queue for tool citations
        from app.services.plan_executor import register_tool_citation_callback, clear_tool_citation_callbacks
        tool_citation_queue = asyncio.Queue()

        # Register callback that pushes citations to the buffer directly
        async def citation_callback(citation):
            citation_buffer.append(citation)
            logger.info(f"📥 Citation added to buffer: {citation.get('tool')} - {citation.get('message')}")

        register_tool_citation_callback(citation_callback)

        # Background task that polls event stream
        event_queue = asyncio.Queue()

        async def consume_events():
            """Consume LangGraph events and put them in queue"""
            nonlocal workflow_running
            try:
                async for event in graph.astream_events(initial_state, version="v2", config={"callbacks": [langfuse_handler]}):
                    await event_queue.put(event)
            finally:
                workflow_running = False
                await event_queue.put(None)  # Sentinel value

        # Start event consumer in background
        event_task = asyncio.create_task(consume_events())

        # Use astream_events to get intermediate node executions WITH start/end events
        result_state = None
        last_node_name = None
        data_already_streamed = False  # Track if we already streamed any data (from stream_chunk_data)

        # Main loop: check both citation buffer and event queue
        while True:
            # First, stream any citations in buffer
            while citation_buffer:
                citation = citation_buffer.pop(0)
                tool_name = citation.get("tool", "")
                message = citation.get("message", "")
                if message:
                    # Extract short tool name (e.g., "travel_search_hotels" -> "search_hotels")
                    tool_short_name = tool_name.split("_", 1)[1] if "_" in tool_name else tool_name

                    status_chunk = {
                        "status_update": message,
                        "tool": tool_short_name,
                        "done": False,
                    }
                    yield f"data: {json.dumps(status_chunk)}\n\n"
                    logger.info(f"📤 Streamed tool citation from buffer: {tool_name} - {message}")

            # Then try to get event with short timeout
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=settings.CHAT_EVENT_QUEUE_TIMEOUT)
                if event is None:  # Sentinel - workflow finished
                    break
            except asyncio.TimeoutError:
                # No event yet, loop back to check citations
                continue

            event_type = event.get("event")
            event_name = event.get("name", "")

            # Detect when agents START (on_chain_start) - send status messages
            if event_type == "on_chain_start":
                # Dynamic lookup of agent instance and its status message
                agent_instance = AGENT_NAME_TO_INSTANCE.get(event_name)
                if agent_instance and hasattr(agent_instance, 'on_chain_start_message') and agent_instance.on_chain_start_message:
                    # Special handling for clarifier: only send for second pass (after itinerary)
                    if event_name == "agent_travel_clarifier" and last_node_name != "itinerary":
                        continue

                    # Extract short agent name from event_name (e.g., "agent_travel_planner" -> "planner")
                    agent_short_name = event_name.split("_")[-1] if "_" in event_name else event_name

                    status_chunk = {
                        "status_update": agent_instance.on_chain_start_message,
                        "agent": agent_short_name,
                        "done": False,
                    }
                    yield f"data: {json.dumps(status_chunk)}\n\n"
                    logger.info(f"📤 Sent status update from {event_name}: {agent_instance.on_chain_start_message}")
                    last_node_name = agent_short_name

            # Detect when nodes complete and check next_agent (for immediate status messages)
            elif event_type == "on_chain_end":
                if event_name == "LangGraph":
                    # Capture final state
                    result_state = event.get("data", {}).get("output", {})
                else:
                    # Check if any node just completed
                    output_data = event.get("data", {}).get("output", {})

                    # STREAM DATA IMMEDIATELY if agent returned stream_chunk_data
                    if isinstance(output_data, dict):
                        stream_data = output_data.get("stream_chunk_data")
                        if stream_data:
                            # Clear placeholder first
                            clear_chunk = {"clear": True, "done": False}
                            yield f"data: {json.dumps(clear_chunk)}\n\n"

                            # Stream the data with its type
                            data_type = stream_data.get("type")
                            data_content = stream_data.get("data")

                            if data_type and data_content:
                                # Send as full object
                                chunk = {
                                    data_type: data_content,
                                    "done": False,
                                }
                                # Check if stream_data has create_new_message flag
                                if stream_data.get("create_new_message"):
                                    chunk["create_new_message"] = True
                                yield f"data: {json.dumps(chunk, cls=DateTimeEncoder)}\n\n"

                                # Mark that we've streamed data
                                data_already_streamed = True
                                logger.info(f"📤 Streamed {data_type} from {event_name}")

                    # Check if next_agent=travel_planner for early status message
                    if isinstance(output_data, dict) and output_data.get("next_agent") == "travel_planner":
                        # Send status message immediately BEFORE travel_planner starts
                        status_chunk = {
                            "status_update": "✈️ Finding the best flights and hotels...",
                            "agent": "planner",
                            "done": False,
                        }
                        yield f"data: {json.dumps(status_chunk)}\n\n"
                        logger.info(f"🏨 Sent status update EARLY (from {event_name} completion with next_agent=travel_planner)")
                        last_node_name = "planner"

        # Wait for event task to complete
        await event_task

        # Stream any remaining citations in buffer
        while citation_buffer:
            citation = citation_buffer.pop(0)
            tool_name = citation.get("tool", "")
            message = citation.get("message", "")
            if message:
                tool_short_name = tool_name.split("_", 1)[1] if "_" in tool_name else tool_name
                status_chunk = {
                    "status_update": message,
                    "tool": tool_short_name,
                    "done": False,
                }
                yield f"data: {json.dumps(status_chunk)}\n\n"
                logger.info(f"📤 Streamed remaining citation from buffer: {tool_name} - {message}")

        # Fallback: if we didn't get final state from events, use astream to get it
        if not result_state:
            logger.warning("⚠️ No final state from astream_events, falling back to astream")
            async for state_update in graph.astream(initial_state, config={"callbacks": [langfuse_handler]}):
                result_state = state_update

        # Clear callbacks after workflow completes
        clear_tool_citation_callbacks()

        # DEBUG: Log result_state keys
        logger.info(f"🔍 DEBUG: result_state keys: {list(result_state.keys())}")

        # Prepare SINGLE consolidated log with ALL metrics
        assistant_text = result_state.get('assistant_text') or ''
        detected_intent = result_state.get("intent", "unknown")

        # Get CallbackHandler trace data
        langfuse_trace_url = None
        if langfuse_handler:
            try:
                # Get the trace URL from CallbackHandler
                trace = langfuse_handler.trace
                if trace:
                    langfuse_trace_url = f"https://cloud.langfuse.com/trace/{trace.id}"
            except Exception as e:
                logger.debug(f"Could not get langfuse trace URL: {e}")

        # SINGLE CONSOLIDATED LOG - All data in one place
        # Cost/token metrics are tracked by Langfuse CallbackHandler and visible in trace URL
        consolidated_log = {
            "event": "query_completed",
            "session_id": session_id,
            "conversation_id": conversation_id,
            "query": message[:200],
            "intent": detected_intent,
            "status": result_state.get("status", "unknown"),
            "final_agent": result_state.get("current_agent"),
            "response_length": len(assistant_text),
            # Langfuse tracking (token/cost data available in trace)
            "langfuse_trace_url": langfuse_trace_url,
        }

        # Log consolidated response metrics in YELLOW
        colored_logger.api_output(consolidated_log, endpoint="/v1/chat/stream")

        # Clear halt state if workflow completed successfully (not halted)
        # NOTE: We don't save halt state here because agents handle that themselves
        # (intent_agent, clarifier_agent, travel_clarifier_agent save to HaltStateManager)
        if result_state.get("status") != "halted" and halt_exists:
            # Workflow completed - clear halt state
            await HaltStateManager.delete_halt_state(session_id)

        # Get the response text and ui_blocks
        response_text = result_state.get("assistant_text", "")
        ui_blocks = result_state.get("ui_blocks", [])

        # Check if workflow is halted - if so, don't stream any text (questions will be in blue box)
        is_halted = result_state.get("status") == "halted" and result_state.get("halt")

        # For product intent, send ui_blocks in the SAME chunk as clear to avoid race condition
        ui_blocks_sent_early = False
        if ui_blocks and result_state.get("intent") == "product" and not data_already_streamed:
            logger.info(f"🔍 DEBUG: Sending UI blocks WITH clear for product intent ({len(ui_blocks)} blocks)")
            # Send ui_blocks AND clear in the same chunk
            combined_chunk = {
                "ui_blocks": ui_blocks,
                "clear": True,
                "done": False,
            }
            yield f"data: {json.dumps(combined_chunk, cls=DateTimeEncoder)}\n\n"
            ui_blocks_sent_early = True
            logger.info(f"📤 Sent {len(ui_blocks)} UI blocks with clear signal")
        elif not data_already_streamed:
            # Clear placeholder ONLY if we haven't already streamed data
            # (If data was streamed, we want to keep it and append followups below it)
            clear_chunk = {
                "clear": True,
                "done": False,
            }
            yield f"data: {json.dumps(clear_chunk)}\n\n"
        else:
            logger.info("🔍 Skipping clear chunk - data already streamed, will append followups")

        # Stream response text if available and NOT halted and NOT already streamed data
        should_stream_text = not is_halted and response_text and not data_already_streamed

        if should_stream_text:
            logger.info(f"🔍 DEBUG: Streaming response text ({len(response_text)} chars)")
            for char in response_text:
                chunk = {
                    "token": char,
                    "done": False,
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                # Small delay for smoother streaming
                await asyncio.sleep(settings.CHAT_STREAM_SLEEP_DELAY)
        else:
            logger.info(f"🔍 DEBUG: Skipping text streaming (halted={is_halted}, has_text={bool(response_text)}, data_streamed={data_already_streamed})")

        # Only include followup questions if the workflow is HALTED (not completed)
        # Just pass through whatever the clarifier agent returns - no processing here
        followups_to_send = None
        if result_state.get("status") == "halted" and result_state.get("halt"):
            followups_to_send = result_state.get("assistant_text")
            logger.info(f"🔍 Workflow HALTED - passing through followups from clarifier agent")
        else:
            logger.info(f"🔍 Workflow COMPLETED - no followup questions")

        # DON'T send ui_blocks in final chunk if we already sent them early (avoids duplicates)
        # Get next_suggestions for follow-up questions at end of response
        next_suggestions = result_state.get("next_suggestions", [])
        if next_suggestions:
            logger.info(f"🔍 Found {len(next_suggestions)} next step suggestions to send")

        final_chunk = {
            "done": True,
            "status": result_state.get("status"),
            "intent": result_state.get("intent"),
            "ui_blocks": [] if ui_blocks_sent_early else ui_blocks,
            "citations": result_state.get("citations", []),
            "followups": followups_to_send,  # Pass through structured data from clarifier agent
            "next_suggestions": next_suggestions,  # Follow-up questions from next_step_suggestion tool
            "user_id": user_id,
        }

        logger.info(f"🔍 DEBUG: Final chunk - has_followups: {followups_to_send is not None}")
        logger.info(f"🔍 DEBUG: Final chunk ui_blocks: {len(final_chunk['ui_blocks'])} blocks")
        yield f"data: {json.dumps(final_chunk, cls=DateTimeEncoder)}\n\n"

        # Save BOTH user and assistant messages to database at the end of stream
        # This includes ALL data that was sent to frontend in message_metadata
        try:
            # 1. Save user message first (use original message, not the one overwritten by status updates)
            user_message_text = original_user_message
            is_suggestion_click = original_user_message.startswith("[SUGGESTION_CLICK]")

            # Build user message metadata
            user_metadata = {}
            if is_suggestion_click:
                user_metadata["is_suggestion_click"] = True

            await chat_history_manager.save_user_message(
                session_id=session_id,
                content=user_message_text,
                message_metadata=user_metadata if user_metadata else None
            )
            logger.info(f"✅ Saved user message to database (session: {session_id})")

            # 2. Save assistant message with ALL data sent to frontend
            # Determine content based on whether halted or normal response
            if is_halted and followups_to_send and isinstance(followups_to_send, dict):
                assistant_content = followups_to_send.get("intro", "")
            else:
                assistant_content = response_text

            # Build assistant message metadata with ALL fields sent to frontend
            assistant_metadata = {}

            # Add all optional fields that were sent to frontend
            if followups_to_send:
                assistant_metadata["followups"] = followups_to_send
            if ui_blocks:
                assistant_metadata["ui_blocks"] = ui_blocks
            if next_suggestions:
                assistant_metadata["next_suggestions"] = next_suggestions
            if result_state.get("citations"):
                assistant_metadata["citations"] = result_state.get("citations")
            if result_state.get("intent"):
                assistant_metadata["intent"] = result_state.get("intent")
            if result_state.get("status"):
                assistant_metadata["status"] = result_state.get("status")

            # Save assistant message with complete metadata
            await chat_history_manager.save_assistant_message(
                session_id=session_id,
                content=assistant_content,
                message_metadata=assistant_metadata if assistant_metadata else None
            )
            logger.info(f"✅ Saved assistant message with metadata to database (session: {session_id})")

        except Exception as save_error:
            logger.error(f"❌ Failed to save messages to database: {save_error}", exc_info=True)

        # Flush Langfuse traces immediately after request completes
        if langfuse_handler:
            try:
                get_langfuse_client().flush()
                logger.debug("Langfuse traces flushed")
            except Exception as flush_error:
                logger.debug(f"Langfuse flush warning: {flush_error}")

    except Exception as e:
        # Log error with centralized logger
        logger.error(
            f"Error in chat_stream: {str(e)}",
            exc_info=True,
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "message_preview": message[:100] if message else ""
            }
        )

        # Return simple error message
        error_chunk = {
            "error": "Something went wrong. If this issue persists please try again.",
            "done": True,
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


@router.get("/conversations")
async def list_conversations(
    session_id: Optional[str] = None,
    session_ids: Optional[str] = None,  # Comma-separated list of session IDs
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    List conversations with proper authorization.

    - Admin users: Can see all conversations (for moderation)
    - Authenticated users: Can see their own conversations
    - Anonymous users: Must provide session_id(s) to see only those sessions

    SECURITY: Never expose all conversations without proper authorization.
    """
    try:
        from app.models.conversation_message import ConversationMessage

        # SECURITY: Authorization check
        is_admin = current_user and current_user.get("type") == "admin"

        # Parse session_ids if provided (comma-separated)
        allowed_sessions = []
        if session_ids:
            allowed_sessions = [s.strip() for s in session_ids.split(',') if s.strip()]
        elif session_id:
            allowed_sessions = [session_id]

        # If not admin and no session_ids provided, return empty (fail-safe)
        if not is_admin and not allowed_sessions:
            logger.warning("Unauthorized attempt to list all conversations without session_ids")
            return {
                "success": True,
                "conversations": []
            }

        # Build base query
        first_msg_subq = (
            select(
                ConversationMessage.session_id,
                func.min(ConversationMessage.sequence_number).label('first_seq')
            )
            .group_by(ConversationMessage.session_id)
            .subquery()
        )

        # Get conversations with first message content
        stmt = (
            select(
                ConversationMessage.session_id,
                ConversationMessage.content,
                ConversationMessage.created_at,
                func.count(ConversationMessage.id).over(partition_by=ConversationMessage.session_id).label('message_count')
            )
            .join(
                first_msg_subq,
                (ConversationMessage.session_id == first_msg_subq.c.session_id) &
                (ConversationMessage.sequence_number == first_msg_subq.c.first_seq)
            )
            .where(ConversationMessage.role == 'user')
        )

        # SECURITY: Filter by allowed session_ids if not admin
        if not is_admin and allowed_sessions:
            stmt = stmt.where(ConversationMessage.session_id.in_(allowed_sessions))

        stmt = stmt.order_by(desc(ConversationMessage.created_at)).limit(50)

        result = await db.execute(stmt)
        rows = result.all()

        conversations = []
        seen_sessions = set()

        for row in rows:
            if row.session_id not in seen_sessions:
                seen_sessions.add(row.session_id)
                conversations.append({
                    "session_id": row.session_id,
                    "preview": row.content[:100] + "..." if len(row.content) > 100 else row.content,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "message_count": row.message_count
                })

        logger.info(f"Listed {len(conversations)} conversations (admin={is_admin}, session_filter={session_id is not None})")

        return {
            "success": True,
            "conversations": conversations
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.post("/conversations")
async def create_conversation():
    """
    Create a new conversation session.

    Returns a new session_id that can be used for chatting.
    """
    new_session_id = str(uuid.uuid4())
    logger.info(f"Created new conversation: {new_session_id}")

    return {
        "success": True,
        "session_id": new_session_id
    }


@router.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Delete a conversation and all its messages.
    """
    try:
        conversation_repo = ConversationRepository(db=db, redis=redis)
        success = await conversation_repo.delete_history(session_id)

        if success:
            logger.info(f"Deleted conversation: {session_id}")
            return {"success": True, "message": "Conversation deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

    except Exception as e:
        logger.error(f"Failed to delete conversation {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Get conversation history for a session

    Args:
        session_id: Session UUID string

    Returns:
        List of messages with role, content, and optional structured_data
    """
    try:
        # Create conversation repository
        conversation_repo = ConversationRepository(db=db, redis=redis)

        # Get conversation history from database/Redis
        history = await conversation_repo.get_history(session_id)

        logger.debug(f"Retrieved {len(history)} messages for session {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "messages": history
        }

    except Exception as e:
        logger.error(f"Failed to get conversation history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Streaming chat endpoint with optional authentication and rate limiting
    Returns Server-Sent Events (SSE) stream

    - **message**: User message
    - **session_id**: Optional session ID (will be created if not provided)

    Authentication: Optional (Bearer token)
    - Authenticated users: Sessions linked to user account, 100 req/hour
    - Anonymous users: Sessions tracked without user link, 10 req/hour

    Rate Limiting:
    - Guest users (no auth): 10 requests per hour (by IP)
    - Authenticated users: 100 requests per hour (by user ID)
    """
    # Generate or use provided session ID
    session_id = chat_request.session_id or str(uuid.uuid4())

    colored_logger.api_input({
        "message": chat_request.message,
        "session_id": session_id,
        "user_id": chat_request.user_id,
        "auth": current_user['username'] if current_user else 'anonymous'
    }, endpoint="/v1/chat/stream")

    # Get or create session with country detection
    from app.services.session_service import get_or_create_session

    db_session_id, returned_user_id, country_code = await get_or_create_session(
        db, request, session_id, chat_request.user_id, current_user
    )
    if not db_session_id or not returned_user_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create or retrieve session"
        )

    logger.debug(f"Session {session_id} → DB ID: {db_session_id}, user: {returned_user_id}, country: {country_code}")

    # Return streaming response with user_id
    # Note: ChatHistoryManager is used internally for saving/loading messages
    return StreamingResponse(
        generate_chat_stream(
            chat_request.message,
            session_id,
            returned_user_id,
            country_code  # Pass detected/stored country_code
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )
