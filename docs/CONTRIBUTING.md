# Contributing to Password Manager

Thank you for considering contributing to the Password Manager project! We appreciate your time and effort. This guide will help you get started with contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [License](#license)

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code. Please report any unacceptable behavior to nsfr750@yandex.com.

## 🚀 Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
   ```bash
   git clone https://github.com/Nsfr750/pass_mgr.git
   cd pass_mgr
   ```
3. Set up the development environment (see below)
4. Create a new branch for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## ✏️ Making Changes

1. Make your changes following the code style guidelines
2. Write or update tests as needed
3. Run tests locally before committing
4. Commit your changes with a descriptive message:
   ```
   feat: add new feature
   fix: fix bug in authentication
   docs: update documentation
   style: format code
   refactor: improve code structure
   test: add test cases
   chore: update dependencies
   ```

## 🔄 Pull Request Process

1. Ensure your fork is up to date with the main branch
2. Rebase your feature branch on top of the main branch
3. Run all tests and ensure they pass
4. Submit a pull request with a clear description of your changes
5. Reference any related issues in your PR description
6. Wait for code review and address any feedback

## 🐛 Reporting Issues

When reporting issues, please include:

1. Description of the problem
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshots if applicable
6. System information (OS, Python version, etc.)

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists in the [ROADMAP.md](ROADMAP.md)
2. Describe the feature and why it would be valuable
3. Include any relevant use cases

## 🎨 Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all new code
- Keep functions small and focused
- Write docstrings for all public functions/classes
- Use meaningful variable and function names
- Keep lines under 88 characters (Black's default)

## 🧪 Testing

1. Write tests for new features and bug fixes
2. Run tests locally before pushing:
   ```bash
   pytest
   ```
3. Ensure test coverage remains high

## 📚 Documentation

- Update relevant documentation when adding new features
- Keep docstrings up to date
- Follow the existing documentation style

## 📄 License

By contributing, you agree that your contributions will be licensed under the [GPLv3 License](LICENSE).

## 🙏 Thank You!

Your contributions make this project better. Thank you for your time and effort!
