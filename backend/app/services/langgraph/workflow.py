"""
LangGraph Workflow - Simplified MCP Architecture
5 main agents: Safety, Intent, Planner, Clarifier, Executor
Plus tiered routing nodes: routing_gate, tiered_executor
"""
from app.core.centralized_logger import get_logger
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.schemas.graph_state import GraphState
from app.core.config import settings
from app.core.colored_logging import get_colored_logger

# Import the 5 main agent classes
from app.agents.safety_agent import SafetyAgent
from app.agents.intent_agent import IntentAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.clarifier_agent import ClarifierAgent
from app.services.plan_executor import PlanExecutor

# Import tiered routing nodes
from app.services.langgraph.nodes.routing_gate import routing_gate_node
from app.services.langgraph.nodes.tiered_executor import tiered_executor_node

logger = get_logger(__name__)
colored_logger = get_colored_logger(__name__)


# Initialize agent instances
safety_agent_instance = SafetyAgent(openai_api_key=settings.OPENAI_API_KEY)
intent_agent_instance = IntentAgent()
planner_agent_instance = PlannerAgent()
clarifier_agent_instance = ClarifierAgent()
plan_executor_instance = PlanExecutor()


# Agent name to instance mapping for dynamic status message lookup
AGENT_NAME_TO_INSTANCE = {
    "agent_safety": safety_agent_instance,
    "agent_intent": intent_agent_instance,
    "agent_planner": planner_agent_instance,
    "agent_clarifier": clarifier_agent_instance,
    "agent_plan_executor": plan_executor_instance,
}


# Agent node wrapper functions
async def safety_node(state: GraphState) -> Dict[str, Any]:
    """Safety & Policy Agent Node"""
    colored_logger.agent_title("SAFETY AGENT - INPUT", agent_name="SafetyAgent")
    colored_logger.agent_data({
        "user_message": state.get('user_message', '')[:100] + "...",
        "session_id": state.get('session_id')
    }, label="Input")

    # Check if we're resuming from a halted state
    session_id = state.get("session_id")
    logger.info(f"  Checking for halt state with session_id: {session_id}")
    if session_id:
        try:
            from app.services.halt_state_manager import HaltStateManager

            halted_state_exists = await HaltStateManager.check_halt_exists(session_id)
            logger.info(f"  Halt state exists: {halted_state_exists}")

            if halted_state_exists:
                # Load halt state using HaltStateManager
                halt_state_data = await HaltStateManager.load_halt_state(session_id)

                if halt_state_data:
                    logger.info(f"  Found halt state - intent: {halt_state_data.get('intent')}, slots: {halt_state_data.get('slots')}")

                    # Only resume if there are actual followup questions
                    followups = halt_state_data.get("followups", [])

                    if not followups or len(followups) == 0:
                        logger.info("  ✗ Halt state exists but NO followups - treating as NEW query, clearing stale halt state")
                        await HaltStateManager.delete_halt_state(session_id)
                    else:
                        logger.info(f"  ✓ Halt state has {len(followups)} followup(s) - RESUMING TO CLARIFIER")

                        # Restore state and route to clarifier
                        resume_update = {
                            "policy_status": "allow",
                            "sanitized_text": state.get("user_message"),
                            "redaction_map": {},
                            "current_agent": "safety",
                            "next_agent": "clarifier",  # Resume to clarifier for slot extraction
                        }

                        # Restore intent, slots, and plan from halt state
                        if halt_state_data.get("intent"):
                            resume_update["intent"] = halt_state_data["intent"]
                            logger.info(f"  ✓ RESTORED INTENT: {halt_state_data['intent']}")

                        if halt_state_data.get("slots"):
                            resume_update["slots"] = halt_state_data["slots"]
                            logger.info(f"  ✓ RESTORED SLOTS: {halt_state_data['slots']}")

                        if halt_state_data.get("plan"):
                            resume_update["plan"] = halt_state_data["plan"]
                            num_steps = len(halt_state_data["plan"].get("steps", []))
                            logger.info(f"  ✓ RESTORED PLAN: {num_steps} steps")

                        return resume_update
            else:
                logger.info("  No halt state found - routing to intent agent (normal flow)")
        except Exception as e:
            logger.error(f"Error checking halt state: {e}", exc_info=True)

    result = await safety_agent_instance.execute(state)

    # Add user message to conversation_history state (don't save to database yet)
    # Database saving happens at the end of the stream in chat.py
    user_message = state.get("user_message")
    conversation_history = state.get("conversation_history", []).copy()

    if user_message:
        # Append user message to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        logger.info(f"[SafetyAgent] Added user message to conversation_history state ({len(conversation_history)} total messages)")

    # Build update dict
    update = {
        "policy_status": result["policy_status"],
        "sanitized_text": result["sanitized_text"],
        "redaction_map": result["redaction_map"],
        "current_agent": "safety",
        "conversation_history": conversation_history,  # Update state with new message
    }

    if result.get("errors"):
        update["errors"] = result["errors"]
        update["status"] = "error"
        update["next_agent"] = None
    elif result["policy_status"] == "block":
        update["status"] = "error"
        update["assistant_text"] = "I cannot process this request due to content policy violations."
        update["next_agent"] = None
    else:
        update["next_agent"] = "intent"

    colored_logger.agent_title("SAFETY AGENT - OUTPUT", agent_name="SafetyAgent")
    colored_logger.agent_data({
        "policy_status": update['policy_status'],
        "next_agent": update.get('next_agent'),
        "errors": update.get('errors', [])
    }, label="Output")

    return update


