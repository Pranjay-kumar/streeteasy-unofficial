from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from .graphql import (
    ENDPOINT,
    build_rental_details_request,
    build_search_request,
    parse_rental_details_response,
    parse_search_response,
)
from .models import RentalDetails, SearchFilters, SearchPage

Transport = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class GraphQLResponseError(RuntimeError):
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
            raise GraphQLResponseError("Unexpected StreetEasy response shape") from exc

    async def rental_details(self, listing_id: str | int) -> RentalDetails:
        payload = await self._transport(
            ENDPOINT, build_rental_details_request(listing_id)
        )
        if payload.get("errors"):
            raise GraphQLResponseError(str(payload["errors"][0]))
        try:
            return parse_rental_details_response(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise GraphQLResponseError("Unexpected StreetEasy response shape") from exc
