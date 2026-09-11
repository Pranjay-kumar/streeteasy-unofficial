from __future__ import annotations

import uuid
from typing import Any

from .models import Listing, SearchFilters, SearchPage

ENDPOINT = "https://api-v6.streeteasy.com/"
MAX_PAGE_SIZE = 500

SEARCH_RENTALS_QUERY = """
query GetListingRental($input: SearchRentalsInput!) {
  searchRentals(input: $input) {
    totalCount
    edges {
      ... on OrganicRentalEdge { node { ...ListingFields } }
      ... on FeaturedRentalEdge { node { ...ListingFields } }
    }
  }
}
fragment ListingFields on SearchRentalListing {
  id areaName bedroomCount buildingType fullBathroomCount halfBathroomCount
  geoPoint { latitude longitude }
  price sourceGroupLabel status street unit urlPath
}
"""


def build_search_request(
    filters: SearchFilters,
    *,
    page: int = 1,
    per_page: int = 100,
    sort: str = "LISTED_AT",
    direction: str = "DESCENDING",
) -> dict[str, Any]:
    if page < 1:
        raise ValueError("page must be at least 1")
    if not 1 <= per_page <= MAX_PAGE_SIZE:
        raise ValueError(f"per_page must be between 1 and {MAX_PAGE_SIZE}")
    return {
        "query": SEARCH_RENTALS_QUERY,
        "variables": {
            "input": {
                "filters": filters.to_graphql(),
                "page": page,
                "perPage": per_page,
                "sorting": {"attribute": sort, "direction": direction},
                "userSearchToken": str(uuid.uuid4()),
                "adStrategy": "NONE",
            }
        },
    }


def parse_search_response(
    payload: dict[str, Any], *, page: int, per_page: int
) -> SearchPage:
    search = payload["data"]["searchRentals"]
    listings: list[Listing] = []
    seen: set[str] = set()
    for edge in search.get("edges", []):
        node = edge.get("node") if isinstance(edge, dict) else None
        if not node or not node.get("urlPath") or node.get("price") is None:
            continue
        listing_id = str(node.get("id") or node["urlPath"].strip("/"))
        if listing_id in seen:
            continue
        seen.add(listing_id)
        full = node.get("fullBathroomCount")
        half = node.get("halfBathroomCount")
        bathrooms = (
            None if full is None and half is None else (full or 0) + 0.5 * (half or 0)
        )
        point = node.get("geoPoint") or {}
        listings.append(
            Listing(
                id=listing_id,
                url="https://streeteasy.com" + node["urlPath"],
                price=int(node["price"]),
                street=node.get("street"),
                unit=node.get("unit"),
                area_name=node.get("areaName"),
                bedrooms=node.get("bedroomCount"),
                bathrooms=bathrooms,
                building_type=node.get("buildingType"),
                listed_by=node.get("sourceGroupLabel"),
                latitude=point.get("latitude"),
                longitude=point.get("longitude"),
                raw=dict(node),
            )
        )
    return SearchPage(
        total_count=int(search.get("totalCount") or 0),
        page=page,
        per_page=per_page,
        listings=tuple(listings),
    )
