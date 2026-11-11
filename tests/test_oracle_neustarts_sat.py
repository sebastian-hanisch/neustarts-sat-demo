"""Orakel-Tests der Neustarts (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12): jeder Kernbaustein gegen einen anderen Rechenweg.

1. Luby-Folge gegen zwei unabhängig geschriebene Wege (Reluctant Doubling nach dem Zustand (u, v), und die rekursive Definition der Veröffentlichung), 200 Glieder.
2. Antwort jeder Strategie gegen Brute Force (alle 2^n Belegungen, n = 10, 60 Formeln) und gegen OR-Tools CP-SAT (Zufallsformeln und Färbungen, `importorskip`);
   jedes Modell wird gegen jede Klausel geprüft (`pruefe_modell`, unabhängig vom Löser).
3. Neustartzeitpunkte aus der Spur gegen die Konfliktzähler: die Abstände der Neustarts summieren sich zur kumulativen Tabelle (jede Grenze ist erreicht).
4. Jede gelernte Klausel ist aus den vorigen per Einheitspropagation herleitbar (RUP-Prüfer in `conftest.py`, eigene Schleife).
Der große Lauf (mehr als 200 Zufallsformeln) steht nicht im Repo, nur diese schnelle Fassung."""

import itertools

import pytest

import nst_algorithm as A
import nst_constants as C
import nst_instanzen as I
import nst_scenario as S
from conftest import rup


# ---------------------------------------------------------------- 1. Luby-Folge
def luby_reluctant_doubling(anzahl):
    """Knuth: Zustand (u, v), Folge 1, 1, 2, 1, 1, 2, 4, ... (anderer Rechenweg als die Rekursion in nst_cdcl.luby)."""
    out, u, v = [], 1, 1
    for _ in range(anzahl):
        out.append(v)
        if (u & -u) == v:
            u, v = u + 1, 1
        else:
            v *= 2
    return out


def luby_rekursiv(i):
    """Definition der Veröffentlichung: t_i = 2^(k-1) für i = 2^k - 1, sonst t_i = t_(i - 2^(k-1) + 1) für 2^(k-1) <= i < 2^k - 1."""
    k = 1
    while (1 << k) - 1 < i:
        k += 1
    if (1 << k) - 1 == i:
        return 1 << (k - 1)
    return luby_rekursiv(i - (1 << (k - 1)) + 1)


def test_luby_gegen_reluctant_doubling_und_rekursion_200_glieder():
    assert luby_reluctant_doubling(200) == [luby_rekursiv(i) for i in range(1, 201)]
    assert A.luby_folge(200) == luby_reluctant_doubling(200)
    assert luby_reluctant_doubling(15) == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]


def test_luby_zeitpunkte_gegen_unabhaengige_summe():
    for einheit in (1, 2, 7, 32):
        folge = luby_reluctant_doubling(40)
        kumulativ = list(itertools.accumulate(einheit * x for x in folge))
        assert A.zeitpunkte(C.STRATEGIE_LUBY, einheit, 40) == kumulativ


def test_geometrische_grenzen_gegen_exakte_bruchrechnung():
    """Grenze i = ⌊u · f^(i−1)⌋, mit Brüchen gerechnet (kein Gleitkomma): u = 100, f = 3/2; und f = 13/10, 11/10, 2."""
    from fractions import Fraction
    for f_text, f_bruch in ((1.5, Fraction(3, 2)), (1.3, Fraction(13, 10)), (1.1, Fraction(11, 10)), (2.0, Fraction(2))):
        erwartet = [int(Fraction(100) * f_bruch ** (i - 1)) for i in range(1, 13)]
        assert A.grenzen(C.STRATEGIE_GEO, 100, 12, faktor=f_text) == pytest.approx(erwartet, abs=1)   # Gleitkomma-Fortschreibung: höchstens 1 daneben
    assert A.grenzen(C.STRATEGIE_GEO, 100, 6) == [int(Fraction(100) * Fraction(3, 2) ** i) for i in range(6)]


# ---------------------------------------------------------------- 2. Antwort gegen Brute Force und CP-SAT
def brute_force(n, klauseln):
    for bits in itertools.product((False, True), repeat=n):
        if all(any((bits[abs(l) - 1] if l > 0 else not bits[abs(l) - 1]) for l in c) for c in klauseln):
            return True
    return False


STRATEGIEN = [(C.STRATEGIE_KEINE, 1), (C.STRATEGIE_LUBY, 1), (C.STRATEGIE_LUBY, 4), (C.STRATEGIE_GEO, 3)]


def test_antwort_jeder_strategie_gleich_brute_force():
    """60 Formeln mit 10 Variablen und 15 bis 60 Klauseln (erfüllbar und unerfüllbar gemischt), vier Einstellungen; Modell geprüft."""
    sat = unsat = 0
    for i in range(60):
        inst = I.rand3(10, 15 + i, 900 + i)
        wahr = brute_force(inst.n, inst.klauseln)
        sat += wahr
        unsat += not wahr
        for strategie, einheit in STRATEGIEN:
            erg = A.lauf(inst, strategie, einheit, seed=i, budget=100000)
            assert erg.antwort is wahr, (i, strategie, einheit)
            if wahr:
                assert I.pruefe_modell(inst.klauseln, erg.modell)
    assert sat >= 10 and unsat >= 10                      # beide Antworten kommen vor


