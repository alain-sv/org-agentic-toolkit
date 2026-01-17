# Testing Skills

## Testing Principles

### Test Pyramid
- **Unit Tests** (70%): Fast, isolated, test individual functions/classes
- **Integration Tests** (20%): Test component interactions
- **E2E Tests** (10%): Test complete user workflows

### Test Quality
- Tests should be **fast**, **independent**, **repeatable**, **self-validating**, and **timely**
- Follow **AAA pattern**: Arrange, Act, Assert
- One assertion per test (when possible)
- Test behavior, not implementation

## Unit Testing

### Python (pytest)
```python
# test_example.py
import pytest
from mymodule import calculate_total

def test_calculate_total_with_valid_input():
    # Arrange
    items = [10, 20, 30]
    
    # Act
    result = calculate_total(items)
    
    # Assert
    assert result == 60

def test_calculate_total_with_empty_list():
    assert calculate_total([]) == 0

def test_calculate_total_raises_on_invalid_input():
    with pytest.raises(ValueError):
        calculate_total(None)
```

### JavaScript (Jest)
```javascript
// example.test.js
import { calculateTotal } from './utils';

describe('calculateTotal', () => {
  test('returns sum of valid numbers', () => {
    // Arrange
    const items = [10, 20, 30];
    
    // Act
    const result = calculateTotal(items);
    
    // Assert
    expect(result).toBe(60);
  });

  test('returns 0 for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  test('throws on invalid input', () => {
    expect(() => calculateTotal(null)).toThrow();
  });
});
```

## Integration Testing

### API Testing
- Test endpoints with real database (test DB)
- Test authentication and authorization
- Test error handling and edge cases
- Use test fixtures for consistent data

### Database Testing
- Use transactions that rollback after tests
- Seed test data before each test
- Clean up test data after tests
- Test migrations up and down

## Test Coverage

### Coverage Goals
- Minimum 80% code coverage
- 100% coverage for critical paths (auth, payments, etc.)
- Focus on coverage quality, not just percentage

### Coverage Tools
- Python: `pytest-cov`
- JavaScript: `jest --coverage`
- Go: `go test -cover`

## Test Data Management

### Fixtures
- Use factories for creating test objects
- Keep fixtures minimal and focused
- Reuse fixtures across tests
- Use realistic but anonymized data

### Mocks and Stubs
- Mock external services (APIs, databases)
- Mock time-dependent functions
- Use dependency injection for testability
- Prefer mocks over real external services

## Test Organization

### File Structure
```
tests/
├── unit/
│   ├── test_models.py
│   └── test_utils.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
└── e2e/
    └── test_user_flows.py
```

### Naming Conventions
- Test files: `test_*.py` or `*.test.js`
- Test functions: `test_*` or `describe/it` blocks
- Descriptive names: `test_user_login_with_valid_credentials`

## Common Testing Patterns

### Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ([1, 2, 3], 6),
    ([], 0),
    ([10], 10),
])
def test_calculate_total(input, expected):
    assert calculate_total(input) == expected
```

### Test Doubles
- **Dummy**: Placeholder object (not used)
- **Fake**: Working implementation (in-memory DB)
- **Stub**: Returns predefined responses
- **Mock**: Verifies interactions
- **Spy**: Records interactions

## Test Maintenance

### Keeping Tests Green
- Fix failing tests immediately
- Don't skip tests without good reason
- Update tests when requirements change
- Remove obsolete tests

### Test Performance
- Run fast tests frequently (unit tests)
- Run slow tests in CI (integration, E2E)
- Use test parallelization
- Cache dependencies in CI

## Best Practices

1. **Write tests first** (TDD) when possible
2. **Test edge cases**: empty inputs, null values, boundary conditions
3. **Test error paths**: invalid inputs, network failures, timeouts
4. **Keep tests simple**: complex tests are hard to maintain
5. **Use descriptive assertions**: clear failure messages
6. **Avoid test interdependencies**: each test should be independent
7. **Test one thing at a time**: focused, single-purpose tests
