import re
from pathlib import Path

source_path = Path("zeroresp_v541.py")
target_path = Path("zeroresp_v542.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace version header and name
text = text.replace("ZeroResp v5.4.1", "ZeroResp v5.4.2")
text = text.replace('"ZeroResp v5.4.1"', '"ZeroResp v5.4.2"')
text = text.replace("def ZeroRespV541(", "def ZeroRespV542(")
text = text.replace("ZeroRespV54Full = ZeroRespV541", "ZeroRespV54Full = ZeroRespV542")

old_block = """        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            can_apologize = not (self.opp_len >= 15 and self._live_coop_rate() < 0.60)
            if can_apologize:"""

new_block = """        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            # v5.4.2 Responsiveness Gate:
            # 1. 0% noise protection: never trigger balance_apology in deterministic matches
            # 2. Overall coop rate floor: live_coop_rate >= 0.60 when history >= 15
            # 3. Responsiveness condition: P(C|our C) - P(C|our D) >= 0.35 when our D >= 2
            noise_attr = self.match_attributes.get("noise")
            if noise_attr == 0.0:
                can_apologize = False
            elif self.opp_len >= 15 and self._live_coop_rate() < 0.60:
                can_apologize = False
            else:
                my_hist = self.history
                opp_hist = opponent.history
                n_c = sum(1 for i in range(len(my_hist) - 1) if my_hist[i] == C)
                n_d = sum(1 for i in range(len(my_hist) - 1) if my_hist[i] == D)
                if n_d >= 2:
                    c_after_c = sum(1 for i in range(len(my_hist) - 1) if my_hist[i] == C and opp_hist[i + 1] == C)
                    c_after_d = sum(1 for i in range(len(my_hist) - 1) if my_hist[i] == D and opp_hist[i + 1] == C)
                    p_c_c = c_after_c / max(1, n_c)
                    p_c_d = c_after_d / max(1, n_d)
                    delta_p = p_c_c - p_c_d
                    can_apologize = (delta_p >= 0.35)
                else:
                    can_apologize = True

            if can_apologize:"""

assert old_block in text, "old_block not found in zeroresp_v541.py"
text = text.replace(old_block, new_block, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully created zeroresp_v542.py")
