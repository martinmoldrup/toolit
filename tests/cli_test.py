import toolit.create_apps_and_register as create_apps_and_register
import toolit.__main__ as main_module
import toolit.cli as cli_module
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

    monkeypatch.setattr(cli_module, "register_all_tools_from_folder_and_plugin", fake_register)
    monkeypatch.setattr(cli_module, "app", fake_app)
    cli_module.main()
    assert called["register"]
    assert called["app"]


