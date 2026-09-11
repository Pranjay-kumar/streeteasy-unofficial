"""Minimal caller-owned persistence and notification adapters."""

from streeteasy_unofficial import Event, MemoryStore


class MyStore(MemoryStore):
    """Replace load/save with database calls in an application."""


class MyNotifier:
    def notify(self, event: Event) -> None:
        # Replace this with email, Slack, a webhook, or an application event bus.
        print(type(event).__name__, event)


store = MyStore()
notifier = MyNotifier()