async def intent_node(state: GraphState) -> Dict[str, Any]:
    """Intent & Slot-Filling Agent Node"""
    colored_logger.agent_title("INTENT AGENT - INPUT", agent_name="IntentAgent")
    colored_logger.agent_data({
        "sanitized_text": state.get('sanitized_text', '')[:100] + "..."
    }, label="Input")

    result = await intent_agent_instance.execute(state)

    # Load slots/followups from HaltStateManager
    from app.services.halt_state_manager import HaltStateManager
    session_id = state.get("session_id")
    halt_state = await HaltStateManager.get_halt_state(session_id) if session_id else None

    # Get slots/followups from HaltStateManager
    slots = halt_state.get("slots", {}) if halt_state else {}
    followups = halt_state.get("followups", []) if halt_state else []
    missing_slots = [f["slot"] for f in followups if isinstance(f, dict) and "slot" in f]

    # Build update dict
    update = {
        "intent": result["intent"],
        "current_agent": "intent",
    }

    # Add optional fields if they exist
    if result.get("intro_text"):
        update["intro_text"] = result["intro_text"]
        update["assistant_text"] = result["intro_text"]
        logger.info(f"  Added intro to assistant_text: {result['intro_text'][:100]}...")

    # Route to planner for all supported intents (including intro)
    if result["intent"] in ["product", "travel", "service", "comparison", "general", "intro"]:
        update["next_agent"] = "planner"
        logger.info(f"  🔄 {result['intent']} intent -> PLANNER AGENT")
    else:
        # Unknown intent - end workflow
        update["status"] = "error"
        update["assistant_text"] = "I'm not sure how to help with that."
        update["next_agent"] = None
        logger.warning(f"  Unknown intent: {result['intent']}")

    colored_logger.agent_title("INTENT AGENT - OUTPUT", agent_name="IntentAgent")
    colored_logger.agent_data({
        "intent": update['intent'],
        "slots": list(slots.keys()),
        "missing_slots": missing_slots,
        "intro_text": (update.get('intro_text', '')[:50] + "...") if update.get('intro_text') else 'None',
        "next_agent": update['next_agent']
    }, label="Output")

    return update


async def planner_node(state: GraphState) -> Dict[str, Any]:
    """Planner Agent Node - Generates dynamic execution plan using MCP tools"""
    colored_logger.agent_title("PLANNER AGENT - INPUT", agent_name="PlannerAgent")
    colored_logger.agent_data({
        "user_message": state.get('user_message', '')[:100] + "...",
        "intent": state.get('intent'),
        "slots": state.get('slots', {}),
    }, label="Input")

    result = await planner_agent_instance.execute(state)

    # Return update dict - always route to clarifier after planning
    update = {
        "plan": result["plan"],
        "current_agent": "planner",
        "status": result.get("status", "running"),
        "next_agent": "clarifier",  # Always go to clarifier to check required slots
    }

    colored_logger.agent_title("PLANNER AGENT - OUTPUT", agent_name="PlannerAgent")
    colored_logger.agent_data({
        "num_steps": len(result["plan"]["steps"]),
        "steps": [step["id"] for step in result["plan"]["steps"]],
        "status": update['status'],
        "next_agent": update['next_agent']
    }, label="Output")

    return update


async def clarifier_node(state: GraphState) -> Dict[str, Any]:
    """Clarifier Agent Node - Checks required slots and generates follow-up questions"""
    colored_logger.agent_title("CLARIFIER AGENT - INPUT", agent_name="ClarifierAgent")
    colored_logger.agent_data({
        "plan_steps": len(state.get('plan', {}).get('steps', [])),
        "current_slots": list(state.get('slots', {}).keys()),
    }, label="Input")

    result = await clarifier_agent_instance.execute(state)

    # Build update dict
    update = {
        "slots": result.get("slots", state.get("slots", {})),
        "followups": result.get("followups", []),
        "current_agent": "clarifier",
    }

    # DEBUG: Log slots being returned from Clarifier
    logger.info(f"🔍 DEBUG: Clarifier returning slots to state: {update['slots']}")

    if result.get("next_question"):
        # HALT - return follow-up question to user
        update["assistant_text"] = result["next_question"]
        update["status"] = "halted"
        update["halt"] = True
        update["next_agent"] = None
        logger.info(f"[Clarifier] HALTED - returning question: {result['next_question']}")
    elif result.get("proceed_to_execution"):
        # All slots filled - proceed to plan executor
        update["next_agent"] = "plan_executor"
        update["status"] = "running"
        logger.info(f"[Clarifier] All slots filled - proceeding to execution")
    else:
        # Default: proceed to plan executor
        update["next_agent"] = "plan_executor"
        update["status"] = "running"

    colored_logger.agent_title("CLARIFIER AGENT - OUTPUT", agent_name="ClarifierAgent")
    colored_logger.agent_data({
        "slots": list(update['slots'].keys()),
        "num_followups": len(update['followups']),
        "next_question": update.get('next_question', 'None'),
        "proceed": result.get("proceed_to_execution", False),
        "status": update['status'],
        "next_agent": update.get('next_agent')
    }, label="Output")

    return update


