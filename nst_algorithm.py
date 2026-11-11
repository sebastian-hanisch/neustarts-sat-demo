"""Neustart-Strategien, Läufe und Zeitleiste (eigener Code dieses Repos; gerechnet wird mit der CDCL-Kopie `nst_cdcl.py`).

Ein **Neustart** wirft alle Entscheidungen weg (zurück auf Stufe 0) und behält alle gelernten Klauseln und die Aktivitäten.
Die Regel des Kerns: Nach einem Konflikt ohne Folgekonflikt wird geprüft, ob seit dem letzten Neustart mindestens `Grenze` Konflikte gezählt wurden
und mindestens eine Entscheidung auf dem Stapel liegt; dann findet der Neustart statt. Liegt die Grenze erreicht, aber der Stapel ist leer
(Konflikt auf Stufe 0), bleibt die „Schuld“ bestehen, und der Neustart folgt, sobald wieder eine Entscheidung steht.

Aufwand wird gezählt (Konflikte, Entscheidungen, Neustarts, gelernte Klauseln), nie in Sekunden.
"""

import statistics
from dataclasses import dataclass, field

import nst_cdcl as K
import nst_constants as C
from nst_cdcl import Loeser, luby

KERN_NAME = {C.STRATEGIE_KEINE: "none", C.STRATEGIE_LUBY: "luby", C.STRATEGIE_GEO: "geo"}


# ---------------------------------------------------------------------------------------------------------------- Strategien
def luby_folge(anzahl: int) -> list:
    """Die ersten `anzahl` Glieder der Luby-Folge 1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8, ..."""
    return [luby(i) for i in range(1, anzahl + 1)]


def grenzen(strategie: str, einheit: int, anzahl: int, faktor: float = C.GEO_FAKTOR) -> list:
    """Die ersten `anzahl` Grenzen (Konflikte zwischen zwei Neustarts). Luby: Einheit mal Luby-Glied.
    Geometrisch: erste Grenze = `einheit`, danach jede mit dem Faktor multipliziert und abgerundet (die Rundung geschieht erst bei der Grenze, nicht bei der Folge)."""
    if strategie == C.STRATEGIE_KEINE:
        return []
    if strategie == C.STRATEGIE_LUBY:
        return [einheit * luby(i) for i in range(1, anzahl + 1)]
    if strategie == C.STRATEGIE_GEO:
        lim, out = float(einheit), []
        for _ in range(anzahl):
            out.append(int(lim))
            lim *= faktor
        return out
    raise ValueError(f"unbekannte Strategie: {strategie}")


def zeitpunkte(strategie: str, einheit: int, anzahl: int, faktor: float = C.GEO_FAKTOR) -> list:
    """Kumulative Summe der Grenzen: nach so vielen Konflikten insgesamt ist die jeweilige Grenze erreicht (Neustart-Schuld entsteht)."""
    summe, out = 0, []
    for g in grenzen(strategie, einheit, anzahl, faktor):
        summe += g
        out.append(summe)
    return out


def kern_optionen(strategie: str, einheit: int, faktor: float = C.GEO_FAKTOR) -> dict:
    return {"restarts": KERN_NAME[strategie], "restart_unit": int(einheit), "restart_factor": float(faktor)}


# ---------------------------------------------------------------------------------------------------------------- Läufe
@dataclass(frozen=True)
class Messung:
    antwort: bool | None
    konflikte: int
    entscheidungen: int
    neustarts: int
    gelernt: int

    @property
    def antwort_text(self) -> str:
        return {True: "erfüllbar", False: "unerfüllbar", None: "Abbruch (Budget)"}[self.antwort]


def messung(erg) -> Messung:
    s = erg.stat
    return Messung(erg.antwort, s["konflikte"], s["entscheidungen"], s["neustarts"], s["gelernt"])


def lauf(inst, strategie: str, einheit: int, *, seed: int = 0, budget: int = C.BUDGET_MESSUNG, faktor: float = C.GEO_FAKTOR,
         feste_regel: bool = False, trace=False):
    """Ein Lauf der CDCL-Kopie. Standard: Aktivität (VSIDS) mit Phasenspeicher und zufälligem Start der Aktivitäten aus dem Löser-Zufalls-Seed.
    `feste_regel=True` (Handbeispiel): kleinste freie Variable, zuerst falsch, kein Zufall. Gibt das volle `Ergebnis` des Kerns zurück."""
    if feste_regel:
        opt = dict(vsids=False, phase_saving=False)
    else:
        opt = dict(vsids=True, phase_saving=True, noise=True, seed=seed)
    return K.solve(inst.n, inst.klauseln, conflict_budget=budget, trace=trace, **opt, **kern_optionen(strategie, einheit, faktor))


def konflikte_je_seed(inst, strategie: str, einheit: int, seeds, *, budget: int = C.BUDGET_MESSUNG, faktor: float = C.GEO_FAKTOR) -> tuple:
    """(Konflikte je Löser-Zufalls-Seed, Antwort der Läufe, Zahl der Abbrüche). Abbrüche zählen mit dem Budget (untere Schranke)."""
    konflikte, antworten, abbrueche = [], set(), 0
    for sd in seeds:
        erg = lauf(inst, strategie, einheit, seed=sd, budget=budget, faktor=faktor)
        konflikte.append(erg.stat["konflikte"])
        if erg.antwort is None:
            abbrueche += 1
        else:
            antworten.add(erg.antwort)
    return konflikte, antworten, abbrueche


