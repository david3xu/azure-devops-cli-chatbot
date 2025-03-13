# Contributing to Azure DevOps CLI Chatbot

Thank you for your interest in contributing to the Azure DevOps CLI Learning Project with Python Chatbot! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Contribution Workflow](#contribution-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project follows an open and inclusive code of conduct. By participating, you are expected to:

- Be respectful and considerate of others
- Value different viewpoints and experiences
- Give and gracefully accept constructive feedback
- Focus on what is best for the community

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/azure-devops-cli-chatbot.git
   cd azure-devops-cli-chatbot
   ```
3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/david3xu/azure-devops-cli-chatbot.git
   ```
4. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

### Using Dev Container (Recommended)

The project includes a development container configuration for Visual Studio Code:

1. Install [Visual Studio Code](https://code.visualstudio.com/)
2. Install [Docker](https://www.docker.com/products/docker-desktop)
3. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
4. Open the project in VS Code and click "Reopen in Container" when prompted

### Manual Setup

If you prefer not to use the dev container:

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

## Contribution Workflow

1. **Sync with upstream** before starting work:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

4. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** to the main repository

## Pull Request Process

1. **Create a Pull Request** from your feature branch to the main repository's `main` branch
2. **Fill in the PR template** with details about your changes
3. **Address review comments** and update your PR as needed
4. **Wait for approval** from at least one maintainer before merging

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use descriptive variable names and function names
- Add docstrings to all functions and classes
- Keep functions focused on a single responsibility
- Use type hints where appropriate

## Testing Guidelines

- Add tests for all new functionality
- Ensure all tests pass before submitting a PR:
  ```bash
  python -m pytest
  ```
- Strive for high test coverage for critical components
- Include both unit tests and integration tests when appropriate

## Documentation

- Update README.md with any relevant changes
- Add docstrings to all public functions and classes
- Keep code comments clear and up to date
- Create or update documentation for new features

---

Thank you for contributing to the Azure DevOps CLI Learning Project with Python Chatbot! 