# YouTube connector domain

This module is intentionally left minimal for now.

YouTube-specific domain objects should be introduced after the adapter/application layer clarifies the real integration shape.

Potential future concepts:

- YouTube channel reference
- YouTube video reference
- YouTube subscription
- YouTube polling cursor
- YouTube playlist reference

Do not model these entities prematurely.

The first implementation should focus on the YouTube adapter:
- channel lookup
- latest videos fetching
- polling
- cursor behavior
- normalization into shared ConnectorEvent

After the adapter is implemented and real use cases are clear, stable YouTube-specific domain objects can be extracted.