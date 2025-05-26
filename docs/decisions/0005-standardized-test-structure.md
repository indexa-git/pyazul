---
status: proposed
date: 2025-05-26
builds-on: {}
story: Improve the structure, maintainability, and clarity of the PyAzul test suite by standardizing practices and separating unit from integration tests.
---

# ADR 0005: Standardized Test Structure and Separation of Unit/Integration Tests

## Context & Problem Statement

The current test suite for `pyazul` has evolved organically. While providing good coverage for API interactions (primarily integration tests), it exhibits inconsistencies in:

- Test structure and organization (all tests currently reside under `tests/services/`).
- Fixture definitions and usage, particularly for settings and service instantiation.
- Handling of test data and reliance on Pydantic model defaults versus explicit settings.
- Lack of a clear distinction between fast, isolated unit tests and slower integration tests that depend on external services (like the Azul API test environment).

This leads to challenges in maintainability, readability, and efficient test execution, especially as the codebase grows.

## Priorities & Constraints

- **Clarity & Maintainability**: The test structure should be easy to understand and navigate.
- **Reliability**: Tests should be stable, with unit tests being independent of external factors.
- **Speed & Efficiency**: Developers should be able to run fast unit tests frequently for quick feedback. Integration tests can run on a different cadence.
- **Developer Workflow**: A clear structure aids developers in writing new tests and understanding existing ones.
- **Comprehensive Coverage**: The structure should support both fine-grained unit testing and end-to-end integration testing.

## Considered Options

1. **Maintain Current Structure**: Continue with the existing ad-hoc structure in `tests/services/`, focusing only on fixing immediate issues.

    - Pros: No immediate refactoring effort.
    - Cons: Does not address underlying inconsistencies; maintainability issues will likely worsen.

2. **Standardize Integration Tests Only**: Improve consistency of fixtures and data handling within the existing `tests/services/` structure without explicitly separating unit tests.

    - Pros: Addresses some consistency issues.
    - Cons: Still lacks the benefits of fast, isolated unit tests; all tests remain integration tests.

3. **Separate Unit and Integration Tests with Standardized Practices**: Implement a clear distinction between unit and integration tests with dedicated directory structures and standardized guidelines for fixtures, data, and mocking.
    - Pros: Aligns with best practices, offers speed and reliability benefits from unit tests, improves clarity and maintainability significantly.
    - Cons: Requires an initial refactoring effort to move and adapt existing tests and to write new unit tests.

## Decision Outcome

Chosen option: **[Option 3: Separate Unit and Integration Tests with Standardized Practices]**

This approach provides the most robust and maintainable long-term solution for the `pyazul` test suite.

### Key Aspects of the Chosen Structure

- **Directory Structure Example**:

    ```
    pyazul/
    ├── pyazul/
    │   ├── api/
    │   ├── core/
    │   ├── models/
    │   ├── services/
    │   └── ...
    ├── tests/
    │   ├── conftest.py         # Global test configurations, main 'settings' fixture
    │   ├── unit/
    │   │   ├── conftest.py     # Unit test specific fixtures (if any)
    │   │   ├── api/
    │   │   │   └── test_client_unit.py
    │   │   ├── core/
    │   │   │   └── test_config_unit.py
    │   │   │   └── test_exceptions_unit.py
    │   │   ├── models/
    │   │   │   └── test_schemas_unit.py
    │   │   └── services/
    │   │       └── test_transaction_service_unit.py
    │   │       └── test_secure_service_unit.py
    │   │       └── ...
    │   └── integration/
    │       ├── conftest.py     # Integration test specific fixtures (if any)
    │       └── services/       # Current tests would move under here
    │           ├── test_datavault_integration.py
    │           ├── test_hold_integration.py
    │           ├── test_payment_integration.py
    │           ├── test_payment_page_integration.py
    │           ├── test_post_integration.py
    │           ├── test_secure_integration.py
    │           ├── test_token_secure_integration.py
    │           ├── test_verify_integration.py
    │           └── test_void_integration.py
    ├── .cursor/
    │   └── rules/
    │       └── test_structure_guidelines.mdc
    └── ...
    ```

