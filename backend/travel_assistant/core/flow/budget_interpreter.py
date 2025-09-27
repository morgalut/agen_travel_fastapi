# core/flow/budget_interpreter.py
import re
from typing import Tuple, Optional

class BudgetInterpreter:
    @staticmethod
    def parse(text: str) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Returns: (unlimited, max_price_per_night, currency)
        Detects "unlimited", else tries numbers + currency.
        """
        if re.search(r"\bunlimited\b|\bno\s*limit\b|\bno budget\b", text, re.I):
            return True, None, None

        # Simple price detection (extend as needed)
        m = re.search(r"(\$|€|£)?\s*(\d{2,5})\s*(usd|eur|gbp|dollars|euros|pounds)?\s*(per\s*night|/night)?", text, re.I)
        if m:
            sym, amount, cur, _ = m.groups()
            amt = float(amount)
            currency = (cur or "").upper() if cur else None
            if not currency and sym:
                currency = {"$": "USD", "€": "EUR", "£": "GBP"}.get(sym)
            return False, amt, currency
        return False, None, None
        