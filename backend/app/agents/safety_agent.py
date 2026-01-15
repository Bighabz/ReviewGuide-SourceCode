"""
Safety & Policy Agent
Responsibilities:
- Text moderation using OpenAI Moderation API
- PII detection and redaction
- Text sanitization
- Policy compliance checks
- Save user message to database after safety checks pass
"""
import re
from app.core.centralized_logger import get_logger
from typing import Dict, Any, Literal
from openai import AsyncOpenAI
from ..schemas.graph_state import GraphState
from app.services.chat_history_manager import chat_history_manager

logger = get_logger(__name__)


class SafetyAgent:
    """Safety and Policy enforcement agent"""

    # PII Detection Patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone_us": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }

    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.on_chain_start_message = "Checking your message for safety..."

    async def execute(self, state: GraphState) -> Dict[str, Any]:
        """
        Execute safety checks on user input

        Input: user_text, conversation_context
        Output: {policy_status, sanitized_text, redaction_map}
        """
        try:
            logger.info(f"Safety Agent executing for session: {state['session_id']}")

            user_text = state["user_message"]
            return await self._execute_safety_checks(user_text)

        except Exception as e:
            logger.error(f"Safety Agent error: {str(e)}", exc_info=True)
            return {
                "policy_status": "allow",
                "sanitized_text": state["user_message"],
                "redaction_map": {},
                "errors": [f"Safety check error: {str(e)}"]
            }

    async def _execute_safety_checks(self, user_text: str) -> Dict[str, Any]:
        """Internal safety check execution"""
        # Step 1: Content Moderation using OpenAI
        moderation_result = await self._moderate_content(user_text)

        # Only block truly harmful content, not mild profanity
        harmful_categories = ["violence", "self-harm", "sexual/minors", "hate/threatening"]
        flagged_harmful = [cat for cat in moderation_result["categories"] if any(harm in cat for harm in harmful_categories)]

        if flagged_harmful:
            logger.warning(f"Blocking harmful content: {flagged_harmful}")
            return {
                "policy_status": "block",
                "sanitized_text": user_text,
                "redaction_map": {},
                "errors": [f"Content flagged for: {', '.join(flagged_harmful)}"]
            }

        # Log but allow content with mild profanity
        if moderation_result["flagged"]:
            logger.info(f"Content flagged but allowing: {moderation_result['categories']}")

        # Step 2: PII Detection and Redaction
        sanitized_text, redaction_map = self._detect_and_redact_pii(user_text)

        # Step 3: Check for jailbreak patterns
        if self._detect_jailbreak_patterns(sanitized_text):
            return {
                "policy_status": "block",
                "sanitized_text": sanitized_text,
                "redaction_map": redaction_map,
                "errors": ["Potential jailbreak attempt detected"]
            }

        # Step 4: Check if clarification needed (too vague or sensitive)
        needs_clarification = self._check_needs_clarification(sanitized_text)

        policy_status = "needs_clarification" if needs_clarification else "allow"

        return {
            "policy_status": policy_status,
            "sanitized_text": sanitized_text,
            "redaction_map": redaction_map,
            "errors": []
        }

    async def _moderate_content(self, text: str) -> Dict[str, Any]:
        """Use OpenAI Moderation API to check content"""
        try:
            response = await self.client.moderations.create(input=text)
            result = response.results[0]

            flagged_categories = []
            if result.flagged:
                # Get all flagged categories from the categories object
                categories_dict = result.categories.model_dump()
                for category, is_flagged in categories_dict.items():
                    if is_flagged:
                        flagged_categories.append(category)

            return {
                "flagged": result.flagged,
                "categories": flagged_categories
            }
        except Exception as e:
            logger.error(f"Moderation API error: {str(e)}", exc_info=True)
            # Fail open - allow content if moderation API fails
            return {"flagged": False, "categories": []}

    def _detect_and_redact_pii(self, text: str) -> tuple[str, Dict[str, str]]:
        """Detect and redact PII from text"""
        sanitized_text = text
        redaction_map = {}

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for i, match in enumerate(matches):
                original = match.group()
                redacted = f"[REDACTED_{pii_type.upper()}_{i}]"
                sanitized_text = sanitized_text.replace(original, redacted)
                redaction_map[redacted] = original
                logger.warning(f"PII detected and redacted: {pii_type}")

        return sanitized_text, redaction_map

    def _detect_jailbreak_patterns(self, text: str) -> bool:
        """Detect potential jailbreak attempts"""
        jailbreak_keywords = [
            "ignore previous",
            "ignore all previous",
            "disregard",
            "forget your",
            "system prompt",
            "as an ai language model",
            "you are now",
            "pretend you are",
            "roleplaying"
        ]

        text_lower = text.lower()
        for keyword in jailbreak_keywords:
            if keyword in text_lower:
                logger.warning(f"Potential jailbreak pattern detected: {keyword}")
                return True

        return False

    def _check_needs_clarification(self, text: str) -> bool:
        """Check if text is too vague and needs clarification"""
        text_lower = text.strip().lower()

        # Allow common greetings - they should be handled by Intent Agent
        common_greetings = ["hi", "hello", "hey", "greetings", "yo"]
        if text_lower in common_greetings:
            return False

        # Very short queries (< 3 chars) might need clarification, except greetings
        if len(text.strip()) < 3:
            return True

        # Check for overly vague queries
        vague_patterns = [
            r"^\s*help\s*$",
            r"^\s*\?\s*$",
            r"^\s*what\s*$",
        ]

        for pattern in vague_patterns:
            if re.match(pattern, text_lower):
                return True

        return False


# Agent node function for LangGraph
async def safety_agent_node(state: GraphState, agent: SafetyAgent) -> GraphState:
    """
    LangGraph node wrapper for Safety Agent
    """
    result = await agent.execute(state)

    # Update state with safety check results
    state.policy_status = result["policy_status"]
    state.sanitized_text = result["sanitized_text"]
    state.redaction_map = result["redaction_map"]

    if result["errors"]:
        state.errors.extend(result["errors"])
        state.status = "error"

    state.current_agent = "safety"

    # Save user message to database after safety checks
    # This ensures the message is saved before other agents process it
    session_id = state.get("session_id")
    user_message = state.get("user_message")
    if session_id and user_message:
        try:
            from app.repositories.conversation_repository import ConversationRepository
            from app.core.database import get_db
            from app.core.redis_client import get_redis

            db_gen = get_db()
            db = await anext(db_gen)
            redis = await get_redis()

            try:
                conversation_repo = ConversationRepository(db=db, redis=redis)
                await conversation_repo.save_message(session_id, "user", user_message)
                logger.info(f"[SafetyAgent] Saved user message to database for session {session_id}")

                # Invalidate cache and reload conversation history so downstream agents have updated history
                await chat_history_manager.invalidate_cache(session_id)
                updated_history = await chat_history_manager.get_history(session_id)
                state["conversation_history"] = updated_history
                logger.info(f"[SafetyAgent] Reloaded conversation history: {len(updated_history)} messages")
            finally:
                await db_gen.aclose()
        except Exception as save_error:
            logger.error(f"[SafetyAgent] Failed to save user message: {save_error}")

    return state
