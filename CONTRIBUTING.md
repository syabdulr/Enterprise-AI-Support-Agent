# Contributing to Enterprise AI Support Agent

Thank you for your interest in contributing to the Enterprise AI Support Agent! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

This project is committed to providing a welcoming and inclusive environment. Please be respectful, constructive, and collaborative in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (optional)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/syabdulr/Enterprise-AI-Support-Agent.git
cd enterprise-ai-support-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 🔄 Development Workflow

### 1. Create a Branch

Create a new branch from `main` for your feature or bugfix:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

### 2. Make Changes

Make your changes following the [coding standards](#coding-standards).

### 3. Run Pre-commit Hooks

Pre-commit hooks will run automatically before each commit:

```bash
# Run manually if needed
pre-commit run --all-files
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/ -v -m unit
pytest tests/ -v -m integration
pytest tests/ -v -m smoke
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```
feat: Add new feature description

Detailed description of what was added and why.

Co-authored-by: Your Name <your.email@example.com>
```

Commit message format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Link to related issues
- Screenshots for UI changes
- Test results

## 📐 Coding Standards

### Python Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Code Formatting

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check formatting
black --check src/ tests/
isort --check-only src/ tests/
```

### Type Hints

Add type hints to all function signatures:

```python
from typing import List, Dict, Optional, Any

def process_incident(
    incident_id: str,
    description: str,
    severity: str = "medium"
) -> Dict[str, Any]:
    """
    Process an incident.
    
    Args:
        incident_id: Unique incident identifier
        description: Incident description
        severity: Incident severity level
        
    Returns:
        Dictionary containing processing results
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def analyze_incident(incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze incident data and return recommendations.
    
    Args:
        incident_data: Dictionary containing incident information
        
    Returns:
        Dictionary with analysis results and recommendations
        
    Raises:
        ValueError: If incident data is invalid
        
    Example:
        >>> analyze_incident({"description": "Database error"})
        {"severity": "high", "resolution": "..."}
    """
    pass
```

### Error Handling

Use custom exceptions from `src.utils.exceptions`:

```python
from src.utils.exceptions import (
    RAGException,
    LLMException,
    ErrorCode
)

def retrieve_documents(query: str) -> List[Dict]:
    """Retrieve documents from RAG system.
    
    Args:
        query: Search query
        
    Returns:
        List of retrieved documents
        
    Raises:
        RAGException: If retrieval fails
    """
    try:
        # retrieval logic
        pass
    except Exception as e:
        raise RAGException(
            message=f"Failed to retrieve documents: {str(e)}",
            error_code=ErrorCode.RETRIEVAL_ERROR,
            recoverable=True
        )
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_rag.py              # RAG module tests
├── test_llm.py              # LLM module tests
├── test_workflow.py         # Workflow tests
├── test_error_handling.py   # Error handling tests
├── test_api.py              # API tests
├── test_integration_rag.py  # RAG integration tests
└── test_smoke.py            # Smoke tests
```

### Writing Tests

Use pytest and follow these conventions:

```python
import pytest
from src.rag.retriever import RAGRetriever

@pytest.fixture
def retriever():
    """Create RAG retriever instance."""
    return RAGRetriever(
        collection_name="test_collection",
        persist_directory="data/test"
    )

@pytest.mark.unit
class TestRAGRetriever:
    """Tests for RAG retriever."""
    
    def test_retrieve_documents(retriever):
        """Test document retrieval."""
        results = retriever.retrieve("test query", n_results=5)
        assert isinstance(results, list)
        assert len(results) <= 5
    
    @pytest.mark.parametrize("query,expected_count", [
        ("database", 5),
        ("network", 3),
    ])
    def test_retrieve_with_different_queries(retriever, query, expected_count):
        """Test retrieval with different queries."""
        results = retriever.retrieve(query, n_results=10)
        assert len(results) == expected_count
```

### Test Categories

- **Unit Tests (`@pytest.mark.unit`)**: Test individual functions/classes
- **Integration Tests (`@pytest.mark.integration`)**: Test component interactions
- **E2E Tests (`@pytest.mark.e2e`)**: Test complete workflows
- **Smoke Tests (`@pytest.mark.smoke`)**: Critical functionality tests

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/ -v -m unit
pytest tests/ -v -m integration
pytest tests/ -v -m e2e
pytest tests/ -v -m smoke

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_rag.py -v

# Run specific test
pytest tests/test_rag.py::TestRAGRetriever::test_retrieve_documents -v
```

### Test Coverage

Maintain at least 80% code coverage. View coverage report:

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # Mac
# or
xdg-open htmlcov/index.html  # Linux
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style docstrings
- Include type hints
- Add usage examples in docstrings

### README.md

Update README.md for:
- New features
- API changes
- Configuration updates
- Installation changes

### API Documentation

Add/update API documentation in FastAPI endpoint docstrings:

```python
@app.post(
    "/incident",
    tags=["incidents"],
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def handle_incident(request: CreateIncidentRequest):
    """
    Submit an incident for processing by the AI agent system.
    
    The incident will be processed through the multi-agent workflow:
    1. Triage agent categorizes and prioritizes
    2. Diagnosis agent analyzes patterns
    3. Resolution agent generates procedures
    4. Escalation agent routes if needed
    
    - **triage**: Categorizes incidents by severity and type
    - **diagnosis**: Analyzes root causes using RAG
    - **resolution**: Recommends solutions and remediation steps
    - **escalation**: Routes to human operators
    """
    pass
```

## 🔀 Pull Request Process

### Before Submitting

1. ✅ Code follows [coding standards](#coding-standards)
2. ✅ All tests pass locally
3. ✅ Coverage maintained at 80%+
4. ✅ Documentation updated
5. ✅ Commit messages are clear
6. ✅ Branch is up-to-date with main

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Self-review completed

## Related Issues
Closes #123
```

### Review Process

1. Automated checks (CI/CD) must pass
2. Code review by maintainers
3. Approval required for merging
4. Squash and merge to main

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Screenshots/logs if applicable

### Feature Requests

Include:
- Clear description of the feature
- Use case or motivation
- Proposed implementation (if applicable)
- Potential alternatives considered

## 💬 Questions

For questions about the project:
- Check existing documentation
- Search existing issues
- Open a new issue with the "question" label

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Enterprise AI Support Agent! 🙌