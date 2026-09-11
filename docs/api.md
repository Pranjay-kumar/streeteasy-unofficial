# API reference

## Clients

- `StreetEasy`: synchronous, visible-Chrome client with `search`, `search_all`, `enrich`, `enrich_all`, and `watch`.
- `AsyncClient`: transport-based async client with the same search and enrichment primitives.

## Search

`SearchFilters` accepts numeric `area_ids`, friendly `neighborhoods`, price and bedroom bounds, bathroom bounds, amenities, pet policy, and availability dates. `search_all` stops at the reported total, an empty page, `max_pages`, or `max_results`, and removes duplicate IDs across pages.

## Monitoring

`StateStore.load(search_key)` returns a `Checkpoint` or `None`; `save` commits a completed checkpoint. `Notifier.notify(event)` receives typed events. Built-in implementations are `MemoryStore`, `JsonFileStore`, and `ConsoleNotifier`.

Events are `NewListing`, `PriceChanged`, `ListingRemoved`, `ListingReturned`, `VerificationRequired`, and `RunFailed`.

## Errors

All SDK errors inherit from `StreetEasyError`. Specific errors include `TransportError`, `AccessChallengeError`, `VerificationTimeoutError`, `SchemaChangedError`, `ListingNotFoundError`, and the backwards-compatible `GraphQLResponseError` and `BrowserTransportError`.
