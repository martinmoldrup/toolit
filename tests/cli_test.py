import toolit.create_apps_and_register as create_apps_and_register
from typer.testing import CliRunner


def test_cli_run_with_no_tools() -> None:
    # Get the commands from the typer cli app
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["--help"])
    assert result.exit_code == 0
    print(result.stdout)


def test_cli_loads_tools_and_plugins_without_plugins() -> None:
    from toolit.cli import initialize_cli
    initialize_cli()
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


