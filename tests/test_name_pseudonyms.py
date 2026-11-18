from concurrent.futures import ThreadPoolExecutor
import re
import unicodedata

import pytest

from meddeid_language_nl import get_profile, pseudonymize_name_text
from meddeid_language_nl.name_pseudonyms import catalog_id

KEY = bytes(range(32))
PROFILES = ("nl-BE", "nl-NL")


def alias(text, profile=PROFILES[0], scope="study-a"):
    return pseudonymize_name_text(text, key=KEY, scope=scope, profile_id=profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_names_are_stable_across_calls_threads_and_normalization(profile):
    expected = alias("Mark Peters", profile)
    assert expected and expected.startswith("[") and expected.endswith("]")
    assert "Mark" not in expected and "Peters" not in expected
    assert alias("  Mark   Peters ", profile) == expected
    assert alias("MARK PETERS", profile) == expected.upper()
    assert alias("mark peters", profile) == expected.lower()
    assert alias("M Peters", profile) == alias("M. Peters", profile).replace(".", "")
    assert alias("Zoë Verhulst", profile) == alias(
        unicodedata.normalize("NFD", "Zoë Verhulst"), profile
    )
    assert alias("Mark Peters", profile, "another-study") != expected
    with ThreadPoolExecutor(4) as workers:
        assert set(workers.map(lambda _: alias("Mark Peters", profile), range(40))) == {
            expected
        }
    assert (
        get_profile(profile).replace_name("Mark Peters", key=KEY, scope="study-a")
        == expected[1:-1]
    )
    assert len(catalog_id(profile)) == 64


@pytest.mark.parametrize("profile", PROFILES)
def test_title_initials_and_label_fallback(profile):
    plain = alias("Mark Peters", profile)
    assert alias("Dr. Mark Peters", profile) == "[Dr. " + plain[1:]
    assert re.fullmatch(r"\[[^\W\d_]\. .+\]", alias("M. Peters", profile))
    assert re.fullmatch(r"\[.+ [^\W\d_]\.\]", alias("Mark P.", profile))
    assert alias("M. Peters", profile) != plain
    assert alias("Mark P.", profile) != plain
    assert alias("?", profile) is None
    assert alias("<onbekend>", profile) is None
    assert alias("[Mark Peters]", profile) is None
    assert alias("A" * 201, profile) is None
    long_initials = alias("A." * 80, profile)
    assert long_initials is not None and len(long_initials) == 162


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Mark Peters", "[Sue-Ann Colen]"),
        ("M. Peters", "[B. Altuntas]"),
        ("Mark P.", "[Maïssara H.]"),
        ("Dr. Peters", "[Dr. Skyla]"),
        ("Anna Jacobs", "[Thorwald De Ridder]"),
        ("Zoë Verhulst", "[Hayke Leenaerts]"),
        ("dr. Linde", "[dr. Fljorim]"),
    ],
)
def test_uza_v1_output_is_unchanged(source, expected):
    assert alias(source) == expected
