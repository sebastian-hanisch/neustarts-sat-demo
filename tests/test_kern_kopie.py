"""Regressionstests der kopierten Kern-Module (nst_rng, nst_instanzen, nst_cdcl): dieselben Handwerte wie im Kern-Paket der Linie.

Die Module sind Kopien von `sat-cp-planung/kern/` (Kern-Version im Modulkopf); die Tests hier laufen ohne den Kern-Ordner."""

import pytest

import nst_cdcl as K
import nst_instanzen as I
from nst_cdcl import Loeser, luby, solve
from nst_rng import SplitMix64


def test_splitmix_bekannte_werte():
    # Veröffentlichte Referenzwerte der SplitMix64-Konvention für Seed 0 (Vigna)
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    assert SplitMix64(12345).next() == 2454886589211414944


def test_rand3_regression_und_praefix():
    inst = I.rand3(20, 30, 1)
    assert inst.n == 20 and len(inst.klauseln) == 30
    assert all(len({abs(l) for l in c}) == 3 for c in inst.klauseln)
    assert I.rand3(20, 40, 1).klauseln[:30] == inst.klauseln          # wächst m, bleiben die früheren Klauseln
    assert I.rand3(20, 30, 1).klauseln == inst.klauseln               # deterministisch
    assert I.rand3(20, 30, 2).klauseln != inst.klauseln


def test_schubfach_handwerte():
    inst = I.pigeonhole(2)                      # 3 Tauben, 2 Löcher
    assert inst.n == 6 and len(inst.klauseln) == 3 + 2 * 3
    assert (1, 2) in inst.klauseln and (-1, -3) in inst.klauseln
    assert solve(inst.n, inst.klauseln).antwort is False


def test_schur_grenze():
    assert solve(*I.schur(13, 3)[:2]).antwort is True
    assert solve(*I.schur(14, 3)[:2]).antwort is False           # S(3) = 13


def test_luby_folge():
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]
    with pytest.raises(ValueError):
        luby(0)


def test_propagation_kette():
    # Auf Stufe 0 werden Klauseln schon beim Aufnehmen vereinfacht: (x1)(¬x1 ∨ x2)(¬x2 ∨ x3) ergibt die Einheiten 1, 2, 3 ohne Grund.
    for watch in (True, False):
        s = Loeser(3, [(1,), (-1, 2), (-2, 3)], watch=watch)
        assert s.propagiere() is None
        assert [s.wert[v] for v in (1, 2, 3)] == [1, 1, 1] and s.spur_lit == [1, 2, 3]
        t = Loeser(3, [(-1, 2), (-2, 3)], watch=watch)
        t.entscheide(1)
        assert t.propagiere() is None
        assert t.spur_lit == [1, 2, 3] and t.grund[2] == 0 and t.grund[3] == 1


@pytest.mark.parametrize("watch", [True, False])
def test_konfliktanalyse_1uip_handrechnung(watch):
    """c1 = (¬1 ∨ 2), c2 = (¬1 ∨ 3 ∨ 5), c3 = (¬2 ∨ 4), c4 = (¬3 ∨ ¬4). Entscheidung ¬5 (Stufe 1), dann 1 (Stufe 2): 1 → 2, 1 ∧ ¬5 → 3, 2 → 4, c4 verletzt.
    Gelernt wird (¬1 ∨ 5), Rücksprung auf Stufe 1, LBD 2."""
    s = Loeser(5, [(-1, 2), (-1, 3, 5), (-2, 4), (-3, -4)], watch=watch)
    s.entscheide(-5)
    assert s.propagiere() is None
    s.entscheide(1)
    k = s.propagiere()
    assert k is not None
    klausel, rueck, lbd = s.analysiere(k)
    assert sorted(klausel) == [-1, 5] and klausel[0] == -1 and rueck == 1 and lbd == 2


def test_rueckspringen_stellt_zustand_her():
    s = Loeser(5, [(-1, 2), (-1, 3, 5), (-2, 4), (-3, -4)])
    s.entscheide(-5)
    s.propagiere()
    s.entscheide(1)
    s.propagiere()
    assert len(s.grenzen) == 2 and s.wert[4] == 1
    s.springe_zurueck(1)
    assert len(s.grenzen) == 1 and s.spur_lit == [-5]
    s.springe_zurueck(0)
    assert s.spur_lit == [] and s.wert[5] == 0 and s.gemerkt[5] is False and s.gemerkt[1] is True


def test_budget_und_zaehler():
    inst = I.pigeonhole(6)
    erg = solve(inst.n, inst.klauseln, conflict_budget=50)
    assert erg.antwort is None and erg.stat["konflikte"] == 50
    voll = solve(inst.n, inst.klauseln)
    assert voll.antwort is False and 0 < voll.stat["gelernt"] <= voll.stat["konflikte"]


def test_schubfach_konfliktzahlen_wie_im_kern():
    """Deterministische Instanzen liefern dieselben Zähler wie im Kern-Paket (Schubfach h = 3 bis 5: 7 / 28 / 159 Konflikte)."""
    assert [solve(p.n, p.klauseln).stat["konflikte"] for p in (I.pigeonhole(h) for h in (3, 4, 5))] == [7, 28, 159]


def test_restart_faktor_standard_ist_der_wert_des_kerns():
    """Die einzige inhaltliche Änderung gegenüber dem Kern: `restart_factor` (Standard 1,5). Mit dem Standard und ausdrücklich 1,5 rechnet der Löser gleich."""
    inst = I.pigeonhole(5)
    a = solve(inst.n, inst.klauseln, restarts="geo", restart_unit=5)
    b = solve(inst.n, inst.klauseln, restarts="geo", restart_unit=5, restart_factor=1.5)
    assert a.stat == b.stat and a.stat["neustarts"] > 0
    c = solve(inst.n, inst.klauseln, restarts="geo", restart_unit=5, restart_factor=2.0)
    assert c.antwort is False and c.stat["neustarts"] != a.stat["neustarts"]
    assert K.Loeser(3, [(1, 2, 3)]).neustart_faktor == 1.5
