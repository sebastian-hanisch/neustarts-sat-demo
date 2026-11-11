"""Inhalt der App: Verdikt-Zeilen je Preset, Expander nach Titel (nie nach Index), Mathe-Blöcke, verbotene Wörter."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import nst_constants as C

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _meldungen(at):
    return [m.value for art in (at.info, at.success, at.warning, at.error) for m in art]


def _expander(at, label):
    return next(e for e in at.expander if e.label == label)


def test_expander_und_ueberschriften_stehen_unter_ihrem_titel():
    at = _app()
    labels = [e.label for e in at.expander]
    assert "📐 Mathematische Formulierung" in labels and "So funktionieren Neustarts" in labels
    assert any("🚧 Wo die Annahmen enden" in s.value for s in at.subheader)
    assert [t.label for t in at.tabs] == ["🔬 Neustartzeitpunkte", "🔬 Streuung gegen Median", "🔬 Familienvergleich", "🔬 Einheit und Faktor"]


def test_kernfrage_und_handbeispiel_beim_start():
    at = _app()
    meldungen = _meldungen(at)
    assert any(m.startswith("Luby (Einheit 32) gegen keine Neustarts, je Aufgabe nach der Schwelle ±20 % des Medians: Färbung: hilft bei") for m in meldungen)
    assert any("Der Lauf mit Luby-Neustarts (Einheit 1) hat 2 Neustarts; Antwort (unerfüllbar) und Konfliktzahl (6) sind dieselben wie ohne Neustarts." in m for m in meldungen)
    metriken = {m.label: m.value for m in at.metric}
    assert metriken == {"Antwort": "unerfüllbar", "Konflikte": "6", "Entscheidungen": metriken["Entscheidungen"], "Neustarts": "2", "gelernte Klauseln": "5"}


@pytest.mark.parametrize("name", [n for n in C.PRESETS if n != "Handbeispiel"])
def test_preset_zeigt_den_lauf_der_seitenleistenaufgabe(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception
    kurz = C.FAMILIE_KURZ[C.PRESETS[name]["familie"]]
    meldungen = _meldungen(at)
    assert any(m.startswith("Antwort ") and "mit Luby-Neustarts (Einheit 32)" in m for m in meldungen), meldungen
    assert at.metric[0].label == "Antwort" and at.metric[0].value in ("erfüllbar", "unerfüllbar")
    assert any(("Aufträge auf 3 Rampen" if kurz == "Färbung" else "Zufalls-3-SAT") in m.value for m in at.markdown)


def test_streuung_rechnet_auf_knopfdruck_und_zeigt_das_verdikt():
    at = _app()
    assert not any(m.startswith(("Färbung: Luby", "Zufallsformel: Luby")) for m in _meldungen(at))
    assert any("noch nichts gerechnet" in i.value for i in at.info)
    at.slider(key="seeds_slider").set_value(5).run()
    at.button(key="streuung_rechnen").click().run()
    assert not at.exception
    verdikt = [m for m in _meldungen(at) if m.startswith("Färbung: Luby")]
    assert verdikt and "Median der Konflikte von" in verdikt[0]
    assert any("Antwort der Aufgabe in allen Läufen" in m.value for m in at.markdown)


def test_mathe_bloecke_je_gleichung_ein_dollar_block():
    text = _expander(_app(), "📐 Mathematische Formulierung").markdown[0].value
    teile = text.split("$$")
    assert len(teile) % 2 == 1 and len(teile) // 2 >= 5                  # gerade Zahl von $$, mindestens fünf Display-Gleichungen
    for block in teile[1::2]:
        assert "\n\n" not in block.strip() and block.count("=") <= 4, block
    assert r"\lfloor u \cdot f^{\,i-1} \rfloor" in text and "2^{k-1}" in text


VERBOTEN = [r"\btr(ä|ae)gt\b", r"\btragen\b", r"Saatwert", r"läuft lokal", r"Schwanz", r"\bvorerst\b", r"\bgeplant\b"]


@pytest.mark.parametrize("datei", ["app.py", "README.md"])
def test_verbotene_woerter_fehlen(datei):
    text = (ROOT / datei).read_text(encoding="utf-8")
    for muster in VERBOTEN:
        assert not re.search(muster, text, re.I), (datei, muster)
