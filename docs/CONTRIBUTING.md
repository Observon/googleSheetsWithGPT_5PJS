# Contributing Guide

Thank you for your interest in contributing! This project welcomes all contributions.

## Getting Started

### 1. Fork & Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/googleSheetsWithGPT_5PJS.git
cd googleSheetsWithGPT_5PJS

# Add upstream remote
git remote add upstream https://github.com/yourusername/googleSheetsWithGPT_5PJS.git
```

### 2. Setup Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate       # macOS/Linux

# Install dev dependencies
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout -b feature/your-feature upstream/main

# Or for bug fixes
git checkout -b bugfix/issue-description upstream/main
```

---

## Code Guidelines

### Style & Format

We use:
- **Black** for code formatting
- **Ruff** for linting
- **Type hints** for all functions

```bash
# Format code
black src tests

# Lint
ruff check src tests --fix

# Check both
black src tests && ruff check src tests
```

### Type Hints

All functions should have return type hints:

```python
# ✅ Good
def analyze_spreadsheet(
    self, 
    file_id: str, 
    file_name: str, 
    prompt: str
) -> Analysis:
    """Process a spreadsheet."""
    ...

# ❌ Bad
def analyze_spreadsheet(self, file_id, file_name, prompt):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def analyze_data(df: pd.DataFrame, threshold: float = 0.5) -> str:
    """
    Analyze data and return insights.
    
    Args:
        df: Input DataFrame to analyze
        threshold: Minimum value threshold (default: 0.5)
    
    Returns:
        Analysis result string
    
    Raises:
        ValidationError: If DataFrame is empty
    """
    if df.empty:
        raise ValidationError("DataFrame is empty")
    ...
```

### Error Handling

Use custom exceptions from `src/domain/exceptions.py`:

```python
# ✅ Good
from src.domain.exceptions import GoogleDriveError

try:
    self.service.files().get(...).execute()
except Exception as e:
    raise GoogleDriveError(f"Failed to get file: {e}")

# ❌ Bad
except Exception as e:
    raise Exception(str(e))
```

### Logging

Use the logger:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation started")
logger.warning("Deprecated usage")
logger.error("Operation failed", exc_info=True)
```

---

## Testing

### Writing Tests

Add tests in `tests/unit/` or `tests/integration/`:

```python
import pytest
from unittest.mock import MagicMock

def test_analyzer_caches_results(mock_cache, sample_dataframe):
    """Test that analyzer stores results in cache."""
    # Arrange
    analyzer = AnalyzerService(cache_adapter=mock_cache)
    
    # Act
    result = analyzer.analyze_spreadsheet(
        "sheet-1", "Test", "prompt"
    )
    
    # Assert
    mock_cache.set.assert_called_once()
    assert result.id is not None
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific file
pytest tests/unit/test_analyzer.py -v

# With markers
pytest tests/ -m unit
```

### Coverage Target

- **Minimum:** 50%
- **Target:** 60-70%
- Focus on: **services** (logic) > **domain** (models) > CLI/adapters

---

## Commit Guidelines

### Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code reorganization
- `test`: Adding/updating tests
- `docs`: Documentation
- `chore`: Dependencies, config
- `perf`: Performance improvements

### Examples

```
feat(analyzer): add caching for GPT calls

Implement file-based cache to reduce duplicate API calls.
Cache is keyed by hash(spreadsheet_id + prompt).

Closes #42
```

```
fix(export): handle special characters in filenames

Previously, special characters like "/" caused export failures.
Now filenames are properly sanitized.
```

### Tips

- Write present tense ("add" not "added")
- Be concise but descriptive
- Reference related issues
- One commit per feature when possible

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**
   ```bash
   pytest tests/ -v
   ```

3. **Format & lint**
   ```bash
   black src tests && ruff check src tests
   ```

4. **Test locally**
   ```bash
   python gdrive_gpt_app.py  # Try the CLI
   uvicorn src.api.main:app  # Try the API
   ```

### PR Template

```markdown
## Description
Brief summary of changes

## Related Issues
Closes #123

## Type of Change
- [x] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed my code
- [ ] Added docstrings
- [ ] Tests pass locally
```

### Review Process

- At least 1 approval required
- All CI checks must pass
- No merge conflicts
- Recently rebased on upstream/main

---

## Documentation

### README Changes

Update [README.md](../README.md) if your change:
- Affects installation
- Adds/removes features
- Changes default behavior

### New Features

Document in:
1. Docstrings (code-level)
2. [ARCHITECTURE.md](ARCHITECTURE.md) (design)
3. [API.md](API.md) (if applicable)
4. [README.md](../README.md) (user-facing)

---

## Architecture Decisions

Before major changes, discuss in an Issue:

1. Create issue with `[RFC]` prefix
2. Include:
   - Problem statement
   - Proposed solution
   - Alternatives considered
   - Impact analysis

### Major Feature Checklist

- [ ] Domain models defined (in `src/domain/`)
- [ ] Adapters for external dependencies
- [ ] Service layer for business logic
- [ ] Exception handling with custom errors
- [ ] Unit tests with mocks
- [ ] Integration tests (if needed)
- [ ] CLI or API integration
- [ ] Documentation
- [ ] Examples or demo code

---

## Project Structure

```
src/
├── domain/       # Add models in models.py, exceptions in exceptions.py
├── adapters/     # Add new external integrations here
├── services/     # Add business logic services here
├── cli/          # Add CLI commands here
└── api/          # Add API endpoints in routes/

tests/
├── unit/         # Unit tests (mocked)
└── integration/  # End-to-end tests

docs/             # Add documentation here
```

---

## Performance Considerations

### Before Implementation

Consider:
- Database queries (add indexes if needed)
- API calls (use cache)
- Memory usage (large DataFrames)
- Network requests (batch them)

### Profiling

```python
import cProfile

profiler = cProfile.Profile()
profiler.enable()

# ... your code ...

profiler.disable()
profiler.print_stats(sort='cumtime')
```

---

## Dependencies

### Adding New Packages

1. **Update** `requirements.txt` AND `pyproject.toml`
2. **Test** the change works locally
3. **Document** why it's needed
4. **Check** for security vulnerabilities
5. **Prefer** minimal, well-maintained packages

### Examples

- ✅ Use: `pydantic` (validation), `fastapi` (web)
- ❌ Avoid: Dead projects, large dependencies, security issues

---

## Release Process

Maintainers will:
1. Update version in `pyproject.toml`
2. Update [CHANGELOG.md](../CHANGELOG.md) (if exists)
3. Create GitHub Release
4. Tag commit: `v1.0.0`

---

## Code Review Checklist

Reviewers will check:

- [ ] Code follows style guidelines
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] No unnecessary dependencies
- [ ] Error handling is proper
- [ ] Logging is adequate
- [ ] Performance is acceptable
- [ ] Security concerns addressed

---

## Questions?

- 📖 Read [ARCHITECTURE.md](ARCHITECTURE.md)
- 🔍 Search [GitHub Issues](https://github.com/yourusername/googleSheetsWithGPT_5PJS/issues)
- 💬 Create a [GitHub Discussion](https://github.com/yourusername/googleSheetsWithGPT_5PJS/discussions)

---

## Code of Conduct

- Be respectful and inclusive
- No harassment or discrimination
- Constructive criticism only
- Assume good intentions

---

**Thank you for contributing!** 🙏

---

**Last Updated:** March 2026
