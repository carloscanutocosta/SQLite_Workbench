# Contributing

Thank you for your interest in contributing to SQLite Workbench.

## Project Scope

SQLite Workbench is a lightweight desktop application for exploring and working with SQLite databases. Contributions should aim to keep the project practical, stable, and easy to use.

## Ways to Contribute

You can contribute by:

- reporting bugs
- suggesting improvements
- improving documentation
- submitting code changes
- testing on Windows, Linux, and macOS
- helping with packaging and release validation

## Before You Start

Please open an issue before starting major changes, especially for:

- UI redesigns
- architectural changes
- dependency changes
- packaging/distribution changes
- new large features

This helps keep the project aligned and avoids duplicate work.

## Development Principles

Contributions should follow these principles:

- keep the app lightweight
- prefer clarity over complexity
- preserve usability for non-expert users
- avoid unnecessary dependencies
- keep behavior predictable
- respect cross-platform compatibility where possible

## Setup

Install dependencies:

```bash
pip install customtkinter pygments
```

Run the app:

```bash
python app.py
```

## Coding Guidelines

Please try to:

- keep code readable and modular
- use clear names
- avoid large unrelated changes in a single pull request
- preserve existing functionality unless the change intentionally updates it
- test changes before submitting

## Pull Requests

When submitting a pull request:

- describe the change clearly
- explain the reason for the change
- include steps to test it
- keep the scope focused
- update documentation if needed

Small, focused pull requests are preferred.

## Issues

When reporting a bug, please include:

- operating system
- Python version
- steps to reproduce
- expected behavior
- actual behavior
- screenshots, if relevant

## Security

Please do not report security vulnerabilities through public issues.

See SECURITY.md for responsible disclosure guidance.

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that applies to the project.