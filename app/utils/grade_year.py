import re

_YEAR_RE = re.compile(r"(\d{4})")


def parse_grade_year(grade: str | None) -> int | None:
    if not grade:
        return None
    match = _YEAR_RE.search(grade)
    return int(match.group(1)) if match else None


def member_list_sort_key(grade: str | None, sort_order: int, member_id: int) -> tuple[int, int, int]:
    year = parse_grade_year(grade)
    return (year if year is not None else 99999, sort_order, member_id)
