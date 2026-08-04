# Registration snippets for Axelrod-Python

## 1. `axelrod/strategies/_strategies.py`

**Import** (with other late / `z` imports, or near related long-memory strategies):

```python
from .zeroresp import ZeroResp
```

**`all_strategies` list** — add alphabetically:

```python
    ZeroResp,
```

## 2. `docs/reference/all_strategies.rst`

If a new module file was added, include:

```rst
.. automodule:: axelrod.strategies.zeroresp
    :members:
```

## 3. Optional: strategy index / bibliography

Docstring `Names` section lists ZeroResp / ZeroResp v2.2 / EpochRedLine.  
No external paper citation is required for an original strategy; if you later publish, add an entry to `docs/reference/bibliography.rst`.

## 4. Classifier table rebuild (if the project still uses it)

```bash
python rebuild_classifier_table.py
```

## 5. Verify import

```python
import axelrod as axl
p = axl.ZeroResp()
print(p.name, p.classifier["stochastic"])
```
