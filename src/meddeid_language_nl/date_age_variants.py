"""High-cardinality date and age formatting helpers.

The generator intentionally keeps the underlying clinical case stable while
varying how dates and ages are written.  The posthoc diversifier uses the same
helpers so old rendered datasets can be rewritten without losing annotation
offset integrity.
"""

from __future__ import annotations

import calendar
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from datetime import timedelta


DUTCH_MONTHS_FULL = [
    "januari",
    "februari",
    "maart",
    "april",
    "mei",
    "juni",
    "juli",
    "augustus",
    "september",
    "oktober",
    "november",
    "december",
]
DUTCH_MONTHS_ABBR = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
DUTCH_WEEKDAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
DUTCH_WEEKDAYS_ABBR = ["ma", "di", "wo", "do", "vr", "za", "zo"]

MONTH_ALIASES: dict[str, int] = {}
for position, (full, abbr) in enumerate(zip(DUTCH_MONTHS_FULL, DUTCH_MONTHS_ABBR), start=1):
    MONTH_ALIASES[full] = position
    MONTH_ALIASES[abbr] = position
    MONTH_ALIASES[f"{abbr}."] = position
MONTH_ALIASES.update({"sept": 9, "sept.": 9})

ROMAN_MONTHS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
for position, roman_month in enumerate(ROMAN_MONTHS, start=1):
    MONTH_ALIASES[roman_month.lower()] = position


RELATIVE_DATE_RE = re.compile(
    r"""(?ix)
    ^
    (?:
        (?:volgende|vorige)\s+(?:week|maand|jaar)
        | over\s+(?:enkele|\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:tot\s*\d+\s*)?
            (?:uur|uren|dag(?:en)?|werkdagen|week|weken|maand(?:en)?|jaar)
        | binnen\s+(?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s*
            (?:tot\s*\d+\s*)?(?:uur|uren|dag(?:en)?|werkdagen|week|weken|maand(?:en)?|jaar)
        | (?:uiterlijk\s+binnen|ten\s+laatste\s+over|na|voor|gedurende|tijdens\s+de\s+komende|voor\s+een\s+periode\s+van|nog|de\s+eerste)\s+
            (?:(?:een\s+)?half|\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:uur|uren|dag(?:en)?|werkdagen|week|weken|maand(?:en)?|jaar)
        | (?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:uur|uren|dag(?:en)?|werkdagen|week|weken|maand(?:en)?|jaar)\s+lang
        | tot\s+over\s+(?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:uur|uren|dag(?:en)?|werkdagen|week|weken|maand(?:en)?|jaar)
        | (?:tegen\s+eind|in\s+de\s+loop\s+van)\s+(?:deze|volgende)\s+(?:week|maand|jaar)
        | voor\s+het\s+einde\s+van\s+de\s+(?:week|maand)
        | (?:de\s+afgelopen|laatste|voorbije|in\s+de\s+voorbije|sinds|al|reeds)\s+
            (?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:uur|uren|dag(?:en)?|week|weken|maand(?:en)?|jaar)
        | sinds\s+(?:vorige|deze)\s+(?:week|maand|jaar)
        | om\s+de\s+andere\s+week
        | om\s+de\s+(?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:dag(?:en)?|week|weken|maand(?:en)?|jaar)
        | elke\s+(?:\d+|een|twee|drie|vier|vijf|zes|zeven|acht|negen|tien)\s+
            (?:dag(?:en)?|week|weken|maand(?:en)?|jaar)
        | \d+\s*-\s*(?:daags|wekelijks|maandelijks|jaarlijks)
        | (?:tweewekelijks|driewekelijks|maandelijks|driemaandelijks|halfjaarlijks|jaarlijks)
        | (?:zwangerschapsduur|amenorroeduur|graviditeitsduur|termijn|GA|PML)\s+
            \d{1,2}\s*w\s*\d\s*d
        | (?:AD|GA)\s+\d{1,2}\s*\+\s*\d\s*weken
        | graviditeitsduur\s+\d{1,2}\s+weken\s+en\s+\d\s+dagen
        | \d{1,2}\s+weken\s+\d\s+dagen\s+zwanger
        | \d{1,2}\s+\d\s*/\s*7\s+weken
    )
    $
    """
)


