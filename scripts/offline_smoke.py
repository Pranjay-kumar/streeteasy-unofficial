"""Verify request construction and parsing without contacting StreetEasy."""

import asyncio

from streeteasy_unofficial import AsyncClient, SearchFilters


async def main() -> None:
    async def fake_transport(endpoint, request):
        assert endpoint == "https://api-v6.streeteasy.com/"
        assert request["variables"]["input"]["filters"]["areas"] == [400]
        return {
            "data": {
                "searchRentals": {
                    "totalCount": 1,
                    "edges": [
                        {
                            "node": {
                                "id": "demo-1",
                                "urlPath": "/building/example/1",
                                "price": 2950,
                                "street": "Example Street",
                                "unit": "1A",
                                "areaName": "Astoria",
                                "bedroomCount": 1,
                                "fullBathroomCount": 1,
                                "halfBathroomCount": 0,
                                "geoPoint": {
                                    "latitude": 40.7644,
                                    "longitude": -73.9235,
                                },
                            }
                        }
                    ],
                }
            }
        }

    page = await AsyncClient(fake_transport).search_rentals(
        SearchFilters(area_ids=(400,), max_price=3000, bedrooms=(1,)),
        per_page=5,
    )
    assert page.total_count == 1
    assert page.listings[0].price == 2950
    print("Offline smoke test passed")


if __name__ == "__main__":
    asyncio.run(main())
