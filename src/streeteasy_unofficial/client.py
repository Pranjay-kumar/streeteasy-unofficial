from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from typing import Any

from .errors import ListingNotFoundError, SchemaChangedError, StreetEasyError
from .graphql import (
    ENDPOINT,
    build_rental_details_request,
    build_search_request,
    parse_rental_details_response,
    parse_search_response,
)
from .models import EnrichmentResult, Listing, RentalDetails, SearchFilters, SearchPage

Transport = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class GraphQLResponseError(StreetEasyError):
    pass


class AsyncClient:
    """A transport-agnostic client.

    Supply an async transport that performs an ordinary authorized POST and
    returns the decoded JSON object. The library deliberately does not manage
    cookies, browser fingerprints, CAPTCHAs, accounts, or access controls.
    """

    def __init__(self, transport: Transport):
        self._transport = transport

    async def search_rentals(
        self,
        filters: SearchFilters,
        *,
        page: int = 1,
        per_page: int = 100,
    ) -> SearchPage:
        request = build_search_request(filters, page=page, per_page=per_page)
        payload = await self._transport(ENDPOINT, request)
        if payload.get("errors"):
            raise GraphQLResponseError(str(payload["errors"][0]))
        try:
            return parse_search_response(payload, page=page, per_page=per_page)
        except (KeyError, TypeError, ValueError) as exc:
            raise SchemaChangedError("Unexpected StreetEasy response shape") from exc

    async def rental_details(self, listing_id: str | int) -> RentalDetails:
        payload = await self._transport(
            ENDPOINT, build_rental_details_request(listing_id)
        )
        if payload.get("errors"):
            raise GraphQLResponseError(str(payload["errors"][0]))
        try:
            return parse_rental_details_response(payload)
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ValueError) and "not found" in str(exc):
                raise ListingNotFoundError(str(exc)) from exc
            raise SchemaChangedError("Unexpected StreetEasy response shape") from exc

    async def search_all(
        self,
        filters: SearchFilters,
        *,
        per_page: int = 100,
        max_pages: int = 10,
        max_results: int | None = None,
    ) -> AsyncIterator[Listing]:
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be at least 1")
        seen: set[str] = set()
        for page_number in range(1, max_pages + 1):
            page = await self.search_rentals(
                filters, page=page_number, per_page=per_page
            )
            for listing in page.listings:
                if listing.id in seen:
                    continue
                seen.add(listing.id)
                yield listing
                if max_results is not None and len(seen) >= max_results:
                    return
            if not page.listings or len(seen) >= page.total_count:
                return

    async def enrich(self, listing: Listing | str | int) -> RentalDetails:
        listing_id = listing.id if isinstance(listing, Listing) else listing
        return await self.rental_details(listing_id)

    async def enrich_all(
        self, listings: Iterable[Listing], *, concurrency: int = 3
    ) -> tuple[EnrichmentResult, ...]:
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        semaphore = asyncio.Semaphore(concurrency)

        async def one(listing: Listing) -> EnrichmentResult:
            async with semaphore:
                try:
                    return EnrichmentResult(listing, await self.enrich(listing))
                except StreetEasyError as exc:
                    return EnrichmentResult(listing, error=str(exc))

        return tuple(await asyncio.gather(*(one(item) for item in listings)))
