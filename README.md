# StreetEasy Unofficial

Typed, transport-agnostic Python helpers for StreetEasy's web GraphQL rental search.

```bash
pip install "streeteasy-unofficial[browser]"
```

```python
from streeteasy_unofficial import AsyncClient, HeadfulBrowserTransport, SearchFilters

async with HeadfulBrowserTransport(
    start_url="https://streeteasy.com/for-rent/astoria/price:-3500",
) as browser:
    client = AsyncClient(browser)
    page = await client.search_rentals(
        SearchFilters(max_price=3500, bedrooms=(0, 1)),
        per_page=100,
    )
    for listing in page.listings:
        print(listing.price, listing.area_name, listing.url)

    details = await client.rental_details(page.listings[0].id)
    print(details.description, details.amenities, details.transit)
```

## What it provides

- Typed search filters and result models.
- GraphQL request construction for the observed `GetListingRental` operation.
- Rental response parsing, bathroom normalization, and per-page deduplication.
- Rental-detail enrichment for descriptions, media, amenities, price data,
  building metadata, nearby transit, and schools.
- Bathroom, amenity, pet, and availability search filters.
- An async client that accepts your transport instead of hiding network behavior.
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

## License

MIT