@dataclass(frozen=True)
class ParsedDate:
    value: date
    precision: str = "day"
    had_degree_prefix: bool = False


def stable_index(key: str, modulo: int) -> int:
    if modulo <= 0:
        raise ValueError("modulo must be positive")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def deterministic_index(*parts: object, modulo: int) -> int:
    return stable_index("|".join(str(part) for part in parts), modulo)


def sample_encounter_date(rng, start_year: int = 2010, end_year: int = 2030) -> date:
    """Sample across full calendar years, including 29/30/31 day months."""

    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def birthdate_for_age(rng, age: int, encounter_date: date) -> date:
    month = rng.randrange(1, 13)
    day = rng.randrange(1, calendar.monthrange(encounter_date.year, month)[1] + 1)
    birth_year = encounter_date.year - age
    if (month, day) > (encounter_date.month, encounter_date.day):
        birth_year -= 1
    day = min(day, calendar.monthrange(birth_year, month)[1])
    return date(birth_year, month, day)


def birthdate_days_before(encounter_date: date, days: int) -> date:
    return encounter_date - timedelta(days=max(0, days))


def birthdate_weeks_before(rng, encounter_date: date, weeks: int) -> date:
    extra_days = rng.randrange(0, 7)
    return birthdate_days_before(encounter_date, weeks * 7 + extra_days)


def birthdate_months_before(rng, encounter_date: date, months: int) -> date:
    month = encounter_date.month - months
    year = encounter_date.year
    while month <= 0:
        month += 12
        year -= 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(encounter_date.day, max_day)
    day = max(1, day - rng.randrange(0, min(4, day)))
    return date(year, month, day)


def _month_token(month: int, variant: int) -> str:
    style = variant % 6
    if style == 0:
        return DUTCH_MONTHS_FULL[month - 1]
    if style == 1:
        return DUTCH_MONTHS_ABBR[month - 1]
    if style == 2:
        abbr = DUTCH_MONTHS_ABBR[month - 1]
        return abbr if abbr == "mei" else f"{abbr}."
    if style == 3:
        return DUTCH_MONTHS_FULL[month - 1].capitalize()
    if style == 4:
        return DUTCH_MONTHS_ABBR[month - 1].upper()
    return ROMAN_MONTHS[month - 1]


def _year_token(year: int, variant: int, *, prefer_four_digit: bool = False) -> str:
    if prefer_four_digit:
        styles = ["yyyy", "yyyy", "yyyy", "yy", "apostrophe_yy"]
    else:
        styles = ["yyyy", "yy", "apostrophe_yy"]
    style = styles[variant % len(styles)]
    if style == "yy":
        return f"{year % 100:02d}"
    if style == "apostrophe_yy":
        return f"'{year % 100:02d}"
    return str(year)


def _day_token(day: int, variant: int) -> str:
    styles = ["plain", "zero"]
    style = styles[variant % len(styles)]
    if style == "zero":
        return f"{day:02d}"
    return str(day)


def _numeric_date(value: date, variant: int, *, allow_ymd: bool = True) -> str:
    separators = ["/", "-", "."]
    separator = separators[variant % len(separators)]
    variant //= len(separators)
    day = f"{value.day:02d}" if variant % 2 else str(value.day)
    variant //= 2
    month = f"{value.month:02d}" if variant % 2 else str(value.month)
    variant //= 2
    year_styles = ["yyyy", "yyyy", "yy"]
    year = str(value.year) if year_styles[variant % len(year_styles)] == "yyyy" else f"{value.year % 100:02d}"
    return separator.join([day, month, year])


def _postprocess_month_token(month: int, variant: int) -> str:
    """Dutch month spellings accepted by the downstream post-process regexes."""

    styles = ["full", "full_capitalized", "abbr", "abbr_dot"]
    style = styles[variant % len(styles)]
    if style == "full":
        return DUTCH_MONTHS_FULL[month - 1]
    if style == "full_capitalized":
        return DUTCH_MONTHS_FULL[month - 1].capitalize()
    abbr = DUTCH_MONTHS_ABBR[month - 1]
    if style == "abbr_dot" and abbr != "mei":
        return f"{abbr}."
    return abbr


