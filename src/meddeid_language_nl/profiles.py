"""Versioned language-profile contract used by model bundles and data tools."""

from __future__ import annotations

from meddeid_core.language import LanguageProfile

from .capabilities import capability_manifest
from .lookups import lookup_categories, lookup_manifest, lookup_values
from .postprocess import post_process_spans


NL_BE = LanguageProfile(
    profile_id="nl-BE",
    version="1",
    language_tags=("nl", "nl-BE"),
    post_process_spans=post_process_spans,
    lookup_categories_provider=lookup_categories,
    lookup_values_provider=lookup_values,
    resource_manifest_provider=lookup_manifest,
    capability_manifest_provider=capability_manifest,
)

_PROFILES = {(NL_BE.profile_id.lower(), NL_BE.version): NL_BE}


def get_profile(profile_id: str, *, version: str) -> LanguageProfile:
    try:
        return _PROFILES[(profile_id.strip().lower(), str(version))]
    except KeyError as exc:
        available = ", ".join(
            f"{profile.profile_id}@{profile.version}" for profile in _PROFILES.values()
        )
        raise ValueError(
            f"unsupported Dutch language profile {profile_id!r}@{version}; "
            f"available: {available}"
        ) from exc
