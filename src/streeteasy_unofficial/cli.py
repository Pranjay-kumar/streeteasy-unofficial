from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

from . import __version__
from .areas import find_areas
from .models import SearchFilters
from .monitor import ConsoleNotifier, JsonFileStore
from .sync import StreetEasy


def _filters(values: argparse.Namespace) -> SearchFilters:
    return SearchFilters(
        neighborhoods=tuple(getattr(values, "neighborhood", ()) or ()),
        max_price=getattr(values, "max_price", None),
        bedrooms=tuple(getattr(values, "bedrooms", ()) or ()),
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="streeteasy")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search", help="Run a visible-Chrome rental search")
    search.add_argument("--neighborhood", action="append", default=[])
    search.add_argument("--max-price", type=int)
    search.add_argument("--bedrooms", action="append", type=float, default=[])
    search.add_argument("--max-results", type=int, default=20)

    enrich = commands.add_parser("enrich", help="Fetch details for one rental")
    enrich.add_argument("listing_id")

    areas = commands.add_parser("areas", help="Find bundled StreetEasy area IDs")
    areas.add_argument("query", nargs="?", default="")

    watch = commands.add_parser("watch", help="Run a monitor from TOML configuration")
    watch.add_argument("--config", type=Path, required=True)

    commands.add_parser("doctor", help="Check local runtime requirements")
    return root


def _client(config: dict | None = None) -> StreetEasy:
    config = config or {}
    return StreetEasy(
        start_url=config.get("start_url", "https://streeteasy.com/for-rent/nyc"),
        profile_dir=config.get("profile_dir", ".streeteasy-browser"),
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "areas":
        for name, area_id in find_areas(args.query):
            print(f"{area_id}\t{name}")
        return 0
    if args.command == "doctor":
        chrome = shutil.which("chrome") or shutil.which("google-chrome")
        try:
            import patchright  # noqa: F401

            browser_support = True
        except ImportError:
            browser_support = False
        print(f"Python: {sys.version.split()[0]}")
        print(f"Browser extra: {'ok' if browser_support else 'missing'}")
        print(
            f"Chrome on PATH: {chrome or 'not found (Patchright may still locate it)'}"
        )
        return int(not browser_support)
    if args.command == "search":
        listings = _client().search_all(_filters(args), max_results=args.max_results)
        for listing in listings:
            print(f"${listing.price:,}\t{listing.area_name}\t{listing.url}")
        return 0
    if args.command == "enrich":
        details = _client().enrich(args.listing_id)
        print(details)
        return 0
    if args.command == "watch":
        config = tomllib.loads(args.config.read_text(encoding="utf-8"))
        search = config.get("search", {})
        monitor = config.get("monitor", {})
        client = _client(config.get("browser"))
        watch = client.watch(
            filters=SearchFilters(
                neighborhoods=tuple(search.get("neighborhoods", ())),
                max_price=search.get("max_price"),
                bedrooms=tuple(search.get("bedrooms", ())),
            ),
            interval=monitor.get("interval", "2h"),
            store=JsonFileStore(monitor.get("state_file", ".streeteasy-state.json")),
            notifier=ConsoleNotifier(),
            search_key=monitor.get("search_key", "default"),
            max_pages=monitor.get("max_pages", 10),
            max_results=monitor.get("max_results"),
        )
        watch.run()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
