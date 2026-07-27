from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    return datetime.fromisoformat(value).date()
