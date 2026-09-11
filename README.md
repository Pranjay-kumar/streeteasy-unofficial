# StreetEasy Unofficial

A typed Python SDK for searching, enriching, and monitoring StreetEasy rentals locally.

```bash
pip install "streeteasy-unofficial[browser]"
```

```python
from streeteasy_unofficial import SearchFilters, StreetEasy

client = StreetEasy()
filters = SearchFilters(
    neighborhoods=("Astoria", "Sunnyside"),
    max_price=3000,
    bedrooms=(1,),
)

for listing in client.search_all(filters, max_results=50):
    print(listing.price, listing.area_name, listing.url)
```

## Monitor a search

```python
from streeteasy_unofficial import ConsoleNotifier, JsonFileStore

watch = client.watch(
    filters=filters,
    interval="2h",
    store=JsonFileStore("apartments.json"),
    notifier=ConsoleNotifier(),
)
watch.run()
```

Monitoring emits typed events for new, changed, removed, and returned listings.
Checkpoints are saved only after every requested search page succeeds.

## CLI

```bash
streeteasy areas astoria
streeteasy search --neighborhood Astoria --max-price 3000 --bedrooms 1
streeteasy enrich LISTING_ID
streeteasy watch --config examples/watch.toml
streeteasy doctor
```

## What it provides

- Typed search filters and result models.
- Friendly neighborhood names backed by a versioned area catalog.
- Automatic cross-page pagination and deduplication.
- Synchronous and asynchronous clients.
- Typed monitoring events with caller-selected persistence and notification adapters.
- GraphQL request construction for the observed `GetListingRental` operation.
- Rental response parsing, bathroom normalization, and per-page deduplication.
- Rental-detail enrichment for descriptions, media, amenities, price data,
  building metadata, nearby transit, and schools.
- Bathroom, amenity, pet, and availability search filters.
- Bounded-concurrency enrichment that retains per-listing failures.
- An optional visible-Chrome transport. It never runs headless.
- Desktop notification, foreground Chrome, and automatic continuation when human verification appears.
- No required runtime dependencies; browser support is an explicit extra.

The current web operation exposes listing ID, URL, price, address, neighborhood, bedrooms, bathrooms, building type, listing source, and coordinates. It does not expose every detail-page field.

## Deliberate boundaries

This project is unofficial and is not affiliated with or endorsed by StreetEasy or Zillow. It does not extract cookies, solve or click CAPTCHAs, spoof browser fingerprints, automate accounts, call tracking mutations, or bypass rate limits. If verification appears, it asks a person to use the visible browser. You are responsible for obtaining permission and following applicable terms, robots directives, and laws.

StreetEasy can change or remove its web operations without notice. Pin versions, cache responsibly, keep request volume low, and treat schema failures as normal operational failures.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m build
twine check dist/*
```

## Test scripts

Run the deterministic offline smoke test:

```bash
python scripts/offline_smoke.py
```

Run a small live Astoria search for one-bedroom rentals under $3,000, then
enrich the first result:

```bash
pip install -e ".[browser]"
python scripts/live_smoke.py
```

Chrome remains visible throughout the live test. If StreetEasy requests human
verification, the script brings Chrome forward, sends a desktop notification,
waits for completion, and then resumes. Change the test inputs with
`--area-id`, `--max-price`, `--bedrooms`, `--per-page`, and `--start-url`.

## License

MIT

See the [API reference](docs/api.md), [endpoint compatibility notes](docs/endpoint-discovery.md), [changelog](CHANGELOG.md), and [contribution guide](CONTRIBUTING.md).
