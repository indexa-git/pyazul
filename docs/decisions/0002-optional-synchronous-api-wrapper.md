---
status: proposed
date: 2025-05-25
builds-on: {}
story: Enhance usability for developers not using asyncio by providing a synchronous API.
---

# ADR 0002: Optional Synchronous API Wrapper

## Context & Problem Statement

The `pyazul` library is currently exclusively asynchronous (`async/await`), leveraging `httpx.AsyncClient` for API calls. While this is efficient for I/O-bound operations and integrates well with modern async frameworks (like FastAPI, as shown in README examples), it presents a barrier to entry or inconvenience for developers working in synchronous codebases or writing simple scripts where an async event loop is not readily available or desired.

Should `pyazul` offer an optional synchronous API wrapper to improve its accessibility?

## Priorities & Constraints

- **Ease of Use**: Developers in synchronous environments should be able to use the library without managing an asyncio event loop explicitly for `pyazul` calls.
- **Maintainability**: The synchronous wrapper should not significantly complicate the core async library or introduce a large maintenance burden.
- **API Consistency**: The synchronous API should mirror the asynchronous API as closely as possible in terms of methods and parameters.
- **Performance**: While convenience is key, the synchronous wrapper should be implemented efficiently (e.g., by properly managing the event loop for its calls).

## Considered Options

1. **No Synchronous Wrapper (Current State)**: Continue with an async-only API.

   - Pros: Simplest to maintain the core library; no additional code.
   - Cons: Limits usability for synchronous use cases; users would have to manage `asyncio.run()` or similar themselves.

2. **Provide a Separate Synchronous Client (`PyAzulSync`)**:

   - Create a parallel set of classes (e.g., `PyAzulSync`, `TransactionServiceSync`) that internally use `httpx.Client` (the synchronous version) and synchronous method definitions.
   - Pros: Clear separation between async and sync versions; potentially more performant for purely synchronous calls as it avoids `asyncio.run()` overhead per call.
   - Cons: Significant code duplication (methods, Pydantic model handling, etc.), leading to a much larger maintenance burden. Keeping features and fixes in sync across two client implementations would be challenging.

3. **Provide a Thin Synchronous Wrapper Around the Async API**:

   - Create a synchronous facade class (e.g., `PyAzulSync` or add sync methods to `PyAzul` distinguished by name or a mode).
   - Synchronous methods in this facade would internally call the corresponding `async` methods of the core library using `asyncio.run()` or a similar mechanism to execute them in a temporary event loop.
   - Example: `PyAzulSync.sale(...)` would call `asyncio.run(core_pyazul_instance.sale(...))`.
   - Pros: Minimal code duplication as it reuses the entire core async logic; easier to maintain feature parity.
   - Cons: Each synchronous call incurs the overhead of starting/stopping an event loop via `asyncio.run()`, which might be less performant for rapid, numerous calls compared to a native sync client. However, for typical API call frequencies, this might be acceptable.

4. **Auto-Generating Sync Wrapper (e.g., using tools like `unasync`)**:
   - Develop the library as async-first.
   - Use a tool (like `unasync`) to automatically generate a synchronous version of the API by transforming the async code (e.g., replacing `async def` with `def`, `await` with direct calls, `AsyncClient` with `Client`).
   - Pros: Single source of truth (the async code); sync version is generated, reducing manual duplication and maintenance.
   - Cons: Introduces a build-time dependency and process; generated code might sometimes need manual adjustments or careful structuring of the async code to translate well.

## Decision Outcome

Chosen option: **[Option 3: Provide a Thin Synchronous Wrapper Around the Async API]** (with consideration for Option 4 if Option 3 proves too cumbersome or unperformant).

Option 3 is preferred initially because:

- **Leverages Existing Code**: It makes maximal reuse of the already well-structured and tested asynchronous core, minimizing new code that needs to be written and maintained specifically for the sync wrapper.
- **Lower Maintenance Overhead (than Option 2)**: Far less duplication than maintaining two separate client implementations.
- **Good User Experience for Simple Cases**: For users needing occasional synchronous calls, the `asyncio.run()` overhead is likely acceptable and the convenience high.

If performance issues arise with Option 3 or the pattern becomes repetitive and error-prone, **Option 4 (Auto-Generating Sync Wrapper)** should be seriously investigated as a more robust long-term solution for maintaining both sync and async interfaces from a single async codebase.

### Expected Consequences

- **Positive**:
  - Increased adoption of the library by users in synchronous environments.
  - Improved ease of use for simple scripting tasks.
- **Neutral/Slightly Positive**:
  - A new synchronous facade class (e.g., `PyAzulSync`) or additional methods would be added to the public API.
- **Potentially Negative**:
  - Performance overhead for each synchronous call due to `asyncio.run()`. This needs to be acceptable for typical use patterns.
  - Care must be taken if the wrapper needs to manage any state across calls, though `PyAzul` is largely stateless per method call for API interactions.

## More Information

- This decision primarily impacts the main `PyAzul` facade ([pyazul/index.py](mdc:pyazul/index.py)) and how it would offer synchronous methods.
- The underlying services and `AzulAPI` client would remain async.
- Python's `asyncio.run()` is the standard way to run an async function from sync code.
