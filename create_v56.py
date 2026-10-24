from pathlib import Path

source_path = Path("zeroresp_v55.py")
target_path = Path("zeroresp_v56.py")

with open(source_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace version header and name
text = text.replace("ZeroResp v5.5", "ZeroResp v5.6")
text = text.replace('"ZeroResp v5.5"', '"ZeroResp v5.6"')

# Add early_exit_warmup to Features.__slots__
old_slots = '''        "circuit_breaker",
    )'''
new_slots = '''        "circuit_breaker",
        "early_exit_warmup",
    )'''
assert old_slots in text, "slots not found"
text = text.replace(old_slots, new_slots, 1)

# Add early_exit_warmup to Features.__init__
old_init_args = '''        pulsed_harvest: bool = True,
        circuit_breaker: bool = True,
    ):'''
new_init_args = '''        pulsed_harvest: bool = True,
        circuit_breaker: bool = True,
        early_exit_warmup: bool = True,
    ):'''
assert old_init_args in text, "init_args not found"
text = text.replace(old_init_args, new_init_args, 1)

old_inits = '''        self.pulsed_harvest = pulsed_harvest
        self.circuit_breaker = circuit_breaker'''
new_inits = '''        self.pulsed_harvest = pulsed_harvest
        self.circuit_breaker = circuit_breaker
        self.early_exit_warmup = early_exit_warmup'''
assert old_inits in text, "inits not found"
text = text.replace(old_inits, new_inits, 1)

# In _init_state:
old_init_state = '''        self.is_rigid = False
        self.last_pulse_step = 0'''
new_init_state = '''        self.is_rigid = False
        self.last_pulse_step = 0
        self.warmup_early_exited = False'''
assert old_init_state in text, "init_state not found"
text = text.replace(old_init_state, new_init_state, 1)

# Early exit warmup logic in strategy:
# In strategy, right after cc_pairs update:
old_cc = '''                    if self.cc_pairs % 5 == 0 and self.cc_pairs > 10:'''
new_cc = '''                    if self.features.early_exit_warmup and not self.warmup_early_exited:
                        if self.cc_pairs >= 10 and self.unprovoked_d == 0 and self.nl_my_flips == 0:
                            self.warmup_early_exited = True
                    if self.cc_pairs % 5 == 0 and self.cc_pairs > 10:'''
assert old_cc in text, "cc not found"
text = text.replace(old_cc, new_cc, 1)

# In _nl_ladder:
old_warmup = '''            in_warmup = self.features.warmup_calibration and (step <= self.WARMUP_TURNS)'''
new_warmup = '''            in_warmup = self.features.warmup_calibration and (step <= self.WARMUP_TURNS) and not self.warmup_early_exited'''
assert old_warmup in text, "warmup not found"
text = text.replace(old_warmup, new_warmup, 1)

# Update footer
old_footer = '''ZeroRespV54 = ZeroResp


def ZeroRespV55Full(**kw):'''

new_footer = '''ZeroRespV54 = ZeroResp
ZeroRespV55 = ZeroResp


def ZeroRespV56Full(**kw):
    """ZeroResp v5.6 с early-exit калибровкой, симметричным сенсором 50/50,
    импульсным сбором и аппаратным стоп-краном."""
    feats = Features(
        adaptive_harvest=True,
        balance_apology=True,
        tactical_prefilter=True,
        profile_memory=True,
        symmetric_noise_sensor=True,
        warmup_calibration=True,
        pulsed_harvest=True,
        circuit_breaker=True,
        early_exit_warmup=True,
    )
    return ZeroResp(features=feats, **kw)


def ZeroRespV55Full(**kw):'''
assert old_footer in text, "footer not found"
text = text.replace(old_footer, new_footer, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Successfully generated {target_path}")