def _postprocess_year_token(year: int, variant: int) -> str:
    styles = ["yyyy", "yyyy", "yy", "apostrophe_yy"]
    style = styles[variant % len(styles)]
    if style == "apostrophe_yy":
        return f"'{year % 100:02d}"
    return str(year) if style == "yyyy" else f"{year % 100:02d}"


def _postprocess_textual_dmy(value: date, variant: int, *, hyphenated: bool = False) -> str:
    day = f"{value.day:02d}" if variant % 2 else str(value.day)
    variant //= 2
    month = _postprocess_month_token(value.month, variant)
    variant //= 4
    year = _postprocess_year_token(value.year, variant)
    separator = "-" if hyphenated else " "
    return separator.join([day, month, year])


def _postprocess_day_month(value: date, variant: int) -> str:
    """Day-month date without a year; accepted by post-process."""

    styles = ["numeric", "numeric_zero", "textual", "textual_zero"]
    style = styles[variant % len(styles)]
    variant //= len(styles)
    if style.startswith("numeric"):
        separator = "/" if variant % 2 == 0 else "-"
        variant //= 2
        day = f"{value.day:02d}" if style == "numeric_zero" else str(value.day)
        month = f"{value.month:02d}" if variant % 2 else str(value.month)
        return separator.join([day, month])

    day = f"{value.day:02d}" if style == "textual_zero" else str(value.day)
    month = _postprocess_month_token(value.month, variant)
    return f"{day} {month}"


def _postprocess_weekday_date(value: date, variant: int) -> str:
    weekday = DUTCH_WEEKDAYS[value.weekday()] if variant % 2 == 0 else DUTCH_WEEKDAYS_ABBR[value.weekday()]
    variant //= 2
    if variant % 2 == 0:
        base = _numeric_date(value, variant, allow_ymd=False).replace(".", "/")
    else:
        base = _postprocess_textual_dmy(value, variant)
    separator = ", " if variant % 3 == 0 else " "
    return f"{weekday}{separator}{base}"


def _postprocess_month_year(value: date, variant: int) -> str:
    styles = ["textual", "textual", "numeric_slash", "numeric_dash"]
    style = styles[variant % len(styles)]
    variant //= len(styles)
    if style == "numeric_slash":
        return f"{value.month}/{value.year}"
    if style == "numeric_dash":
        return f"{value.month:02d}-{value.year}"
    month = _postprocess_month_token(value.month, variant)
    return f"{month} {value.year}"


def _postprocess_year_only(value: date, variant: int) -> str:
    return str(value.year)


def format_named_date_profile(value: date, profile_name: str, variant: int = 0) -> str:
    """Render one of the named date profiles used by date-focused cases."""

    if profile_name == "numeric_slash_long":
        return f"{value.day:02d}/{value.month:02d}/{value.year}"
    if profile_name == "numeric_slash_short":
        return f"{value.day}/{value.month}/{value.year % 100:02d}"
    if profile_name == "numeric_dash_long":
        return f"{value.day:02d}-{value.month:02d}-{value.year}"
    if profile_name == "numeric_dash_short":
        return f"{value.day}-{value.month}-{value.year % 100:02d}"
    if profile_name == "numeric_dot_long":
        return f"{value.day}.{value.month}.{value.year}"
    if profile_name == "textual_full":
        return f"{value.day} {DUTCH_MONTHS_FULL[value.month - 1]} {value.year}"
    if profile_name == "textual_abbr_dot":
        month = DUTCH_MONTHS_ABBR[value.month - 1]
        month = month if month == "mei" else f"{month}."
        return f"{value.day} {month} {value.year}"
    if profile_name == "textual_hyphen":
        return f"{value.day}-{DUTCH_MONTHS_ABBR[value.month - 1]}-{value.year}"
    if profile_name == "weekday_numeric":
        weekday = DUTCH_WEEKDAYS[value.weekday()]
        return f"{weekday} {value.day}/{value.month}/{value.year}"
    if profile_name == "weekday_textual":
        weekday = DUTCH_WEEKDAYS_ABBR[value.weekday()]
        return f"{weekday} {value.day} {DUTCH_MONTHS_FULL[value.month - 1]} {value.year}"
    if profile_name == "day_month_numeric":
        return f"{value.day}/{value.month}"
    if profile_name == "day_month_textual":
        return f"{value.day} {DUTCH_MONTHS_FULL[value.month - 1]}"
    if profile_name == "month_year":
        return f"{DUTCH_MONTHS_FULL[value.month - 1]} {value.year}"
    if profile_name == "numeric_month_year_slash":
        return f"{value.month:02d}/{value.year}"
    if profile_name == "year_only":
        return str(value.year)
    return format_date_variant(value, variant, slot="date")


