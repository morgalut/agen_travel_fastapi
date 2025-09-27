# core/flow/temporal_resolver.py
import re
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

IL_TZ = ZoneInfo("Asia/Jerusalem")

class TemporalResolver:
    """
    Resolves phrases like:
      - "in 2 days from now" + "staying for 14 days"
      - "in 1 week" + "for 10 days"
    into concrete start/end dates using Asia/Jerusalem.
    """

    @staticmethod
    def _extract_relative_days(text: str) -> Optional[int]:
        # Examples: "in 2 days", "in 1 day from now", "in 2 weeks", etc.
        m = re.search(r"\bin\s+(\d+)\s+(day|days|week|weeks)\b", text, re.I)
        if not m: 
            return None
        qty = int(m.group(1))
        unit = m.group(2).lower()
        return qty * (7 if "week" in unit else 1)

    @staticmethod
    def _extract_duration_days(text: str) -> Optional[int]:
        m = re.search(r"\b(\d+)\s+(day|days|night|nights|week|weeks)\b", text, re.I)
        if not m: 
            return None
        qty = int(m.group(1))
        unit = m.group(2).lower()
        if "week" in unit:
            return qty * 7
        # If "nights" provided, treat nights as days for hotel booking window
        return qty

    @classmethod
    def resolve(cls, text: str) -> Tuple[Optional[date], Optional[date], Optional[int]]:
        now = datetime.now(IL_TZ).date()
        rel_days = cls._extract_relative_days(text)
        dur_days = cls._extract_duration_days(text)

        start: Optional[date] = None
        end: Optional[date] = None
        nights: Optional[int] = None

        if rel_days:
            start = now + timedelta(days=rel_days)
        if dur_days:
            nights = dur_days
        if start and nights:
            end = start + timedelta(days=nights)  # checkout date
        return start, end, nights
