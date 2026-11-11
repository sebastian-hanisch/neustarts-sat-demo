"""Neustart-Strategien und Läufe gegen das Handbeispiel (von Hand nachgerechnet, `sat-cp-planung/handbeispiele/hb_04.py`).

Handwerte: Luby-Folge 1 bis 15, Neustartzeitpunkte (Einheit 1, 2, 32; geometrisch 100, ×1,5), Lauf an der Formel G mit fester Entscheidungsregel."""

import pytest

import nst_algorithm as A
import nst_constants as C
from conftest import rup


def test_luby_folge_von_hand():
    assert A.luby_folge(15) == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]


@pytest.mark.parametrize("einheit, erwartet", [
    (1, [1, 2, 4, 5, 6, 8, 12, 13]),
    (2, [2, 4, 8, 10, 12, 16, 24, 26]),
    (32, [32, 64, 128, 160, 192, 256, 384, 416]),
])
def test_luby_zeitpunkte_von_hand(einheit, erwartet):
    """Kumulativ: Einheit 1: 1, 1+1, 2+2, 4+1, ... Die Tabelle ist die Summe der Grenzen u · (1, 1, 2, 1, 1, 2, 4, 1)."""
    assert A.zeitpunkte(C.STRATEGIE_LUBY, einheit, 8) == erwartet
    assert A.grenzen(C.STRATEGIE_LUBY, einheit, 3) == [einheit, einheit, 2 * einheit]


def test_geometrische_grenzen_und_zeitpunkte_von_hand():
    """100, 150, 225, 337 (aus 337,5), 506 (aus 506,25), 759 (aus 759,375): die Rundung geschieht erst bei der Grenze, nicht in der Folge; kumulativ 100, 250, 475, 812, 1 318, 2 077."""
    assert A.grenzen(C.STRATEGIE_GEO, 100, 6) == [100, 150, 225, 337, 506, 759]
    assert A.zeitpunkte(C.STRATEGIE_GEO, 100, 6) == [100, 250, 475, 812, 1318, 2077]
    assert A.grenzen(C.STRATEGIE_GEO, 10, 4, faktor=2.0) == [10, 20, 40, 80]


def test_keine_neustarts_hat_keine_grenzen():
    assert A.grenzen(C.STRATEGIE_KEINE, 32, 5) == [] and A.zeitpunkte(C.STRATEGIE_KEINE, 32, 5) == []
    with pytest.raises(ValueError):
        A.grenzen("zufaellig", 1, 1)


GELERNT = [{3, 1}, {4, -3, 1}, {-4}, {1}, {3}]   # die fünf gelernten Klauseln von G (hb_04_out.txt), als Mengen


@pytest.mark.parametrize("einheit, neustarts", [(1, [1, 4]), (2, [4]), (32, [])])
def test_handbeispiel_lauf_gleich_handwert(g, einheit, neustarts):
    """Formel G, Entscheidung: kleinste freie Variable, zuerst falsch. 6 Konflikte (der sechste auf Stufe 0: unerfüllbar), 5 gelernte Klauseln,
    Rücksprungstufen 1, 1, 0, 0, 0; Neustarts nach Konflikt 1 und 4 (Einheit 1), nach 4 (Einheit 2), keine (Einheit 32)."""
    zl = A.zeitleiste(g, C.STRATEGIE_LUBY, einheit, feste_regel=True)
    erg = zl.ergebnis
    assert erg.antwort is False and erg.stat["konflikte"] == 6 and erg.stat["gelernt"] == 5 and erg.stat["neustarts"] == len(neustarts)
    assert [n[0] for n in zl.neustarts] == neustarts
    assert zl.konflikt_stufe == [3, 3, 1, 1, 2, 0]
    assert zl.lernstufe == [1, 1, 0, 0, 0]
    gelernt = [set(e[1]) for e in erg.spur if e[0] == "lerne"]
    assert gelernt == GELERNT


