"""Generate zeroresp_v544.py: v5.4.2 + cycler contour.

Data-driven redesign of the hybrid-switch idea (2026-10-24). Loss analysis
showed the #1 leak of v5.4.2 vs the library leaders is the Cycler family
(CyclerCCD at 5% noise: v5.3 3.369 vs v5.4.2 2.207, -1.16 SPT): under channel
noise the periodic D's of a cycler read as unprovoked, nl_balance drops,
balance_apology fires and resets the harvest. Fix: when the opponent matches
a fixed period (2-6, window up to 18, noise-tolerant), balance_apology never
fires and the base v5.3 contour keeps exploiting.
"""
from pathlib import Path

source_path = Path("zeroresp_v542.py")
target_path = Path("zeroresp_v544.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Version strings
text = text.replace("ZeroResp v5.4.2", "ZeroResp v5.4.4")
text = text.replace("def ZeroRespV542(", "def ZeroRespV544(")
text = text.replace("ZeroRespV54Full = ZeroRespV542", "ZeroRespV54Full = ZeroRespV544")

# 2. Factory: enable the cycler contour
old_factory = '''def ZeroRespV544(**kw):
    """ZeroResp v5.4.4 со стабильным balance_apology и защитными гейтами."""
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True)
    return ZeroResp(features=feats, **kw)'''
new_factory = '''def ZeroRespV544(**kw):
    """ZeroResp v5.4.4: гейты v5.4.2 + контур цикликов (без извинений
    против доказанной фиксированной периодики оппонента)."""
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True,
                      cycler_contour=True)
    return ZeroResp(features=feats, **kw)'''
assert old_factory in text, "factory block not found"
text = text.replace(old_factory, new_factory, 1)

# 3. Features slot + ctor param + assignment
text = text.replace('''        "profile_memory",
    )''', '''        "profile_memory",
        "cycler_contour",
    )''', 1)
text = text.replace('''        profile_memory: bool = False,
    ):''', '''        profile_memory: bool = False,
        cycler_contour: bool = False,
    ):''', 1)
text = text.replace('''        self.profile_memory = profile_memory

    def asdict''', '''        self.profile_memory = profile_memory
        self.cycler_contour = cycler_contour

    def asdict''', 1)

# 4. Latch state
text = text.replace(
    "        self.p_noise_est = 0.0",
    "        self.p_noise_est = 0.0\n"
    "        self._fixed_period_latch = False  # v5.4.4: доказанный циклик", 1)

# 5. Period detector method, inserted before _update_target_warmth
anchor = "    def _update_target_warmth(self):"
method = '''    def _detect_fixed_period(self, opponent) -> bool:
        """v5.4.4: детект фиксированной периодичности оппонента.

        Периоды 2-6, окно до 18 последних ходов оппонента (минимум 12),
        порог несовпадений ~15% (толерантность к канальному шуму).
        Период 1 исключён (урок v5.3: так выглядит Grudger). Класс
        залипает до конца матча: паттерн циклика не исчезает.
        """
        if self._fixed_period_latch:
            return True
        hist = list(opponent.history)
        if len(hist) < 12:
            return False
        window = hist[-18:]
        n = len(window)
        # Зеркальная защита: реципрокаторы (TFT-класс) воспроизводят наш
        # собственный паттерн с лагом 1 - их "период" производен от наших
        # ходов (в т.ч. от периодических проб лестницы), это не
        # самогенерируемый цикл. Совпадение с нашим лагом-1 >= 80% -
        # периодический детект не засчитывается.
        my_hist = list(self.history)
        if len(my_hist) > n:
            my_window = my_hist[-(n + 1):-1]
            agree = sum(1 for i in range(n) if window[i] == my_window[i])
            if agree >= int(n * 0.80):
                return False
        for p in range(2, 7):
            cmp_pairs = n - p
            if cmp_pairs < 8:
                continue
            mism = sum(1 for i in range(p, n) if window[i] != window[i - p])
            if mism <= max(1, int(cmp_pairs * 0.15)):
                self._fixed_period_latch = True
                return True
        return False

'''
assert anchor in text, "method anchor not found"
text = text.replace(anchor, method + anchor, 1)

# 6. Gate: cycler contour routes before the v5.4.2 checks
old_gate = '''            noise_attr = self.match_attributes.get("noise")
            if noise_attr == 0.0:
                can_apologize = False
            elif self.opp_len >= 15 and self._live_coop_rate() < 0.60:
                can_apologize = False'''
new_gate = '''            noise_attr = self.match_attributes.get("noise")
            # v5.4.4 Cycler Contour: против доказанного фиксированного
            # периодического паттерна извинение не запускается - периодические
            # D это паттерн оппонента, эксплуатацию ведёт базовый контур v5.3
            # (утечка v5.4.2: -1.16 SPT на CyclerCCD при 5% шума).
            if self.features.cycler_contour and self._detect_fixed_period(opponent):
                can_apologize = False
            elif noise_attr == 0.0:
                can_apologize = False
            elif self.opp_len >= 15 and self._live_coop_rate() < 0.60:
                can_apologize = False'''
assert old_gate in text, "gate block not found"
text = text.replace(old_gate, new_gate, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully created zeroresp_v544.py")
