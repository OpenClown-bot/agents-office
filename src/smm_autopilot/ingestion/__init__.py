from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class FetchedItem:
    external_id: str
    title: Optional[str]
    body: str
    url: Optional[str]
    image_url: Optional[str]
    published_at: Optional[str]


def __getattr__(name: str) -> object:
    if name == "SourceIngester":
        from smm_autopilot.ingestion.service import SourceIngester

        return SourceIngester
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SourceIngester", "FetchedItem"]
