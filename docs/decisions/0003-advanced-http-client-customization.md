---
status: proposed
date: 2025-05-25
builds-on: {}
story: Allow users more control over the HTTP client for advanced scenarios like custom proxies, timeouts, or retry strategies.
---

# ADR 0003: Advanced HTTP Client Customization

## Context & Problem Statement

The `pyazul` library internally creates and manages an `httpx.AsyncClient` instance within `AzulAPI` ([pyazul/api/client.py](mdc:pyazul/api/client.py)). While `AzulAPI` handles common configurations like SSL context (from `AzulSettings`) and default timeouts, users with advanced networking requirements (e.g., specific proxy configurations, custom retry strategies beyond the built-in alternate URL retry, fine-grained timeout controls, custom transport layers, or event hooks) currently have no way to customize or provide their own `httpx.AsyncClient` instance.

Should `pyazul` allow users to provide a pre-configured `httpx.AsyncClient` instance?

## Priorities & Constraints

- **Flexibility**: Users with advanced needs should be able to customize HTTP client behavior.
- **Maintain Internal Defaults**: The library should still work out-of-the-box with sensible default client behavior if no custom client is provided.
- **Encapsulation**: Avoid exposing too many low-level HTTP client details directly on the `PyAzul` or `AzulSettings` API if a simpler mechanism suffices.
- **Security**: Ensure that if a user provides a custom client, critical security configurations managed by `pyazul` (like SSL context for Azul certs, specific Auth headers) are still correctly applied or that the user is made aware of their responsibility.

## Considered Options

1. **No Custom Client (Current State)**: `AzulAPI` always creates its own `httpx.AsyncClient` with fixed internal configurations (plus what `AzulSettings` provides for certs/timeouts).

   - Pros: Simple for the library to manage; consistent client behavior.
   - Cons: No flexibility for users with advanced proxy, retry, or transport needs.

2. **Expose More `AzulSettings` for HTTP Client Params**: Add more fields to `AzulSettings` for common `httpx.AsyncClient` parameters (e.g., proxy URLs, more timeout options, retry counts).

   - Pros: Keeps configuration within the existing `AzulSettings` pattern.
   - Cons: Can lead to a bloated `AzulSettings` if many `httpx` options are exposed; might still not cover all advanced use cases (like custom transports or event hooks).

3. **Allow Passing a Pre-configured `httpx.AsyncClient` to `AzulAPI` (and thus to `PyAzul`)**:
   - Modify `AzulAPI.__init__` to optionally accept an `httpx.AsyncClient` instance.
   - If provided, `AzulAPI` uses this instance. If not, it creates its own as it does currently.
   - `PyAzul.__init__` would also be modified to optionally accept this client and pass it to `AzulAPI`.
   - **Crucial Consideration**: If a user provides their own client, `AzulAPI` must still ensure its own SSL context (from `AzulSettings` for Azul certs) is used, or clearly document that the user-provided client must be pre-configured with the appropriate `verify` settings. Azul-specific headers (`Auth1`, `Auth2`) are added per-request by `AzulAPI` so these would still apply.
   - Pros: Maximum flexibility for users – they can configure the client exactly as needed.
   - Cons: Users need to understand `httpx.AsyncClient` configuration. Potential for misconfiguration if the interaction regarding SSL/verify context isn't handled or documented clearly.

## Decision Outcome

Chosen option: **[Option 3: Allow Passing a Pre-configured `httpx.AsyncClient` to `AzulAPI`]**

This option offers the highest degree of flexibility for users with advanced networking requirements, which is often necessary when dealing with enterprise environments, specific proxy setups, or complex network policies.

To mitigate potential issues:

- **Documentation**: Clearly document how to pass a custom client and the responsibilities of the user regarding its configuration, especially SSL/TLS verification if they intend to override `pyazul`'s default certificate handling.
- **Sensible Merging/Defaults**: When a custom client is passed to `AzulAPI`, `AzulAPI` should ideally still attempt to apply its specific SSL context derived from `AzulSettings` _unless_ the user-provided client already has a custom SSL context explicitly set. `AzulAPI` will continue to manage Azul-specific authentication headers (`Auth1`/`Auth2`) on each request.
- The default behavior (library creates and manages its own client) must remain for ease of use in common scenarios.

### Expected Consequences

- **Positive**:
  - Library becomes usable in a wider range of network environments.
  - Users gain fine-grained control over HTTP behavior for optimization or specific requirements.
- **Neutral/Slightly Positive**:
  - `PyAzul` and `AzulAPI` constructors will have an additional optional parameter (`http_client: Optional[httpx.AsyncClient] = None`).
- **Potentially Negative**:
  - Increased complexity for users who choose to provide their own client if they are not familiar with `httpx` configuration details.
  - Risk of user misconfiguration (e.g., disabling SSL verification inappropriately) if documentation and warnings are not clear.

## More Information

- This change primarily affects `[pyazul/api/client.py](mdc:pyazul/api/client.py)` (`AzulAPI.__init__`) and `[pyazul/index.py](mdc:pyazul/index.py)` (`PyAzul.__init__`).
- The `httpx` documentation on advanced client configuration, transports, and SSL would be relevant for users choosing this option.
- The library should continue to set its `base_headers` and per-request `Auth1`/`Auth2` headers even on a user-provided client.
