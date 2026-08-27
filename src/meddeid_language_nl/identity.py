"""Dutch language-profile identifiers."""

PROFILE_IDS = ("nl-BE", "nl-NL")


def normalize_profile_id(profile_id: str) -> str:
    normalized = profile_id.strip().replace("_", "-").lower()
    for available in PROFILE_IDS:
        if normalized == available.lower():
            return available
    raise ValueError(
        f"unsupported Dutch language profile {profile_id!r}; "
        f"available: {', '.join(PROFILE_IDS)}"
    )
