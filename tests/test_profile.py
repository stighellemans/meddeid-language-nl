import pytest

from meddeid_language_nl import get_profile, lookup_manifest, lookup_source, lookup_values


@pytest.mark.parametrize("profile_id", ["nl-BE", "nl-NL"])
def test_explicit_dutch_profiles_resolve(profile_id: str) -> None:
    profile = get_profile(profile_id)
    profile.validate_language(profile_id.replace("-", "_"))
    assert profile.language_tags == (profile_id,)

    with pytest.raises(ValueError, match="incompatible"):
        profile.validate_language("nl")


@pytest.mark.parametrize("requested", ["nl", "NL", "nl-DE"])
def test_bare_or_unsupported_dutch_fails(requested: str) -> None:
    with pytest.raises(ValueError, match="nl-BE, nl-NL"):
        get_profile(requested)


def test_lookup_providers_are_profile_scoped() -> None:
    for profile_id in ("nl-BE", "nl-NL"):
        assert len(lookup_values(profile_id, "first_names")) > 10_000
        assert len(lookup_values(profile_id, "family_names")) > 10_000
        assert lookup_source(profile_id).endswith(f"{profile_id} lookup resources")
    assert "Gent" in lookup_values("nl-BE", "localities")
    assert "Amsterdam" in lookup_values("nl-NL", "localities")


@pytest.mark.parametrize("profile_id", ["nl-BE", "nl-NL"])
def test_profile_manifest_pins_every_resource_hash(profile_id: str) -> None:
    profile = get_profile(profile_id)
    manifest = profile.manifest()
    assert manifest["profile_id"] == profile_id
    assert manifest["resources"] == lookup_manifest(profile_id)
    capability = manifest["capabilities"]["subannotation"]
    assert capability["profile_id"] == profile_id
    assert capability["ruleset_id"] == f"core-pii-{profile_id.lower()}"
    assert len(capability["profile_manifest_sha256"]) == 64
    assert profile.lookup_values("first_names") == lookup_values(profile_id, "first_names")
    assert all(
        len(resource["sha256"]) == 64 and resource["values"] > 0
        for resource in manifest["resources"]["resources"].values()
    )
