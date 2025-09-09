# Toolit
Model Context Protocol (MCP) Server, Typer CLI and Visual Studio Code tasks in one, provides an easy way to configure your own DevTools in a project.

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
# devtools/my_commands.py
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
toolit create-vscode-tasks-json
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

## Creating Plugins
Toolit supports a plugin system that allows you to create and share your own tools as separate packages. This makes it easy to reuse tools across different projects, without needing to copy and update tools across multiple codebases.

To create a plugin, follow these steps:
1. Create a new Python package for your plugin. You can use tools like `setuptools`, `poetry` or `uv` to set up your package structure.
2. In your package, create a module where you define your tools using the `@tool` decorator.
3. Make sure to include `toolit` as a dependency in your package's `setup.py` or `pyproject.toml`.
4. Register your plugin with Toolit by adding an entry point in your `setup.py` or `pyproject.toml`, so Toolit can discover your tools when the package is installed. The entry point is called `toolit_plugins`.
5. Publish your package to PyPI or install it from a git repository where you need it.

## Contributing
We welcome contributions to Toolit! If you have ideas for new features, improvements, or bug fixes, please open an issue or submit a pull request on our GitHub repository. We appreciate your feedback and support in making Toolit even better for the community.
