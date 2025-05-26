---
status: implemented
date: 2025-05-26
builds-on:
story: Improve separation of concerns and simplify service dependencies by centralizing API endpoint and authentication parameter selection within the AzulAPI client.
---

# Consolidate API Settings Logic within AzulAPI

## Context & Problem Statement

Currently, while `AzulAPI` handles some settings-based selections (like choosing between standard and 3DS authentication keys based on an `is_secure` flag), there's a potential for services to also access the `AzulSettings` object to determine API call parameters like base URLs or other specific settings. This can lead to a diluted responsibility for `AzulAPI` and require services to carry `AzulSettings` as a dependency even if their primary need is just to make API calls via `AzulAPI`. The goal is to make `AzulAPI` the sole authority on how to communicate with the Azul gateway once it's configured.

## Priorities & Constraints

- **Clear Separation of Concerns**: `AzulAPI` should be the single point of truth for how to construct and send requests to the Azul API, including selecting appropriate endpoints and authentication credentials.
- **Simplified Service Dependencies**: Services should ideally only depend on `AzulAPI` for API interactions, reducing the need to also depend on `AzulSettings` if `AzulAPI` can derive all necessary call parameters.
- **Maintainability**: Centralizing this logic should make the codebase easier to understand and maintain, as changes to endpoint selection or auth logic would be localized to `AzulAPI`.
- **Ease of Use**: While the `PyAzul` facade simplifies things for the end-user, internal consistency and clarity benefit development and testing.

## Considered Options

- **Option 1: Services Retain Access to `AzulSettings` for API Parameters**: Services continue to potentially use `AzulSettings` to determine specific API call details (e.g., base URLs for different environments or transaction types). This is the implicit status quo if not actively changed.
- **Option 2: `AzulAPI` Fully Manages API Call Parameters**: `AzulAPI`, once initialized with `AzulSettings`, becomes solely responsible for selecting the correct base URLs, authentication keys, and other necessary parameters for an API call, primarily based on its internal settings and explicit flags like `is_secure` passed during request method calls. Services would not need to consult `AzulSettings` for these details.

## Decision Outcome

Chosen option: **Option 2: `AzulAPI` Fully Manages API Call Parameters**

`AzulAPI` will be enhanced to fully encapsulate the logic for selecting appropriate API base URLs (e.g., dev vs. prod, standard vs. secure/3DS) and any other settings-derived parameters needed for making API calls. This complements its existing responsibility for choosing authentication keys.

Services will primarily rely on the `is_secure` flag (and potentially other flags if new distinct API endpoints/behaviors are introduced) when calling methods on `AzulAPI`. `AzulAPI` will then use these flags in conjunction with its `self.settings` to make all necessary choices.

This means that most services, after this change, might no longer require direct injection of `AzulSettings` if their only use of it was to determine API call parameters. They would only need the `api_client` instance. `SecureService` is a known exception due to its specific needs for URL manipulation (`TermUrl`, `MethodNotificationUrl`) and session management, which might still benefit from direct `settings` access.

### Expected Consequences

- **Reduced Coupling**: Services (excluding potentially `SecureService`) will be less coupled to the `AzulSettings` structure for API call mechanics.
- **Improved Clarity**: The responsibility for choosing API endpoints and auth details will be clearly located within `AzulAPI`.
- **Simplified Service Signatures**: Constructors for many services might be simplified to only require `api_client`.
- **Refactoring Effort**: `AzulAPI` will need to be refactored to include this expanded logic. Services might need minor adjustments if they were previously deriving API call parameters from `settings`.
- **Testing**: Unit testing for `AzulAPI` will become even more critical as it handles more complex decision-making. Service testing might become simpler as they delegate more to `AzulAPI`.

## More Information

- This decision builds upon the existing architecture where `AzulAPI` already selects authentication keys (standard vs. 3DS) based on `is_secure` and `AzulSettings`.
- See `configuration_management.mdc` and `architecture_overview.mdc` for context on the current roles of `AzulAPI` and `AzulSettings`.
