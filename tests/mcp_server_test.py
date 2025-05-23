import pytest
import toolit.create_apps_and_register as create_apps_and_register


@pytest.mark.asyncio
async def test_mcp_server() -> None:
    """Test the mcp server tool is available."""
    def some_tool() -> None:
        """Tool for testing purpose."""
        pass
    create_apps_and_register.register_command(some_tool, name="some_tool")
    tools = await create_apps_and_register.mcp.list_tools()
    tool_instance = [tool for tool in tools if tool.name == "some_tool"][0]
    assert bool(tool_instance) is not False
