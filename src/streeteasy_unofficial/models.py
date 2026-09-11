from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """Filters observed in StreetEasy's public rental search request."""

    area_ids: tuple[int, ...] = ()
    min_price: int | None = None
    max_price: int | None = None
    bedrooms: tuple[float, ...] = ()
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

    def to_graphql(self) -> dict[str, Any]:
        result: dict[str, Any] = {"rentalStatus": self.rental_status}
        if self.area_ids:
            result["areas"] = list(dict.fromkeys(self.area_ids))
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
                "minimum": values[0],
                "maximum": values[-1],
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
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SearchPage:
    total_count: int
    page: int
    per_page: int
    listings: tuple[Listing, ...]
