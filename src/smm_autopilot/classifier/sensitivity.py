from __future__ import annotations

from smm_autopilot.db import Database


async def load_sensitivity_keywords(db: Database) -> list[str]:
    rows = await db.execute_read("SELECT keyword FROM sensitivity_keyword")
    return [row["keyword"] for row in rows]


def check_sensitivity(body: str, keywords: list[str]) -> bool:
    lower_body = body.lower()
    for keyword in keywords:
        if keyword.lower() in lower_body:
            return True
    return False
