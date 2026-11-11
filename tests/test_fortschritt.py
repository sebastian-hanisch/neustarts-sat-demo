"""Reiter „Streuung gegen Median“ mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os

from streamlit.testing.v1 import AppTest

import nst_algorithm as A
import nst_constants as C
import nst_fortschritt as F
import nst_scenario as S

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _ungepuffert(familie, n, seed, seeds, budget):
    """Die Rechnung der App vor der Änderung: je Strategie `konflikte_je_seed` über alle Löser-Zufalls-Seeds auf einmal."""
    inst = S.aufgabe(familie, n, seed)
    konf, antworten, abbr = {}, set(), {}
    for s, einheit in F.KONFIG.items():
        konf[s], ans, abbr[s] = A.konflikte_je_seed(inst, s, einheit, range(seeds), budget=budget)
        antworten |= ans
    return inst, konf, abbr, antworten


def test_zwischengespeicherte_streuung_ist_gleich_der_ungepufferten():
    F.lauf_konflikte.clear()
    for familie, n, seed, seeds, budget in ((C.FAMILIE_FAERBUNG, 60, 1, 4, 3000), (C.FAMILIE_ZUFALL, 50, 2, 3, 2000)):
        direkt = _ungepuffert(familie, n, seed, seeds, budget)
        for _ in range(2):                                                   # zweiter Aufruf aus dem Zwischenspeicher
            inst, konf, abbr, antworten, sek = F.streuung(familie, n, seed, seeds, budget)
            assert (inst, konf, abbr, antworten) == direkt, (familie, n)
            assert sek >= 0


def test_zweiter_aufruf_rechnet_nichts_neu_ein_anderer_parameter_schon():
    F.lauf_konflikte.clear()
    v0 = F.gerechnet()
    erste = F.streuung(C.FAMILIE_FAERBUNG, 60, 1, 3, 2000)
    assert F.gerechnet() - v0 == 9
    v1 = F.gerechnet()
    assert F.streuung(C.FAMILIE_FAERBUNG, 60, 1, 3, 2000) == erste and F.gerechnet() == v1
    mehr = F.streuung(C.FAMILIE_FAERBUNG, 60, 1, 5, 2000)
    assert F.gerechnet() - v1 == 6, "bei mehr Löser-Zufalls-Seeds werden nur die neuen Läufe gerechnet"
    assert [mehr[1][s][:3] for s in C.STRATEGIEN] == [erste[1][s] for s in C.STRATEGIEN]
    v2 = F.gerechnet()
    andere_aufgabe = F.streuung(C.FAMILIE_FAERBUNG, 60, 2, 3, 2000)
    assert F.gerechnet() - v2 == 9 and andere_aufgabe[0] != erste[0], "ein anderer Zufalls-Seed der Aufgabe darf nicht aus dem Zwischenspeicher kommen"
    assert andere_aufgabe[1:4] == _ungepuffert(C.FAMILIE_FAERBUNG, 60, 2, 3, 2000)[1:]
    v3 = F.gerechnet()
    F.streuung(C.FAMILIE_FAERBUNG, 60, 1, 3, 1000)
    assert F.gerechnet() - v3 == 9, "ein anderes Budget darf nicht aus dem Zwischenspeicher kommen"
    v4 = F.gerechnet()
    F.streuung(C.FAMILIE_FAERBUNG, 70, 1, 3, 2000)
    assert F.gerechnet() - v4 == 9, "ein anderes n darf nicht aus dem Zwischenspeicher kommen"


def test_fortschritt_meldet_jeden_lauf_in_ordnung():
    F.lauf_konflikte.clear()
    meldungen = []
    F.streuung(C.FAMILIE_FAERBUNG, 40, 1, 2, 1000, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(i, 6) for i in range(1, 7)]


def test_app_zweiter_klick_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    F.lauf_konflikte.clear()
    v0 = F.gerechnet()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.slider(key="seeds_slider").set_value(5).run(timeout=TIMEOUT)
    at.button(key="streuung_rechnen").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    erste = [d.value.to_dict("records") for d in at.dataframe]
    v = F.gerechnet()
    assert v - v0 == 15
    at.button(key="streuung_rechnen").click().run(timeout=TIMEOUT)
    assert not at.exception and F.gerechnet() == v
    assert [d.value.to_dict("records") for d in at.dataframe] == erste
