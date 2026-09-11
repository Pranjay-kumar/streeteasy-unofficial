from __future__ import annotations

import uuid
from typing import Any

from .models import Listing, RentalDetails, SearchFilters, SearchPage

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
  availableAt livingAreaSize noFee netEffectivePrice price priceDelta priceChangedAt
  photos { key } hasVideos hasTour3d sourceGroupLabel status street unit urlPath
}
"""

RENTAL_DETAILS_QUERY = """
query RentalListingDetailsFederated($listingID: ID!) {
  rentalByListingId(id: $listingID) {
    id status description buildingId availableAt createdAt updatedAt
    pricing { price noFee leaseTermMonths monthsFree priceDelta priceChanges { changedAt } }
    propertyDetails {
      address { street houseNumber streetName city state zipCode unit }
      roomCount bedroomCount fullBathroomCount halfBathroomCount livingAreaSize
      amenities { list doormanTypes parkingTypes sharedOutdoorSpaceTypes storageSpaceTypes }
      features { list fireplaceTypes privateOutdoorSpaceTypes views }
    }
    media { photos { key } floorPlans { key } videos { imageUrl id provider } tour3dUrl assetCount }
    upcomingOpenHouses { id startTime endTime appointmentOnly }
    propertyHistory { listingId sourceGroupLabel rentalEventsOfInterest { date price } }
  }
  buildingByRentalListingId(id: $listingID) {
    id name type residentialUnitCount yearBuilt status
    address { street city state zipCode }
    area { name }
    policies { list petPolicy { catsAllowed dogsAllowed maxDogWeight restrictedDogBreeds } }
    nearby { transitStations { name distance routes geo { latitude longitude } } }
  }
  getBuildingExpressByRentalListingId(id: $listingID) {
    nearbySchools { name district grades id idstr geoCenter { latitude longitude } }
  }
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
                available_at=node.get("availableAt"),
                living_area_size=node.get("livingAreaSize"),
                no_fee=node.get("noFee"),
                net_effective_price=node.get("netEffectivePrice"),
                price_delta=node.get("priceDelta"),
                price_changed_at=node.get("priceChangedAt"),
                photo_keys=tuple(
                    photo["key"]
                    for photo in node.get("photos") or ()
                    if isinstance(photo, dict) and photo.get("key")
                ),
                has_videos=node.get("hasVideos"),
                has_tour3d=node.get("hasTour3d"),
                raw=dict(node),
            )
        )
    return SearchPage(
        total_count=int(search.get("totalCount") or 0),
        page=page,
        per_page=per_page,
        listings=tuple(listings),
    )


def build_rental_details_request(listing_id: str | int) -> dict[str, Any]:
    if not str(listing_id).strip():
        raise ValueError("listing_id cannot be empty")
    return {
        "query": RENTAL_DETAILS_QUERY,
        "variables": {"listingID": str(listing_id)},
    }


def parse_rental_details_response(payload: dict[str, Any]) -> RentalDetails:
    data = payload["data"]
    rental = data["rentalByListingId"]
    if not rental:
        raise ValueError("rental listing was not found")
    pricing = rental.get("pricing") or {}
    prop = rental.get("propertyDetails") or {}
    media = rental.get("media") or {}
    amenities = prop.get("amenities") or {}
    features = prop.get("features") or {}
    building = data.get("buildingByRentalListingId") or {}
    nearby = building.get("nearby") or {}
    express = data.get("getBuildingExpressByRentalListingId") or {}
    return RentalDetails(
        id=str(rental["id"]),
        status=rental.get("status"),
        description=rental.get("description"),
        building_id=str(rental["buildingId"]) if rental.get("buildingId") else None,
        available_at=rental.get("availableAt"),
        created_at=rental.get("createdAt"),
        updated_at=rental.get("updatedAt"),
        price=pricing.get("price"),
        no_fee=pricing.get("noFee"),
        address=dict(prop.get("address") or {}),
        amenities=tuple(amenities.get("list") or ()),
        features=tuple(features.get("list") or ()),
        photo_keys=tuple(
            item["key"] for item in media.get("photos") or () if item.get("key")
        ),
        floor_plan_keys=tuple(
            item["key"] for item in media.get("floorPlans") or () if item.get("key")
        ),
        tour3d_url=media.get("tour3dUrl"),
        building_name=building.get("name"),
        year_built=building.get("yearBuilt"),
        transit=tuple(dict(item) for item in nearby.get("transitStations") or ()),
        schools=tuple(dict(item) for item in express.get("nearbySchools") or ()),
        raw=dict(data),
    )
