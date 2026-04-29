import toolit.create_apps_and_register as create_apps_and_register
import toolit.__main__ as main_module
import toolit.cli as cli_module
import enum
import pytest
from typer.testing import CliRunner


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


def test_cli_main_registers_tools_and_runs_app(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {"register": False, "app": False}

    def fake_register() -> None:
        called["register"] = True

    def fake_app() -> None:
        called["app"] = True

    monkeypatch.setattr(cli_module, "_registration_done", False)
    monkeypatch.setattr(cli_module, "register_all_tools_from_folder_and_plugin", fake_register)
    monkeypatch.setattr(cli_module, "app", fake_app)
    cli_module.main()
    assert called["register"]
    assert called["app"]


def test_cli_list_str_input_is_converted_from_comma_separated_tokens() -> None:
    captured: dict[str, list[str]] = {}

    def list_str_tool(items: list[str]) -> None:
        captured["items"] = items

    create_apps_and_register.register_command(
        list_str_tool,
        name="test-list-str-input-is-converted-from-comma-separated-tokens",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["test-list-str-input-is-converted-from-comma-separated-tokens", "alpha, beta, gamma"],
    )

    assert result.exit_code == 0
    assert captured["items"] == ["alpha", "beta", "gamma"]


def test_cli_list_int_input_is_converted_from_comma_separated_tokens() -> None:
    captured: dict[str, list[int]] = {}

    def list_int_tool(numbers: list[int]) -> None:
        captured["numbers"] = numbers

    create_apps_and_register.register_command(
        list_int_tool,
        name="test-list-int-input-is-converted-from-comma-separated-tokens",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["test-list-int-input-is-converted-from-comma-separated-tokens", "1, 2, 3"],
    )

    assert result.exit_code == 0
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
        name="test-list-enum-input-accepts-enum-names-and-values",
    )

    runner = CliRunner()
    result = runner.invoke(
        create_apps_and_register.app,
        ["test-list-enum-input-accepts-enum-names-and-values", "LOW, high"],
    )

    assert result.exit_code == 0
    assert captured["levels"] == [TestLevel.LOW, TestLevel.HIGH]



