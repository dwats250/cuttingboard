"""
Minimal confirmation module to satisfy intraday_state_engine dependencies.

This is a placeholder implementation to restore system integrity.
DO NOT extend without a proper PRD.
"""

# Direction constants
DIRECTION_UP = "UP"
DIRECTION_DOWN = "DOWN"

# State constants
STATE_BREAK_ONLY = "BREAK_ONLY"
STATE_HOLD_CONFIRMED = "HOLD_CONFIRMED"
STATE_FAILURE_CONFIRMED = "FAILURE_CONFIRMED"

class LevelConfirmation:
    def __init__(self, state: str):
        self.state = state

def evaluate_level_confirmation(*args, **kwargs):
    """
    Minimal stub.

    Returns a neutral state so downstream logic does not break.
    Replace with real implementation later.
    """
    return LevelConfirmation(STATE_BREAK_ONLY)
