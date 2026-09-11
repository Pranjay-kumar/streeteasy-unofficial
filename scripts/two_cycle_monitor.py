"""Offline two-cycle example showing new, changed, and removed events."""

from streeteasy_unofficial import ConsoleNotifier, Listing, MemoryStore, SearchFilters
from streeteasy_unofficial.monitor import Watch


class DemoClient:
    def __init__(self):
        self.cycles = iter(
            [
                [Listing("a", "https://streeteasy.com/a", 3000)],
                [
                    Listing("a", "https://streeteasy.com/a", 2850),
                    Listing("b", "https://streeteasy.com/b", 2950),
                ],
            ]
        )

    def search_all(self, *args, **kwargs):
        return iter(next(self.cycles))


watch = Watch(DemoClient(), SearchFilters(), "2h", MemoryStore(), ConsoleNotifier())
watch.run_once()
watch.run_once()
