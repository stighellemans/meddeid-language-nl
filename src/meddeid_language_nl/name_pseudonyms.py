"""Stable name aliases from the installed nl locale resources."""

from functools import lru_cache

from meddeid_core.name_boundaries import protect_name_boundaries
from meddeid_core.name_components import ComponentCatalog, configuration

from .identity import normalize_profile_id
from .lookups import lookup_values


@lru_cache(maxsize=2)
def _catalog(profile_id: str) -> ComponentCatalog:
    return ComponentCatalog(
        lookup_values(profile_id, "first_names"),
        lookup_values(profile_id, "family_names"),
        prefixes=lookup_values(profile_id, "prefixes"),
        surname_particles=lookup_values(profile_id, "interfixes"),
    )


_CLINICAL_LABELS = frozenset("patiënt patiënte patient patienten patiënten arts dokter contactpersoon ondergetekende naam".split())


def protect_boundaries(text, spans, *, profile_id, selected_labels=None):
    return protect_name_boundaries(text, spans, _catalog(normalize_profile_id(profile_id)),
                                   selected_labels, _CLINICAL_LABELS)


def catalog_id(profile_id: str = "nl-BE") -> str:
    return _catalog(normalize_profile_id(profile_id)).catalog_id()


def name_replacement(
    text: str, *, key: bytes, scope: str, profile_id: str = "nl-BE"
) -> str | None:
    """Return an alias body without brackets, or None for a label fallback."""
    return _catalog(normalize_profile_id(profile_id)).replace(
        text, key=key, scope=scope
    )


def pseudonymize_name_text(
    text: str,
    *,
    key: bytes | None = None,
    scope: str | None = None,
    profile_id: str = "nl-BE",
) -> str | None:
    """Return a bracketed alias; use the original label when this returns None."""
    key, scope = configuration(key, scope)
    body = name_replacement(text, key=key, scope=scope, profile_id=profile_id)
    return None if body is None else "[" + body + "]"
