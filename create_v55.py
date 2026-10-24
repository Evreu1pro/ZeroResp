import re
from pathlib import Path

source_path = Path("zeroresp_v54.py")
target_path = Path("zeroresp_v55.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace version header and name
text = text.replace("ZeroResp v5.4-proto", "ZeroResp v5.5")
text = text.replace('"ZeroResp v5.4-proto"', '"ZeroResp v5.5"')

# Add new feature flags to Features.__slots__
old_slots = '''        "tactical_prefilter",
        "profile_memory",
    )'''

new_slots = '''        "tactical_prefilter",
        "profile_memory",
        # v5.5 new
        "symmetric_noise_sensor",
        "warmup_calibration",
        "pulsed_harvest",
        "circuit_breaker",
    )'''
assert old_slots in text, "old_slots not found"
text = text.replace(old_slots, new_slots, 1)

# Add parameters to Features.__init__
old_init_args = '''        adaptive_harvest: bool = False,
        balance_apology: bool = False,
        tactical_prefilter: bool = False,
        profile_memory: bool = False,
    ):'''

new_init_args = '''        adaptive_harvest: bool = True,
        balance_apology: bool = True,
        tactical_prefilter: bool = True,
        profile_memory: bool = True,
        symmetric_noise_sensor: bool = True,
        warmup_calibration: bool = True,
        pulsed_harvest: bool = True,
        circuit_breaker: bool = True,
    ):'''
assert old_init_args in text, "old_init_args not found"
text = text.replace(old_init_args, new_init_args, 1)

# Add assignments in Features.__init__
old_inits = '''        self.tactical_prefilter = tactical_prefilter
        self.profile_memory = profile_memory'''

new_inits = '''        self.tactical_prefilter = tactical_prefilter
        self.profile_memory = profile_memory
        self.symmetric_noise_sensor = symmetric_noise_sensor
        self.warmup_calibration = warmup_calibration
        self.pulsed_harvest = pulsed_harvest
        self.circuit_breaker = circuit_breaker'''
assert old_inits in text, "old_inits not found"
text = text.replace(old_inits, new_inits, 1)

# Update ZeroResp class attributes
old_class_attrs = '''    NL_BALANCE_FLOOR = -4  # ниже этого баланса - принудительный откат в C
    NL_SOFTNESS_FLOOR = 0.30  # ниже этого forg эксплуатация не пробуется'''

new_class_attrs = '''    NL_BALANCE_FLOOR = -4  # ниже этого баланса - принудительный откат в C
    NL_SOFTNESS_FLOOR = 0.30  # ниже этого forg эксплуатация не пробуется
    WARMUP_TURNS = 20         # раунды начальной калибровки
    PULSE_COOLDOWN = 10       # минимальная пауза между импульсами харвеста под шумом'''
assert old_class_attrs in text, "old_class_attrs not found"
text = text.replace(old_class_attrs, new_class_attrs, 1)

# In _init_state:
old_init_state = '''        self._known_soft_opponent = False
        self._profile_checked = False'''

new_init_state = '''        self._known_soft_opponent = False
        self._profile_checked = False
        self.is_rigid = False
        self.last_pulse_step = 0'''
assert old_init_state in text, "old_init_state not found"
text = text.replace(old_init_state, new_init_state, 1)

# In _nl_noise_proven:
old_noise_proven = '''    def _nl_noise_proven(self) -> bool:
        # Канальный шум доказывается только НАШИМИ флипами C->D: D оппонента
        # и наш шум не различить, а собственный флип — независимое доказательство.
        # При 0% nl_my_flips == 0 и лестница уснёт (поведение как в v5.2 без потерь).
        return self.nl_my_flips > 0'''

new_noise_proven = '''    def _nl_noise_proven(self) -> bool:
        if self.nl_my_flips > 0:
            return True
        if self.features.symmetric_noise_sensor:
            # Двусторонний сенсор 50/50: если в мирной фазе (CC) оппонент выдал >=2 unprovoked D
            # при достаточном числе наблюдений (>=10 пар CC) - это статистическое доказательство шума
            return (self.unprovoked_d >= 2 and self.cc_pairs >= 10)
        return False'''
assert old_noise_proven in text, "old_noise_proven not found"
text = text.replace(old_noise_proven, new_noise_proven, 1)

# Replace noise estimation in strategy:
old_est = '''                    if self.cc_pairs % 5 == 0 and self.cc_pairs > 10:
                        if self._nl_active():
                            total = self.cc_pairs + self.nl_my_obs
                            est_n = self.unprovoked_d + self.nl_my_flips
                        else:
                            total, est_n = self.cc_pairs, self.unprovoked_d
                        self.p_noise_est = est_n / max(1, total)'''

new_est = '''                    if self.cc_pairs % 5 == 0 and self.cc_pairs > 10:
                        if self.features.symmetric_noise_sensor or self._nl_active():
                            total = self.cc_pairs + self.nl_my_obs
                            est_n = self.unprovoked_d + self.nl_my_flips
                        else:
                            total, est_n = self.cc_pairs, self.unprovoked_d
                        self.p_noise_est = est_n / max(1, total)'''
assert old_est in text, "old_est not found"
text = text.replace(old_est, new_est, 1)

# Now in _nl_ladder: harvest planning logic
# We update the harvest gate to support warmup, rigidity, and pulsed harvesting under noise
old_ladder_harvest = '''            if self.features.adaptive_harvest:
                # v5.4: непрерывная вероятность/размер вместо бинарного 0.6-гейта
                softness = (forg - self.NL_SOFTNESS_FLOOR) / (1.0 - self.NL_SOFTNESS_FLOOR)
                softness = max(0.0, min(1.0, softness))
                if (
                    softness > 0 and min_d and not blocked_tactical
                    and self.nl_balance >= 0 and not self._is_noisy_regime()
                    and self._random.random() < softness
                ):
                    size = int(round(
                        self.NL_HARVEST_MIN + softness * (self.NL_HARVEST_MAX - self.NL_HARVEST_MIN)
                    ))
                    self.nl_harvest_size = max(self.NL_HARVEST_MIN, size)
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(6, 10)
            else:
                if (
                    forg > 0.6 and min_d and not blocked_tactical
                    and self.nl_balance >= 0 and not self._is_noisy_regime()
                ):
                    self.nl_harvest_size = self._random.randint(self.NL_HARVEST_MIN, self.NL_HARVEST_MAX)
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(6, 10)'''

new_ladder_harvest = '''            # v5.5: Warmup & Rigidity check
            in_warmup = self.features.warmup_calibration and (step <= self.WARMUP_TURNS)
            if self.opp_defects_after_my_D > 0 and self.my_D <= 3:
                # Оппонент ответил D на наши первые вынужденные/шумовые D -> жёсткий!
                self.is_rigid = True

            can_harvest = (
                not in_warmup
                and not self.is_rigid
                and min_d
                and not blocked_tactical
                and self.nl_balance >= 0
            )

            is_noisy = self._is_noisy_regime()

            if can_harvest and is_noisy and self.features.pulsed_harvest:
                # v5.5: Импульсный харвест под шумом!
                # Вместо пачки 3-4 D (которая вызывает войну), даём ровно 1 импульс D
                # с обязательным кулдауном и проверкой реакции
                softness = (forg - self.NL_SOFTNESS_FLOOR) / (1.0 - self.NL_SOFTNESS_FLOOR)
                softness = max(0.0, min(1.0, softness))
                if (
                    softness > 0.4
                    and (step - self.last_pulse_step >= self.PULSE_COOLDOWN)
                    and self._random.random() < softness
                ):
                    self.nl_harvest_size = 1
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(4, 8)
                    self.last_pulse_step = step
            elif can_harvest and not is_noisy:
                if self.features.adaptive_harvest:
                    softness = (forg - self.NL_SOFTNESS_FLOOR) / (1.0 - self.NL_SOFTNESS_FLOOR)
                    softness = max(0.0, min(1.0, softness))
                    if softness > 0 and self._random.random() < softness:
                        size = int(round(
                            self.NL_HARVEST_MIN + softness * (self.NL_HARVEST_MAX - self.NL_HARVEST_MIN)
                        ))
                        self.nl_harvest_size = max(self.NL_HARVEST_MIN, size)
                        self.nl_harvest_left = 0
                        self.nl_harvest_postponed = 0
                        self.nl_harvest_scheduled_at = step + self._random.randint(6, 10)
                elif forg > 0.6:
                    self.nl_harvest_size = self._random.randint(self.NL_HARVEST_MIN, self.NL_HARVEST_MAX)
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(6, 10)'''
assert old_ladder_harvest in text, "old_ladder_harvest not found"
text = text.replace(old_ladder_harvest, new_ladder_harvest, 1)

# Add Circuit Breaker in strategy:
old_balance_apology = '''        # v5.4: баланс ушёл в минус из-за нашей же эксплуатации - откатываем
        # запланированные удары/харвест и подталкиваем к примирению, не трогая
        # обычный debt/queue (это реакция на риск от НАШЕЙ инициативы, а не
        # капитуляция перед чужой агрессией)
        if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
            self.nl_scheduled = []
            self.nl_harvest_left = 0
            self.nl_harvest_scheduled_at = 0
            self.nl_harvest_postponed = 0
            self.nl_harvest_size = 0
            self.nl_evidence = 0
            self.nl_window.clear()
            self.echo_forgive = max(self.echo_forgive, 2)
            self.warmth = max(self.warmth, 0.6)
            self.target_warmth = max(self.target_warmth, 0.6)'''

new_balance_apology = '''        # v5.5: Аппаратный Стоп-кран (Circuit Breaker) + Balance Apology
        # Если баланс ушёл в минус или оппонент наказал наш импульс дефекта
        pulse_punished = (
            self.features.circuit_breaker
            and self.last_pulse_step > 0
            and (step - self.last_pulse_step) <= 3
            and opponent.history
            and opponent.history[-1] == D
        )
        if pulse_punished:
            self.is_rigid = True  # оппонент огрызнулся на импульс -> больше не трогаем!

        trip_breaker = (
            (self.features.circuit_breaker and self.nl_balance < 0 and self.last_pulse_step > 0)
            or (self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR)
            or pulse_punished
        )

        if trip_breaker:
            self.nl_scheduled = []
            self.nl_harvest_left = 0
            self.nl_harvest_scheduled_at = 0
            self.nl_harvest_postponed = 0
            self.nl_harvest_size = 0
            self.nl_evidence = 0
            self.nl_window.clear()
            self.echo_forgive = max(self.echo_forgive, 2)
            self.warmth = max(self.warmth, 0.65)
            self.target_warmth = max(self.target_warmth, 0.65)'''
assert old_balance_apology in text, "old_balance_apology not found"
text = text.replace(old_balance_apology, new_balance_apology, 1)

# Add factory function at the end
old_footer = '''ZeroRespV5 = ZeroResp
ZeroRespV51 = ZeroResp
ZeroRespV52 = ZeroResp


def ZeroRespV54Full(**kw):
    """Прототип со всеми v5.4-экспериментами включёнными сразу."""
    feats = Features(adaptive_harvest=True, balance_apology=True,
                      tactical_prefilter=True, profile_memory=True)
    return ZeroResp(features=feats, **kw)'''

new_footer = '''ZeroRespV5 = ZeroResp
ZeroRespV51 = ZeroResp
ZeroRespV52 = ZeroResp
ZeroRespV54 = ZeroResp


def ZeroRespV55Full(**kw):
    """ZeroResp v5.5 с симметричным сенсором 50/50, фазой калибровки,
    импульсным харвестом и аппаратным стоп-краном."""
    feats = Features(
        adaptive_harvest=True,
        balance_apology=True,
        tactical_prefilter=True,
        profile_memory=True,
        symmetric_noise_sensor=True,
        warmup_calibration=True,
        pulsed_harvest=True,
        circuit_breaker=True,
    )
    return ZeroResp(features=feats, **kw)'''
assert old_footer in text, "old_footer not found"
text = text.replace(old_footer, new_footer, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Successfully wrote {target_path}")
