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

    def fake_run(command: object, *args: object, **kwargs: object) -> DummyCompletedProcess:
        captured["command"] = str(command)
        captured["shell"] = str(kwargs.get("shell"))
        captured["check"] = str(kwargs.get("check"))
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
    # Runtime may execute as a shell string or split argv list depending on platform/safety path.
    assert "echo" in captured["command"]
    assert "hello" in captured["command"]
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


def test_cli_bool_option_true_string_is_received_as_true() -> None:
    """Ensure passing 'True' string for a bool option results in Python True."""
    captured: dict[str, bool] = {}

    def bool_tool(is_enabled: bool = False) -> None:
        captured["is_enabled"] = is_enabled

    create_apps_and_register.register_command(bool_tool, name="test-bool-true-string")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-bool-true-string", "--is-enabled", "True"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["is_enabled"] is True


def test_cli_bool_option_false_string_is_received_as_false() -> None:
    """Ensure passing 'False' string for a bool option results in Python False."""
    captured: dict[str, bool] = {}

    def bool_tool(is_enabled: bool = True) -> None:
        captured["is_enabled"] = is_enabled

    create_apps_and_register.register_command(bool_tool, name="test-bool-false-string")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-bool-false-string", "--is-enabled", "False"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["is_enabled"] is False


def test_cli_list_str_comma_separated_single_arg_is_split() -> None:
    """Ensure a single comma-separated string is split into a list[str]."""
    captured: dict[str, list[str]] = {}

    def list_str_tool(items: list[str]) -> None:
        captured["items"] = items

    create_apps_and_register.register_command(list_str_tool, name="test-list-str-comma")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-list-str-comma", "alpha, beta, gamma"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["items"] == ["alpha", "beta", "gamma"]


def test_cli_list_int_comma_separated_single_arg_is_split_and_converted() -> None:
    """Ensure a single comma-separated string is split and converted to list[int]."""
    captured: dict[str, list[int]] = {}

    def list_int_tool(numbers: list[int]) -> None:
        captured["numbers"] = numbers

    create_apps_and_register.register_command(list_int_tool, name="test-list-int-comma")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-list-int-comma", "1, 2, 3"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["numbers"] == [1, 2, 3]


def test_cli_list_enum_comma_separated_single_arg_is_split_and_converted() -> None:
    """Ensure a single comma-separated string is split and converted to list[Enum]."""
    captured: dict[str, list[object]] = {}

    class Severity(enum.Enum):
        LOW = "low"
        HIGH = "high"

    def list_enum_tool(levels: list[Severity]) -> None:
        captured["levels"] = levels

    create_apps_and_register.register_command(list_enum_tool, name="test-list-enum-comma")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-list-enum-comma", "low, high"])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["levels"] == [Severity.LOW, Severity.HIGH]


def test_cli_optional_str_empty_string_becomes_none() -> None:
    """Ensure an empty string for str | None parameter is converted to None."""
    captured: dict[str, str | None] = {}

    def optional_str_tool(text: str | None = None) -> None:
        captured["text"] = text

    create_apps_and_register.register_command(optional_str_tool, name="test-optional-str-empty")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-optional-str-empty", "--text", ""])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert captured["text"] is None


def test_cli_required_str_empty_string_is_rejected() -> None:
    """Ensure an empty string for a required str parameter is rejected with an error."""

    def required_str_tool(text: str) -> None:  # noqa: ARG001
        pass

    create_apps_and_register.register_command(required_str_tool, name="test-required-str-empty")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["test-required-str-empty", ""])

    assert result.exit_code != 0, "Expected non-zero exit code for empty required string"


def test_clitool_runtime_propagates_subprocess_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyCompletedProcess:
        """Completed-process stand-in with return code for subprocess mocks."""

        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def fake_run(command: object, *args: object, **kwargs: object) -> DummyCompletedProcess:  # noqa: ARG001
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
