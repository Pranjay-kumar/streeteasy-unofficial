from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .errors import StreetEasyError
from .events import (
    Event,
    ListingRemoved,
    ListingReturned,
    NewListing,
    PriceChanged,
    RunFailed,
)
from .models import Listing, SearchFilters


@dataclass(slots=True)
class Checkpoint:
    current: dict[str, Listing]
    seen_ids: set[str]


class StateStore(Protocol):
    def load(self, search_key: str) -> Checkpoint | None: ...
    def save(self, search_key: str, checkpoint: Checkpoint) -> None: ...


class Notifier(Protocol):
    def notify(self, event: Event) -> None: ...


class MemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, Checkpoint] = {}

    def load(self, search_key: str) -> Checkpoint | None:
        return self._items.get(search_key)

    def save(self, search_key: str, checkpoint: Checkpoint) -> None:
        self._items[search_key] = checkpoint


class JsonFileStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self, search_key: str) -> Checkpoint | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        item = payload.get(search_key)
        if not item:
            return None
        return Checkpoint(
            current={key: Listing(**value) for key, value in item["current"].items()},
            seen_ids=set(item["seen_ids"]),
        )

    def save(self, search_key: str, checkpoint: Checkpoint) -> None:
        payload = (
            json.loads(self.path.read_text(encoding="utf-8"))
            if self.path.exists()
            else {}
        )
        payload[search_key] = {
            "current": {
                key: asdict(value) for key, value in checkpoint.current.items()
            },
            "seen_ids": sorted(checkpoint.seen_ids),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.path)


class ConsoleNotifier:
    def notify(self, event: Event) -> None:
        print(f"[{event.occurred_at.isoformat()}] {type(event).__name__}: {event}")


class DesktopNotifier:
    def notify(self, event: Event) -> None:
        from .browser import _desktop_notice

        _desktop_notice(type(event).__name__, str(event))


def parse_interval(value: str | float) -> float:
    if isinstance(value, (int, float)):
        seconds = float(value)
    else:
        text = value.strip().lower()
        units = {"s": 1, "m": 60, "h": 3600}
        if not text or text[-1] not in units:
            raise ValueError("interval must end in s, m, or h")
        seconds = float(text[:-1]) * units[text[-1]]
    if seconds <= 0:
        raise ValueError("interval must be positive")
    return seconds


class Watch:
    def __init__(
        self,
        client,
        filters: SearchFilters,
        interval,
        store: StateStore,
        notifier: Notifier,
        *,
        search_key: str = "default",
        max_pages: int = 10,
        max_results: int | None = None,
    ) -> None:
        self.client = client
        self.filters = filters
        self.interval = parse_interval(interval)
        self.store = store
        self.notifier = notifier
        self.search_key = search_key
        self.max_pages = max_pages
        self.max_results = max_results
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def run_once(self) -> tuple[Event, ...]:
        if not self._lock.acquire(blocking=False):
            return ()
        try:
            listings = None
            last_error = None
            for attempt in range(3):
                try:
                    listings = tuple(
                        self.client.search_all(
                            self.filters,
                            max_pages=self.max_pages,
                            max_results=self.max_results,
                        )
                    )
                    break
                except StreetEasyError as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(2**attempt)
            if listings is None:
                event = RunFailed.now(self.search_key, message=str(last_error))
                self.notifier.notify(event)
                return (event,)

            previous = self.store.load(self.search_key)
            current = {item.id: item for item in listings}
            events: list[Event] = []
            if previous:
                for listing_id, listing in current.items():
                    old = previous.current.get(listing_id)
                    if old and old.price != listing.price:
                        events.append(
                            PriceChanged.now(
                                self.search_key,
                                listing=listing,
                                old_price=old.price,
                                new_price=listing.price,
                            )
                        )
                    elif not old and listing_id in previous.seen_ids:
                        events.append(
                            ListingReturned.now(self.search_key, listing=listing)
                        )
                    elif not old:
                        events.append(NewListing.now(self.search_key, listing=listing))
                for listing_id, listing in previous.current.items():
                    if listing_id not in current:
                        events.append(
                            ListingRemoved.now(self.search_key, listing=listing)
                        )
                seen = previous.seen_ids | current.keys()
            else:
                events.extend(
                    NewListing.now(self.search_key, listing=item) for item in listings
                )
                seen = set(current)
            self.store.save(
                self.search_key, Checkpoint(current=current, seen_ids=set(seen))
            )
            for event in events:
                self.notifier.notify(event)
            return tuple(events)
        finally:
            self._lock.release()

    def run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            self.run_once()
            remaining = max(0, self.interval - (time.monotonic() - started))
            self._stop.wait(remaining)

    def stop(self) -> None:
        self._stop.set()