def _postprocess_date_range(value: date, variant: int) -> str:
    """Readable date ranges without time/cue prefixes or compact date tokens."""

    max_delta = calendar.monthrange(value.year, value.month)[1] - value.day
    if max_delta <= 0:
        return _postprocess_textual_dmy(value, variant)
    end_day = value.day + 1 + variant % min(14, max_delta)
    variant //= 14
    month = _postprocess_month_token(value.month, variant)
    variant //= 4
    year = _postprocess_year_token(value.year, variant)
    templates = [
        "{start} t.e.m. {end} {month} {year}",
        "{start} tot {end} {month} {year}",
        "{start}-{end} {month} {year}",
        "{start} t/m {end} {month} {year}",
    ]
    return templates[variant % len(templates)].format(
        start=value.day,
        end=end_day,
        month=month,
        year=year,
    )


def _compact_numeric_date(value: date, variant: int) -> str:
    styles = [
        f"{value.day:02d}{value.month:02d}{value.year}",
        f"{value.day:02d}{value.month:02d}{value.year % 100:02d}",
        f"{value.year}{value.month:02d}{value.day:02d}",
        f"{value.year % 100:02d}{value.month:02d}{value.day:02d}",
    ]
    return styles[variant % len(styles)]


def _textual_date(value: date, variant: int, *, include_year: bool = True) -> str:
    month = _month_token(value.month, variant)
    variant //= 6
    day = _day_token(value.day, variant)
    variant //= 2
    year = _year_token(value.year, variant, prefer_four_digit=True)
    variant //= 5
    templates = [
        "{day} {month} {year}",
        "{day}-{month}-{year}",
        "{day}/{month}/{year}",
        "{day}.{month}.{year}",
        "{day} {month} '{short_year}",
        "{month} {day}, {year}",
        "{day}{month}{year}",
        "{day}{month}'{short_year}",
        "{day} {month} {short_year}",
        "{day}. {month} {year}",
        "{day} {month} {year}.",
        "{day} {month} {year}",
        "{day} {month} {year}",
    ]
    template = templates[variant % len(templates)]
    if not include_year and "{year}" in template:
        template = "{day} {month}"
    rendered = template.format(day=day, month=month, year=year, short_year=f"{value.year % 100:02d}")
    return rendered.replace("..", ".")


