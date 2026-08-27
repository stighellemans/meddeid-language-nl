"""Dutch language-profile registrations for Belgium and the Netherlands."""

from __future__ import annotations

from functools import partial

from meddeid_core.language import LanguageProfile

from .capabilities import capability_manifest
from .date_pseudonyms import birth_date_variants, date_replacement
from .identity import PROFILE_IDS, normalize_profile_id
from .lookups import lookup_categories, lookup_manifest, lookup_values
from .postprocess import post_process_spans


def _profile(profile_id: str) -> LanguageProfile:
    return LanguageProfile(
        profile_id=profile_id,
        language_tags=(profile_id,),
        post_process_spans=post_process_spans,
        lookup_categories_provider=partial(lookup_categories, profile_id),
        lookup_values_provider=partial(lookup_values, profile_id),
        resource_manifest_provider=partial(lookup_manifest, profile_id),
        capability_manifest_provider=partial(capability_manifest, profile_id),
        date_replacement_provider=date_replacement,
        birth_date_variants_provider=birth_date_variants,
    )


NL_BE = _profile("nl-BE")
NL_NL = _profile("nl-NL")
_PROFILES = {profile.profile_id.lower(): profile for profile in (NL_BE, NL_NL)}


def get_profile(profile_id: str) -> LanguageProfile:
    return _PROFILES[normalize_profile_id(profile_id).lower()]
