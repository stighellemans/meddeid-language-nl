"""Stable access to profile-scoped Dutch lookup resources."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files

from .identity import normalize_profile_id


COMMON_LOOKUP_FILES = {
    "first_names": "first_names.txt",
    "family_names": "family_names.txt",
    "prefixes": "prefixes.txt",
    "interfixes": "interfixes.txt",
    "interfix_surnames": "interfix_surnames.txt",
    "streets": "streets.txt",
    "localities": "localities.txt",
    "hospitals": "hospitals.txt",
    "healthcare_institutions": "healthcare_institutions.txt",
}
LOOKUP_FILES = {
    "nl-BE": {
        **COMMON_LOOKUP_FILES,
        "postal_localities": "postal_localities.txt",
        "postal_code_localities": "postal_code_localities.txt",
    },
    "nl-NL": COMMON_LOOKUP_FILES,
}


def lookup_categories(profile_id: str) -> tuple[str, ...]:
    profile_id = normalize_profile_id(profile_id)
    return tuple(LOOKUP_FILES[profile_id])


@lru_cache(maxsize=None)
def lookup_values(profile_id: str, category: str) -> tuple[str, ...]:
    profile_id = normalize_profile_id(profile_id)
    try:
        filename = LOOKUP_FILES[profile_id][category]
    except KeyError as exc:
        supported = ", ".join(lookup_categories(profile_id))
        raise KeyError(
            f"unknown {profile_id} lookup category {category!r}; "
            f"expected one of: {supported}"
        ) from exc

    path = files("meddeid_language_nl").joinpath(
        "resources", profile_id, "lookup", filename
    )
    values = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not values:
        raise RuntimeError(f"packaged {profile_id} lookup is empty: {category}")
    return values


def lookup_source(profile_id: str) -> str:
    profile_id = normalize_profile_id(profile_id)
    return f"meddeid-language-nl 0.2.1 {profile_id} lookup resources"


@lru_cache(maxsize=2)
def lookup_manifest(profile_id: str) -> dict:
    """Return immutable release facts for a profile's packaged resources."""

    profile_id = normalize_profile_id(profile_id)
    resources = {}
    root = files("meddeid_language_nl").joinpath("resources", profile_id, "lookup")
    for category, filename in LOOKUP_FILES[profile_id].items():
        content = root.joinpath(filename).read_bytes()
        resources[category] = {
            "filename": filename,
            "sha256": sha256(content).hexdigest(),
            "values": len(lookup_values(profile_id, category)),
        }
    notice = root.joinpath("SOURCES.md").read_bytes()
    provenance = {
        "filename": "SOURCES.md",
        "sha256": sha256(notice).hexdigest(),
    }
    upstream_license = root.joinpath("DEDUCE-LICENSE.md")
    if upstream_license.is_file():
        provenance["upstream_license_filename"] = "DEDUCE-LICENSE.md"
        provenance["upstream_license_sha256"] = sha256(
            upstream_license.read_bytes()
        ).hexdigest()
    return {
        "manifest_version": "meddeid.language-resources.v1",
        "package": "meddeid-language-nl",
        "package_version": "0.2.1",
        "profile_id": profile_id,
        "resources": resources,
        "provenance": provenance,
    }


def manifests() -> dict[str, dict]:
    return {profile_id: lookup_manifest(profile_id) for profile_id in LOOKUP_FILES}
