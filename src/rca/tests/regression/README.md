# RCA Regression Testing Framework

This directory contains regression tests for the RCA system, designed to ensure backward compatibility as we implement new features for Milestone 2 and beyond.

## Purpose

The regression tests verify that:
1. All public interfaces of the RCAAgent remain stable
2. The behavior of existing functionality is preserved when adding new features
3. Error handling works correctly across component boundaries
4. Custom extensions can be integrated without breaking existing code

## Test Matrix

The [test_matrix.md](./test_matrix.md) file documents all public interfaces that need to be maintained for backward compatibility, including:
- Method signatures
- Return structures
- Stability requirements
- Current test coverage

## Running Tests

### Local Testing with Real Azure Services

To run the tests locally with real Azure services:

```bash
# Run all regression tests
python -m pytest src/rca/tests/regression/ -v

# Run a specific test
python -m pytest src/rca/tests/regression/test_agent_backward_compatibility.py::TestRCAAgentBackwardCompatibility::test_process_simple_query -v

# Run with coverage reporting
python -m pytest src/rca/tests/regression/ --cov=src.rca.agents -v
```

### Environment Setup

These tests require Azure service connections. Ensure you have a `.env.azure` file in the project root with:

```
AZURE_OPENAI_API_KEY=<your-openai-api-key>
AZURE_OPENAI_ENDPOINT=<your-openai-endpoint>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding
AZURE_SEARCH_ADMIN_KEY=<your-search-admin-key>
AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
AZURE_SEARCH_INDEX=gptkbindex
AZURE_SEARCH_API_VERSION=2023-11-01
AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4o-mini
```

## Continuous Integration

The tests are automatically run via GitHub Actions when:
- Code is pushed to branches matching `feature/milestone*`
- Pull requests are created against the main branch
- Changes are made to files in the `src/rca/` directory

See the workflow configuration in [.github/workflows/rca-regression-tests.yml](/.github/workflows/rca-regression-tests.yml).

## Test Structure

### Main Test Components

- **`test_agent_backward_compatibility.py`**: Comprehensive tests for the RCAAgent's public interfaces
- **`test_matrix.md`**: Documentation of all interfaces requiring compatibility
- **`__init__.py`**: Package initialization with version info

### Test Cases Organization

The tests are organized by interface type:
1. **Initialization Tests**: Verify agent creation with various configurations
2. **Processing Tests**: Verify query handling and response generation
3. **Error Handling Tests**: Verify proper error detection and reporting
4. **Extension Tests**: Verify the ability to extend the agent with custom tools

## Adding New Tests

When adding new features, follow these steps to maintain backward compatibility:

1. Document the new interface in `test_matrix.md`
2. Create tests that verify the interface behaves as expected
3. Add regression tests for any edge cases or error conditions
4. Ensure all existing tests continue to pass

### Example: Adding Tests for a New Feature

```python
def test_new_feature_backward_compatibility(self):
    """Test that the new feature doesn't break existing functionality"""
    # Test existing behavior still works
    result = self.agent.process(self.test_query)
    self.assertIn("response", result)
    
    # Test new feature works alongside existing features
    enhanced_result = self.agent.process_with_enhancement(self.test_query)
    self.assertIn("response", enhanced_result)
    self.assertIn("enhancement_data", enhanced_result)
```

## Troubleshooting

### Common Issues

- **Connection Errors**: Make sure your `.env.azure` file has valid credentials
- **Test Failures**: Check that your changes maintain backward compatibility
- **Slow Tests**: These tests connect to real Azure services, so they may take time

For help, please contact the RCA system maintainers. 