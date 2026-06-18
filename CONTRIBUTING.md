# Contributing to HR Assist Pro

Thank you for your interest in contributing to HR Assist Pro! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sayada-ume/RAG_SYSTEM.git
cd RAG_SYSTEM

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks (optional)
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow PEP 8 style guidelines
- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed

### 3. Code Quality Checks

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy . --ignore-missing-imports

# Security check with bandit
bandit -r .

# Run tests
pytest tests/ -v --cov
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: describe your changes clearly"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring
- `perf:` for performance improvements

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

## Pull Request Guidelines

- Provide a clear description of changes
- Reference related issues (#issue_number)
- Include screenshots for UI changes
- Ensure all tests pass
- Keep commits clean and organized

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Documentation

- Update README.md for major changes
- Add docstrings to new functions and classes
- Include usage examples
- Keep docs up-to-date

## Issues

- Before starting, check if an issue exists
- Provide detailed information about bugs
- Include steps to reproduce
- Suggest improvements with examples

## Project Structure

```
RAG_SYSTEM/
├── app.py                  # Main Streamlit application
├── config.py              # Configuration management
├── logging_config.py      # Logging setup
├── guardrails.py          # Security & validation
├── ingest.py              # PDF ingestion
├── llm.py                 # LLM integration
├── rag_pipeline.py        # RAG pipeline
├── reranker.py            # Reranking logic
├── utils.py               # Utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
└── chroma_db/             # Vector database
```

## Communication

- Use GitHub issues for bugs and features
- Discuss major changes before implementing
- Be patient and respectful

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to HR Assist Pro! 🚀
