"""Portable capability descriptors shared with non-Python MedDeID tools."""

from __future__ import annotations

import json
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files


@lru_cache(maxsize=1)
def subannotation_capability_manifest() -> dict:
    path = files("meddeid_language_nl").joinpath(
        "resources", "subannotation", "profile.json"
    )
    content = path.read_bytes()
    profile = json.loads(content)
    return {
        "contract_version": profile["contractVersion"],
        "profile_id": profile["profileId"],
        "profile_version": profile["profileVersion"],
        "ruleset_id": profile["rulesetId"],
        "ruleset_version": profile["rulesetVersion"],
        "runtime": "javascript",
        "package": profile["javascript"]["package"],
        "export": profile["javascript"]["export"],
        "profile_manifest_sha256": sha256(content).hexdigest(),
    }


def capability_manifest() -> dict:
    return {"subannotation": subannotation_capability_manifest()}
