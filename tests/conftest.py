"""Gemeinsame Fixtures: das Handbeispiel G, an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nst_scenario as S  # noqa: E402


@pytest.fixture
def g():
    """Handbeispiel G: 6 Variablen, 11 Klauseln, unerfüllbar (alle 64 Belegungen von Hand geprüft, hier noch einmal in test_rng_scenario.py)."""
    return S.HANDBEISPIEL_G


def rup(vorher, klausel) -> bool:
    """Unabhängiger RUP-Prüfer (Einheitspropagation auf die Negation der Klausel; eigene Schleife, kein Code aus nst_cdcl.py).
    Wahr genau dann, wenn aus `vorher` mit der verneinten `klausel` ein Widerspruch durch Einheitspropagation folgt."""
    wert = {abs(l): (l < 0) for l in klausel}
    geaendert = True
    while geaendert:
        geaendert = False
        for c in vorher:
            offen, erfuellt = [], False
            for l in c:
                w = wert.get(abs(l))
                if w is None:
                    offen.append(l)
                elif w == (l > 0):
                    erfuellt = True
                    break
            if erfuellt:
                continue
            if not offen:
                return True
            if len(offen) == 1:
                wert[abs(offen[0])] = offen[0] > 0
                geaendert = True
    return False