def test_handbeispiel_neustartdetails(g):
    """Einheit 1: Der erste Neustart folgt nach Konflikt 1 aus Stufe 1, der zweite nach Konflikt 4 (drei Konflikte seit dem ersten) aus Stufe 1.
    Einheit 2: Die Grenze 2 ist nach Konflikt 2 erreicht, doch Konflikt 3 und 4 landen auf Stufe 0; erst nach Konflikt 4 steht wieder eine Entscheidung (Stufe 1)."""
    z1 = A.zeitleiste(g, C.STRATEGIE_LUBY, 1, feste_regel=True)
    assert z1.neustarts == [(1, 1, 1, 1), (4, 1, 3, 4)]       # (Konflikte, Stufe davor, Konflikte seit dem letzten Neustart, gelernte Klauseln)
    z2 = A.zeitleiste(g, C.STRATEGIE_LUBY, 2, feste_regel=True)
    assert z2.neustarts == [(4, 1, 4, 4)]


def test_handbeispiel_jede_gelernte_klausel_ist_aus_den_vorigen_herleitbar(g):
    """RUP (eigener Prüfer in conftest.py): jede gelernte Klausel folgt per Einheitspropagation aus G und den vorher gelernten; am Ende die leere Klausel."""
    erg = A.lauf(g, C.STRATEGIE_LUBY, 1, feste_regel=True, trace=True)
    db = [list(c) for c in g.klauseln]
    lernschritte = [e[1] for e in erg.spur if e[0] == "lerne"]
    assert len(lernschritte) == 5 and erg.antwort is False
    for klausel in lernschritte:
        assert rup(db, klausel)
        db.append(list(klausel))
    assert rup(db, [])


def test_handbeispiel_klauselzahl_am_ende(g):
    """Nur (x3 ∨ x1) und (x4 ∨ ¬x3 ∨ x1) haben mehr als ein Literal und stehen in der Datenbank; (¬x4), (x1), (x3) sind Einheiten auf Stufe 0: 11 + 2 Klauseln."""
    s = A.ZeitleistenLoeser(g.n, g.klauseln, vsids=False, phase_saving=False, restarts="luby", restart_unit=1, trace=True)
    s.loese()
    assert s.stat["gelernt"] == 5 and len(s.klauseln) == 11 + 2


def test_messung_und_statistik():
    xs = [5, 1, 9, 3, 7, 2, 8, 4, 6, 10]
    v = A.verteilung(xs, abbrueche=1)
    assert (v.median, v.minimum, v.maximum, v.abbrueche, v.n) == (5.5, 1, 10, 1, 10)
    assert v.p90 == 10                                   # Rang min(10 - 1, int(0,9 · 10)) = 9 -> zehnter Wert
    assert A.perzentil(list(range(1, 11)), 0.5) == 6 and A.perzentil([4], 0.9) == 4


def test_lauf_gibt_antwort_und_zaehler(g):
    erg = A.lauf(g, C.STRATEGIE_KEINE, 1, feste_regel=True)
    m = A.messung(erg)
    assert (m.antwort, m.konflikte, m.neustarts, m.gelernt, m.antwort_text) == (False, 6, 0, 5, "unerfüllbar")
    assert m.entscheidungen == erg.stat["entscheidungen"] > 0


def test_ereigniszeilen_des_handbeispiels(g):
    zeilen = A.ereignis_zeilen(A.lauf(g, C.STRATEGIE_LUBY, 1, feste_regel=True, trace=True).spur)
    texte = [z[2] for z in zeilen]
    assert texte[0] == "Entscheide ¬x1 (Stufe 1)"
    assert "Lerne (x3 ∨ x1), Rücksprung auf Stufe 1 (LBD 2)" in texte
    assert sum(1 for z in zeilen if z[1] == "neustart") == 2
    assert [z[0] for z in zeilen] == list(range(1, len(zeilen) + 1))
    assert any("Konflikt Nr. 6" in t and "Stufe 0" in t for t in texte)


