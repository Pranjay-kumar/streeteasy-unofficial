from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .models import Listing


@dataclass(frozen=True, slots=True)
class Event:
    search_key: str
    occurred_at: datetime

    @classmethod
    def now(cls, search_key: str, **values):
        return cls(
            search_key=search_key, occurred_at=datetime.now(timezone.utc), **values
        )


@dataclass(frozen=True, slots=True)
class NewListing(Event):
    listing: Listing


@dataclass(frozen=True, slots=True)
class PriceChanged(Event):
    listing: Listing
    old_price: int
    new_price: int


@dataclass(frozen=True, slots=True)
class ListingRemoved(Event):
    listing: Listing


@dataclass(frozen=True, slots=True)
class ListingReturned(Event):
    listing: Listing


@dataclass(frozen=True, slots=True)
class VerificationRequired(Event):
    message: str


@dataclass(frozen=True, slots=True)
class RunFailed(Event):
    message: str