async def plan_executor_node(state: GraphState) -> Dict[str, Any]:
    """Plan Executor Node - Executes MCP-based dynamic plan with parallel execution"""
    colored_logger.agent_title("PLAN EXECUTOR - INPUT", agent_name="PlanExecutor")
    plan = state.get("plan", {})

    # DEBUG: Log slots in state at Plan Executor input
    slots_in_state = state.get("slots", {})
    logger.info(f"🔍 DEBUG: Plan Executor node received state with slots: {slots_in_state}")

    colored_logger.agent_data({
        "num_steps": len(plan.get("steps", [])),
        "step_ids": [step["id"] for step in plan.get("steps", [])],
    }, label="Input")

    # Execute the plan
    results = await plan_executor_instance.execute(plan, state)

    # Extract results
    update = {
        "assistant_text": results.get("assistant_text", ""),
        "ui_blocks": results.get("ui_blocks", []),
        "citations": results.get("citations", []),
        "next_suggestions": results.get("next_suggestions", []),
        "tool_citations": results.get("tool_citations", []),  # Include tool citations
        "current_agent": "plan_executor",
        "status": "halted" if results.get("halt") else "completed",
        "next_agent": None,
    }

    # Handle halt state
    if results.get("halt"):
        update["halt"] = True
        update["followups"] = results.get("followups", [])
        update["followup_questions"] = results.get("questions", [])

    colored_logger.agent_title("PLAN EXECUTOR - OUTPUT", agent_name="PlanExecutor")
    colored_logger.agent_data({
        "assistant_text_length": len(update['assistant_text']),
        "num_citations": len(update['citations']),
        "num_ui_blocks": len(update['ui_blocks']),
        "halted": results.get("halt", False),
        "status": update['status']
    }, label="Output")

    return update


# Routing function
def route_next_agent(state: GraphState) -> str:
    """Determine next agent based on state"""
    status = state.get("status", "running")
    next_agent = state.get("next_agent")

    if status in ["error", "completed", "halted"]:
        return END

    # Route based on next_agent field
    if next_agent:
        return next_agent

    return END


# Build the graph
def build_workflow() -> StateGraph:
    """Build the LangGraph workflow with 5 agents plus tiered routing nodes"""
    logger.info("Building LangGraph workflow (5 agents + tiered routing)")

    workflow = StateGraph(GraphState)

    # Add the 5 main agent nodes
    workflow.add_node("agent_safety", safety_node)
    workflow.add_node("agent_intent", intent_node)
    workflow.add_node("agent_planner", planner_node)
    workflow.add_node("agent_clarifier", clarifier_node)
    workflow.add_node("agent_plan_executor", plan_executor_node)

    # Add tiered routing nodes
    workflow.add_node("routing_gate", routing_gate_node)
    workflow.add_node("tiered_executor", tiered_executor_node)

    # Set entry point
    workflow.set_entry_point("agent_safety")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent_safety",
        route_next_agent,
        {
            "intent": "agent_intent",
            "clarifier": "agent_clarifier",  # For resuming halt state
            "tiered_executor": "tiered_executor",  # For resuming from consent halt
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "agent_intent",
        route_next_agent,
        {
            "planner": "agent_planner",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "agent_planner",
        route_next_agent,
        {
            "clarifier": "agent_clarifier",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "agent_clarifier",
        route_next_agent,
        {
            "plan_executor": "agent_plan_executor",
            "routing_gate": "routing_gate",  # Route to hybrid routing gate
            END: END,
        }
    )

    # Routing gate decides between tiered executor and LLM planner
    workflow.add_conditional_edges(
        "routing_gate",
        route_next_agent,
        {
            "tiered_executor": "tiered_executor",
            "planner": "agent_planner",
            END: END,
        }
    )

    # Tiered executor routes to plan_executor (synthesizer) or halts
    workflow.add_conditional_edges(
        "tiered_executor",
        route_next_agent,
        {
            "synthesizer": "agent_plan_executor",  # synthesizer maps to plan_executor
            "plan_executor": "agent_plan_executor",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "agent_plan_executor",
        route_next_agent,
        {
            END: END,
        }
    )

    logger.info("✅ Workflow compiled: Safety → Intent → Planner → Clarifier → [RoutingGate → TieredExecutor] → Executor")
    return workflow.compile()


# Create global workflow instance
graph = build_workflow()
logger.info("LangGraph workflow compiled successfully")
