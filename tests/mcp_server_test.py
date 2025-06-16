"""Test for mcp server tool availability."""

import pytest
import importlib.util
import toolit.create_apps_and_register as create_apps_and_register

mcp_spec = importlib.util.find_spec("mcp")
mcp_installed: bool = mcp_spec is not None


@pytest.mark.skipif(not mcp_installed, reason="mcp package is not installed")
@pytest.mark.asyncio
async def test_mcp_server() -> None:
    """Test the mcp server tool is available."""
    assert create_apps_and_register.mcp is not None, (
        "This test should only run if mcp is installed. create_apps_and_register.mcp is None indicating it is not installed."
    )

    def some_tool() -> None:
        """Tool for testing purpose."""
        pass

    create_apps_and_register.register_command(some_tool, name="some_tool")
    tools = await create_apps_and_register.mcp.list_tools()
    tool_instance = next(tool for tool in tools if tool.name == "some_tool")
    assert bool(tool_instance) is not False