def test_schubfach_3_im_kern_hat_nur_einen_neustart_nach_konflikt_2():
    """Der Plan beschrieb für PHP(3) (4 Tauben, 3 Löcher) Neustarts nach den Konflikten 1, 2, 4, 5 (Einheit 1). Der Kern rechnet bei gleicher Regel anders:
    6 Konflikte, 5 gelernte Klauseln, ein einziger Neustart (nach Konflikt 2), bei Einheit 1 und bei Einheit 2. Die Demo benutzt deshalb G als Handbeispiel (Abweichung in der README)."""
    import nst_instanzen as I
    p = I.pigeonhole(3)
    assert (p.n, len(p.klauseln)) == (12, 22)
    for einheit in (1, 2):
        zl = A.zeitleiste(p, C.STRATEGIE_LUBY, einheit, feste_regel=True)
        assert zl.ergebnis.antwort is False and zl.ergebnis.stat["konflikte"] == 6 and zl.ergebnis.stat["gelernt"] == 5
        assert [n[0] for n in zl.neustarts] == [2]
        gelernt = [e[1] for e in zl.ergebnis.spur if e[0] == "lerne"]
        assert gelernt == [[-5, 12, 9], [-3], [-6, 11, 8], [-2], [-6]]


def test_g_alle_drei_einheiten_gleiche_konflikte_verschiedene_neustartzahl(g):
    """Zweig-Test auf G: die Zahl der Neustarts ist bei Einheit 1, 2 und 32 verschieden (2, 1, 0), Konflikte und gelernte Klauseln sind gleich (6 und 5)."""
    ergebnisse = [A.lauf(g, C.STRATEGIE_LUBY, u, feste_regel=True) for u in (1, 2, 32)]
    assert [e.stat["neustarts"] for e in ergebnisse] == [2, 1, 0]
    assert {(e.stat["konflikte"], e.stat["gelernt"]) for e in ergebnisse} == {(6, 5)}


def test_tatsaechliche_neustarts_liegen_auf_oder_nach_den_fruehesten_zeitpunkten():
    """Der Plan nahm an, Einheit 1 erzeuge auf einer Aufgabe ohne Konflikt auf Stufe 0 genau die frühesten Zeitpunkte der Tabelle (1, 2, 4, 5, …). Das gilt nur, wenn nach jedem
    Konflikt eine Propagation ohne Folgekonflikt endet: Färbung n = 60, Zufalls-Seed 707 (4 Konflikte, keiner auf Stufe 0) erreicht die Tabelle (1, 2, 4); Zufalls-Seed 702 (8 Konflikte,
    keiner auf Stufe 0) liegt mit 2, 4, 7, 8 auf oder nach den Tabellenwerten 1, 2, 4, 5: ein Folgekonflikt verschiebt den Neustart."""
    import nst_scenario as S
    gleich = A.zeitleiste(S.aufgabe(C.FAMILIE_FAERBUNG, 60, 707), C.STRATEGIE_LUBY, 1, seed=0)
    assert 0 not in gleich.konflikt_stufe and [n[0] for n in gleich.neustarts] == [1, 2, 4] == A.zeitpunkte(C.STRATEGIE_LUBY, 1, 3)
    spaeter = A.zeitleiste(S.aufgabe(C.FAMILIE_FAERBUNG, 60, 702), C.STRATEGIE_LUBY, 1, seed=0)
    roh = [n[0] for n in spaeter.neustarts]
    assert 0 not in spaeter.konflikt_stufe and roh == [2, 4, 7, 8]
    assert all(r >= t for r, t in zip(roh, A.zeitpunkte(C.STRATEGIE_LUBY, 1, len(roh)))) and roh != A.zeitpunkte(C.STRATEGIE_LUBY, 1, len(roh))
