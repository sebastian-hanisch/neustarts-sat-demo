"""Eigenschaften der Neustarts und Zweig-Tests (Nullspalten-Regel: jede Variante weicht auf mindestens einer Aufgabe der Messreihe von der Nachbarvariante ab)."""

import pytest

import nst_algorithm as A
import nst_constants as C
import nst_evaluation as E
import nst_scenario as S


# ---------------------------------------------------------------- Eigenschaften
def test_die_antwort_haengt_nicht_von_der_strategie_ab():
    """Auf Färbungen mit n = 50 (erfüllbar und unerfüllbar gemischt) gibt jede Strategie und Einheit dieselbe Antwort; Abbrüche kommen nicht vor."""
    antworten = set()
    for i in range(12):
        inst = S.aufgabe(C.FAMILIE_FAERBUNG, 50, 600 + i)
        je_aufgabe = set()
        for strategie, einheit in ((C.STRATEGIE_KEINE, 1), (C.STRATEGIE_LUBY, 1), (C.STRATEGIE_LUBY, 32), (C.STRATEGIE_GEO, 5), (C.STRATEGIE_GEO, 100)):
            erg = A.lauf(inst, strategie, einheit, seed=i, budget=50000)
            assert erg.antwort is not None
            je_aufgabe.add(erg.antwort)
        assert len(je_aufgabe) == 1, i
        antworten |= je_aufgabe
    assert antworten == {True, False}


def test_ohne_neustarts_gibt_es_keine_neustart_ereignisse():
    inst = S.aufgabe(C.FAMILIE_FAERBUNG, 90, 801)
    zl = A.zeitleiste(inst, C.STRATEGIE_KEINE, 1, seed=0)
    assert zl.ergebnis.stat["konflikte"] > 20                 # ein Lauf mit Konflikten, sonst wäre die Aussage leer
    assert zl.ergebnis.stat["neustarts"] == 0 and zl.neustarts == [] and not [e for e in zl.ergebnis.spur if e[0] == "neustart"]


def test_derselbe_zufalls_seed_gibt_dieselbe_konfliktzahl():
    inst = S.aufgabe(C.FAMILIE_FAERBUNG, 80, 801)
    for strategie, einheit in ((C.STRATEGIE_KEINE, 1), (C.STRATEGIE_LUBY, 8), (C.STRATEGIE_GEO, 20)):
        a = A.konflikte_je_seed(inst, strategie, einheit, range(6), budget=20000)
        b = A.konflikte_je_seed(inst, strategie, einheit, range(6), budget=20000)
        assert a == b
    ks = A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, range(12), budget=20000)[0]
    assert len(set(ks)) > 1                                       # verschiedene Löser-Seeds streuen (sonst wären 30 Läufe eine Zahl)


def test_neustarts_verwerfen_nur_entscheidungen_gelernte_klauseln_bleiben():
    """Bei jedem Neustart steht die Zahl der gelernten Klauseln fest (sie ist nicht kleiner geworden) und danach beginnt die Suche auf Stufe 0:
    das nächste Ereignis nach „springe 0“ ist eine Entscheidung auf Stufe 1 oder das Ende."""
    inst = S.aufgabe(C.FAMILIE_FAERBUNG, 90, 802)
    zl = A.zeitleiste(inst, C.STRATEGIE_LUBY, 2, seed=1)
    spur = zl.ergebnis.spur
    for i, e in enumerate(spur):
        if e[0] == "neustart":
            assert spur[i + 1] == ("springe", 0)
            if i + 2 < len(spur):
                assert spur[i + 2][0] in ("entscheide", "konflikt") and (spur[i + 2][0] == "konflikt" or spur[i + 2][2] == 1)
    assert zl.neustarts


def test_jede_strategie_ist_auf_einer_live_aufgabe_nicht_tot():
    """Zweig-Test live: Luby und geometrisch lösen Neustarts aus, und die Konfliktzahlen weichen von „keine“ ab (Färbung n = 90, 8 Löser-Seeds)."""
    inst = S.aufgabe(C.FAMILIE_FAERBUNG, 90, 801)
    keine = A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, range(8), budget=20000)[0]
    luby = A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 8, range(8), budget=20000)[0]
    geo = A.konflikte_je_seed(inst, C.STRATEGIE_GEO, 20, range(8), budget=20000)[0]
    assert keine != luby and luby != geo and keine != geo
    assert A.zeitleiste(inst, C.STRATEGIE_LUBY, 8).neustarts and A.zeitleiste(inst, C.STRATEGIE_GEO, 20).neustarts