- **Actual Directories**:
  - `tests/unit/`: For all unit tests, further subdivided by the module being tested (e.g., `api/`, `core/`, `models/`, `services/`).
  - `tests/integration/`: For all integration tests (current tests in `tests/services/` will move here, e.g., `tests/integration/services/`).
  - `[tests/conftest.py](mdc:tests/conftest.py)`: For global fixtures like `settings()`. Component-specific conftest files can exist within `unit` or `integration` subdirectories.
- **Test Types**:
  - **Unit Tests**: Focus on individual classes/methods in isolation. External dependencies (especially network calls like `httpx.AsyncClient.post` or `AzulAPI._async_request`) are mocked.

- **Integration Tests**: Focus on the interaction between `pyazul` and the live Azul API (test environment). Rely on actual network calls and `.env` configuration.

- **Fixture Standardization (as per guidelines to be detailed in a separate rule)**:
  - A global, session-scoped `settings()` fixture in `tests/conftest.py` using `get_azul_settings()`.
  - Service fixtures (e.g., `transaction_service`) dependent on `settings()`, instantiating `AzulAPI` and then the service.
  - Test data fixtures sourcing common values (`Store`, `Channel`) from `settings()` and relying on Pydantic model defaults where appropriate, with test-specific values being explicit.
  - Clear instantiation of Pydantic models in tests.

- **Mocking**: `pytest-mock` (`mocker` fixture) to be used for unit tests.

### Development Plan for Restructuring

**Phase 1: Setup and Initial Migration**

1. **Create Directory Structure**:
    - `tests/unit/`
    - `tests/integration/`
    - `tests/integration/services/`
2. **Move Existing Service Tests**:
    - Move test files from `tests/services/*` to `tests/integration/services/`.
    - Rename files to reflect their integration nature (e.g., `test_payment_integration.py`).
3. **Update `[tests/conftest.py](mdc:tests/conftest.py)`**:
    - Ensure the primary `settings()` fixture is defined with `scope="session"`.
    - Relocate or ensure service fixtures are appropriately scoped (e.g., within integration test files or an integration-specific conftest).
4. **Adapt Integration Test Imports/Fixtures**: Update paths and fixture usage as needed.
5. **Initial Test Run**: Execute `pytest tests/integration` to confirm existing tests pass post-migration.

**Phase 2: Standardize Integration Test Fixtures**

1. **Refactor Service Fixtures**: Ensure consistency, dependency on global `settings()`, and proper instantiation of `AzulAPI` and services.
2. **Refactor Test Data Fixtures**: Align with guidelines for sourcing data (settings, model defaults, test-specific values).
3. **Verify Test Run**: Re-run `pytest tests/integration`.

**Phase 3: Introduce Unit Tests**

1. **Create Unit Test Files** (e.g., `tests/unit/models/test_schemas_unit.py`, `tests/unit/api/test_client_unit.py`, `tests/unit/services/test_transaction_service_unit.py`).
2. **Write Unit Tests For**:
    - Pydantic model validation and default values.
    - Core components like `AzulSettings` (mocking environment/file access).
    - `AzulAPI` helper methods (mocking inputs/outputs).
    - Service logic (mocking `AzulAPI` calls to test service-level data transformation, error handling, and flow control).
3. **Iterate**: Incrementally add unit tests for good coverage.

**Phase 4: Refine and Review**

1. **Assess Test Coverage**: Use tools like `pytest-cov`.
2. **Update Guidelines**: Refine the formal test structure guidelines document/rule if needed.
3. **CI Configuration**: Set up CI to run unit tests frequently and integration tests on an appropriate schedule.

### Expected Consequences

- **Positive**:
  - Improved test suite organization and maintainability.
  - Faster feedback loop for developers via quick unit tests.
  - More reliable testing due to isolation in unit tests.
  - Clearer distinction of test scopes and purposes.
  - Enhanced ability to configure CI/CD pipelines for efficient testing.
- **Neutral/Effort**: Requires initial time investment for refactoring and writing new unit tests.

## More Information

- This decision will be complemented by a detailed Test Structure Guideline document (to be generated as a Cursor Rule).
- See existing ADRs for context on other architectural decisions, e.g., `[0001-pluggable-3ds-session-management.md](mdc:docs/decisions/0001-pluggable-3ds-session-management.md)`. The `pyazul` test suite aims for robustness and clarity, similar to goals in other ADRs regarding the main library code.
