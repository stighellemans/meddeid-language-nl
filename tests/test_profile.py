import pytest

from meddeid_language_nl import get_profile, lookup_manifest, lookup_source, lookup_values


def test_nl_be_profile_is_versioned_and_accepts_dutch_tags() -> None:
    profile = get_profile("nl-BE", version="1")
    profile.validate_language("nl")
    profile.validate_language("nl_BE")

    with pytest.raises(ValueError, match="incompatible"):
        profile.validate_language("fr-BE")


def test_lookup_provider_is_owned_by_language_package() -> None:
    assert len(lookup_values("first_names")) > 10_000
    assert len(lookup_values("family_names")) > 10_000
    assert lookup_source().startswith("meddeid-language-nl ")
    assert "belgian-deduce" not in lookup_source()


def test_profile_manifest_pins_every_resource_hash() -> None:
    profile = get_profile("nl-BE", version="1")
    manifest = profile.manifest()
    assert manifest["profile_id"] == "nl-BE"
    assert manifest["profile_version"] == "1"
    assert manifest["resources"] == lookup_manifest()
    assert profile.lookup_values("first_names") == lookup_values("first_names")
    assert all(
        len(resource["sha256"]) == 64 and resource["values"] > 0
        for resource in manifest["resources"]["resources"].values()
    )