def perzentil(werte, q: float):
    """Rang-Perzentil wie in der Vormessung: sortierte Liste, Index min(Länge − 1, ⌊q · Länge⌋)."""
    xs = sorted(werte)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


@dataclass(frozen=True)
class Verteilung:
    median: float
    p90: float
    maximum: float
    minimum: float
    abbrueche: int
    n: int


def verteilung(konflikte, abbrueche: int = 0) -> Verteilung:
    return Verteilung(statistics.median(konflikte), perzentil(konflikte, 0.9), max(konflikte), min(konflikte), abbrueche, len(konflikte))


# ---------------------------------------------------------------------------------------------------------------- Zeitleiste
class ZeitleistenLoeser(Loeser):
    """`Loeser`, der nur die Ereignisse der Zeitleiste in `ereignisse` schreibt (entscheide, konflikt, lerne, springe, neustart).
    Der Kern begrenzt die Spur auf 5 000 Ereignisse; auf Aufgaben mit hundert Variablen füllen die Folgerungen („schliesse“) sie in Sekunden,
    deshalb werden sie hier verworfen. Gerechnet wird genau wie im Kern (nur `_ereignis` ist überschrieben)."""

    ERLAUBT = ("entscheide", "konflikt", "lerne", "springe", "neustart")

    def _ereignis(self, *e):
        if e[0] in self.ERLAUBT:
            self.ereignisse.append(e)


@dataclass
class Zeitleiste:
    """Verlauf eines Laufs je Konflikt (Listen gleicher Länge) und die Neustarts."""
    ergebnis: object
    konflikt_stufe: list = field(default_factory=list)       # Entscheidungsstufe, auf der Konflikt Nr. i + 1 auftrat
    lernstufe: list = field(default_factory=list)            # Rücksprungstufe nach Konflikt Nr. i + 1
    klausellaenge: list = field(default_factory=list)        # Länge der gelernten Klausel
    neustarts: list = field(default_factory=list)            # je Neustart: (Konflikte bis dahin, Stufe vor dem Neustart, Konflikte seit dem letzten Neustart, gelernte Klauseln bis dahin)


def zeitleiste(inst, strategie: str, einheit: int, *, seed: int = 0, budget: int = C.BUDGET_MESSUNG, faktor: float = C.GEO_FAKTOR,
               feste_regel: bool = False) -> Zeitleiste:
    """Lauf mit Zeitleiste. Die Neustarts werden aus den Ereignissen des Kerns abgelesen (Zahl der Konflikte, Stufe vor dem Neustart)."""
    if feste_regel:
        opt = dict(vsids=False, phase_saving=False)
    else:
        opt = dict(vsids=True, phase_saving=True, noise=True, seed=seed)
    loeser = ZeitleistenLoeser(inst.n, inst.klauseln, trace=True, **opt, **kern_optionen(strategie, einheit, faktor))
    erg = loeser.loese(conflict_budget=budget)
    zl = Zeitleiste(erg)
    stufe, konflikte, seit, gelernt = 0, 0, 0, 0
    for e in erg.spur:
        art = e[0]
        if art == "entscheide":
            stufe = e[2]
        elif art == "springe":
            stufe = e[1]
        elif art == "konflikt":
            konflikte += 1
            seit += 1
            zl.konflikt_stufe.append(e[2])
        elif art == "lerne":
            gelernt += 1
            zl.lernstufe.append(e[2])
            zl.klausellaenge.append(len(e[1]))
        elif art == "neustart":
            zl.neustarts.append((konflikte, stufe, seit, gelernt))
            seit = 0
    return zl


def ereignis_zeilen(spur) -> list:
    """Lesbare Zeilen der vollen Spur (für das Handbeispiel): (Nr., Art, Text). „beteiligt“ wird übersprungen."""
    from nst_scenario import klausel_text, literal_text
    zeilen, konflikte = [], 0
    for e in spur:
        art = e[0]
        if art == "entscheide":
            text = f"Entscheide {literal_text(e[1])} (Stufe {e[2]})"
        elif art == "schliesse":
            text = f"Folgere {literal_text(e[1])} aus {klausel_text(e[2])} (Stufe {e[3]})"
        elif art == "konflikt":
            konflikte += 1
            text = f"Konflikt Nr. {konflikte}: {klausel_text(e[1])} ist verletzt (Stufe {e[2]})"
        elif art == "lerne":
            text = f"Lerne {klausel_text(e[1])}, Rücksprung auf Stufe {e[2]} (LBD {e[3]})"
        elif art == "springe":
            text = f"Springe zurück auf Stufe {e[1]}"
        elif art == "neustart":
            text = f"**Neustart** nach {konflikte} {'Konflikt' if konflikte == 1 else 'Konflikten'} insgesamt: alle Entscheidungen verworfen, gelernte Klauseln bleiben"
        elif art == "loesche":
            text = f"Lösche {e[1]} gelernte Klauseln"
        else:
            continue
        zeilen.append((len(zeilen) + 1, art, text))
    return zeilen
