"""Unofficial, transport-agnostic StreetEasy search helpers."""

from .browser import BrowserTransportError, HeadfulBrowserTransport
from .client import AsyncClient, GraphQLResponseError
from .errors import (
    AccessChallengeError,
    ListingNotFoundError,
    SchemaChangedError,
    StreetEasyError,
    TransportError,
    VerificationTimeoutError,
)
from .events import (
    Event,
    ListingRemoved,
    ListingReturned,
    NewListing,
    PriceChanged,
    RunFailed,
    VerificationRequired,
)
from .models import (
    EnrichmentResult,
    Listing,
    RentalDetails,
    SearchFilters,
    SearchPage,
    media_url,
)
from .monitor import (
    ConsoleNotifier,
    DesktopNotifier,
    JsonFileStore,
    MemoryStore,
    Notifier,
    StateStore,
)
from .sync import StreetEasy

__all__ = [
    "AccessChallengeError",
    "AsyncClient",
    "BrowserTransportError",
    "ConsoleNotifier",
    "DesktopNotifier",
    "EnrichmentResult",
    "Event",
    "GraphQLResponseError",
    "HeadfulBrowserTransport",
    "JsonFileStore",
    "Listing",
    "ListingNotFoundError",
    "ListingRemoved",
    "ListingReturned",
    "MemoryStore",
    "NewListing",
    "Notifier",
    "PriceChanged",
    "RentalDetails",
    "RunFailed",
    "SchemaChangedError",
    "SearchFilters",
    "SearchPage",
    "StateStore",
    "StreetEasy",
    "StreetEasyError",
    "TransportError",
    "VerificationRequired",
    "VerificationTimeoutError",
    "media_url",
]
__version__ = "0.2.0"
