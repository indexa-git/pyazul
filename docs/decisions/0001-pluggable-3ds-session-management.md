---
status: proposed
date: { YYYY-MM-DD } # To be filled with current date
builds-on: {}
story: Improve 3DS session management for production readiness and flexibility, as identified in library evaluation.
---

# ADR 0001: Pluggable 3D Secure Session Management

## Context & Problem Statement

The current 3D Secure (3DS) implementation in `pyazul` (specifically within `[pyazul/services/secure.py](mdc:pyazul/services/secure.py)`) manages 3DS session state (including `secure_id` to `azul_order_id` mapping, processed method flags, and transaction states) using internal Python dictionaries. While functional for single-instance applications or testing, this approach lacks persistence and scalability required for robust production environments, especially those involving multiple server instances or serverless functions.

A more flexible solution is needed to allow users to integrate their own session storage mechanisms (e.g., Redis, databases) without modifying the core library logic.

## Priorities & Constraints

- **Flexibility**: Users should be able to provide their own session storage backend.
- **Production Readiness**: The solution should support persistent and shared session storage suitable for distributed systems.
- **Ease of Use**: The default behavior should remain simple (e.g., in-memory store for basic use/testing), with clear instructions for custom implementations.
- **Maintainability**: The library's internal logic for 3DS flow should not be overly complicated by the session management abstraction.
- **Minimal Breaking Changes (if any)**: Ideally, this can be added extensibly.

## Considered Options

1. **Current In-Memory Dictionary**: Keep the existing internal dictionary-based session management within `SecureService`. (This is the state after reverting the prior implementation attempt).

   - Pros: Simple, no immediate changes needed.
   - Cons: Not suitable for production, no persistence, doesn't scale across multiple instances.

2. **Pluggable Session Store via Abstract Base Class (ABC)**:

   - Define an ABC (`ThreeDSSessionStore`) in `pyazul.core.sessions` outlining methods for session operations (e.g., `save_session`, `get_session`, `delete_session`, `mark_method_processed`, `is_method_processed`, `get_transaction_state`, `set_transaction_state`).
   - Provide a default `InMemorySessionStore` implementation of this ABC, using dictionaries (similar to the current internal logic but encapsulated).
   - Modify `SecureService` to accept an instance of `ThreeDSSessionStore` in its constructor and use it for all session-related operations.
   - Modify `PyAzul` to accept an optional `session_store` argument in its constructor. If none is provided, it defaults to instantiating `InMemorySessionStore`. This store instance is then passed to `SecureService`.
   - Users can implement the `ThreeDSSessionStore` ABC with their preferred backend (Redis, database, etc.) and pass their custom store instance when initializing `PyAzul`.

3. **Callback-Based Session Management**: Require the user to implement specific callback functions for saving/loading session data, which `SecureService` would call.
   - Pros: Shifts responsibility entirely to the user.
   - Cons: Can be more cumbersome for the user to implement multiple callbacks, potentially tighter coupling with library internals if callbacks are too granular.

## Decision Outcome

Chosen option: **[Option 2: Pluggable Session Store via Abstract Base Class (ABC)]**

This approach was chosen because:

- **Balances Flexibility and Ease of Use**: It provides a clear contract (the ABC) for custom implementations while offering a sensible default (`InMemorySessionStore`) for simple use cases and backward compatibility with current behavior if no custom store is provided.
- **Production Viability**: Directly addresses the need for persistent and potentially distributed session storage by allowing users to integrate robust backends.
- **Decoupling**: Decouples the 3DS session storage logic from the core `SecureService` flow logic, making both more maintainable.
- **Clear Interface**: The ABC methods clearly define the required session operations.

### Expected Consequences

- **Positive**:
  - Library becomes more suitable for production use in diverse environments.
  - Users gain control over 3DS session persistence and scalability.
  - Clear separation of concerns regarding session storage.
- **Neutral/Slightly Positive**:
  - Users wanting custom storage will need to implement the `ThreeDSSessionStore` interface.
  - The `PyAzul` constructor will have an additional optional parameter (`session_store`).
- **Potentially Negative (if not managed well)**:
  - If the ABC interface is not well-designed, it might be restrictive or difficult to implement for some backends (mitigated by making methods async and using simple data types).

## More Information

- The initial implementation of this was started and then reverted to document this ADR first.
- Relevant files for implementation would be:
  - `pyazul/core/sessions.py` (new file for ABC and InMemorySessionStore)
  - `pyazul/services/secure.py` (to use the injected store)
  - `pyazul/index.py` (to accept and pass the store instance)
  - `pyazul/__init__.py` (to export session store classes)
- The [README.md](mdc:README.md) would need updates to document this feature.
