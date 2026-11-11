"""Kennzahlen, Verdikte (reine Funktionen) und Auswertung der vorgerechneten Messreihen.

Jedes Verdikt ist `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`. Jede Zahl im Text stammt aus den übergebenen Werten.
Schwellen (vor der Messung festgelegt, `tests/test_verdicts.py` schreibt sie fest):
  - „neutral“: der Quotient Median(mit Neustarts) / Median(ohne) liegt in [0,8; 1,2] (Band ±20 %, Grenzen inklusive); darunter „hilft“, darüber „schadet“;
  - Kurve „flach“: der größte Median-Quotient ist höchstens das 1,2-Fache des kleinsten.
"""

import json
import statistics
from pathlib import Path

import nst_algorithm as A
import nst_constants as C

HILFT, NEUTRAL, SCHADET = "hilft", "neutral", "schadet"


# ---------------------------------------------------------------------------------------------------------------- Zahlenformat
def zahl(x) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner (1 234, normales Leerzeichen), Halbe mit Dezimalkomma."""
    if isinstance(x, float) and not x.is_integer():
        return dezimal(x)
    return f"{int(x):,}".replace(",", " ")


def dezimal(x: float, stellen: int = 1) -> str:
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def prozent(q: float) -> str:
    """Quotient als Abweichung in Prozent mit Vorzeichen: 0,45 -> „−55 %“, 1,53 -> „+53 %“."""
    p = round((q - 1.0) * 100)
    return ("+" if p > 0 else "−" if p < 0 else "±") + f"{abs(p)} %"


# ---------------------------------------------------------------------------------------------------------------- Einordnung
def quotient(mit: float, ohne: float) -> float:
    """Median mit Neustarts durch Median ohne; ohne Konflikte auf beiden Seiten 1, sonst unendlich."""
    if ohne == 0:
        return 1.0 if mit == 0 else float("inf")
    return mit / ohne


def einordnung(q: float) -> str:
    """„hilft“ unter 0,8, „schadet“ über 1,2, dazwischen (Grenzen inklusive) „neutral“."""
    r = round(q - 1.0, 9)
    if r < -C.NEUTRAL_BAND:
        return HILFT
    if r > C.NEUTRAL_BAND:
        return SCHADET
    return NEUTRAL


def haeufigkeiten(quotienten) -> dict:
    z = {HILFT: 0, NEUTRAL: 0, SCHADET: 0}
    for q in quotienten:
        z[einordnung(q)] += 1
    return z


# ---------------------------------------------------------------------------------------------------------------- Reiter 1
def _strategie_text(strategie: str, einheit: int) -> str:
    if strategie == C.STRATEGIE_KEINE:
        return "ohne Neustarts"
    if strategie == C.STRATEGIE_LUBY:
        return f"mit Luby-Neustarts (Einheit {einheit})"
    return f"mit geometrischen Neustarts (erste Grenze {einheit})"


def verdict_handbeispiel(mit: A.Messung, ohne: A.Messung, strategie: str, einheit: int) -> tuple:
    """Verdikt zum Handbeispiel: nur die Mechanik, kein Nutzen. `mit` ist der Lauf mit der gewählten Strategie, `ohne` der Lauf ohne Neustarts."""
    if mit.antwort != ohne.antwort:
        return "error", f"Die Antworten unterscheiden sich ({mit.antwort_text} gegen {ohne.antwort_text}): das darf nicht vorkommen."
    wo = _strategie_text(strategie, einheit)
    if strategie == C.STRATEGIE_KEINE:
        return "info", f"Das Handbeispiel ist {mit.antwort_text}; der Lauf {wo} braucht {mit.konflikte} Konflikte und lernt {mit.gelernt} Klauseln."
    if mit.konflikte == ohne.konflikte:
        return "info", (f"Der Lauf {wo} hat {mit.neustarts} {'Neustart' if mit.neustarts == 1 else 'Neustarts'}; Antwort ({mit.antwort_text}) und Konfliktzahl ({mit.konflikte}) "
                        "sind dieselben wie ohne Neustarts. An dieser kleinen Aufgabe zeigt das Beispiel nur die Mechanik, keinen Nutzen.")
    return "info", (f"Der Lauf {wo} braucht {mit.konflikte} Konflikte bei {mit.neustarts} {'Neustart' if mit.neustarts == 1 else 'Neustarts'}, ohne Neustarts {ohne.konflikte} Konflikte; "
                    "an einer einzelnen Aufgabe sagt das nichts über die Wirkung der Neustarts.")


def verdict_lauf(m: A.Messung, strategie: str, einheit: int) -> tuple:
    """Verdikt zum Einzellauf der Zeitleiste (Reiter 1, Aufgabe aus der Seitenleiste)."""
    wo = _strategie_text(strategie, einheit)
    if m.antwort is None:
        return "warning", f"Das Budget wurde erreicht: nach {zahl(m.konflikte)} Konflikten {wo} ist keine Antwort bekannt (die Zahl ist eine untere Schranke)."
    if m.neustarts == 0:
        return "info", f"Antwort {m.antwort_text} nach {zahl(m.konflikte)} Konflikten {wo}; es gab keinen Neustart."
    return "info", (f"Antwort {m.antwort_text} nach {zahl(m.konflikte)} Konflikten {wo}, {zahl(m.neustarts)} {'Neustart' if m.neustarts == 1 else 'Neustarts'}. "
                    "Ein einzelner Lauf zeigt keine Wirkung; die Reiter „Streuung gegen Median“ und „Familienvergleich“ messen sie.")


# ---------------------------------------------------------------------------------------------------------------- Reiter 2
def zeile_streuung(konflikte, abbrueche: int) -> dict:
    v = A.verteilung(konflikte, abbrueche)
    return {"median": v.median, "p90": v.p90, "max": v.maximum, "min": v.minimum, "abbrueche": v.abbrueche, "n": v.n}


def verdict_streuung(zeilen: dict, familie_kurz: str) -> tuple:
    """`zeilen`: Strategie -> {median, p90, max, abbrueche, n} für „keine“, „luby“, „geo“ (aus `zeile_streuung`).
    Verdikt für Luby gegen „keine“ mit der Schwelle ±20 % des Medians; die Aussage „kleiner als die Streuung“ steht nur da, wenn sie stimmt."""
    k, l = zeilen[C.STRATEGIE_KEINE], zeilen[C.STRATEGIE_LUBY]
    q = quotient(l["median"], k["median"])
    kl = einordnung(q)
    ab = sum(z["abbrueche"] for z in zeilen.values())
    zusatz = f" {ab} Läufe brachen am Budget ab; ihre Konfliktzahlen sind untere Schranken." if ab else ""
    if kl == HILFT:
        text = (f"{familie_kurz}: Luby senkt den Median der Konflikte von {zahl(k['median'])} auf {zahl(l['median'])} ({prozent(q)}) "
                f"und das 90-Prozent-Rang-Maß (P90) von {zahl(k['p90'])} auf {zahl(l['p90'])} (Maximum {zahl(k['max'])} gegen {zahl(l['max'])}).")
        art = "success"
    elif kl == SCHADET:
        text = (f"{familie_kurz}: Luby erhöht den Median der Konflikte von {zahl(k['median'])} auf {zahl(l['median'])} ({prozent(q)}, außerhalb des Bandes ±20 %) "
                f"und das P90 von {zahl(k['p90'])} auf {zahl(l['p90'])}.")
        art = "warning"
    else:
        text = (f"{familie_kurz}: Luby verändert den Median der Konflikte von {zahl(k['median'])} auf {zahl(l['median'])} ({prozent(q)}, innerhalb des Bandes ±20 %: neutral); "
                f"das P90 geht von {zahl(k['p90'])} auf {zahl(l['p90'])}.")
        art = "info"
        if abs(k["median"] - l["median"]) < k["p90"] - k["median"]:
            text += f" Der Unterschied der Mediane ({zahl(abs(k['median'] - l['median']))}) ist kleiner als die Streuung ohne Neustarts (P90 minus Median = {zahl(k['p90'] - k['median'])})."
    g = zeilen.get(C.STRATEGIE_GEO)
    if g is not None:
        qg = quotient(g["median"], k["median"])
        text += f" Geometrisch: Median {zahl(g['median'])} ({prozent(qg)}, {einordnung(qg)}), P90 {zahl(g['p90'])}."
    return art, text + zusatz


# ---------------------------------------------------------------------------------------------------------------- Messdatei
_DATEI = Path(__file__).with_name(C.MESSUNG_DATEI)
_cache = {}


def lade_messung() -> dict:
    """Die vorgerechneten Messreihen (Datei `nst_messung_vorgerechnet.json`, Messskript `tools/messung_neustarts.py`)."""
    if "daten" not in _cache:
        _cache["daten"] = json.loads(_DATEI.read_text(encoding="utf-8"))
    return _cache["daten"]


def aufgaben_zeilen(daten: dict, familie: str) -> list:
    """Je Aufgabe der Messreihe (Reiter 3): Antwort, Median/P90/Maximum je Strategie, Quotienten und Einordnung für Luby und geometrisch."""
    zeilen = []
    for a in daten["mess"][familie]:
        zeile = {"index": a["index"], "seed": a["seed"], "antwort": a["antwort"], "abbrueche": a["abbrueche"]}
        for s in C.STRATEGIEN:
            zeile[s] = zeile_streuung(a[s], 0)
        for s in (C.STRATEGIE_LUBY, C.STRATEGIE_GEO):
            q = quotient(zeile[s]["median"], zeile[C.STRATEGIE_KEINE]["median"])
            zeile["q_" + s] = q
            zeile["klasse_" + s] = einordnung(q)
            zeile["p90_q_" + s] = quotient(zeile[s]["p90"], zeile[C.STRATEGIE_KEINE]["p90"])
        zeilen.append(zeile)
    return zeilen


def familien_zusammenfassung(zeilen: list, strategie: str) -> dict:
    qs = [z["q_" + strategie] for z in zeilen]
    pq = [z["p90_q_" + strategie] for z in zeilen]
    return {"n": len(zeilen), "haeufigkeit": haeufigkeiten(qs), "median_quotient": statistics.median(qs),
            "min_quotient": min(qs), "max_quotient": max(qs),
            "p90_kleiner": sum(1 for q in pq if q < 1.0), "median_p90_quotient": statistics.median(pq)}


def verdict_familien(zusammen: dict) -> tuple:
    """`zusammen`: Familien-Kurzname -> Zusammenfassung für Luby (aus `familien_zusammenfassung`). Zählt Aufgaben, sagt nichts über die Familie im Allgemeinen."""
    teile = []
    for name, z in zusammen.items():
        h = z["haeufigkeit"]
        teile.append(f"{name}: hilft bei {h[HILFT]}, neutral bei {h[NEUTRAL]}, schadet bei {h[SCHADET]} von {z['n']} Aufgaben "
                     f"(Quotient der Mediane Luby / keine: Median {dezimal(z['median_quotient'], 2)}, kleinster {dezimal(z['min_quotient'], 2)}, größter {dezimal(z['max_quotient'], 2)}); "
                     f"das P90 liegt bei {z['p90_kleiner']} von {z['n']} Aufgaben unter dem ohne Neustarts (Quotient der P90: Median {dezimal(z['median_p90_quotient'], 2)})")
    return "info", "Luby (Einheit 32) gegen keine Neustarts, je Aufgabe nach der Schwelle ±20 % des Medians: " + "; ".join(teile) + "."


def verdict_kern(zusammen: dict) -> tuple:
    """Verdikt der Kernfrage über der Reiter-Leiste, aus den vorgerechneten Messreihen (beide Familien)."""
    art, text = verdict_familien(zusammen)
    return art, text + " Gemessen an diesen Aufgaben und Größen; keine Aussage über andere Familien."


# ---------------------------------------------------------------------------------------------------------------- Reiter 4
def kurve_quotienten(daten: dict, familie: str) -> dict:
    """Je Einstellung („luby:4“, …, „geo:1.1“, …) die Quotienten Median(Einstellung) / Median(keine) je Aufgabe, in Aufgabenreihenfolge."""
    aufgaben = daten["kurve"][familie]
    out = {}
    for u in daten["meta"]["kurve_einheiten"]:
        out[f"luby:{u}"] = [quotient(statistics.median(a["luby"][str(u)]), statistics.median(a["keine"])) for a in aufgaben]
    for f in daten["meta"]["kurve_faktoren"]:
        out[f"geo:{f}"] = [quotient(statistics.median(a["geo"][str(f)]), statistics.median(a["keine"])) for a in aufgaben]
    return out


def kurve_zeilen(daten: dict, familie: str) -> list:
    """Je Einstellung: Median, kleinster und größter Quotient über die Aufgaben und die Einordnung des Medians."""
    zeilen = []
    for name, qs in kurve_quotienten(daten, familie).items():
        m = statistics.median(qs)
        zeilen.append({"name": name, "median": m, "min": min(qs), "max": max(qs), "klasse": einordnung(m), "hilft": haeufigkeiten(qs)[HILFT], "n": len(qs)})
    return zeilen


def kurven_spreizung(medians: list) -> float:
    """Verhältnis größter zu kleinster Median-Quotient einer Kurve."""
    return max(medians) / min(medians)


def verdict_kurve(zeilen: list, art: str, familie_kurz: str) -> tuple:
    """`art`: „luby“ oder „geo“. Flach, wenn der größte Median-Quotient der Kurve höchstens das 1,2-Fache des kleinsten ist; die beste Einstellung wird nur als „in dieser Messung am niedrigsten“ genannt."""
    kurve = [z for z in zeilen if z["name"].startswith(art + ":")]
    spr = kurven_spreizung([z["median"] for z in kurve])
    bester = min(kurve, key=lambda z: z["median"])
    schlechtester = max(kurve, key=lambda z: z["median"])
    name = {"luby": "Luby-Einheit", "geo": "geometrischer Faktor"}[art]
    wert = lambda z: z["name"].split(":")[1].replace(".", ",")
    if round(spr, 9) <= C.FLACH_VERHAELTNIS:
        return "info", (f"{familie_kurz}, {name}: die Kurve ist flach (größter Median-Quotient {dezimal(schlechtester['median'], 2)} gegen kleinster {dezimal(bester['median'], 2)}, "
                        f"Verhältnis {dezimal(spr, 2)} ≤ {dezimal(C.FLACH_VERHAELTNIS, 1)}): im Median über die Aufgaben ändert sich die Wirkung nur wenig; "
                        f"je Aufgabe liegen die Quotienten dieser Kurve zwischen {dezimal(min(z['min'] for z in kurve), 2)} und {dezimal(max(z['max'] for z in kurve), 2)}.")
    return "info", (f"{familie_kurz}, {name}: die Kurve ist nicht flach (Median-Quotient von {dezimal(bester['median'], 2)} bei {wert(bester)} bis {dezimal(schlechtester['median'], 2)} bei {wert(schlechtester)}, "
                    f"Verhältnis {dezimal(spr, 2)} > {dezimal(C.FLACH_VERHAELTNIS, 1)}). {wert(bester)} liegt in dieser Messung am niedrigsten; als allgemein gültig gilt das nicht.")


# ---------------------------------------------------------------------------------------------------------------- Tabellen
def tabelle_zeitpunkte(einheiten=(1, 2, 32), anzahl: int = C.TABELLEN_ZEILEN) -> list:
    """Zeilen „Einheit u: kumulative Neustartzeitpunkte“ (Luby), dazu die geometrische Folge (100, ×1,5)."""
    zeilen = [[f"Luby, Einheit {u}"] + A.zeitpunkte(C.STRATEGIE_LUBY, u, anzahl) for u in einheiten]
    zeilen.append(["geometrisch (100, ×1,5)"] + A.zeitpunkte(C.STRATEGIE_GEO, C.GEO_START_MESSUNG, anzahl))
    return zeilen
