"""Zufallsgenerator, Aufgaben und Handbeispiel G: feste Werte, Größen, Gleichheit bei gleichem Seed."""

import itertools

import nst_constants as C
import nst_instanzen as I
import nst_rng as R
import nst_scenario as S


def test_splitmix64_referenzwerte_und_ganzzahlig():
    g = R.SplitMix64(0)
    assert [g.next() for _ in range(2)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4]
    assert R.SplitMix64(7).below(10) == R.SplitMix64(7).below(10)
    assert isinstance(R.SplitMix64(1).next(), int) and isinstance(R.SplitMix64(1).below(5), int)


def test_kein_python_random_im_laufzeitcode():
    """Zufall nur über SplitMix64: weder `import random` noch ein Aufruf von `hash()` in den Laufzeitmodulen (Quelltext per ast gelesen, Docstrings zählen nicht)."""
    import ast
    from pathlib import Path
    wurzel = Path(__file__).resolve().parent.parent
    for datei in list(wurzel.glob("nst_*.py")) + [wurzel / "app.py"]:
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Import):
                assert "random" not in [a.name.split(".")[0] for a in knoten.names], datei.name
            elif isinstance(knoten, ast.ImportFrom):
                assert (knoten.module or "").split(".")[0] != "random", datei.name
            elif isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name):
                assert knoten.func.id != "hash", datei.name


def test_handbeispiel_g_ist_unerfuellbar_alle_64_belegungen():
    g = S.HANDBEISPIEL_G
    assert (g.n, len(g.klauseln)) == (6, 11)
    for bits in itertools.product((False, True), repeat=g.n):
        modell = {i + 1: b for i, b in enumerate(bits)}
        assert not I.pruefe_modell(g.klauseln, modell)


def test_aufgabe_ist_deterministisch_und_vom_seed_abhaengig():
    a = S.aufgabe(C.FAMILIE_FAERBUNG, 40, 5)
    assert a.klauseln == S.aufgabe(C.FAMILIE_FAERBUNG, 40, 5).klauseln
    assert a.klauseln != S.aufgabe(C.FAMILIE_FAERBUNG, 40, 6).klauseln
    z = S.aufgabe(C.FAMILIE_ZUFALL, 40, 5)
    assert z.klauseln == S.aufgabe(C.FAMILIE_ZUFALL, 40, 5).klauseln != S.aufgabe(C.FAMILIE_ZUFALL, 40, 6).klauseln


def test_groessen_der_aufgaben():
    """Färbung: n Aufträge, 3 Rampen, round(n · 4,5 / 2) Konflikte: 3n Variablen und n + 3 · Konflikte Klauseln. Zufall: n Variablen, round(4,26 n) Klauseln."""
    f = S.aufgabe(C.FAMILIE_FAERBUNG, 120, 500)
    assert f.n == 360 and len(f.meta["kanten"]) == 270 and len(f.klauseln) == 120 + 3 * 270
    z = S.aufgabe(C.FAMILIE_ZUFALL, 100, 500)
    assert z.n == 100 and len(z.klauseln) == 426


def test_messaufgaben_der_reihe():
    for i in range(len(C.FAERBUNG_AUFGABEN)):
        f = S.messaufgabe(C.FAMILIE_FAERBUNG, i)
        assert f.n == 480 and len(f.meta["kanten"]) == 360 and f.meta["seed"] == 500 + i and f.meta["einkleidung"] == "rampen"
    for i in range(len(C.ZUFALL_AUFGABEN)):
        z = S.messaufgabe(C.FAMILIE_ZUFALL, i)
        assert z.n == 150 and len(z.klauseln) == 639 and z.meta["seed"] == 2000 + i
    assert S.anzahl_messaufgaben(C.FAMILIE_FAERBUNG) == 10 and S.anzahl_messaufgaben(C.FAMILIE_ZUFALL) == 12     # mindestens zehn je Familie


def test_klauseltexte_und_beschreibung():
    assert S.klausel_text((3, -1)) == "(x3 ∨ ¬x1)" and S.klausel_text([]) == "(leer)"
    assert S.beschreibung(S.HANDBEISPIEL_G) == "Handbeispiel G: 6 Variablen, 11 Klauseln"
    assert "120 Aufträge auf 3 Rampen, 270 Konflikte (mittlerer Grad 4,5)" in S.beschreibung(S.aufgabe(C.FAMILIE_FAERBUNG, 120, 500))
    assert "Zufalls-3-SAT: 100 Variablen, 426 Klauseln (4,26 je Variable)" in S.beschreibung(S.aufgabe(C.FAMILIE_ZUFALL, 100, 500))
