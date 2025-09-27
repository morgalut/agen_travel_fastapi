# travel_assistant/core/responders/budget_responder.py
from typing import Dict, Any, Tuple
from .base_responder import BaseResponder
import re

class BudgetResponder(BaseResponder):
    """
    Answers:
      - “How much money should I spend for a week in Europe?”
      - “What’s a daily budget for Italy?”
    Approach:
      1) Infer duration (default 7 days).
      2) Recognize region (Europe) or reuse last destination.
      3) Provide transparent, tiered per-day ranges + total for the duration.
      4) Share a line-item breakdown and levers to go up/down.
    """

    # Simple region tiers (EUR/day). Tune these ranges as you learn from users.
    # We avoid overfitting and keep ranges conservative & explainable.
    EUROPE_DAILY_EUR = {
        "backpacker": (70, 110),     # hostels, transit passes, street food
        "midrange":   (150, 250),    # 3* hotels, casual dining, intercity trains
        "comfort":    (250, 400),    # 4* hotels, mix of dining, some tours
        "luxury":     (450, 700),    # 5* hotels, fine dining, private tours/transfers
    }

    # If user hints at cheaper subregions, we can narrow the lower band slightly.
    EASTERN_HINTS = {"poland","hungary","romania","bulgaria","czech","slovakia","slovenia","croatia","baltic","estonia","latvia","lithuania"}
    WESTERN_HINTS = {"france","germany","netherlands","belgium","austria","switzerland","uk","ireland","denmark","norway","sweden","finland","iceland","spain","italy","portugal","greece"}

    def _days_from_duration(self, duration: str) -> int:
        if not duration:
            return 7
        m = re.search(r"(\d+)", str(duration))
        if not m:
            return 7
        return max(1, int(m.group(1)))

    def _sum_range(self, per_day: Tuple[int,int], days: int) -> Tuple[int,int]:
        return per_day[0]*days, per_day[1]*days

    def _normalize(self, s: str) -> str:
        return (s or "").lower()

    async def respond(self, entities: Dict[str, Any], external: Dict[str, Any], context: Dict[str, Any]) -> str:
        dest = self._normalize(entities.get("destination") or context.get("destination") or "europe")
        duration = entities.get("duration") or context.get("duration") or "7 days"
        days = self._days_from_duration(duration)

        # Choose base region band
        base = dict(self.EUROPE_DAILY_EUR)
        # Light regional nudge (keep conservative, not absolute)
        if any(h in dest for h in self.EASTERN_HINTS):
            base["backpacker"] = (60, 100)
            base["midrange"]   = (130, 220)
        elif "switzerland" in dest or "norway" in dest or "iceland" in dest:
            base["backpacker"] = (90, 140)
            base["midrange"]   = (180, 300)

        bp_total = self._sum_range(base["backpacker"], days)
        mr_total = self._sum_range(base["midrange"], days)
        cf_total = self._sum_range(base["comfort"], days)
        lx_total = self._sum_range(base["luxury"], days)

        out = [
            f"**How much for {days} days in {dest.capitalize()}? (EUR)**",
            "",
            f"**Backpacker:** €{bp_total[0]:,}–€{bp_total[1]:,}  _(€{base['backpacker'][0]}–€{base['backpacker'][1]}/day)_",
            f"**Mid-range:**  €{mr_total[0]:,}–€{mr_total[1]:,}  _(€{base['midrange'][0]}–€{base['midrange'][1]}/day)_",
            f"**Comfort:**    €{cf_total[0]:,}–€{cf_total[1]:,}  _(€{base['comfort'][0]}–€{base['comfort'][1]}/day)_",
            f"**Luxury:**     €{lx_total[0]:,}–€{lx_total[1]:,}  _(€{base['luxury'][0]}–€{base['luxury'][1]}/day)_",
            "",
            "**Typical Daily Split (mid-range guide)**",
            "• Lodging: 45–55% (city & season sensitive)",
            "• Food & drink: 20–30%",
            "• Transit (local/intercity): 10–20%",
            "• Sights & tours: 10–20%",
            "",
            "**Levers to Lower Cost**",
            "• Travel in shoulder season; book trains/buses early.",
            "• Choose 2–3 hubs vs. many hops; use day trips.",
            "• Mix in apartments/hostels; cook some meals.",
            "",
            "Tell me **which countries/cities**, **travel style** (hostel/3*/4–5*), and **must-do activities**, and I’ll pin a tighter range and build a line-item plan."
        ]
        return "\n".join(out)
