"""Messskript der vorgerechneten Reihen (Reiter 3 und 4): schreibt `nst_messung_vorgerechnet.json` (**vorgerechnet, nicht live**).

Aufruf (Test-venv, aus dem Repo-Ordner):
    python -X utf8 tools/messung_neustarts.py --familie faerbung --teil mess  --out TEIL1.json
    python -X utf8 tools/messung_neustarts.py --familie zufall    --teil kurve --out TEIL2.json
    python -X utf8 tools/messung_neustarts.py --zusammen TEIL1.json TEIL2.json ...        # schreibt nst_messung_vorgerechnet.json

Teil `mess` (Reiter 3, Familienvergleich): je Aufgabe der festen Reihe (Färbung n = 160, Grad 4,5, 10 Aufgaben; Zufalls-3-SAT n = 150, m = 639, 12 Aufgaben)
30 Löser-Zufalls-Seeds (0 bis 29; zufälliger Start der Aktivitäten) für „keine“, Luby (Einheit 32) und geometrisch (erste Grenze 100, Faktor 1,5), Budget 200 000 Konflikte.
Teil `kurve` (Reiter 4): je Aufgabe 10 Löser-Zufalls-Seeds (0 bis 9) für „keine“, Luby mit Einheit 4, 8, 16, 32, 64, 128, 256 und geometrisch mit Faktor 1,1 / 1,3 / 1,5 / 2 (erste Grenze 100).
Gespeichert werden die Konfliktzahlen je Seed (Abbrüche am Budget zählen mit dem Budget) und die Antwort der Aufgabe (sie muss in allen Läufen gleich sein).
Aufwand wird nur in Konflikten gemessen; Sekunden stehen nirgends im Ergebnis.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import nst_algorithm as A  # noqa: E402
import nst_constants as C  # noqa: E402
import nst_scenario as S  # noqa: E402

FAMILIEN = {"faerbung": C.FAMILIE_FAERBUNG, "zufall": C.FAMILIE_ZUFALL}


def _antwort(antworten: set, abbrueche: int) -> str:
    if len(antworten) > 1:
        raise RuntimeError("Läufe widersprechen sich: erfüllbar und unerfüllbar")
    if not antworten:
        return "Abbruch"
    return "erfüllbar" if True in antworten else "unerfüllbar"


def messe_aufgabe(inst, teil: str) -> dict:
    antworten, abbr = set(), 0
    if teil == "mess":
        seeds = range(C.MESS_SEEDS)
        konf = {}
        configs = {"keine": (C.STRATEGIE_KEINE, 1, C.GEO_FAKTOR),
                   "luby": (C.STRATEGIE_LUBY, C.LUBY_EINHEIT_MESSUNG, C.GEO_FAKTOR),
                   "geo": (C.STRATEGIE_GEO, C.GEO_START_MESSUNG, C.GEO_FAKTOR)}
        for name, (strat, einheit, faktor) in configs.items():
            ks, ans, ab = A.konflikte_je_seed(inst, strat, einheit, seeds, budget=C.BUDGET_MESSUNG, faktor=faktor)
            konf[name] = ks
            antworten |= ans
            abbr += ab
        return {"antwort": _antwort(antworten, abbr), "abbrueche": abbr, **konf}
    seeds = range(C.KURVE_SEEDS)
    ks, ans, ab = A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, seeds, budget=C.BUDGET_MESSUNG)
    out = {"keine": ks, "luby": {}, "geo": {}}
    antworten |= ans
    abbr += ab
    for u in C.KURVE_EINHEITEN:
        ks, ans, ab = A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, u, seeds, budget=C.BUDGET_MESSUNG)
        out["luby"][str(u)] = ks
        antworten |= ans
        abbr += ab
    for f in C.KURVE_FAKTOREN:
        ks, ans, ab = A.konflikte_je_seed(inst, C.STRATEGIE_GEO, C.GEO_START_MESSUNG, seeds, budget=C.BUDGET_MESSUNG, faktor=f)
        out["geo"][str(f)] = ks
        antworten |= ans
        abbr += ab
    out["antwort"] = _antwort(antworten, abbr)
    out["abbrueche"] = abbr
    return out


def teil_messen(familie_key: str, teil: str, out: Path, von: int = 0, bis: int | None = None) -> None:
    """Misst die Aufgaben von … bis … (Indizes ab 0, `bis` ausgeschlossen); mehrere Teildateien einer Familie lassen sich mit `--zusammen` vereinen."""
    familie = FAMILIEN[familie_key]
    aufgaben = []
    for i in range(von, S.anzahl_messaufgaben(familie) if bis is None else bis):
        t0 = time.perf_counter()
        inst = S.messaufgabe(familie, i)
        eintrag = {"index": i, "seed": (C.FAERBUNG_AUFGABEN if familie == C.FAMILIE_FAERBUNG else C.ZUFALL_AUFGABEN)[i]}
        eintrag.update(messe_aufgabe(inst, teil))
        aufgaben.append(eintrag)
        print(f"{familie_key} {teil} Aufgabe {i}: {eintrag['antwort']}, {time.perf_counter() - t0:.0f} s", flush=True)
        out.write_text(json.dumps({"familie": familie, "teil": teil, "aufgaben": aufgaben}, ensure_ascii=False), encoding="utf-8")


def zusammen(teile: list, ziel: Path) -> None:
    data = {"meta": {
        "skript": C.MESSSKRIPT,
        "budget": C.BUDGET_MESSUNG,
        "mess_seeds": C.MESS_SEEDS,
        "kurve_seeds": C.KURVE_SEEDS,
        "luby_einheit": C.LUBY_EINHEIT_MESSUNG,
        "geo_start": C.GEO_START_MESSUNG,
        "geo_faktor": C.GEO_FAKTOR,
        "kurve_einheiten": list(C.KURVE_EINHEITEN),
        "kurve_faktoren": list(C.KURVE_FAKTOREN),
        "faerbung": {"n": C.FAERBUNG_N, "grad": C.GRAD, "rampen": C.RAMPEN, "seeds": list(C.FAERBUNG_AUFGABEN)},
        "zufall": {"n": C.ZUFALL_N, "m": C.ZUFALL_M, "seeds": list(C.ZUFALL_AUFGABEN)},
        "kern": "nst_cdcl.py (Kern-Version 832b2c10dfdea62d, Option restart_factor ergänzt)",
        "einheit": "Konflikte bis zur Antwort; Abbrüche zählen mit dem Budget (untere Schranke); keine Sekunden",
    }, "mess": {}, "kurve": {}}
    for pfad in teile:
        teil = json.loads(Path(pfad).read_text(encoding="utf-8"))
        data[teil["teil"]].setdefault(teil["familie"], []).extend(teil["aufgaben"])
    for teil in data["mess"], data["kurve"]:
        for familie in teil:
            teil[familie].sort(key=lambda a: a["index"])
            if [a["index"] for a in teil[familie]] != list(range(len(teil[familie]))):
                raise RuntimeError(f"Aufgaben von {familie} sind nicht lückenlos: {[a['index'] for a in teil[familie]]}")
    ziel.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    print("geschrieben:", ziel, ziel.stat().st_size, "Bytes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--familie", choices=list(FAMILIEN))
    ap.add_argument("--teil", choices=["mess", "kurve"])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--von", type=int, default=0, help="erste Aufgabe (Index ab 0)")
    ap.add_argument("--bis", type=int, default=None, help="letzte Aufgabe + 1 (Standard: alle)")
    ap.add_argument("--zusammen", nargs="+", type=Path, help="Teildateien zusammenführen und nst_messung_vorgerechnet.json schreiben")
    args = ap.parse_args()
    if args.zusammen:
        zusammen(args.zusammen, ROOT / C.MESSUNG_DATEI)
    else:
        teil_messen(args.familie, args.teil, args.out, args.von, args.bis)
