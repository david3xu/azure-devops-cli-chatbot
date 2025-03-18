# Development Container Configuration

This directory contains the configuration for the Visual Studio Code Development Container (Dev Container) used for this project. Using this container provides a consistent development environment with all required dependencies pre-installed.

## Features

The development container includes:

- Python 3.8
- Azure CLI with Azure DevOps extension
- Azure Developer CLI (azd)
- JQ for JSON processing
- Bicep CLI for infrastructure as code
- Additional useful command line tools and utilities

## Prerequisites

To use this Dev Container, you need:

1. Visual Studio Code
2. Docker installed on your machine
3. "Remote - Containers" extension for VS Code

## Usage

When you open this project in VS Code with the Remote - Containers extension installed, you'll be prompted to "Reopen in Container". Click this prompt to build and start the container.

Alternatively, you can:

1. Press F1 to open the command palette
2. Type "Remote-Containers: Reopen in Container" and select it

## Container Configuration

- `devcontainer.json`: Defines the container configuration, VS Code settings, and extensions
- `Dockerfile`: Defines the container image and installed tools

## Installed VS Code Extensions

The container comes with several VS Code extensions pre-installed:

- Python extension for VS Code
- Pylance for Python IntelliSense
- Docker extension
- Azure CLI extension
- Azure Resource Manager Tools
- YAML support

## Port Forwarding

The container forwards port 8000 to your local machine, allowing you to access the FastAPI application running in the container.

## Post-Creation Commands

After the container is created, it automatically runs `pip install -r requirements.txt` to install project dependencies.

## Customization

If you need to customize the container further:

1. Modify the `Dockerfile` to install additional packages
2. Update `devcontainer.json` to change VS Code settings or add more extensions
3. Rebuild the container (F1 > "Remote-Containers: Rebuild Container") 