# ---------------------------------------------------------------- Zweig-Tests an der vorgerechneten Messreihe
def test_zweig_jede_strategie_weicht_in_der_messreihe_von_der_nachbarstrategie_ab():
    daten = E.lade_messung()
    for fam in C.FAMILIEN:
        aufgaben = daten["mess"][fam]
        for a, b in ((C.STRATEGIE_KEINE, C.STRATEGIE_LUBY), (C.STRATEGIE_LUBY, C.STRATEGIE_GEO), (C.STRATEGIE_KEINE, C.STRATEGIE_GEO)):
            verschieden = sum(1 for x in aufgaben if x[a] != x[b])
            assert verschieden >= 1, (fam, a, b)
            assert verschieden == len(aufgaben), (fam, a, b)    # in dieser Messreihe sogar auf jeder Aufgabe


def test_zweig_jede_einstellung_der_kurven_weicht_von_ihrer_nachbarin_ab():
    daten = E.lade_messung()
    meta = daten["meta"]
    for fam in C.FAMILIEN:
        aufgaben = daten["kurve"][fam]
        einheiten = [str(u) for u in meta["kurve_einheiten"]]
        faktoren = [str(f) for f in meta["kurve_faktoren"]]
        for a, b in zip(einheiten, einheiten[1:]):
            assert any(x["luby"][a] != x["luby"][b] for x in aufgaben), (fam, a, b)
        for a, b in zip(faktoren, faktoren[1:]):
            assert any(x["geo"][a] != x["geo"][b] for x in aufgaben), (fam, a, b)
        assert any(x["keine"] != x["luby"][einheiten[0]] for x in aufgaben)


def test_keine_nullspalte_in_der_messreihe():
    """Eine Spalte mit lauter Nullen hieße: die Variante läuft nie (toter Zweig). Kein Median ist 0, und es gibt in jeder Strategie Läufe mit Konflikten."""
    daten = E.lade_messung()
    for fam in C.FAMILIEN:
        for a in daten["mess"][fam]:
            for s in C.STRATEGIEN:
                assert len(a[s]) == daten["meta"]["mess_seeds"] and max(a[s]) > 0 and all(x >= 0 for x in a[s])
        for a in daten["kurve"][fam]:
            assert all(max(v) > 0 for v in a["luby"].values()) and all(max(v) > 0 for v in a["geo"].values())


def test_messdatei_ist_vollstaendig_und_konsistent():
    daten = E.lade_messung()
    meta = daten["meta"]
    assert meta["budget"] == C.BUDGET_MESSUNG and meta["mess_seeds"] == C.MESS_SEEDS and meta["kurve_seeds"] == C.KURVE_SEEDS
    assert len(daten["mess"][C.FAMILIE_FAERBUNG]) == 10 and len(daten["mess"][C.FAMILIE_ZUFALL]) == 12
    assert len(daten["kurve"][C.FAMILIE_FAERBUNG]) == 10 and len(daten["kurve"][C.FAMILIE_ZUFALL]) == 12
    for fam in C.FAMILIEN:
        for a in daten["mess"][fam]:
            assert a["antwort"] in ("erfüllbar", "unerfüllbar") and a["abbrueche"] == 0           # kein Abbruch am Budget in der Messreihe
        for a in daten["kurve"][fam]:
            assert a["antwort"] in ("erfüllbar", "unerfüllbar") and a["abbrueche"] == 0
            assert len(a["keine"]) == C.KURVE_SEEDS and set(a["luby"]) == {str(u) for u in C.KURVE_EINHEITEN} and set(a["geo"]) == {str(f) for f in C.KURVE_FAKTOREN}
        # beide Teile derselben Aufgabe haben dieselbe Antwort
        assert [a["antwort"] for a in daten["mess"][fam]] == [a["antwort"] for a in daten["kurve"][fam]]
    # die Löser-Seeds 0 bis 9 der Kurve sind die ersten zehn der Messreihe: gleiche Läufe, gleiche Konfliktzahlen für „keine“, Luby 32 und geometrisch 100 × 1,5
    for fam in C.FAMILIEN:
        for m, k in zip(daten["mess"][fam], daten["kurve"][fam]):
            assert m["keine"][: C.KURVE_SEEDS] == k["keine"]
            assert m["luby"][: C.KURVE_SEEDS] == k["luby"]["32"]
            assert m["geo"][: C.KURVE_SEEDS] == k["geo"]["1.5"]
