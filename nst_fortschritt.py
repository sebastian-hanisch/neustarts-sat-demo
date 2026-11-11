"""Reiter „Streuung gegen Median“ mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Aufgabe ist hier ein Lauf: Strategie und Löser-Zufalls-Seed auf der festen Aufgabe. `lauf_konflikte` ruft `nst_algorithm.konflikte_je_seed` für genau einen
Löser-Zufalls-Seed auf und wird einzeln zwischengespeichert (`st.cache_data`, höchstens 300 Einträge: gut drei Einstellungen zu 3 × 30 Läufen). Ändert
jemand nur die Zahl der Löser-Zufalls-Seeds, kommen die schon gerechneten Läufe aus dem Zwischenspeicher. Der Fortschrittsbalken zählt die fertigen Läufe.
Die Konflikte, Antworten und Abbrüche sind gleich denen der ungepufferten Rechnung (`tests/test_fortschritt.py`); die Rechenzeit ist die Summe der
Zeiten, in denen die Läufe tatsächlich gerechnet wurden (nur Anzeige)."""

import time
from contextlib import contextmanager

import streamlit as st

import nst_algorithm as A
import nst_constants as C
import nst_scenario as S

_ZAEHLER = {"gerechnet": 0}
KONFIG = {C.STRATEGIE_KEINE: 1, C.STRATEGIE_LUBY: C.LUBY_EINHEIT_MESSUNG, C.STRATEGIE_GEO: C.GEO_START_MESSUNG}


def gerechnet() -> int:
    """Wie viele Läufe in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=300)
def lauf_konflikte(familie: str, n: int, seed: int, strategie: str, einheit: int, loeser_seed: int, budget: int) -> tuple:
    """(Konflikte, Antwort-Menge, Abbrüche, Sekunden) eines Laufs: gleich `A.konflikte_je_seed(inst, strategie, einheit, [loeser_seed], budget=budget)`."""
    _ZAEHLER["gerechnet"] += 1
    t0 = time.perf_counter()
    konf, antworten, abbr = A.konflikte_je_seed(S.aufgabe(familie, n, seed), strategie, einheit, [loeser_seed], budget=budget)
    return konf[0], antworten, abbr, time.perf_counter() - t0


def streuung(familie: str, n: int, seed: int, seeds: int, budget: int, melde=None) -> tuple:
    """Wie `_streuung` der App ohne Zwischenspeicher: (Aufgabe, Konflikte je Strategie, Abbrüche je Strategie, Antworten, Rechenzeit der Läufe);
    `melde(fertig, gesamt)` wird nach jedem Lauf aufgerufen."""
    inst = S.aufgabe(familie, n, seed)
    konf, antworten, abbr, sek, fertig, gesamt = {}, set(), {}, 0.0, 0, len(KONFIG) * seeds
    for strategie, einheit in KONFIG.items():
        konf[strategie], abbr[strategie] = [], 0
        for s in range(seeds):
            k, ans, ab, t = lauf_konflikte(familie, n, seed, strategie, einheit, s, budget)
            konf[strategie].append(k)
            antworten |= ans
            abbr[strategie] += ab
            sek += t
            fertig += 1
            if melde:
                melde(fertig, gesamt)
    return inst, konf, abbr, antworten, sek


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()
