# Change log
All notable changes to this project will be documented in this file.

*NOTE:* Version 0.X.X might have breaking changes in bumps of the minor version number. This is because the project is still in early development and the API is not yet stable. It will still be marked clearly in the release notes.

## [0.3.0] - 09-09-2025
- Added toolit `create-vscode-tasks-json` CLI command to create the `.vscode/tasks.json` file from the command line.
- Improved error handling and user feedback when the `devtools` folder does not exist.

## [0.2.0] - 16-06-2025
- Fix problem with subdependencies not being installed
- Add support for python 3.9
- Make the use of MCP optional so you can use toolit without installing the `mcp` package, then it will still have the CLI and VS Code task generation features.
- Update documentation with examples and usage instructions
- Added continous integration with GitHub Actions to enforce code quality in the main branch

## [0.1.0] - 25-05-2025
- Added a script to create a `.vscode/tasks.json` file for use in Visual Studio Code
- Improved documentation with examples and usage instructions
- Added new decorators for groups of commands. Can run a group of tools in sequence or in parallel. (only supported for tasks.json creation, so far)

## [0.0.1] - 23-05-2025
- Initial release of toolit
- Basic functionality for creating tools that run for both MCP and typer cli