def test_antwort_gleich_cpsat_auf_zufallsformeln_und_faerbungen():
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")

    def cpsat(inst):
        m = cp_model.CpModel()
        x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, inst.n + 1)]
        for c in inst.klauseln:
            m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
        status = cp_model.CpSolver().Solve(m)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.INFEASIBLE)
        return status != cp_model.INFEASIBLE

    aufgaben = [I.rand3(40, 170, 300 + i) for i in range(14)] + [S.aufgabe(C.FAMILIE_FAERBUNG, 40, 700 + i) for i in range(10)]
    antworten = set()
    for i, inst in enumerate(aufgaben):
        wahr = cpsat(inst)
        antworten.add(wahr)
        for strategie, einheit in STRATEGIEN:
            erg = A.lauf(inst, strategie, einheit, seed=i, budget=100000)
            assert erg.antwort is wahr, (i, strategie, einheit)
            if wahr:
                assert I.pruefe_modell(inst.klauseln, erg.modell)
    assert antworten == {True, False}


# ---------------------------------------------------------------- 3. Neustartzeitpunkte gegen Konfliktzähler
def _rohe_neustarts(spur):
    """Konflikte vor jedem Neustart, direkt aus der Spur gezählt (kein Hilfscode der Demo)."""
    k, out = 0, []
    for e in spur:
        if e[0] == "konflikt":
            k += 1
        elif e[0] == "neustart":
            out.append(k)
    return out


@pytest.mark.parametrize("strategie, einheit", [(C.STRATEGIE_LUBY, 1), (C.STRATEGIE_LUBY, 4), (C.STRATEGIE_GEO, 10)])
def test_neustartabstaende_summieren_sich_zur_kumulativen_tabelle(strategie, einheit):
    """Der i-te Neustart folgt nach mindestens T_i Konflikten (T_i = Summe der Grenzen g_1 bis g_i), jeder Abstand ist mindestens g_i,
    und die Summe der Abstände bis zum i-ten Neustart ist gleich der Konfliktzahl dort."""
    gesehen = 0
    for i in range(8):
        inst = S.aufgabe(C.FAMILIE_FAERBUNG, 90, 800 + i)
        zl = A.zeitleiste(inst, strategie, einheit, seed=i)
        roh = _rohe_neustarts(zl.ergebnis.spur)
        assert roh == [n[0] for n in zl.neustarts] and len(roh) == zl.ergebnis.stat["neustarts"]
        grenzen = A.grenzen(strategie, einheit, len(roh))
        zp = A.zeitpunkte(strategie, einheit, len(roh))
        abstaende = [b - a for a, b in zip([0] + roh[:-1], roh)]
        assert all(ab >= g for ab, g in zip(abstaende, grenzen))
        assert all(r >= t for r, t in zip(roh, zp))
        assert sum(abstaende) == (roh[-1] if roh else 0)
        gesehen += len(roh)
    assert gesehen >= 10                                        # die Reihe enthält Neustarts (sonst prüft der Test nichts)


def test_nach_jedem_neustart_steht_der_loeser_auf_stufe_0():
    """Auf das Ereignis „neustart“ folgt unmittelbar „springe 0“; die Zahl der gelernten Klauseln wird nie kleiner."""
    inst = S.aufgabe(C.FAMILIE_FAERBUNG, 80, 801)
    erg = A.zeitleiste(inst, C.STRATEGIE_LUBY, 4, seed=3).ergebnis
    spur = erg.spur
    positionen = [i for i, e in enumerate(spur) if e[0] == "neustart"]
    assert positionen
    assert all(spur[i + 1] == ("springe", 0) for i in positionen)
    verlauf, gelernt = [], 0
    for e in spur:
        if e[0] == "lerne":
            gelernt += 1
        if e[0] == "neustart":
            verlauf.append(gelernt)
    assert verlauf == sorted(verlauf) and gelernt == erg.stat["gelernt"] >= verlauf[-1]


# ---------------------------------------------------------------- 4. RUP
def test_jede_gelernte_klausel_ist_rup_aus_den_vorigen():
    """Ohne Löschen: die Klauseln, die der Löser lernt (Beweisprotokoll des Kerns), folgen jede aus der Formel und den vorher gelernten; unerfüllbar endet mit der leeren Klausel."""
    pruefungen = unsat = 0
    for i in range(10):
        inst = I.rand3(22, 100, 40 + i)
        for strategie, einheit in ((C.STRATEGIE_LUBY, 2), (C.STRATEGIE_GEO, 4)):
            erg = A.K.solve(inst.n, inst.klauseln, proof=True, restarts=A.KERN_NAME[strategie], restart_unit=einheit, noise=True, seed=i)
            db = [list(c) for c in inst.klauseln]
            for art, klausel in erg.beweis:
                assert art == "a"
                assert rup(db, klausel), (i, strategie, klausel)
                db.append(list(klausel))
                pruefungen += 1
            if erg.antwort is False:
                unsat += 1
                assert erg.beweis[-1] == ("a", [])
    assert pruefungen > 100 and unsat >= 3
