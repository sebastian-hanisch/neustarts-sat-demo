"""Randfälle der Neustarts (DEMO-PLAYBOOK §12): Formel ohne Konflikt, Konflikt vor der ersten Entscheidung, n = 1, Einheit 1, Budget 0 und 1."""

import pytest

import nst_algorithm as A
import nst_constants as C
import nst_evaluation as E
import nst_scenario as S

ALLE = [(C.STRATEGIE_KEINE, 1), (C.STRATEGIE_LUBY, 1), (C.STRATEGIE_GEO, 1), (C.STRATEGIE_LUBY, 32)]


def _lauf(n, klauseln, strategie, einheit, **kw):
    inst = S.Instanz(n, klauseln, {})
    return A.lauf(inst, strategie, einheit, feste_regel=True, **kw)


@pytest.mark.parametrize("strategie, einheit", ALLE)
def test_formel_ohne_konflikt_hat_nie_einen_neustart(strategie, einheit):
    """(x1 ∨ x2 ∨ x3): die erste Entscheidung (¬x1) und die zweite (¬x2) erzwingen x3; kein Konflikt, also nie ein Neustart, auch nicht bei Einheit 1."""
    erg = _lauf(3, [(1, 2, 3)], strategie, einheit)
    assert erg.antwort is True and erg.stat["konflikte"] == 0 and erg.stat["neustarts"] == 0
    zl = A.zeitleiste(S.Instanz(3, [(1, 2, 3)], {}), strategie, einheit, feste_regel=True)
    assert zl.neustarts == [] and zl.konflikt_stufe == []


@pytest.mark.parametrize("strategie, einheit", ALLE)
def test_unerfuellbar_auf_stufe_0_ohne_entscheidung(strategie, einheit):
    """(x1) ∧ (¬x1): schon beim Aufnehmen widersprüchlich; keine Entscheidung, kein Konflikt im Löser, kein Neustart."""
    erg = _lauf(1, [(1,), (-1,)], strategie, einheit)
    assert erg.antwort is False and erg.stat["konflikte"] == 0 and erg.stat["entscheidungen"] == 0 and erg.stat["neustarts"] == 0


@pytest.mark.parametrize("strategie, einheit", ALLE)
def test_unerfuellbar_mit_konflikt_auf_stufe_0(strategie, einheit):
    """Alle vier Klauseln über zwei Variablen: Konflikt 1 auf Stufe 1 lernt eine Einheit, Konflikt 2 liegt auf Stufe 0 (Antwort unerfüllbar); dabei kein Neustart,
    weil auf Stufe 0 nichts zu verwerfen ist."""
    klauseln = [(1, 2), (-1, 2), (1, -2), (-1, -2)]
    erg = _lauf(2, klauseln, strategie, einheit)
    assert erg.antwort is False and erg.stat["konflikte"] == 2 and erg.stat["gelernt"] == 1 and erg.stat["neustarts"] == 0
    zl = A.zeitleiste(S.Instanz(2, klauseln, {}), strategie, einheit, feste_regel=True)
    assert zl.konflikt_stufe == [1, 0]


@pytest.mark.parametrize("strategie, einheit", ALLE)
def test_n_gleich_1(strategie, einheit):
    for klauseln, antwort in (([(1,)], True), ([(-1,)], True), ([], True)):
        erg = _lauf(1, klauseln, strategie, einheit)
        assert erg.antwort is antwort and erg.stat["neustarts"] == 0
        if antwort:
            assert erg.modell is not None and set(erg.modell) == {1}


def test_einheit_1_grenzen_und_geometrische_folge_ab_1():
    assert A.grenzen(C.STRATEGIE_LUBY, 1, 7) == [1, 1, 2, 1, 1, 2, 4]
    assert A.grenzen(C.STRATEGIE_GEO, 1, 5) == [1, 1, 2, 3, 5]           # 1, 1,5, 2,25, 3,375, 5,0625 abgerundet
    assert A.zeitpunkte(C.STRATEGIE_GEO, 1, 5) == [1, 2, 4, 7, 12]


@pytest.mark.parametrize("budget", [0, 1])
def test_budget_0_und_1_brechen_nach_dem_ersten_konflikt_ab(budget):
    """Der Kern prüft das Budget nach einem Konflikt: Budget 0 und 1 stoppen beide nach genau einem Konflikt (Antwort „Abbruch“, nie ein Fehler).
    Eine Formel ohne Konflikt wird auch mit Budget 0 beantwortet."""
    for strategie, einheit in ALLE:
        erg = _lauf(6, list(S.HANDBEISPIEL_G.klauseln), strategie, einheit, budget=budget)
        assert erg.antwort is None and erg.stat["konflikte"] == 1 and erg.stat["neustarts"] == 0
        m = A.messung(erg)
        assert m.antwort_text == "Abbruch (Budget)"
    assert _lauf(3, [(1, 2, 3)], C.STRATEGIE_LUBY, 1, budget=budget).antwort is True


def test_budget_2_laesst_den_ersten_neustart_zu():
    """G mit Einheit 1 und Luby: nach Konflikt 1 folgt der erste Neustart; mit Budget 2 stoppt der Lauf nach Konflikt 2 (Konfliktzahl = Budget, nie mehr)."""
    erg = _lauf(6, list(S.HANDBEISPIEL_G.klauseln), C.STRATEGIE_LUBY, 1, budget=2)
    assert erg.antwort is None and erg.stat["konflikte"] == 2 and erg.stat["neustarts"] == 1


def test_verteilung_mit_einem_einzigen_lauf():
    v = A.verteilung([7])
    assert (v.median, v.p90, v.maximum, v.minimum, v.n) == (7, 7, 7, 7, 1)


def test_quotient_ohne_konflikte():
    assert E.quotient(0, 0) == 1.0 and E.quotient(5, 0) == float("inf") and E.quotient(0, 5) == 0.0
    assert E.einordnung(E.quotient(0, 0)) == E.NEUTRAL and E.einordnung(E.quotient(5, 0)) == E.SCHADET
