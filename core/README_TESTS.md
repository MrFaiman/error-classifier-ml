# Testing Guide

## Overview

Test suite using pytest for the error classification system.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_tfidf.py           # TF-IDF vectorizer tests
├── test_bm25.py            # BM25 ranking tests
├── test_similarity.py      # Similarity search tests
├── test_api_endpoints.py   # API endpoint tests
└── test_docs_security.py   # Security tests for docs API
```

## Running Tests

### Install pytest

```bash
pip install pytest pytest-cov
```

### Run all tests

```bash
cd core
pytest
```

### Run specific test file

```bash
pytest tests/test_tfidf.py
```

### Run specific test class

```bash
pytest tests/test_tfidf.py::TestTfidfVectorizer
```

### Run specific test

```bash
pytest tests/test_tfidf.py::TestTfidfVectorizer::test_fit_transform
```

### Run with coverage

```bash
pytest --cov=src --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run with markers

```bash
# Run only security tests
pytest -m security

# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## Test Categories

### Unit Tests

Test individual components in isolation:
- **test_tfidf.py**: TF-IDF vectorization, tokenization, IDF calculation
- **test_bm25.py**: BM25 scoring, parameter effects, query handling
- **test_similarity.py**: Cosine similarity, Euclidean distance, k-NN search

### Security Tests

Test security measures:
- **test_docs_security.py**: Path traversal prevention, file type restrictions, input validation

### Integration Tests

Test API endpoints and component interactions:
- **test_api_endpoints.py**: HTTP endpoints, request/response validation, error handling

## Test Fixtures

Located in `conftest.py`:

- **sample_documents**: Pre-defined document corpus for testing
- **sample_queries**: Common test queries
- **temp_docs_dir**: Temporary directory with sample markdown files

## Writing New Tests

### Test Structure

```python
class TestYourComponent:
    """Test your component"""
    
    def test_feature(self):
        """Test a specific feature"""
        # Arrange
        component = YourComponent()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixture(sample_documents):
    """Use a fixture"""
    vectorizer = TfidfVectorizer()
    vectorizer.fit_transform(sample_documents)
    assert len(vectorizer.vocabulary_) > 0
```

### Testing Exceptions

```python
def test_invalid_input():
    """Test exception handling"""
    with pytest.raises(ValueError):
        component.method_with_invalid_input()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_multiple_inputs(input, expected):
    assert process(input) == expected
```

## Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** that explain what is being tested
3. **Arrange-Act-Assert** pattern
4. **Use fixtures** for common setup
5. **Test edge cases** (empty input, None, extremes)
6. **Test error conditions** not just happy paths
7. **Keep tests isolated** - no dependencies between tests
8. **Mock external dependencies** (MongoDB, file system)

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd core
    pip install pytest pytest-cov
    pytest --cov=src --cov-report=xml
```

## Coverage Goals

- **Core algorithms**: >90% coverage
- **API controllers**: >80% coverage
- **Security functions**: 100% coverage

## Debugging Tests

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Run with pdb on failure
pytest --pdb

# Run last failed tests only
pytest --lf
```

## Performance Testing

For slow tests, mark them:

```python
@pytest.mark.slow
def test_slow_operation():
    # Long running test
    pass
```

Run fast tests only:
```bash
pytest -m "not slow"
```
