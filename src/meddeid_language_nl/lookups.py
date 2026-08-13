"""Stable access to the lookup resources owned by the ``nl-BE`` profile."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from importlib.resources import files


LOOKUP_FILES = {
    "first_names": "first_names.txt",
    "family_names": "family_names.txt",
    "prefixes": "prefixes.txt",
    "interfixes": "interfixes.txt",
    "interfix_surnames": "interfix_surnames.txt",
    "streets": "streets.txt",
    "localities": "localities.txt",
    "postal_localities": "postal_localities.txt",
    "postal_code_localities": "postal_code_localities.txt",
    "hospitals": "hospitals.txt",
    "healthcare_institutions": "healthcare_institutions.txt",
}


def lookup_categories() -> tuple[str, ...]:
    return tuple(LOOKUP_FILES)


@lru_cache(maxsize=None)
def lookup_values(category: str) -> tuple[str, ...]:
    try:
        filename = LOOKUP_FILES[category]
    except KeyError as exc:
        supported = ", ".join(lookup_categories())
        raise KeyError(
            f"unknown nl-BE lookup category {category!r}; expected one of: {supported}"
        ) from exc

    path = files("meddeid_language_nl").joinpath("resources", "lookup", filename)
    values = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not values:
        raise RuntimeError(f"packaged nl-BE lookup is empty: {category}")
    return values


def lookup_source() -> str:
    return "meddeid-language-nl 0.1.0 nl-BE lookup resources"


@lru_cache(maxsize=1)
def lookup_manifest() -> dict:
    """Return immutable-release facts for every packaged lookup resource."""

    resources = {}
    root = files("meddeid_language_nl").joinpath("resources", "lookup")
    for category, filename in LOOKUP_FILES.items():
        content = root.joinpath(filename).read_bytes()
        resources[category] = {
            "filename": filename,
            "sha256": sha256(content).hexdigest(),
            "values": len(lookup_values(category)),
        }
    notice = root.joinpath("SOURCES.md").read_bytes()
    return {
        "manifest_version": "meddeid.language-resources.v1",
        "package": "meddeid-language-nl",
        "package_version": "0.1.0",
        "profile_id": "nl-BE",
        "resources": resources,
        "provenance": {
            "filename": "SOURCES.md",
            "sha256": sha256(notice).hexdigest(),
        },
    }
