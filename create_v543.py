"""Generate zeroresp_v543.py: v5.4.2 + hybrid noise switch between the two
apology contours.

Design (user proposal, 2026-10-24): the balance_apology gate contour is
selected by the estimated channel noise p_noise_est:
- quiet channel (p_est < HYBRID_P_EST_THRESHOLD) -> static v5.4.1 gate
  (apologize unless the opponent is a proven defector);
- noisy channel -> v5.4.2 responsiveness gate (delta_p >= 0.35).
hybrid_noise_switch=False keeps pure v5.4.2 behavior.
"""
import re
from pathlib import Path

source_path = Path("zeroresp_v542.py")
target_path = Path("zeroresp_v543.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Version strings
text = text.replace("ZeroResp v5.4.2", "ZeroResp v5.4.3")
text = text.replace("def ZeroRespV542(", "def ZeroRespV543(")
text = text.replace("ZeroRespV54Full = ZeroRespV542", "ZeroRespV54Full = ZeroRespV543")

# 2. Factory: enable the switch and update its docstring
old_factory = '''def ZeroRespV543(**kw):
    """ZeroResp v5.4.3 со стабильным balance_apology и защитными гейтами."""
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True)
    return ZeroResp(features=feats, **kw)'''
new_factory = '''def ZeroRespV543(**kw):
    """ZeroResp v5.4.3: гейты v5.4.2 + гибридный переключатель контура по шуму."""
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True,
                      hybrid_noise_switch=True)
    return ZeroResp(features=feats, **kw)'''
assert old_factory in text, "factory block not found"
text = text.replace(old_factory, new_factory, 1)

# 3. Features slot + ctor param + assignment
text = text.replace('''        "profile_memory",
    )''', '''        "profile_memory",
        "hybrid_noise_switch",
    )''', 1)
text = text.replace('''        profile_memory: bool = False,
    ):''', '''        profile_memory: bool = False,
        hybrid_noise_switch: bool = False,
    ):''', 1)
text = text.replace('''        self.profile_memory = profile_memory

    def asdict''', '''        self.profile_memory = profile_memory
        self.hybrid_noise_switch = hybrid_noise_switch

    def asdict''', 1)

# 4. Class constants: noise threshold and minimum history before the quiet
#    contour is allowed in a match with noise
text = text.replace(
    "    NL_BALANCE_FLOOR = -4  # ниже этого баланса - принудительный откат в C",
    "    NL_BALANCE_FLOOR = -4  # ниже этого баланса - принудительный откат в C\n"
    "    # v5.4.3: порог p_noise_est между тихим (статический гейт v5.4.1) и\n"
    "    # шумным (гейт отзывчивости v5.4.2) контуром balance_apology.\n"
    "    # В матче с шумом тихий контур требует доказательства канала:\n"
    "    # пока opp_len < HYBRID_MIN_HISTORY, действует отзывчивый контур.\n"
    "    HYBRID_P_EST_THRESHOLD = 0.03\n"
    "    HYBRID_MIN_HISTORY = 15", 1)

# 5. The gate itself: route by estimated channel noise
old_gate = '''        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            # v5.4.2 Responsiveness Gate:
            # 1. 0% noise protection: never trigger balance_apology in deterministic matches
            # 2. Overall coop rate floor: live_coop_rate >= 0.60 when history >= 15
            # 3. Responsiveness condition: P(C|our C) - P(C|our D) >= 0.35 when our D >= 2
            noise_attr = self.match_attributes.get("noise")
            if noise_attr == 0.0:
                can_apologize = False
            elif self.opp_len >= 15 and self._live_coop_rate() < 0.60:
                can_apologize = False'''
new_gate = '''        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            # v5.4.3 Hybrid Noise Switch: контур гейта выбирается оценкой шума
            # канала. Тихий канал ведёт статический гейт v5.4.1, шумный -
            # гейт отзывчивости v5.4.2 (delta_p >= 0.35). Доказательства
            # шумного канала (доктрина v5.3: свой флип доказывает шум):
            # накопленный p_est >= порога ИЛИ хотя бы один наш флип C->D.
            # p_noise_est - оценщик с холодным стартом (обновляется после
            # cc_pairs > 10), его 0.0 означает "нет данных", поэтому без
            # собственного флипа канал шумным не считается до накопления.
            # Без hybrid_noise_switch поведение = v5.4.2.
            noise_attr = self.match_attributes.get("noise")
            match_noisy = noise_attr not in (0.0, None)
            channel_noisy = match_noisy and (
                self.p_noise_est >= self.HYBRID_P_EST_THRESHOLD
                or self.nl_my_flips > 0
                or self.opp_len < self.HYBRID_MIN_HISTORY)
            if (self.features.hybrid_noise_switch and not channel_noisy):
                # статический контур v5.4.1: уступаем только доказанному
                # дефектеру, без требования отзывчивости
                can_apologize = not (self.opp_len >= 15 and self._live_coop_rate() < 0.60)
            elif self.opp_len >= 15 and self._live_coop_rate() < 0.60:
                can_apologize = False'''
assert old_gate in text, "gate block not found"
text = text.replace(old_gate, new_gate, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully created zeroresp_v543.py")
