from pathlib import Path

source_path = Path("zeroresp_v54.py")
target_path = Path("zeroresp_v541.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace version name
text = text.replace('name = "ZeroResp v5.4-proto"', 'name = "ZeroResp v5.4.1"')

old_bal = """        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            self.nl_scheduled = []
            self.nl_harvest_left = 0
            self.nl_harvest_scheduled_at = 0
            self.nl_harvest_postponed = 0
            self.nl_harvest_size = 0
            self.nl_evidence = 0
            self.nl_window.clear()
            self.echo_forgive = max(self.echo_forgive, 2)
            self.warmth = max(self.warmth, 0.6)
            self.target_warmth = max(self.target_warmth, 0.6)"""

new_bal = """        # v5.4.1: balance_apology защищён двойным гейтом:
        # 1. Не капитулировать перед Random / дефекторами (live_coop_rate >= 0.60)
        # 2. Не ломать детерминированную эксплуатацию на 0% шуме (требуется noisy_regime при короткой истории)
        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            can_apologize = not (self.opp_len >= 15 and self._live_coop_rate() < 0.60)
            if can_apologize:
                self.nl_scheduled = []
                self.nl_harvest_left = 0
                self.nl_harvest_scheduled_at = 0
                self.nl_harvest_postponed = 0
                self.nl_harvest_size = 0
                self.nl_evidence = 0
                self.nl_window.clear()
                self.echo_forgive = max(self.echo_forgive, 2)
                self.warmth = max(self.warmth, 0.6)
                self.target_warmth = max(self.target_warmth, 0.6)"""

assert old_bal in text, "old_bal not found"
text = text.replace(old_bal, new_bal, 1)

old_helper = """def ZeroRespV54Full(**kw):
    \"\"\"Прототип со всеми v5.4-экспериментами включёнными сразу.\"\"\"
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True)
    return ZeroResp(features=feats, **kw)"""

new_helper = """def ZeroRespV541(**kw):
    \"\"\"ZeroResp v5.4.1 со стабильным balance_apology и защитными гейтами.\"\"\"
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True)
    return ZeroResp(features=feats, **kw)


ZeroRespV54Full = ZeroRespV541"""

assert old_helper in text, "old_helper not found"
text = text.replace(old_helper, new_helper, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully generated zeroresp_v541.py")
