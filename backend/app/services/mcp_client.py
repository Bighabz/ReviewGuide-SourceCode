"""
MCP Client for FastAPI Backend

This client connects to the MCP server and provides a simple interface
for calling MCP tools from the backend.
"""

import asyncio
import json
from app.core.centralized_logger import get_logger
import subprocess
import sys
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core.colored_logging import get_colored_logger

logger = get_logger(__name__)
colored_logger = get_colored_logger(__name__)


class MCPClient:
    """
    MCP Client for connecting to ReviewGuide MCP server.

    This client manages the connection to the MCP server running as a subprocess
    and provides methods for discovering and calling tools.
    """

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.tools: Dict[str, Any] = {}
        self._client_context = None
        self._connected = False

    async def connect(self):
        """
        Connect to the MCP server via stdio.

        Starts the MCP server as a subprocess and establishes communication.
        """
        if self._connected:
            logger.info("MCP client already connected")
            return

        try:
            logger.info("Connecting to MCP server...")

            # Set up environment with proper PYTHONPATH (portable path)
            import os
            from pathlib import Path

            # Get the backend directory dynamically
            backend_dir = Path(__file__).parent.parent.parent.resolve()
            mcp_server_path = backend_dir / "mcp_server" / "main.py"

            env = os.environ.copy()
            env["PYTHONPATH"] = str(backend_dir)

            # Define server parameters
            server_params = StdioServerParameters(
                command=sys.executable,  # Use same Python interpreter
                args=[str(mcp_server_path)],
                env=env  # Use environment with PYTHONPATH
            )

            # Connect to server
            self._client_context = stdio_client(server_params)
            read_stream, write_stream = await self._client_context.__aenter__()

            # Initialize session
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()

            # Initialize the session
            await self.session.initialize()

            # Discover available tools
            await self._discover_tools()

            self._connected = True
            logger.info(f"✅ MCP client connected successfully with {len(self.tools)} tools")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}", exc_info=True)
            raise RuntimeError(f"MCP connection failed: {e}")

    async def _discover_tools(self):
        """
        Discover available tools from the MCP server.

        Queries the server for its tool list and stores them locally.
        """
        try:
            response = await self.session.list_tools()
            self.tools = {tool.name: tool for tool in response.tools}
            logger.info(f"Discovered {len(self.tools)} MCP tools:")
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}", exc_info=True)
            raise

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments as dict

        Returns:
            Tool result as dict

        Raises:
            ValueError: If tool not found or call fails
        """
        if not self._connected:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        if name not in self.tools:
            available = ", ".join(self.tools.keys())
            raise ValueError(f"Tool '{name}' not found. Available: {available}")

        try:
            # Log tool call (BLUE) - full input
            colored_logger.tool_call(name, arguments)

            # Call the tool
            result = await self.session.call_tool(name, arguments)

            # Extract text content from result
            if result.content and len(result.content) > 0:
                text_content = result.content[0].text

                # Log empty responses for debugging
                if not text_content or text_content.strip() == "":
                    print(f"Tool {name} returned empty string")
                    logger.error(f"Tool {name} returned empty string. Full result: {result}")
                    return {"error": "Tool returned empty response", "success": False}

                result_data = json.loads(text_content)

                # Log tool result (BLUE) - full output
                colored_logger.tool_result(name, result_data)

                return result_data
            else:
                raise ValueError(f"Tool {name} returned empty response")

        except json.JSONDecodeError as e:
            print(f"Tool {name} returned invalid JSON: {e}")
            logger.error(f"Tool {name} returned invalid JSON: {e}. Text was: {text_content if 'text_content' in locals() else 'NO CONTENT'}")
            return {"error": f"Invalid JSON response: {e}", "success": False}
        except Exception as e:
            logger.error(f"Tool {name} call failed: {e}", exc_info=True)
            return {"error": str(e), "success": False}

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools.

        Returns:
            List of tool definitions with name, description, and input schema
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in self.tools.values()
        ]

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool definition.

        Args:
            name: Tool name

        Returns:
            Tool definition or None if not found
        """
        tool = self.tools.get(name)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        return None

    async def disconnect(self):
        """
        Disconnect from the MCP server.

        Closes the session and cleans up resources.
        """
        if not self._connected:
            return

        try:
            if self.session:
                await self.session.__aexit__(None, None, None)

            if self._client_context:
                await self._client_context.__aexit__(None, None, None)

            self._connected = False
            self.session = None
            self.tools = {}

            logger.info("MCP client disconnected")

        except Exception as e:
            logger.error(f"Error disconnecting MCP client: {e}", exc_info=True)

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    """
    Get or create the global MCP client instance.

    Returns:
        Connected MCP client

    Raises:
        RuntimeError: If connection fails
    """
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.connect()

    elif not _mcp_client._connected:
        await _mcp_client.connect()

    return _mcp_client


async def disconnect_mcp_client():
    """
    Disconnect the global MCP client.

    Should be called on application shutdown.
    """
    global _mcp_client

    if _mcp_client:
        await _mcp_client.disconnect()
        _mcp_client = None
