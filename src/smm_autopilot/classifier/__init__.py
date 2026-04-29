from __future__ import annotations


def __getattr__(name: str) -> object:
    if name == "ClassifierService":
        from smm_autopilot.classifier.service import ClassifierService

        return ClassifierService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ClassifierService"]
