"""Portable capability descriptors shared with non-Python MedDeID tools."""

from __future__ import annotations

import json
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files

from .identity import normalize_profile_id


@lru_cache(maxsize=2)
def subannotation_capability_manifest(profile_id: str) -> dict:
    profile_id = normalize_profile_id(profile_id)
    path = files("meddeid_language_nl").joinpath(
        "resources", "subannotation", f"{profile_id}.json"
    )
    content = path.read_bytes()
    profile = json.loads(content)
    return {
        "contract_version": profile["contractVersion"],
        "profile_id": profile["profileId"],
        "ruleset_id": profile["rulesetId"],
        "runtime": "javascript",
        "package": profile["javascript"]["package"],
        "export": profile["javascript"]["export"],
        "profile_manifest_sha256": sha256(content).hexdigest(),
    }


def capability_manifest(profile_id: str) -> dict:
    return {"subannotation": subannotation_capability_manifest(profile_id)}
