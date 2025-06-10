import toolit.create_apps_and_register as create_apps_and_register
from typer.testing import CliRunner


def a_new_command_registered() -> None:
    """Test a new command is registered."""
    print("This is a new command registered.")


def test_cli_command_is_regitered() -> None:
    # Get the commands from the typer cli app
    create_apps_and_register.register_command(a_new_command_registered, name="a-new-command-registered")
    runner = CliRunner()
    result = runner.invoke(create_apps_and_register.app, ["--help"])
    assert result.exit_code == 0
    assert "a-new-command-registered" in result.stdout
