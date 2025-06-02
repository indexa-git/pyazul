---
status: proposed
date: 2024-12-19
story: Reorganize PyAzul models structure to align with Azul's business domains for better developer experience and maintainability
---

# Reorganize Models by Business Domain

## Context & Problem Statement

The current PyAzul models are organized by technical concerns (`schemas.py` for general models, `secure.py` for 3DS models), which creates confusion and doesn't align with how Azul organizes their services. Developers working with PyAzul need to understand both the business domain they're working with and hunt across different files to find related models.

The current structure mixes different business domains in the same files:

- `schemas.py` contains transaction models, DataVault models, and Payment Page models
- `secure.py` contains only 3D Secure models
- Import patterns show inconsistency, with some code importing from top-level `pyazul.models` and others from specific modules

## Priorities & Constraints

- **Developer Experience**: Models should be discoverable based on business intent
- **Backwards Compatibility**: Existing imports should continue to work during transition
- **Alignment with Azul Documentation**: Structure should match how Azul organizes their services
- **Maintainability**: Related models should be co-located for easier maintenance
- **Clear Separation of Concerns**: Each domain should have clear boundaries

## Considered Options

### Option 1: Keep Current Technical Structure

- Continue with `schemas.py` and `secure.py` organization
- Pros: No breaking changes, minimal effort
- Cons: Doesn't scale well, confusing for developers, misaligned with business domains

### Option 2: Business Domain Organization

Organize models by Azul's business domains:

- `payment/` - Core payment processing (Sale, Hold, Refund, Void, Post)
- `datavault/` - Card tokenization and token management
- `three_ds/` - 3D Secure authentication and challenge flows
- `payment_page/` - Hosted payment page integration
- `verification/` - Transaction status and verification
- `recurring/` - Subscription and recurring payment management
- `installments/` - Payment plans and installment models
- `dcc/` - Dynamic Currency Conversion

### Option 3: Hybrid Approach

- Keep current structure but add domain-specific modules
- Pros: Gradual migration possible
- Cons: Creates duplication and confusion during transition

### Option 4: Functional Organization

- Group by operation type (requests, responses, errors)
- Pros: Clear technical boundaries
- Cons: Doesn't match business understanding

## Decision Outcome

Chosen option: **Option 2: Business Domain Organization**

This approach aligns with how Azul documents and organizes their services, making it intuitive for developers to find relevant models. Each domain will have its own directory with focused responsibilities.

### Implementation Plan

1. **Phase 1**: Create new domain-based structure while maintaining backwards compatibility
   - Create domain directories under `pyazul/models/`
   - Move existing models to appropriate domains
   - Update `__init__.py` to re-export from new locations

2. **Phase 2**: Update internal imports and services
   - Update service classes to import from new locations
   - Update tests to use new structure
   - Add deprecation warnings for old import paths

3. **Phase 3**: Documentation and examples
   - Update documentation to reflect new structure
   - Update examples to demonstrate domain-based usage
   - Create migration guide for existing users

### Expected Consequences

**Positive:**

- Improved developer experience through intuitive model discovery
- Better alignment with Azul's business organization
- Easier maintenance with co-located related models
- Clearer separation of concerns
- More scalable structure for future Azul service additions

**Negative:**

- Initial migration effort required
- Temporary import complexity during transition
- Need to update existing code and documentation

**Neutral:**

- Larger number of files and directories
- Need for clear naming conventions across domains

## More Information

### Supporting Evidence from Azul Documentation

The official Azul documentation clearly organizes services by business domains:

1. **Payment Processing**: Core transaction operations (Sale, Hold, Refund, Void, Post)
2. **Bóveda de Datos (DataVault)**: Card tokenization with methods like ProcessDatavault
3. **3D Secure**: Complete authentication flows with dedicated endpoints and models
4. **Payment Page**: Hosted payment integration with specific parameters and responses
5. **Recurring Payments**: Subscription management with frequency-based models
6. **Installments (Cuotas)**: Payment plan functionality
7. **DCC**: Dynamic Currency Conversion with rate inquiry and conversion models

### Domain Responsibilities

**payment/**

- Core transaction models: SaleTransactionModel, HoldTransactionModel, RefundTransactionModel
- Common response models and error handling
- Base transaction functionality

**datavault/**

- DataVaultRequestModel, DataVaultResponseModel
- Token management models
- Card storage and retrieval models

**three_ds/**

- 3DS authentication models: SecureSaleRequest, SecureTokenSale
- Challenge flow models: CardHolderInfo, ThreeDSAuth
- Authentication response models

**payment_page/**

- PaymentPageModel and related configuration
- Hosted payment form models
- Page-specific response handling

**verification/**

- Transaction verification and status models
- Query and lookup functionality

**recurring/**

- Subscription models and frequency configurations
- Recurring payment scheduling models

**installments/**

- Payment plan models
- Installment configuration and calculation models

**dcc/**

- Currency conversion models
- Rate inquiry and conversion response models

### References

- [Azul API Documentation](https://dev.azul.com.do/) - Official service organization
- [Domain-Driven Design by Eric Evans](https://domainlanguage.com/ddd/) - Principles for domain organization
- [Python Package Organization Best Practices](https://docs.python-guide.org/writing/structure/) - Python-specific guidance
- [Pydantic Model Organization](https://pydantic-docs.helpmanual.io/usage/models/#model-signature) - Framework-specific patterns
