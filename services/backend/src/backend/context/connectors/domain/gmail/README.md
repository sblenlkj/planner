# Gmail connector domain

This module is intentionally left minimal for now.

Gmail-specific domain objects should be introduced only after the adapter/application layer proves which concepts are stable in the real integration.

Potential future concepts:

- Gmail message reference
- Gmail thread reference
- Gmail history cursor
- Gmail label reference
- Gmail watch/subscription state
- Gmail matching rule/filter

Do not model these entities prematurely.

The first implementation should focus on the Gmail adapter:
- OAuth/token usage
- message listing
- message reading
- history synchronization
- optional watch/webhook mechanism
- normalization into shared ConnectorEvent

After the adapter is implemented and real use cases are clear, stable Gmail-specific domain objects can be extracted.