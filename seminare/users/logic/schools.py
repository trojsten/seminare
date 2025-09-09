from datetime import date

from seminare.users.models import Grade

DEFAULT_GRADES = {
    "gym": [
        Grade.SS1,
        Grade.SS2,
        Grade.SS3,
        Grade.SS4,
        Grade.SS5,
    ],
    "zs": [
        Grade.YOUNG,
        Grade.YOUNG,
        Grade.YOUNG,
        Grade.YOUNG,
        Grade.ZS5,
        Grade.ZS6,
        Grade.ZS7,
        Grade.ZS8,
        Grade.ZS9,
    ],
}
DEFAULT_GRADES["ss"] = DEFAULT_GRADES["gym"]
DEFAULT_GRADES["gym:8"] = DEFAULT_GRADES["zs"][5:] + DEFAULT_GRADES["gym"][:4]


def get_grade_map(school_type: str) -> list[Grade]:
    if school_type in DEFAULT_GRADES:
        return DEFAULT_GRADES[school_type]
    if ":" in school_type:
        base_type, _ = school_type.split(":", 1)
        if base_type in DEFAULT_GRADES:
            return DEFAULT_GRADES[base_type]

    raise ValueError(f"School type {school_type} is unknown.")


def get_grade_from_type_year(school_type: str, year: int) -> Grade | None:
    if school_type == "uni":
        return Grade.OLD

    try:
        map = get_grade_map(school_type)
    except ValueError:
        return None

    if year < 0 or year >= len(map):
        return None

    return map[year]


def date_to_academic_year(date: date) -> int:
    september = date.replace(month=9, day=1)
    if date < september:
        return date.year - 1
    return date.year
