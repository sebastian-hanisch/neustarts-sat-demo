"""Szenario: die Aufgaben der Demo (Handbeispiel G, Aufträge auf Rampen, Zufalls-3-SAT).

Alle Zufallsaufgaben stammen aus dem SplitMix64 (`nst_rng.py`) über `nst_instanzen.py`; gleiche Angaben geben dieselbe Aufgabe.
Literale sind ganze Zahlen (+v wahr, -v falsch).
"""

import nst_constants as C
import nst_instanzen as I
from nst_instanzen import Instanz

# Handbeispiel G: 6 Variablen, 11 Klauseln, unerfüllbar (alle 64 Belegungen von Hand und im Test geprüft)
HANDBEISPIEL_G = Instanz(
    6,
    [(-4, -1, 2), (-4, -6), (1, 4, 5), (5, -3, -1), (1, -4, 3), (6, 5), (-6, 4, 3), (3, 6), (-5, -4), (-5, -3, 4), (-5, 3)],
    {"art": "handbeispiel", "erfuellbar": False},
)


def aufgabe(familie: str, n: int, seed: int) -> Instanz:
    """Aufgabe der gewählten Familie: Färbung = n Aufträge, mittlerer Grad 4,5, 3 Rampen; Zufall = n Variablen, gerundet 4,26 n Klauseln."""
    if familie == C.FAMILIE_FAERBUNG:
        return I.rampen_instanz(n, C.GRAD, seed, C.RAMPEN)
    if familie == C.FAMILIE_ZUFALL:
        return I.rand3(n, round(C.KLAUSEL_VERHAELTNIS * n), seed)
    raise ValueError(f"unbekannte Familie: {familie}")


def messaufgabe(familie: str, index: int) -> Instanz:
    """Aufgabe Nr. `index` (ab 0) der festen Messreihe: Färbung n = 160 (Seeds 500 + i), Zufall n = 150, m = 639 (Seeds 2000 + i)."""
    if familie == C.FAMILIE_FAERBUNG:
        return I.rampen_instanz(C.FAERBUNG_N, C.GRAD, C.FAERBUNG_AUFGABEN[index], C.RAMPEN)
    if familie == C.FAMILIE_ZUFALL:
        return I.rand3(C.ZUFALL_N, C.ZUFALL_M, C.ZUFALL_AUFGABEN[index])
    raise ValueError(f"unbekannte Familie: {familie}")


def anzahl_messaufgaben(familie: str) -> int:
    return len(C.FAERBUNG_AUFGABEN) if familie == C.FAMILIE_FAERBUNG else len(C.ZUFALL_AUFGABEN)


def beschreibung(inst: Instanz) -> str:
    """Eine Zeile zur Aufgabe für die Anzeige."""
    meta = inst.meta
    if meta.get("art") == "handbeispiel":
        return f"Handbeispiel G: {inst.n} Variablen, {len(inst.klauseln)} Klauseln"
    if meta.get("art") == "faerbung":
        return (f"{meta['n_knoten']} Aufträge auf {meta['k']} Rampen, {len(meta['kanten'])} Konflikte (mittlerer Grad {str(meta['grad']).replace('.', ',')}); "
                f"{inst.n} Variablen, {len(inst.klauseln)} Klauseln")
    return f"Zufalls-3-SAT: {inst.n} Variablen, {len(inst.klauseln)} Klauseln ({f'{len(inst.klauseln) / inst.n:.2f}'.replace('.', ',')} je Variable)"


def literal_text(lit: int) -> str:
    return f"x{lit}" if lit > 0 else f"¬x{-lit}"


def klausel_text(klausel) -> str:
    return "(" + " ∨ ".join(literal_text(l) for l in klausel) + ")" if klausel else "(leer)"
