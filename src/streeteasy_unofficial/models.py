from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """Filters observed in StreetEasy's public rental search request."""

    area_ids: Sequence[int] = ()
    neighborhoods: Sequence[str] = ()
    min_price: int | None = None
    max_price: int | None = None
    bedrooms: Sequence[float] = ()
    min_bathrooms: float | None = None
    max_bathrooms: float | None = None
    amenities: Sequence[str] = ()
    optional_amenities: Sequence[str] = ()
    pets_allowed: bool | None = None
    available_after: str | None = None
    available_before: str | None = None
    rental_status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if self.min_price is not None and self.min_price < 0:
            raise ValueError("min_price cannot be negative")
        if self.max_price is not None and self.max_price < 0:
            raise ValueError("max_price cannot be negative")
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot exceed max_price")
        if any(value < 0 for value in self.bedrooms):
            raise ValueError("bedrooms cannot contain negative values")
        ordered = sorted(set(self.bedrooms))
        if any(right - left > 1 for left, right in pairwise(ordered)):
            raise ValueError(
                "bedrooms must be a contiguous range because the source accepts minimum and maximum"
            )
        if self.min_bathrooms is not None and self.min_bathrooms < 0:
            raise ValueError("min_bathrooms cannot be negative")
        if self.max_bathrooms is not None and self.max_bathrooms < 0:
            raise ValueError("max_bathrooms cannot be negative")
        if (
            self.min_bathrooms is not None
            and self.max_bathrooms is not None
            and self.min_bathrooms > self.max_bathrooms
        ):
            raise ValueError("min_bathrooms cannot exceed max_bathrooms")

    def to_graphql(self) -> dict[str, Any]:
        from .areas import resolve_areas

        result: dict[str, Any] = {"rentalStatus": self.rental_status}
        area_ids = (*self.area_ids, *resolve_areas(self.neighborhoods))
        if area_ids:
            result["areas"] = list(dict.fromkeys(area_ids))
        if self.min_price is not None or self.max_price is not None:
            price: dict[str, int] = {}
            if self.min_price is not None:
                price["lowerBound"] = self.min_price
            if self.max_price is not None:
                price["upperBound"] = self.max_price
            result["price"] = price
        if self.bedrooms:
            values = sorted(set(self.bedrooms))
            result["bedrooms"] = {
                "lowerBound": values[0],
                "upperBound": values[-1],
            }
        if self.min_bathrooms is not None or self.max_bathrooms is not None:
            result["bathrooms"] = {
                "lowerBound": self.min_bathrooms,
                "upperBound": self.max_bathrooms,
            }
        if self.amenities:
            result["amenities"] = list(dict.fromkeys(self.amenities))
        if self.optional_amenities:
            result["optionalAmenities"] = list(dict.fromkeys(self.optional_amenities))
        if self.pets_allowed is not None:
            result["petsAllowed"] = self.pets_allowed
        if self.available_after or self.available_before:
            result["available"] = {
                "startDate": self.available_after,
                "endDate": self.available_before,
            }
        return result


@dataclass(frozen=True, slots=True)
class Listing:
    id: str
    url: str
    price: int
    street: str | None = None
    unit: str | None = None
    area_name: str | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    building_type: str | None = None
    listed_by: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    available_at: str | None = None
    living_area_size: int | None = None
    no_fee: bool | None = None
    net_effective_price: int | None = None
    price_delta: int | None = None
    price_changed_at: str | None = None
    photo_keys: tuple[str, ...] = ()
    has_videos: bool | None = None
    has_tour3d: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def photo_urls(self) -> tuple[str, ...]:
        return tuple(media_url(key) for key in self.photo_keys)


@dataclass(frozen=True, slots=True)
class SearchPage:
    total_count: int
    page: int
    per_page: int
    listings: tuple[Listing, ...]


@dataclass(frozen=True, slots=True)
class RentalDetails:
    id: str
    status: str | None = None
    description: str | None = None
    building_id: str | None = None
    available_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    price: int | None = None
    no_fee: bool | None = None
    address: dict[str, Any] = field(default_factory=dict)
    amenities: tuple[str, ...] = ()
    features: tuple[str, ...] = ()
    photo_keys: tuple[str, ...] = ()
    floor_plan_keys: tuple[str, ...] = ()
    tour3d_url: str | None = None
    building_name: str | None = None
    year_built: int | None = None
    transit: tuple[dict[str, Any], ...] = ()
    schools: tuple[dict[str, Any], ...] = ()
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def photo_urls(self) -> tuple[str, ...]:
        return tuple(media_url(key) for key in self.photo_keys)

    @property
    def floor_plan_urls(self) -> tuple[str, ...]:
        return tuple(media_url(key) for key in self.floor_plan_keys)


@dataclass(frozen=True, slots=True)
class EnrichmentResult:
    listing: Listing
    details: RentalDetails | None = None
    error: str | None = None


def media_url(key: str, *, size: str = "se_large_800_400") -> str:
    return f"https://photos.zillowstatic.com/fp/{key}-{size}.jpg"
