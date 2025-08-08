class Rules:
    """
    Run-time rule tracking.

    Rules:
      1) Do not step on lava (red tiles).
      2) Do not get caught by the monster.
      3) Do not stand still for ~2 seconds.

    Scoring:
      - Lemons add +1 point. No limit.

    Lives / Penalties:
      - On any rule break, you lose one heart. If hearts remain, the run resets
        but the SCORE IS KEPT. On a brand-new run or after Game Over, score is 0.
    """

    def __init__(self):
        self.score = 0
        self.resets = 0              # number of penalties (for stats if needed)
        self._broken = False
        self.last_broken_msg = ""

    # ---- Events ----
    def on_item_picked(self):
        self.score += 1

    def break_rule(self, rule_number: int, msg: str):
        self._broken = True
        self.last_broken_msg = f"Rule {rule_number} broken: {msg}"

    # ---- Helpers ----
    def any_broken(self) -> bool:
        return self._broken

    def reset_run_state(self):
        """Clear the broken flag/message after a soft reset. Score is kept."""
        self._broken = False
        self.last_broken_msg = ""
