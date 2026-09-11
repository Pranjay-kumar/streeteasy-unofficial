from __future__ import annotations

import json
from collections.abc import Sequence
from functools import lru_cache
from importlib.resources import files


class UnknownAreaError(ValueError):
    pass


@lru_cache(maxsize=1)
def area_catalog() -> dict[str, int]:
    resource = files("streeteasy_unofficial").joinpath("data/areas.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    return dict(payload["areas"])


def find_areas(query: str = "") -> tuple[tuple[str, int], ...]:
    needle = query.strip().casefold()
    return tuple(
        sorted(
            (
                (name, area_id)
                for name, area_id in area_catalog().items()
                if needle in name.casefold()
            ),
            key=lambda item: item[0].casefold(),
        )
    )


def resolve_areas(names: Sequence[str]) -> tuple[int, ...]:
    lookup = {name.casefold(): area_id for name, area_id in area_catalog().items()}
    resolved = []
    for name in names:
        try:
            resolved.append(lookup[name.strip().casefold()])
        except KeyError as exc:
            matches = ", ".join(item[0] for item in find_areas(name)) or "none"
            raise UnknownAreaError(
                f"Unknown area {name!r}; close matches: {matches}"
            ) from exc
    return tuple(resolved)