def _compact_textual_date(value: date, variant: int) -> str:
    month = _month_token(value.month, variant)
    month_compact = month.replace(".", "")
    short_year = f"{value.year % 100:02d}"
    styles = [
        f"{value.day}{month_compact}{value.year}",
        f"{value.day:02d}{month_compact}{value.year}",
        f"{value.day:02d}{month_compact.upper()}{short_year}",
        f"{value.day}{month_compact.upper()}{short_year}",
        f"{value.day}-{month_compact.upper()}-{short_year}",
        f"{value.day}.{month_compact}.{value.year}",
    ]
    return styles[(variant // 6) % len(styles)]


def _weekday_date(value: date, variant: int) -> str:
    weekday = DUTCH_WEEKDAYS[value.weekday()] if variant % 2 == 0 else DUTCH_WEEKDAYS_ABBR[value.weekday()]
    variant //= 2
    base = _textual_date(value, variant) if variant % 2 else _numeric_date(value, variant, allow_ymd=False)
    variant //= 2
    templates = [
        "{weekday} {base}",
        "{weekday}, {base}",
        "{base} ({weekday})",
        "{base}, {weekday}",
        "{weekday} d.d. {base}",
    ]
    return templates[variant % len(templates)].format(weekday=weekday, base=base)


def _date_time(value: date, variant: int) -> str:
    hour = deterministic_index(value.isoformat(), variant, "hour", modulo=14) + 7
    minute = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55][variant % 12]
    base = _numeric_date(value, variant, allow_ymd=False) if variant % 3 else _textual_date(value, variant)
    time_styles = [
        f"{hour:02d}:{minute:02d}",
        f"{hour}u{minute:02d}",
        f"{hour:02d}.{minute:02d}",
        f"{hour} h {minute:02d}",
    ]
    joiners = [" ", " om ", " rond ", ", "]
    return f"{base}{joiners[(variant // 12) % len(joiners)]}{time_styles[(variant // 48) % len(time_styles)]}"


def _cued_date(value: date, variant: int) -> str:
    base = _numeric_date(value, variant, allow_ymd=False) if variant % 2 else _textual_date(value, variant)
    cues = ["d.d.", "dd.", "dd", "datum"]
    return f"{cues[(variant // 2) % len(cues)]} {base}"


def _date_range(value: date, variant: int) -> str:
    end = value + timedelta(days=1 + variant % 14)
    if value.month == end.month and value.year == end.year:
        month = _month_token(value.month, variant)
        year = _year_token(value.year, variant, prefer_four_digit=True)
        templates = [
            f"{value.day}-{end.day}/{value.month}/{value.year}",
            f"{value.day} t.e.m. {end.day} {month} {year}",
            f"{value.day}-{end.day} {month} {year}",
            f"{value.day}/{value.month} tot {end.day}/{end.month}/{value.year}",
            f"{value.day}/{value.month} t/m {end.day}/{end.month}/{value.year}",
        ]
        return templates[(variant // 14) % len(templates)]
    left = _numeric_date(value, variant, allow_ymd=False)
    right = _numeric_date(end, variant // 5, allow_ymd=False)
    return [f"{left}-{right}", f"{left} t.e.m. {right}", f"{left} tot {right}", f"{left} t/m {right}"][
        (variant // 70) % 4
    ]


def _month_year(value: date, variant: int) -> str:
    month = _month_token(value.month, variant)
    year = _year_token(value.year, variant, prefer_four_digit=True)
    templates = ["{month} {year}", "{month}-{year}", "{month}/{year}", "{month} '{short_year}"]
    return templates[(variant // 6) % len(templates)].format(month=month, year=year, short_year=f"{value.year % 100:02d}")


def _year_only(value: date, variant: int) -> str:
    return [str(value.year), f"'{value.year % 100:02d}", f"{value.year % 100:02d}"][
        variant % 3
    ]


def format_date_variant(value: date, index: int, slot: str = "date", precision: str = "day") -> str:
    """Render a date using forms accepted by the downstream post-process rules."""

    variant = deterministic_index(value.isoformat(), index, slot, precision, modulo=100_000)
    if precision == "month":
        return _postprocess_month_year(value, variant)
    if precision == "month_day":
        return _postprocess_day_month(value, variant)
    if precision == "year":
        return _postprocess_year_only(value, variant)

    if slot == "birthdate":
        styles = [
            "numeric",
            "numeric",
            "numeric",
            "textual",
            "textual",
            "textual_hyphen",
        ]
    else:
        bucket = variant % 100
        variant //= 100
        if bucket < 55:
            return _postprocess_day_month(value, variant)
        if bucket < 75:
            return _postprocess_year_only(value, variant)
        if bucket < 80:
            return _postprocess_month_year(value, variant)
        styles = [
            "numeric",
            "numeric",
            "numeric",
            "textual",
            "textual",
            "textual_hyphen",
            "weekday",
            "range",
        ]
    style = styles[variant % len(styles)]
    variant //= len(styles)
    if style == "textual":
        return _postprocess_textual_dmy(value, variant)
    if style == "textual_hyphen":
        return _postprocess_textual_dmy(value, variant, hyphenated=True)
    if style == "weekday":
        return _postprocess_weekday_date(value, variant)
    if style == "range":
        return _postprocess_date_range(value, variant)
    return _numeric_date(value, variant, allow_ymd=False)


def date_context_prefix(index: int, slot: str) -> str:
    if slot != "birthdate":
        return ""
    values = ["", "", "", "", "°", "geb.", "geboren"]
    return values[deterministic_index(index, slot, "birth-prefix", modulo=len(values))]


def age_text_variant(age_text: str, index: int, age_group: str | None = None) -> str:
    parts = age_text.split()
    if not parts:
        return age_text
    amount = parts[0]
    unit = parts[1] if len(parts) > 1 else "jaar"
    lower_unit = unit.lower()

    if lower_unit.startswith("dag"):
        variants = [
            f"{amount} dagen",
            f"{amount} dag",
            f"{amount}dagen",
            f"{amount}dag",
        ]
        if amount == "1":
            variants.append("1 dag")
        return variants[deterministic_index(age_text, index, age_group or "", modulo=len(variants))]

    if lower_unit.startswith(("week", "wek")) or lower_unit in {"wkn", "wk"}:
        variants = [
            f"{amount} weken",
            f"{amount} week",
            f"{amount}weken",
            f"{amount}week",
        ]
        if amount == "1":
            variants.append("1 week")
        return variants[deterministic_index(age_text, index, age_group or "", modulo=len(variants))]

    if lower_unit.startswith("maand") or lower_unit == "mnd":
        variants = [
            f"{amount} maanden",
            f"{amount} mnd",
            f"{amount} maand" if amount == "1" else f"{amount} maanden",
            f"{amount}mnd",
            f"{amount}maanden",
            f"{amount}maand",
        ]
        return variants[deterministic_index(age_text, index, age_group or "", modulo=len(variants))]

    variants = [
        f"{amount} jaar",
        f"{amount} jaren",
        f"{amount} j.",
        f"{amount} j",
        f"{amount} jr",
        f"{amount}jr",
        f"{amount} jarig",
        f"{amount} jarige",
    ]
    if age_group in {"toddler", "preschool_child"}:
        variants.extend([f"{amount} jaar", f"{amount} jarig"])
    return variants[deterministic_index(age_text, index, age_group or "", modulo=len(variants))]


_DEGREE_PREFIX_RE = re.compile(r"^\s*[°º]\s*")
_DATE_CUE_PREFIX_RE = re.compile(r"^\s*(?:d\.?d\.?|dd\.?|datum|geb\.?|geboren)\s+", re.I)
_WEEKDAY_PREFIX_RE = re.compile(
    r"^\s*(?:ma|di|wo|do|vr|za|zo|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)[,\s]+",
    re.I,
)
_NUMERIC_RE = re.compile(r"(?P<a>\d{1,4})[./\-_ ](?P<b>\d{1,2})[./\-_ ](?P<c>'?\d{2,4})")
_ISO_COMPACT_RE = re.compile(r"\b(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})\b")
_COMPACT_NUMERIC_RE = re.compile(r"\b(?P<value>\d{6}|\d{8})\b")
_COMPACT_TEXTUAL_RE = re.compile(r"(?P<d>\d{1,2})(?P<m>[A-Za-zÀ-ÿ.]{1,12})(?P<y>'?\d{2,4})", re.I)
_TEXTUAL_SHARED_RANGE_RE = re.compile(
    r"(?P<d1>\d{1,2})\s*(?:t\.?e\.?m\.?|t/m|tot|[-–—])\s*"
    r"(?P<d2>\d{1,2})\s+(?P<m>[A-Za-zÀ-ÿ.]+)\s+(?P<y>'?\d{2,4})",
    re.I,
)
_NUMERIC_SHARED_RANGE_RE = re.compile(
    r"(?P<d1>\d{1,2})\s*[-–—]\s*(?P<d2>\d{1,2})(?P<sep>[/.])(?P<m>\d{1,2})(?P=sep)(?P<y>'?\d{2,4})"
)
_TEXTUAL_RE = re.compile(
    r"(?P<d>\d{1,2})\.?\s*[-/. ]\s*(?P<m>[A-Za-zÀ-ÿ.]+)\.?\s*[-/. ]?\s*(?P<y>'?\d{2,4})",
    re.I,
)
_TEXTUAL_MDY_RE = re.compile(
    r"(?P<m>[A-Za-zÀ-ÿ.]+)\s+(?P<d>\d{1,2})(?!\d)\.?,?\s+(?P<y>'?\d{2,4})",
    re.I,
)
_NUMERIC_DAY_MONTH_RE = re.compile(r"(?<!\d)(?P<d>\d{1,2})(?P<sep>[/-])(?P<m>\d{1,2})(?!\d)")
_TEXTUAL_DAY_MONTH_RE = re.compile(r"(?<!\d)(?P<d>\d{1,2})\s+(?P<m>[A-Za-zÀ-ÿ.]+)(?!\s+'?\d)", re.I)
_NUMERIC_MONTH_YEAR_RE = re.compile(r"(?<!\d)(?P<m>\d{1,2})(?P<sep>[/-])(?P<y>\d{4})(?!\d)")
_MONTH_YEAR_RE = re.compile(r"(?P<m>[A-Za-zÀ-ÿ.]+)\s*[-/ ]\s*(?P<y>'?\d{2,4})", re.I)


def _expand_year(raw_year: str, *, label: str) -> int:
    raw = raw_year.strip().lstrip("'")
    year = int(raw)
    if year >= 100:
        return year
    if label == "Age_Birthdate":
        return 2000 + year if year <= 30 else 1900 + year
    return 2000 + year


def _adjust_year_for_label(year: int, *, label: str) -> int:
    if label == "Age_Birthdate" and year > 2030:
        return year - 100
    return year


def _safe_date(year: int, month: int, day: int, *, label: str = "Date") -> date | None:
    try:
        return date(_adjust_year_for_label(year, label=label), month, day)
    except ValueError:
        return None


def _missing_year_default(label: str) -> int:
    return 2000 if label == "Age_Birthdate" else 2026


def _dutch_month_number(raw_month: str) -> int | None:
    token = raw_month.lower().rstrip(".")
    if token.upper() in ROMAN_MONTHS:
        return None
    return MONTH_ALIASES.get(token)


def _parse_compact_numeric(raw: str, *, label: str) -> date | None:
    if len(raw) == 8:
        if raw[:4].isdigit() and 1900 <= int(raw[:4]) <= 2099:
            parsed = _safe_date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]), label=label)
            if parsed is not None:
                return parsed
        return _safe_date(int(raw[4:8]), int(raw[2:4]), int(raw[:2]), label=label)

    first, middle, last = raw[:2], raw[2:4], raw[4:6]
    candidates: list[date] = []
    if 20 <= int(last) <= 30:
        parsed = _safe_date(_expand_year(last, label=label), int(middle), int(first), label=label)
        if parsed is not None:
            candidates.append(parsed)
    parsed = _safe_date(_expand_year(first, label="Date"), int(middle), int(last), label=label)
    if parsed is not None:
        candidates.append(parsed)
    parsed = _safe_date(_expand_year(last, label=label), int(middle), int(first), label=label)
    if parsed is not None:
        candidates.append(parsed)
    return candidates[0] if candidates else None


def parse_date_text(text: str, *, label: str = "Date") -> ParsedDate | None:
    """Parse the current generator's date strings plus common posthoc outputs."""

    had_degree = bool(_DEGREE_PREFIX_RE.match(text))
    cleaned = _DEGREE_PREFIX_RE.sub("", text).strip()
    while True:
        previous = cleaned
        cleaned = _DATE_CUE_PREFIX_RE.sub("", cleaned)
        cleaned = _WEEKDAY_PREFIX_RE.sub("", cleaned)
        if cleaned == previous:
            break
    cleaned = re.sub(r"\s+(?:om|rond)\s+\d{1,2}(?::|u| h |\.)\d{0,2}.*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*,?\s*(?<![.\d])\d{1,2}(?::|u| h |\.)\d{2}(?![.\d])\s*$", "", cleaned, flags=re.I)
    cleaned = re.sub(
        r"\s*,?\s*(?:ma|di|wo|do|vr|za|zo|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\s*$",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\s*\((?:ma|di|wo|do|vr|za|zo|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\)\s*$", "", cleaned, flags=re.I)

    if RELATIVE_DATE_RE.fullmatch(cleaned):
        return ParsedDate(date(2000, 1, 1), "relative", had_degree)

    compact = _ISO_COMPACT_RE.fullmatch(cleaned)
    if compact:
        parsed = _safe_date(int(compact.group("y")), int(compact.group("m")), int(compact.group("d")), label=label)
        if parsed is not None:
            return ParsedDate(parsed, "day", had_degree)

    compact_numeric = _COMPACT_NUMERIC_RE.fullmatch(cleaned)
    if compact_numeric:
        parsed = _parse_compact_numeric(compact_numeric.group("value"), label=label)
        return ParsedDate(parsed, "day", had_degree) if parsed else None

    textual_shared_range = _TEXTUAL_SHARED_RANGE_RE.search(cleaned)
    if textual_shared_range:
        month = MONTH_ALIASES.get(textual_shared_range.group("m").lower().rstrip("."))
        if month:
            parsed = _safe_date(
                _expand_year(textual_shared_range.group("y"), label=label),
                month,
                int(textual_shared_range.group("d1")),
                label=label,
            )
            return ParsedDate(parsed, "day", had_degree) if parsed else None

    numeric_shared_range = _NUMERIC_SHARED_RANGE_RE.search(cleaned)
    if numeric_shared_range:
        parsed = _safe_date(
            _expand_year(numeric_shared_range.group("y"), label=label),
            int(numeric_shared_range.group("m")),
            int(numeric_shared_range.group("d1")),
            label=label,
        )
        return ParsedDate(parsed, "day", had_degree) if parsed else None

    compact_textual = _COMPACT_TEXTUAL_RE.fullmatch(cleaned)
    if compact_textual:
        month = MONTH_ALIASES.get(compact_textual.group("m").lower().rstrip("."))
        if month:
            parsed = _safe_date(
                _expand_year(compact_textual.group("y"), label=label),
                month,
                int(compact_textual.group("d")),
                label=label,
            )
            return ParsedDate(parsed, "day", had_degree) if parsed else None

    numeric = _NUMERIC_RE.search(cleaned)
    if numeric:
        a, b, c = numeric.group("a"), numeric.group("b"), numeric.group("c")
        if len(a) == 4:
            year, month, day = int(a), int(b), int(c)
        elif int(b) > 12 and int(a) <= 12:
            month, day, year = int(a), int(b), _expand_year(c, label=label)
        else:
            day, month, year = int(a), int(b), _expand_year(c, label=label)
        parsed = _safe_date(year, month, day, label=label)
        return ParsedDate(parsed, "day", had_degree) if parsed else None

    textual = _TEXTUAL_RE.search(cleaned)
    if textual:
        month = MONTH_ALIASES.get(textual.group("m").lower().rstrip("."))
        if month:
            parsed = _safe_date(
                _expand_year(textual.group("y"), label=label),
                month,
                int(textual.group("d")),
                label=label,
            )
            return ParsedDate(parsed, "day", had_degree) if parsed else None

    textual_mdy = _TEXTUAL_MDY_RE.search(cleaned)
    if textual_mdy:
        month = MONTH_ALIASES.get(textual_mdy.group("m").lower().rstrip("."))
        if month:
            parsed = _safe_date(
                _expand_year(textual_mdy.group("y"), label=label),
                month,
                int(textual_mdy.group("d")),
                label=label,
            )
            return ParsedDate(parsed, "day", had_degree) if parsed else None

    numeric_month_year = _NUMERIC_MONTH_YEAR_RE.fullmatch(cleaned)
    if numeric_month_year:
        parsed = _safe_date(
            int(numeric_month_year.group("y")),
            int(numeric_month_year.group("m")),
            1,
            label=label,
        )
        return ParsedDate(parsed, "month", had_degree) if parsed else None

    numeric_day_month = _NUMERIC_DAY_MONTH_RE.fullmatch(cleaned)
    if numeric_day_month:
        parsed = _safe_date(
            _missing_year_default(label),
            int(numeric_day_month.group("m")),
            int(numeric_day_month.group("d")),
            label=label,
        )
        return ParsedDate(parsed, "month_day", had_degree) if parsed else None

    textual_day_month = _TEXTUAL_DAY_MONTH_RE.fullmatch(cleaned)
    if textual_day_month:
        month = _dutch_month_number(textual_day_month.group("m"))
        if month:
            parsed = _safe_date(
                _missing_year_default(label),
                month,
                int(textual_day_month.group("d")),
                label=label,
            )
            return ParsedDate(parsed, "month_day", had_degree) if parsed else None

    month_year = _MONTH_YEAR_RE.fullmatch(cleaned)
    if month_year:
        month = MONTH_ALIASES.get(month_year.group("m").lower().rstrip("."))
        if month:
            return ParsedDate(date(_expand_year(month_year.group("y"), label=label), month, 1), "month", had_degree)

    if re.fullmatch(r"'?\d{2,4}", cleaned):
        return ParsedDate(date(_expand_year(cleaned, label=label), 1, 1), "year", had_degree)

    return None
