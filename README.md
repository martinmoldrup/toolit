# Toolit
MCP Server and Typer CLI in one, provides an easy way to configure your own DevTools in a project.

## Installation
To get started with Toolit, install the package via pip:

```bash
pip install toolit
```

## Usage
Add a folder called `devtools` to your project root. Create python modules, you decide the name, in this folder. Add the tool decorator to functions you want to expose as commands.

```python
from toolit import tool
@tool
def my_command():
    """This is a command that can be run from the CLI."""
    print("Hello from my_command!")
```

Toolit will automatically discover these modules and make them available as commands.

## Contributing
We welcome contributions to ToolIt! If you have ideas for new features, improvements, or bug fixes, please open an issue or submit a pull request on our GitHub repository. We appreciate your feedback and support in making ToolIt even better for the community.
