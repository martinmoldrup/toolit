# Toolit
MCP Server and Typer CLI in one, provides an easy way to configure your own DevTools in a project.

## Installation
To get started with Toolit, install the package via pip:

```bash
pip install toolit
```

If you want mcp server support, you can install the optional dependency:

```bash
pip install toolit[mcp]
```
Note: MCP support is not available on python 3.9, since it is not supported by the `mcp` package.

## Usage
Add a folder called `devtools` to your project root. Create python modules, you decide the name, in this folder. Add the tool decorator to functions you want to expose as commands.

```python
from toolit import tool
@tool
def my_command(to_print: str = "Hello, World!") -> None:
    """This is a command that can be run from the CLI."""
    print(to_print)
```

Toolit will automatically discover these modules and make them available as commands.

Now you can run your command from the command line:

```bash
toolit --help  # To see available commands
toolit my-command --to_print "Hello, Toolit!"  # To run your command
```

## Create the VS code tasks.json file
You can automatically create a `tasks.json` file for Visual Studio Code to run your ToolIt commands directly from the editor. This is useful for integrating your development tools into your workflow.

To create the `.vscode/tasks.json` file, run the following command in your terminal:
```bash
python -m toolit.create_tasks_json
```
NOTE: THIS WILL OVERWRITE YOUR EXISTING `.vscode/tasks.json` FILE IF IT EXISTS!

## Chaining Commands
You can chain multiple using the `@sequential_group_of_tools` and `@parallel_group_of_tools` decorators to create more complex workflows. Functions decorated with these decorators should always return a list of callable functions.

```python
from toolit import tool, sequential_group_of_tools, parallel_group_of_tools
from typing import Callable

@tool
def first_command() -> None:
    print("First command executed.")

@tool
def second_command() -> None:
    print("Second command executed.")

@sequential_group_of_tools
def my_sequential_commands() -> list[Callable]:
    return [first_command, second_command]

@parallel_group_of_tools
def my_parallel_commands() -> list[Callable]:
    return [first_command, second_command]
```

This will create a group of commands in the `tasks.json` file that can be executed sequentially or in parallel.

## Contributing
We welcome contributions to Toolit! If you have ideas for new features, improvements, or bug fixes, please open an issue or submit a pull request on our GitHub repository. We appreciate your feedback and support in making Toolit even better for the community.
