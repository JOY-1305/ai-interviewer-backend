from typing import Dict, List, Any

DEFAULT_VERSION = "v1"

# Simple, transparent, deterministic rules.
# You can tune later without changing the frontend.
WEIGHTS = {
    "TAB_HIDDEN": 8,
    "WINDOW_BLUR": 6,
    "PASTE": 10,
    "COPY": 4,
    "CUT": 4,
    "FULLSCREEN_EXIT": 12,
}

def compute_integrity(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns:
      {"score": int 0-100, "flags": {...}}
    """
    counts: Dict[str, int] = {}
    penalty = 0

    for e in events:
        et = (e.get("event_type") or "").upper().strip()
        counts[et] = counts.get(et, 0) + 1
        penalty += WEIGHTS.get(et, 0)

    # Escalation rule: repeated tab switches hurt more
    tab = counts.get("TAB_HIDDEN", 0)
    if tab >= 3:
        penalty += (tab - 2) * 5

    # clamp
    score = max(0, min(100, 100 - penalty))

    # map to readable flags
    flags = {
        "version": DEFAULT_VERSION,
        "counts": counts,
        "penalty": penalty,
    }
    return {"score": score, "flags": flags}
