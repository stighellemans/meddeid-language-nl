"""Render event dates and clinical ages from their original context."""

from datetime import date, timedelta

from . import date_pseudonyms


def date_body(text, *, offset, reference, profile_id, before="", after=""):
    return date_pseudonyms.pseudonymize_date_text_body(
        text,
        label="Date",
        date_shift_days=offset,
        document_creation_date=reference.isoformat() if reference else None,
        context_before=before,
        context_after=after,
    )


def age_body(text, *, offset, reference, profile_id, before="", after=""):
    expression = date_pseudonyms.parse_age_expression(text)
    if expression is not None:
        return date_pseudonyms.render_age_expression(
            expression, reference or date(2000, 1, 1)
        )
    kind = date_pseudonyms.nearest_age_birthdate_context(before, after)
    if (
        text.strip().isdigit()
        and 0 <= int(text.strip()) <= 120
        and kind not in {"jaar", "year", "maand", "month", "dag", "day"}
    ):
        return text
    # Birth day/month components alone do not specify a birthdate.
    if kind in {"maand", "month", "dag", "day"} and text.strip().isdigit():
        return None
    ambiguous = date_pseudonyms.NUMERIC_SHARED_MONTH_RANGE_RE.fullmatch(text.strip())
    if (
        ambiguous
        and 1 <= int(ambiguous["start_day"]) <= int(ambiguous["end_day"]) <= 31
        and 1 <= int(ambiguous["month"]) <= 12
    ):
        # e.g. 1-3/09 can mean 1 March 2009 OR 1-3 September without a year.
        return None
    try:
        parsed = date_pseudonyms.parse_date_text(text, document_date=reference)
    except ValueError:
        return None
    if (
        parsed.granularity in {"day_month", "month_name", "month_phase"}
        or parsed.style.get("has_year") is False
        or parsed.style.get("kind") == "numeric_day_year"
    ):
        return None
    if reference is not None:
        return date_pseudonyms.render_birthdate_age_interval(
            parsed.start, parsed.end, reference
        )
    if offset:
        return date_pseudonyms.render_year_interval(
            (parsed.start + timedelta(days=offset)).year,
            (parsed.end + timedelta(days=offset)).year,
        )
    return None
