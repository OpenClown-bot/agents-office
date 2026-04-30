from __future__ import annotations


def __getattr__(name: str) -> object:
    if name == "DraftGeneratorService":
        from smm_autopilot.drafting.service import DraftGeneratorService

        return DraftGeneratorService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["DraftGeneratorService"]
