import toolit.create_apps_and_register as create_apps_and_register
import toolit.__main__ as main_module
import toolit.cli as cli_module
import enum
import pytest
from typer.testing import CliRunner
from toolit import clitool


def test_cli_run_with_no_tools() -> None:
    # Get the commands from the typer cli app
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["--help"])
    assert result.exit_code == 0
    print(result.stdout)


def test_cli_loads_tools_and_plugins_without_plugins() -> None:
    from toolit.register_all_tool_and_plugins import register_all_tools_from_folder_and_plugin
    register_all_tools_from_folder_and_plugin()
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["--help"])
    assert result.exit_code == 0

def a_new_command_registered() -> None:
    """Test a new command is registered."""
    print("This is a new command registered.")


def test_cli_command_is_registered() -> None:
    # Get the commands from the typer cli app
    create_apps_and_register.register_command(a_new_command_registered, name="a-new-command-registered")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["--help"])
    assert result.exit_code == 0
    assert "a-new-command-registered" in result.stdout


def test_module_main_invokes_app(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {"value": False}

    def fake_main() -> None:
        called["value"] = True

    monkeypatch.setattr(main_module, "main", fake_main)
    main_module.main()
    assert called["value"]


def test_cli_list_str_input_is_converted_from_comma_separated_tokens() -> None:
    captured: dict[str, list[str]] = {}

    def list_str_tool(items: list[str]) -> None:
        captured["items"] = items

    create_apps_and_register.register_command(
        list_str_tool,
        name="dummycommand",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["dummycommand", "alpha", "beta", "gamma"],
    )

    assert result.exit_code == 0, f"CLI invocation failed with output: {result.output}, captured: {captured}"
    assert captured["items"] == ["alpha", "beta", "gamma"]


def test_cli_list_int_input_is_converted_from_comma_separated_tokens() -> None:
    captured: dict[str, list[int]] = {}

    def list_int_tool(numbers: list[int]) -> None:
        captured["numbers"] = numbers

    create_apps_and_register.register_command(
        list_int_tool,
        name="dummycommand",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["dummycommand", "1", "2", "3"],
    )

    assert result.exit_code == 0, f"CLI invocation failed with output: {result.output}, captured: {captured}"
    assert captured["numbers"] == [1, 2, 3]


def test_cli_list_enum_input_accepts_enum_names_and_values() -> None:
    captured: dict[str, list[object]] = {}

    class TestLevel(enum.Enum):
        LOW = "low"
        HIGH = "high"

    def list_enum_tool(levels: list[TestLevel]) -> None:
        captured["levels"] = levels

    create_apps_and_register.register_command(
        list_enum_tool,
        name="dummycommand",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["dummycommand", "low", "high"],
    )

    assert result.exit_code == 0, f"CLI invocation failed with output: {result.output}, captured: {captured}"
    assert captured["levels"] == [TestLevel.LOW, TestLevel.HIGH]


def test_cli_optional_list_omitted_preserves_none_default() -> None:
    captured: dict[str, list[str] | None] = {}

    def optional_list_tool(values: list[str] | None = None) -> None:
        captured["values"] = values

    create_apps_and_register.register_command(
        optional_list_tool,
        name="test-optional-list-omitted-preserves-none-default",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["test-optional-list-omitted-preserves-none-default"],
    )

    assert result.exit_code == 0, f"CLI invocation failed with output: {result.output}, captured: {captured}"
    assert captured["values"] is None


def test_clitool_runtime_executes_returned_shell_command(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    class DummyCompletedProcess:
        """Completed-process stand-in with return code for subprocess mocks."""

        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def fake_run(command: str, shell: bool, check: bool) -> DummyCompletedProcess:  # noqa: FBT001
        captured["command"] = command
        captured["shell"] = str(shell)
        captured["check"] = str(check)
        return DummyCompletedProcess(returncode=0)

    monkeypatch.setattr(create_apps_and_register.subprocess, "run", fake_run)

    @clitool
    def run_echo(target: str) -> str:
        return f"echo {target}"

    create_apps_and_register.register_command(run_echo, name="test-clitool-runtime-executes-returned-shell-command")
    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["test-clitool-runtime-executes-returned-shell-command", "hello"],
    )

    assert result.exit_code == 0, result.output
    assert captured["command"] == "echo hello"
    assert captured["shell"] == "True"
    assert captured["check"] == "False"


def test_clitool_runtime_requires_string_return_type() -> None:
    @clitool
    def returns_wrong_type() -> int:  # type: ignore[return-value]
        return 42

    create_apps_and_register.register_command(returns_wrong_type, name="test-clitool-runtime-requires-string-return-type")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-clitool-runtime-requires-string-return-type"])

    assert result.exit_code == 1
    assert "must return a string command" in result.output


def test_clitool_runtime_propagates_subprocess_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyCompletedProcess:
        """Completed-process stand-in with return code for subprocess mocks."""

        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def fake_run(command: str, shell: bool, check: bool) -> DummyCompletedProcess:  # noqa: ARG001, FBT001
        return DummyCompletedProcess(returncode=9)

    monkeypatch.setattr(create_apps_and_register.subprocess, "run", fake_run)

    @clitool
    def returns_failing_command() -> str:
        return "exit 9"

    create_apps_and_register.register_command(
        returns_failing_command,
        name="test-clitool-runtime-propagates-subprocess-exit-code",
    )
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-clitool-runtime-propagates-subprocess-exit-code"])

    assert result.exit_code == 9
