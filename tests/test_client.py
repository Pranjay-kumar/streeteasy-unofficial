import asyncio

import pytest

from streeteasy_unofficial import (
    AsyncClient,
    GraphQLResponseError,
    HeadfulBrowserTransport,
    SearchFilters,
)
from streeteasy_unofficial.graphql import build_search_request


def test_filter_request_shape_and_bounds():
    filters = SearchFilters(
        area_ids=(100, 100), min_price=2000, max_price=3500, bedrooms=(0, 1)
    )
    request = build_search_request(filters, page=2, per_page=50)
    search = request["variables"]["input"]
    assert search["page"] == 2
    assert search["perPage"] == 50
    assert search["filters"] == {
        "rentalStatus": "ACTIVE",
        "areas": [100],
        "price": {"lowerBound": 2000, "upperBound": 3500},
        "bedrooms": {"minimum": 0, "maximum": 1},
    }
    with pytest.raises(ValueError):
        build_search_request(filters, per_page=501)


def test_client_parses_and_deduplicates():
    payload = {
        "data": {
            "searchRentals": {
                "totalCount": 1,
                "edges": [
                    {
                        "node": {
                            "id": "123",
                            "urlPath": "/building/example/1",
                            "price": 2995,
                            "street": "Example Street",
                            "unit": "1",
                            "areaName": "Astoria",
                            "bedroomCount": 1,
                            "fullBathroomCount": 1,
                            "halfBathroomCount": 1,
                            "geoPoint": {"latitude": 40.7, "longitude": -73.9},
                        }
                    },
                    {"node": {"id": "123", "urlPath": "/duplicate", "price": 1}},
                ],
            }
        }
    }

    async def transport(endpoint, body):
        assert endpoint == "https://api-v6.streeteasy.com/"
        assert "GetListingRental" in body["query"]
        return payload

    page = asyncio.run(
        AsyncClient(transport).search_rentals(SearchFilters(), per_page=10)
    )
    assert page.total_count == 1
    assert len(page.listings) == 1
    assert page.listings[0].bathrooms == 1.5


def test_graphql_errors_are_explicit():
    async def transport(endpoint, body):
        return {"errors": [{"message": "nope"}]}

    with pytest.raises(GraphQLResponseError, match="nope"):
        asyncio.run(AsyncClient(transport).search_rentals(SearchFilters()))


def test_visible_transport_notifies_and_waits_for_a_person():
    notices = []

    class Locator:
        def __init__(self, page, selector):
            self.page = page
            self.selector = selector

        async def count(self):
            if self.selector == "#px-captcha":
                self.page.checks += 1
                return int(self.page.checks == 1)
            return 0

        async def inner_text(self):
            return ""

    class Page:
        checks = 0

        def locator(self, selector):
            return Locator(self, selector)

        async def bring_to_front(self):
            return None

    transport = HeadfulBrowserTransport(
        start_url="https://streeteasy.com/",
        verification_timeout=3,
        notify=lambda title, message: notices.append((title, message)),
    )
    transport._page = Page()
    asyncio.run(transport._wait_for_human_if_needed())
    assert [title for title, _ in notices] == [
        "StreetEasy needs your attention",
        "StreetEasy verification complete",
    ]
