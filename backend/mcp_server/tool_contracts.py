"""
Tool Contract Loader

Dynamically loads tool contracts from all MCP tools.
"""

import importlib
import sys
from app.core.centralized_logger import get_logger
from pathlib import Path
from typing import Dict, List
from app.lib.toon_python import encode

logger = get_logger(__name__)


def load_all_tool_contracts() -> List[Dict]:
    """
    Load TOOL_CONTRACT from all tool modules.

    Returns:
        List of tool contracts with name, purpose, requires, produces
    """
    contracts = []
    tools_dir = Path(__file__).parent / "tools"

    # Get all Python files in tools directory
    tool_files = [
        f.stem for f in tools_dir.glob("*.py")
        if f.stem != "__init__" and f.stem != "base_tool" and not f.stem.startswith("_")
    ]

    for tool_name in sorted(tool_files):
        try:
            # Import the tool module (reload to get fresh data)
            module_name = f"tools.{tool_name}"
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # Check if it has TOOL_CONTRACT
            if hasattr(module, "TOOL_CONTRACT"):
                contract = module.TOOL_CONTRACT
                contracts.append(contract)
            else:
                logger.warning(f"Tool {tool_name} missing TOOL_CONTRACT")

        except Exception as e:
            logger.error(f"Failed to load contract from {tool_name}: {e}")

    return contracts


def format_contracts_for_prompt(contracts: List[Dict]) -> str:
    """
    Format tool contracts into TOON format for LLM prompt.
    Uses TOON to reduce token consumption by ~40%.

    Returns:
        TOON formatted string describing all tools
    """
    # Group by category
    product_tools = []
    travel_tools = []
    meta_tools = []

    for contract in contracts:
        name = contract["name"]
        # Flatten for TOON tabular format
        flat_contract = {
            "name": name,
            "purpose": contract["purpose"],
            "requires": "+".join(contract.get("requires", [])) or "None",
            "produces": "+".join(contract.get("produces", []))
        }

        if name.startswith("product_"):
            product_tools.append(flat_contract)
        elif name.startswith("travel_"):
            travel_tools.append(flat_contract)
        else:
            meta_tools.append(flat_contract)

    lines = ["AVAILABLE TOOLS:\n"]

    # Product tools in TOON format
    if product_tools:
        lines.append("PRODUCT TOOLS:")
        product_toon = encode({"tools": product_tools})
        lines.append(product_toon)
        lines.append("")

    # Travel tools in TOON format
    if travel_tools:
        lines.append("TRAVEL TOOLS:")
        travel_toon = encode({"tools": travel_tools})
        lines.append(travel_toon)
        lines.append("")

    # Meta tools in TOON format
    if meta_tools:
        lines.append("META TOOLS:")
        meta_toon = encode({"tools": meta_tools})
        lines.append(meta_toon)
        lines.append("")

    # Add ordering rules
    lines.append("RULES:")
    lines.append("- Tools can only run if ALL 'requires' fields exist in state")
    lines.append("- Tools write to their 'produces' fields in state")
    lines.append("- Multiple tools can run in parallel if their 'requires' are satisfied")
    lines.append("- Always end with a compose tool to generate user response")

    return "\n".join(lines)


# Cache contracts on module load - use functools.lru_cache for thread-safe caching
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_contracts_cached():
    """Load and cache tool contracts (cached permanently)."""
    return load_all_tool_contracts()


@lru_cache(maxsize=1)
def get_tool_catalog() -> str:
    """
    Get formatted tool catalog (cached).

    Returns:
        Formatted tool catalog string for LLM prompt
    """
    contracts = _get_contracts_cached()
    return format_contracts_for_prompt(contracts)


@lru_cache(maxsize=1)
def get_tool_contracts_dict() -> Dict[str, Dict]:
    """
    Get tool contracts as a dictionary keyed by tool name (cached).

    Returns:
        Dict mapping tool_name -> contract
    """
    contracts = _get_contracts_cached()
    # Convert list to dict - note: can't cache dict directly as it's mutable
    return {c["name"]: c for c in contracts}


def get_default_tools_for_intent(intent: str) -> List[Dict]:
    """
    Get default tools for a specific intent.

    Returns tools that have is_default=True and match the intent.
    Note: The planner no longer auto-adds these to plans - it uses
    get_required_tools_from_dependencies() instead. This function
    is kept for other use cases that need to know default tools.

    Args:
        intent: The user intent (product, travel, general, etc.)

    Returns:
        List of default tool contracts for the intent
    """
    contracts = _get_contracts_cached()
    default_tools = []

    for contract in contracts:
        tool_intent = contract.get("intent", "")
        is_default = contract.get("is_default", False)

        # Include if: is_default AND (matches intent OR is "all" intent)
        if is_default and (tool_intent == intent or tool_intent == "all"):
            default_tools.append(contract)

    return default_tools


