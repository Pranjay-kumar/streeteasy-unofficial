import asyncio

from streeteasy_unofficial import (
    AsyncClient,
    JsonFileStore,
    Listing,
    ListingRemoved,
    ListingReturned,
    MemoryStore,
    NewListing,
    PriceChanged,
    RunFailed,
    SearchFilters,
    StreetEasyError,
    media_url,
)
from streeteasy_unofficial.areas import UnknownAreaError, find_areas
from streeteasy_unofficial.monitor import Watch, parse_interval


def listing(identifier: str, price: int) -> Listing:
    return Listing(identifier, f"https://streeteasy.com/{identifier}", price)


def test_area_resolution_and_media_urls():
    assert SearchFilters(neighborhoods=("Astoria", "sunnyside")).to_graphql()[
        "areas"
    ] == [401, 403]
    island_matches = dict(find_areas("island"))
    assert island_matches["Long Island City"] == 402
    assert island_matches["Staten Island"] == 500
    assert media_url("abc").endswith("/abc-se_large_800_400.jpg")
    try:
        SearchFilters(neighborhoods=("Atlantis",)).to_graphql()
    except UnknownAreaError as exc:
        assert "Atlantis" in str(exc)
    else:
        raise AssertionError("unknown area should fail")


def test_search_all_paginates_and_deduplicates():
    calls = []

    async def transport(endpoint, body):
        page = body["variables"]["input"]["page"]
        calls.append(page)
        nodes = {
            1: [listing("a", 1), listing("b", 2)],
            2: [listing("b", 2), listing("c", 3)],
        }[page]
        return {
            "data": {
                "searchRentals": {
                    "totalCount": 3,
                    "edges": [
                        {
                            "node": {
                                "id": item.id,
                                "urlPath": f"/{item.id}",
                                "price": item.price,
                            }
                        }
                        for item in nodes
                    ],
                }
            }
        }

    async def collect():
        return [
            item.id
            async for item in AsyncClient(transport).search_all(
                SearchFilters(), per_page=2
            )
        ]

    assert asyncio.run(collect()) == ["a", "b", "c"]
    assert calls == [1, 2]


class Recorder:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


class SequenceClient:
    def __init__(self, results):
        self.results = iter(results)

    def search_all(self, *args, **kwargs):
        return iter(next(self.results))


def test_monitor_event_transitions_and_checkpointing():
    first = [listing("a", 3000), listing("b", 2500)]
    second = [listing("a", 2800), listing("c", 2400)]
    third = [listing("a", 2800), listing("b", 2500), listing("c", 2400)]
    recorder = Recorder()
    watch = Watch(
        SequenceClient([first, second, third]),
        SearchFilters(),
        "2h",
        MemoryStore(),
        recorder,
    )
    assert all(isinstance(item, NewListing) for item in watch.run_once())
    events = watch.run_once()
    assert any(isinstance(item, PriceChanged) for item in events)
    assert any(isinstance(item, ListingRemoved) for item in events)
    assert any(
        isinstance(item, NewListing) and item.listing.id == "c" for item in events
    )
    assert any(isinstance(item, ListingReturned) for item in watch.run_once())


def test_intervals():
    assert parse_interval("2h") == 7200
    assert parse_interval("30m") == 1800


def test_json_store_round_trip(tmp_path):
    from streeteasy_unofficial.monitor import Checkpoint

    store = JsonFileStore(tmp_path / "state.json")
    item = listing("saved", 2700)
    store.save("search", Checkpoint({item.id: item}, {item.id}))
    restored = store.load("search")
    assert restored.current["saved"].price == 2700
    assert restored.seen_ids == {"saved"}


def test_enrichment_keeps_individual_failures():
    async def transport(endpoint, body):
        listing_id = body["variables"]["listingID"]
        if listing_id == "bad":
            return {"errors": [{"message": "detail unavailable"}]}
        return {
            "data": {
                "rentalByListingId": {"id": listing_id},
                "buildingByRentalListingId": None,
                "getBuildingExpressByRentalListingId": None,
            }
        }

    items = [listing("good", 1), listing("bad", 2)]
    results = asyncio.run(AsyncClient(transport).enrich_all(items, concurrency=2))
    assert results[0].details.id == "good"
    assert results[1].details is None
    assert "detail unavailable" in results[1].error


def test_failed_monitor_run_does_not_replace_checkpoint():
    class BrokenClient:
        def search_all(self, *args, **kwargs):
            raise StreetEasyError("temporary failure")

    store = MemoryStore()
    original = listing("still-current", 2500)
    from streeteasy_unofficial.monitor import Checkpoint

    store.save("default", Checkpoint({original.id: original}, {original.id}))
    recorder = Recorder()
    events = Watch(BrokenClient(), SearchFilters(), 0.001, store, recorder).run_once()
    assert isinstance(events[0], RunFailed)
    assert store.load("default").current == {original.id: original}
