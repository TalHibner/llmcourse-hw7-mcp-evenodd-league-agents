# Contributing to MCP Even/Odd League

First off, thank you for considering contributing to the MCP Even/Odd League Multi-Agent System! It's people like you that make this project a great learning resource for the community.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing Requirements](#testing-requirements)
6. [Pull Request Process](#pull-request-process)
7. [Reporting Bugs](#reporting-bugs)
8. [Suggesting Enhancements](#suggesting-enhancements)
9. [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful of differing viewpoints and experiences, and accept constructive criticism gracefully.

### Our Standards

**Examples of behavior that contributes to a positive environment:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**

- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of async Python and FastAPI
- Familiarity with multi-agent systems (helpful but not required)

### Quick Contribution Workflow

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/llmcourse-hw7-mcp-evenodd-league-agents.git
cd llmcourse-hw7-mcp-evenodd-league-agents

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL-OWNER/llmcourse-hw7-mcp-evenodd-league-agents.git

# 4. Create a feature branch
git checkout -b feature/my-awesome-feature

# 5. Make your changes and commit
git add .
git commit -m "Add my awesome feature"

# 6. Push to your fork
git push origin feature/my-awesome-feature

# 7. Open a Pull Request on GitHub
```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

**Development dependencies include:**
- pytest (testing framework)
- pytest-asyncio (async test support)
- pytest-cov (coverage reporting)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)

### 3. Verify Installation

```bash
# Run tests to verify everything works
pytest

# Check code formatting
black --check .

# Run linter
flake8

# Run type checker
mypy SHARED/ agents/
```

### 4. Set Up Pre-commit Hooks (Optional but Recommended)

```bash
pip install pre-commit
pre-commit install
```

This will automatically run black, flake8, and mypy before each commit.

---

## Code Style Guidelines

We follow industry-standard Python conventions to maintain code quality and readability.

### General Principles

- **Readability counts**: Code is read more often than it's written
- **Explicit is better than implicit**: Clear naming and obvious logic
- **DRY (Don't Repeat Yourself)**: Extract common patterns into functions
- **Single Responsibility**: Each function/class should do one thing well
- **Type hints everywhere**: Use type annotations for all function signatures

### Python Style Guide

We use **PEP 8** with some modifications:

#### Formatting

```bash
# Run Black formatter on all files
black .

# Check formatting without making changes
black --check .
```

**Black configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]
```

#### Linting

```bash
# Run flake8 linter
flake8 SHARED/ agents/ tests/

# Ignore specific errors (configured in pyproject.toml)
```

**Key flake8 rules:**
- Maximum line length: 100 characters
- No wildcard imports (`from module import *`)
- No unused imports or variables
- Proper spacing around operators

#### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `player_id`, `match_result` |
| Functions | snake_case | `calculate_standings()`, `handle_request()` |
| Classes | PascalCase | `LeagueManager`, `JWTAuthenticator` |
| Constants | UPPER_SNAKE_CASE | `MAX_PLAYERS`, `DEFAULT_TIMEOUT` |
| Private methods | _leading_underscore | `_internal_helper()` |
| Modules | snake_case | `config_loader.py`, `mcp_client.py` |

### Type Hints

**Always use type hints** for function signatures:

```python
# Good ✅
def calculate_score(wins: int, draws: int, losses: int) -> int:
    """Calculate total points based on match results."""
    return (wins * 3) + (draws * 1) + (losses * 0)

# Bad ❌
def calculate_score(wins, draws, losses):
    return (wins * 3) + (draws * 1) + (losses * 0)
```

**Use Pydantic models for complex data:**

```python
from pydantic import BaseModel

class PlayerStats(BaseModel):
    player_id: str
    wins: int
    draws: int
    losses: int
    points: int
```

**Type checking:**

```bash
mypy SHARED/ agents/ --strict
```

### Docstrings

Use **Google-style docstrings** for all public functions and classes:

```python
def register_player(player_meta: PlayerMeta, league_id: str) -> LeagueRegisterResponse:
    """
    Register a new player in the league.

    Args:
        player_meta: Player metadata including display name and endpoint
        league_id: Unique identifier for the league

    Returns:
        Registration response with player_id and auth_token

    Raises:
        LeagueFullError: If maximum players limit is reached
        ValidationError: If player_meta is invalid

    Example:
        >>> meta = PlayerMeta(display_name="MyBot", contact_endpoint="http://localhost:8101/mcp")
        >>> response = register_player(meta, "TEST_LEAGUE")
        >>> print(response.player_id)
        'P01'
    """
    # Implementation...
```

**Minimum docstring requirements:**
- One-line summary (what the function does)
- Args section (if parameters exist)
- Returns section (if function returns a value)
- Raises section (if function can raise exceptions)

### Async/Await Guidelines

```python
# Use async def for I/O-bound operations
async def call_remote_api(endpoint: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint)
        return response.json()

# Use regular def for CPU-bound operations
def calculate_winner(choice_a: str, choice_b: str, drawn_number: int) -> str:
    is_even = (drawn_number % 2 == 0)
    # ... calculation logic
```

**Best practices:**
- Use `async with` for context managers
- Use `asyncio.gather()` for parallel operations
- Avoid blocking calls in async functions
- Use `asyncio.to_thread()` for CPU-bound work in async context

---

## Testing Requirements

We maintain **70%+ test coverage** for all code. Every pull request must include tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=SHARED --cov=agents --cov-report=term-missing

# Run specific test file
pytest tests/test_jwt_auth.py

# Run tests matching a pattern
pytest -k "test_player"

# Run with verbose output
pytest -v

# Run async tests
pytest tests/test_async_handlers.py
```

### Writing Tests

#### Unit Tests

```python
# tests/test_standings.py
import pytest
from agents.league_manager.standings import StandingsCalculator
from SHARED.league_sdk.models import StandingEntry

def test_standings_update_win():
    """Test standings update when player wins"""
    calculator = StandingsCalculator(win_points=3, draw_points=1, loss_points=0)

    standings = [
        StandingEntry(
            rank=1, player_id="P01", display_name="Player 1",
            played=0, wins=0, draws=0, losses=0, points=0
        )
    ]

    match_result = {
        "status": "WIN",
        "score": {"P01": 3, "P02": 0}
    }

    updated = calculator.update_standings(standings, match_result)

    assert updated[0].wins == 1
    assert updated[0].points == 3
    assert updated[0].played == 1
```

#### Async Tests

```python
# tests/test_async_handlers.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_handle_match_result():
    """Test async match result handling"""
    handler = ResultHandler(league_id="TEST", ...)

    # Mock async MCP client
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(return_value={"status": "ok"})

    with patch('agents.league_manager.handlers.MCPClient') as MockMCP:
        MockMCP.return_value.__aenter__.return_value = mock_mcp
        MockMCP.return_value.__aexit__.return_value = AsyncMock()

        await handler.handle_match_result(report, player_endpoints)

        # Verify MCP client was called
        mock_mcp.call_tool.assert_called()
```

#### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_match_flow():
    """Test complete match flow from invitation to result"""
    # Set up league manager, referee, and players
    # Execute full match
    # Verify results
    pass
```

### Test Coverage Requirements

- **Minimum 70%** overall coverage
- **90%+** for critical components (auth, game logic, standings)
- **100%** for new features

**Check coverage:**

```bash
pytest --cov=SHARED --cov=agents --cov-report=html
open htmlcov/index.html  # View detailed coverage report
```

### Testing Checklist

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Coverage is ≥70% (`pytest --cov`)
- [ ] New features have tests
- [ ] Edge cases are tested
- [ ] Async functions use `@pytest.mark.asyncio`
- [ ] Mocks are used for external dependencies
- [ ] Test names are descriptive (`test_what_when_expected`)

---

## Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout feature/my-feature
   git rebase main
   ```

2. **Run the full test suite:**
   ```bash
   pytest
   pytest --cov=SHARED --cov=agents
   black --check .
   flake8
   mypy SHARED/ agents/
   ```

3. **Update documentation:**
   - Update README.md if adding user-facing features
   - Update docs/API.md if changing APIs
   - Add docstrings to new functions/classes
   - Update CHANGELOG.md

### Pull Request Template

```markdown
## Description

Brief description of changes (1-2 paragraphs)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist

- [ ] My code follows the code style of this project
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have updated the documentation accordingly
- [ ] All new and existing tests passed
- [ ] I have updated CHANGELOG.md

## Screenshots (if applicable)

Add screenshots or examples of the change

## Related Issues

Fixes #(issue number)
```

### Review Process

1. **Automated checks** run on your PR (GitHub Actions)
   - All tests must pass
   - Coverage must meet requirements
   - Linting must pass

2. **Code review** by maintainers
   - At least one approval required
   - Address all feedback and requested changes

3. **Merge:**
   - Squash and merge (default)
   - Rebase and merge (for clean history)
   - Create a merge commit (for feature branches)

### After Merge

Your contribution will be included in the next release and credited in:
- CHANGELOG.md
- Contributors section (if applicable)
- Release notes

---

## Reporting Bugs

### Before Submitting a Bug Report

1. **Check existing issues:** Search GitHub issues to avoid duplicates
2. **Verify with latest version:** Ensure bug exists in latest code
3. **Isolate the problem:** Create a minimal reproduction case

### Bug Report Template

```markdown
## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Start league manager with '...'
2. Register player '....'
3. See error

## Expected Behavior

What you expected to happen

## Actual Behavior

What actually happened (include error messages, logs)

## Environment

- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 13]
- Python version: [e.g., 3.10.5]
- Project version/commit: [e.g., 1.0.0 or commit hash]

## Logs

```
Paste relevant log output here
```

## Additional Context

Add any other context about the problem here
```

---

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
## Feature Description

Clear and concise description of the proposed feature

## Motivation

Why is this feature needed? What problem does it solve?

## Proposed Solution

Detailed explanation of how the feature should work

## Alternatives Considered

What other approaches were considered and why were they rejected?

## Additional Context

- Mockups or diagrams (if applicable)
- Related issues or PRs
- Implementation complexity estimate
```

---

## Documentation

### Documentation Standards

All documentation should be:
- **Clear and concise**: Use simple language
- **Complete**: Include all necessary information
- **Accurate**: Keep docs up-to-date with code
- **Practical**: Include examples and use cases

### Types of Documentation

1. **Code Documentation**
   - Docstrings for all public APIs
   - Inline comments for complex logic
   - Type hints for all functions

2. **User Documentation**
   - README.md (getting started guide)
   - QUICKSTART.md (quick examples)
   - docs/API.md (complete API reference)

3. **Developer Documentation**
   - CONTRIBUTING.md (this file)
   - DESIGN.md (architecture decisions)
   - IMPLEMENTATION_SUMMARY.md (technical details)

4. **Examples and Tutorials**
   - docs/examples/ (code examples)
   - doc/message-examples/ (protocol examples)

### Updating Documentation

When making changes, update:
- [ ] Code docstrings
- [ ] README.md (if user-facing changes)
- [ ] docs/API.md (if API changes)
- [ ] CHANGELOG.md (for all changes)
- [ ] Migration guide (for breaking changes)

---

## Project Structure

Understanding the codebase structure:

```
├── SHARED/                    # Shared libraries (all agents)
│   ├── league_sdk/           # Core SDK
│   │   ├── models.py         # Pydantic models (16 message types)
│   │   ├── auth.py           # JWT authentication
│   │   ├── logger.py         # Structured logging
│   │   ├── mcp_client.py     # JSON-RPC client
│   │   └── repositories.py   # Data persistence
│   └── config/               # Configuration files
│
├── agents/                   # Agent implementations
│   ├── league_manager/       # Central orchestrator
│   ├── referee/              # Match execution
│   └── player/               # Player strategies
│
├── tests/                    # Test suite (227 tests, 71% coverage)
│   ├── test_sdk.py           # SDK unit tests
│   ├── test_jwt_auth.py      # Auth tests (26 tests)
│   └── test_integration.py   # Integration tests
│
└── docs/                     # Documentation
    ├── API.md                # API reference
    ├── BENCHMARKS.md         # Performance benchmarks
    └── examples/             # Code examples
```

---

## Common Development Tasks

### Adding a New Player Strategy

```python
# 1. Create strategy class in agents/player/strategy.py
class MyNewStrategy:
    def choose(self, opponent_id: str, match_history: List[dict]) -> ParityChoice:
        # Your logic here
        return ParityChoice.EVEN

# 2. Add tests in tests/test_player.py
def test_my_new_strategy():
    strategy = MyNewStrategy()
    choice = strategy.choose("P02", [])
    assert choice in [ParityChoice.EVEN, ParityChoice.ODD]

# 3. Update documentation in README.md
```

### Adding a New Message Type

```python
# 1. Define Pydantic model in SHARED/league_sdk/models.py
class MyNewMessage(BaseModel):
    sender: str
    timestamp: datetime
    # ... fields

# 2. Add to MessageType enum
class MessageType(str, Enum):
    MY_NEW_MESSAGE = "MY_NEW_MESSAGE"
    # ... existing types

# 3. Handle in appropriate agent (league_manager/referee/player main.py)
# 4. Add to docs/API.md
# 5. Create example in doc/message-examples/
# 6. Write tests
```

### Adding a New Configuration Option

```python
# 1. Add to .env.example
MY_NEW_CONFIG=default_value

# 2. Add to config models (if using config files)
# 3. Document in README.md Environment Variables table
# 4. Use in code via os.getenv("MY_NEW_CONFIG", "default")
```

---

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Security issues**: See SECURITY.md
- **Pull requests**: Follow the process above

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Educational License).

---

## Recognition

Contributors will be acknowledged in:
- CHANGELOG.md for each release
- GitHub contributors page
- Special mentions for significant contributions

Thank you for contributing to MCP Even/Odd League! 🎉

---

**Last Updated**: 2025-12-31
**Maintained By**: MCP Development Team
