"""Run a deliberately small search and enrichment check in visible Chrome."""

import argparse
import asyncio
from pathlib import Path

from streeteasy_unofficial import AsyncClient, HeadfulBrowserTransport, SearchFilters


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search StreetEasy in visible Chrome and enrich the first result."
    )
    parser.add_argument("--area-id", type=int, default=400)
    parser.add_argument("--max-price", type=int, default=3000)
    parser.add_argument("--bedrooms", type=float, default=1)
    parser.add_argument("--per-page", type=int, default=5, choices=range(1, 21))
    parser.add_argument(
        "--start-url",
        default="https://streeteasy.com/for-rent/astoria/price:-3000%7Cbeds:1",
    )
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=Path(".streeteasy-browser"),
    )
    return parser.parse_args()


async def main() -> None:
    args = arguments()
    filters = SearchFilters(
        area_ids=(args.area_id,),
        max_price=args.max_price,
        bedrooms=(args.bedrooms,),
    )
    async with HeadfulBrowserTransport(
        start_url=args.start_url,
        profile_dir=args.profile_dir,
    ) as browser:
        client = AsyncClient(browser)
        page = await client.search_rentals(filters, per_page=args.per_page)
        print(f"StreetEasy reported {page.total_count} matching rentals")
        for listing in page.listings:
            print(f"${listing.price:,} | {listing.area_name} | {listing.url}")

        if not page.listings:
            print("No listing was available to enrich")
            return

        details = await client.rental_details(page.listings[0].id)
        print("\nEnriched first result")
        print(f"Building: {details.building_name or 'Unknown'}")
        print(f"Amenities: {', '.join(details.amenities) or 'None reported'}")
        print(f"Photos: {len(details.photo_keys)}")
        print(f"Nearby transit stops: {len(details.transit)}")


if __name__ == "__main__":
    asyncio.run(main())