def get_required_tools_from_dependencies(selected_tools: List[str], intent: str) -> List[str]:
    """
    Expand selected tools by:
    1. Following their post dependencies recursively
    2. Adding required default tools (is_default=True AND is_required=True)
    3. Adding optional default tools (is_default=True, is_required=False) whose pre deps are satisfied

    Args:
        selected_tools: List of tool names selected by LLM
        intent: The user intent (to filter tools)

    Returns:
        List of all tool names (selected + post deps + default tools)
    """
    contracts = _get_contracts_cached()

    # Build lookup dict - filter by intent
    tool_lookup = {}
    required_default_tools = []  # is_default=True AND is_required=True
    optional_default_tools = []  # is_default=True AND is_required=False

    for c in contracts:
        tool_intent = c.get("intent", "")
        if tool_intent == intent or tool_intent == "all":
            tool_lookup[c["name"]] = c

            # Collect default tools for this intent
            if c.get("is_default"):
                if c.get("is_required"):
                    required_default_tools.append(c["name"])
                else:
                    optional_default_tools.append(c["name"])

    # Start with selected tools
    all_tools = set(selected_tools)
    to_process = list(selected_tools)

    # Follow both pre and post dependencies recursively
    while to_process:
        current = to_process.pop(0)
        contract = tool_lookup.get(current)
        if not contract:
            continue

        tools_field = contract.get("tools", {})

        # Add pre dependencies (tools that must run before current)
        pre_tools = tools_field.get("pre", [])
        for pre_tool in pre_tools:
            if pre_tool not in all_tools and pre_tool in tool_lookup:
                all_tools.add(pre_tool)
                to_process.append(pre_tool)

        # Add post dependencies (tools that must run after current)
        post_tools = tools_field.get("post", [])
        for post_tool in post_tools:
            if post_tool not in all_tools and post_tool in tool_lookup:
                all_tools.add(post_tool)
                to_process.append(post_tool)

    # Add required default tools (always add, regardless of pre deps)
    for required_tool in required_default_tools:
        if required_tool not in all_tools:
            all_tools.add(required_tool)

    # Add optional default tools whose pre dependencies are satisfied
    changed = True
    while changed:
        changed = False
        for optional_tool in optional_default_tools:
            if optional_tool in all_tools:
                continue

            contract = tool_lookup.get(optional_tool)
            if not contract:
                continue

            tools_field = contract.get("tools", {})
            pre_deps = tools_field.get("pre", [])

            # Empty pre = NOT auto-added (must be selected by LLM or in post deps)
            # Non-empty pre = add only if ALL pre deps are satisfied
            if pre_deps and all(dep in all_tools for dep in pre_deps):
                all_tools.add(optional_tool)
                changed = True

    return list(all_tools)


def get_selectable_tools_for_intent(intent: str) -> List[Dict]:
    """
    Get tools that LLM can select for a specific intent.

    Returns tools that are NOT default (is_default=False or not set).
    Default tools are auto-added and should not be shown to LLM.

    Args:
        intent: The user intent (product, travel, general, etc.)

    Returns:
        List of selectable tool contracts (non-default tools)
    """
    contracts = _get_contracts_cached()
    selectable_tools = []

    for contract in contracts:
        tool_name = contract.get("name", "unknown")
        tool_intent = contract.get("intent", "")
        is_default = contract.get("is_default", False)

        # Only include tools that match the intent
        if tool_intent != intent and tool_intent != "all":
            continue

        # Skip default tools - they are auto-added, not selected by LLM
        if is_default:
            logger.debug(f"[get_selectable_tools] Skipping default tool: {tool_name}")
            continue

        logger.info(f"[get_selectable_tools] Including non-default tool: {tool_name} (is_default={is_default})")
        selectable_tools.append(contract)

    logger.info(f"[get_selectable_tools] For intent={intent}, selectable tools: {[t['name'] for t in selectable_tools]}")
    return selectable_tools


def get_non_default_tools_for_intent(intent: str) -> List[Dict]:
    """
    DEPRECATED: Use get_selectable_tools_for_intent() instead.
    Kept for backward compatibility.
    """
    return get_selectable_tools_for_intent(intent)


def format_non_default_contracts_for_prompt(intent: str) -> str:
    """
    Format selectable (entry-point) tool contracts for LLM prompt.
    Downstream tools are auto-added based on dependencies.

    Args:
        intent: The user intent

    Returns:
        TOON formatted string describing selectable tools
    """
    contracts = get_selectable_tools_for_intent(intent)

    if not contracts:
        return "No entry-point tools available for this intent."

    lines = ["ENTRY-POINT TOOLS (select which to use):\n"]

    flat_contracts = []
    for contract in contracts:
        flat_contract = {
            "name": contract["name"],
            "purpose": contract["purpose"],
            "produces": "+".join(contract.get("produces", []))
        }

        # Include not_for field if present
        not_for = contract.get("not_for")
        if not_for:
            # not_for can be list or already joined string
            if isinstance(not_for, list):
                flat_contract["not_for"] = ", ".join(not_for)
            else:
                flat_contract["not_for"] = not_for

        flat_contracts.append(flat_contract)

    toon_output = encode({"tools": flat_contracts})
    lines.append(toon_output)

    lines.append("\nRULES:")
    lines.append("- Select entry-point tools based on what user is asking for")
    lines.append("- Read each tool's 'purpose' field to understand what it DOES")
    lines.append("- Read each tool's 'not_for' field (if present) to understand what it should NOT be used for")
    lines.append("- 'not_for' lists purposes handled by other specialized tools - do NOT select a tool if the user's request matches its 'not_for' field")
    lines.append("- Prefer specialized tools over general/fallback tools when applicable")
    lines.append("- Downstream tools (normalize, affiliate, compose) are auto-added via dependencies")
    lines.append("- You must select at least one tool")

    return "\n".join(lines)
