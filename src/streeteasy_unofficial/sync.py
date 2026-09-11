from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

from .browser import HeadfulBrowserTransport
from .client import AsyncClient
from .models import EnrichmentResult, Listing, RentalDetails, SearchFilters, SearchPage
from .monitor import Notifier, StateStore, Watch


class StreetEasy:
    def __init__(
        self,
        *,
        start_url: str = "https://streeteasy.com/for-rent/nyc",
        profile_dir: str | Path = ".streeteasy-browser",
        verification_timeout: float = 600,
    ) -> None:
        self.start_url = start_url
        self.profile_dir = profile_dir
        self.verification_timeout = verification_timeout
        self._watch_notifier = None
        self._watch_key = "default"

    def _browser_notice(self, title: str, message: str) -> None:
        from .browser import _desktop_notice
        from .events import VerificationRequired

        _desktop_notice(title, message)
        if "needs your attention" in title.lower() and self._watch_notifier:
            self._watch_notifier.notify(
                VerificationRequired.now(self._watch_key, message=message)
            )

    def _run(self, operation):
        async def execute():
            async with HeadfulBrowserTransport(
                start_url=self.start_url,
                profile_dir=self.profile_dir,
                verification_timeout=self.verification_timeout,
                notify=self._browser_notice,
            ) as transport:
                return await operation(AsyncClient(transport))

        return asyncio.run(execute())

    def search(
        self, filters: SearchFilters, *, page: int = 1, per_page: int = 100
    ) -> SearchPage:
        return self._run(
            lambda client: client.search_rentals(filters, page=page, per_page=per_page)
        )

    def search_all(
        self,
        filters: SearchFilters,
        *,
        per_page: int = 100,
        max_pages: int = 10,
        max_results: int | None = None,
    ) -> Iterator[Listing]:
        async def collect(client):
            return [
                item
                async for item in client.search_all(
                    filters,
                    per_page=per_page,
                    max_pages=max_pages,
                    max_results=max_results,
                )
            ]

        return iter(self._run(collect))

    def enrich(self, listing: Listing | str | int) -> RentalDetails:
        return self._run(lambda client: client.enrich(listing))

    def enrich_all(
        self, listings, *, concurrency: int = 3
    ) -> tuple[EnrichmentResult, ...]:
        return self._run(
            lambda client: client.enrich_all(listings, concurrency=concurrency)
        )

    def watch(
        self,
        *,
        filters: SearchFilters,
        interval: str | float,
        store: StateStore,
        notifier: Notifier,
        search_key: str = "default",
        max_pages: int = 10,
        max_results: int | None = None,
    ) -> Watch:
        self._watch_notifier = notifier
        self._watch_key = search_key
        return Watch(
            self,
            filters,
            interval,
            store,
            notifier,
            search_key=search_key,
            max_pages=max_pages,
            max_results=max_results,
        )
