"""Verdikte an von Hand gesetzten Zeilen (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier.

Die Schwelle „neutral“ (Quotient in [0,8; 1,2], Grenzen inklusive) und die Schwelle „Kurve flach“ (größter höchstens das 1,2-Fache des kleinsten) stehen vor der Messung fest."""

import pytest

import nst_algorithm as A
import nst_constants as C
import nst_evaluation as E


def zeile(median, p90, maximum, abbrueche=0, minimum=1, n=30):
    return {"median": median, "p90": p90, "max": maximum, "min": minimum, "abbrueche": abbrueche, "n": n}


def drei(keine, luby, geo=None):
    z = {C.STRATEGIE_KEINE: keine, C.STRATEGIE_LUBY: luby}
    if geo is not None:
        z[C.STRATEGIE_GEO] = geo
    return z


# ---------------------------------------------------------------- Schwelle und Format
def test_schwelle_neutral_ist_beidseitig_inklusive():
    assert C.NEUTRAL_BAND == 0.20 and C.FLACH_VERHAELTNIS == 1.2
    assert E.einordnung(E.quotient(80, 100)) == E.NEUTRAL       # genau 0,8
    assert E.einordnung(E.quotient(79, 100)) == E.HILFT
    assert E.einordnung(E.quotient(120, 100)) == E.NEUTRAL      # genau 1,2
    assert E.einordnung(E.quotient(121, 100)) == E.SCHADET
    assert E.einordnung(1.0) == E.NEUTRAL
    # R2-artig (Vormessung 1 087,5 -> 1 661, +53 %): schadet; R0 und R4-artig (-13 %, -14 %): neutral; C5-artig (287,5 -> 65): hilft
    assert E.einordnung(E.quotient(1661, 1087.5)) == E.SCHADET
    assert E.einordnung(E.quotient(2545.5, 2934)) == E.NEUTRAL and E.einordnung(E.quotient(2597, 3031.5)) == E.NEUTRAL
    assert E.einordnung(E.quotient(65, 287.5)) == E.HILFT


def test_haeufigkeiten_zaehlt_die_drei_klassen():
    assert E.haeufigkeiten([0.5, 0.8, 1.0, 1.2, 1.3, 2.0, 0.1]) == {E.HILFT: 2, E.NEUTRAL: 3, E.SCHADET: 2}


def test_zahlenformat():
    assert E.zahl(1234567) == "1 234 567" and E.zahl(116.5) == "116,5" and E.zahl(49.0) == "49" and E.zahl(0) == "0"
    assert E.dezimal(0.4545, 2) == "0,45" and E.dezimal(1234.56) == "1 234,6"
    assert E.prozent(0.45) == "−55 %" and E.prozent(1.53) == "+53 %" and E.prozent(1.0) == "±0 %" and E.prozent(1.2) == "+20 %"


# ---------------------------------------------------------------- Reiter 2
def test_verdict_streuung_hilft_nennt_median_und_p90():
    kind, text = E.verdict_streuung(drei(zeile(287.5, 951, 1364), zeile(65, 166, 331), zeile(130.5, 231, 252)), "Färbung")
    assert kind == "success"
    assert text == ("Färbung: Luby senkt den Median der Konflikte von 287,5 auf 65 (−77 %) und das 90-Prozent-Rang-Maß (P90) von 951 auf 166 (Maximum 1 364 gegen 331). "
                    "Geometrisch: Median 130,5 (−55 %, hilft), P90 231.")


def test_verdict_streuung_schadet_ausserhalb_des_bandes():
    kind, text = E.verdict_streuung(drei(zeile(1087.5, 2064, 3021), zeile(1661, 3118, 4151)), "Zufallsformel")
    assert kind == "warning"
    assert text == "Zufallsformel: Luby erhöht den Median der Konflikte von 1 087,5 auf 1 661 (+53 %, außerhalb des Bandes ±20 %) und das P90 von 2 064 auf 3 118."


def test_verdict_streuung_neutral_mit_und_ohne_der_aussage_kleiner_als_die_streuung():
    kind, text = E.verdict_streuung(drei(zeile(2934, 4825, 5804), zeile(2545.5, 4147, 4653), zeile(2237.5, 3453, 3750)), "Zufallsformel")
    assert kind == "info"
    assert "(−13 %, innerhalb des Bandes ±20 %: neutral)" in text and "das P90 geht von 4 825 auf 4 147" in text
    assert "Der Unterschied der Mediane (388,5) ist kleiner als die Streuung ohne Neustarts (P90 minus Median = 1 891)." in text
    assert "Geometrisch: Median 2 237,5 (−24 %, hilft), P90 3 453." in text
    # Unterschied größer als die Streuung: der Satz entfällt (Median 100 -> 110, P90 nur 105)
    _, text2 = E.verdict_streuung(drei(zeile(100, 105, 110), zeile(110, 120, 130)), "Färbung")
    assert "kleiner als die Streuung" not in text2 and "+10 %" in text2


def test_verdict_streuung_bandgrenzen_und_abbrueche():
    assert E.verdict_streuung(drei(zeile(100, 150, 200), zeile(80, 100, 100)), "x")[0] == "info"             # genau 0,8: neutral
    assert E.verdict_streuung(drei(zeile(100, 150, 200), zeile(79, 100, 100)), "x")[0] == "success"
    assert E.verdict_streuung(drei(zeile(100, 150, 200), zeile(120, 100, 100)), "x")[0] == "info"
    assert E.verdict_streuung(drei(zeile(100, 150, 200), zeile(121, 100, 100)), "x")[0] == "warning"
    _, text = E.verdict_streuung(drei(zeile(100, 150, 200, abbrueche=2), zeile(50, 80, 90, abbrueche=1)), "x")
    assert text.endswith(" 3 Läufe brachen am Budget ab; ihre Konfliktzahlen sind untere Schranken.")
    _, ohne = E.verdict_streuung(drei(zeile(100, 150, 200), zeile(50, 80, 90)), "x")
    assert "brachen" not in ohne


# ---------------------------------------------------------------- Reiter 1
def _m(antwort, konflikte, neustarts, gelernt=5):
    return A.Messung(antwort, konflikte, 10, neustarts, gelernt)


def test_verdict_handbeispiel_alle_zweige():
    ohne = _m(False, 6, 0)
    kind, text = E.verdict_handbeispiel(_m(False, 6, 2), ohne, C.STRATEGIE_LUBY, 1)
    assert kind == "info" and text.startswith("Der Lauf mit Luby-Neustarts (Einheit 1) hat 2 Neustarts; Antwort (unerfüllbar) und Konfliktzahl (6) sind dieselben wie ohne Neustarts.")
    assert "nur die Mechanik, keinen Nutzen" in text
    assert "hat 1 Neustart;" in E.verdict_handbeispiel(_m(False, 6, 1), ohne, C.STRATEGIE_GEO, 5)[1]
    assert "mit geometrischen Neustarts (erste Grenze 5)" in E.verdict_handbeispiel(_m(False, 6, 1), ohne, C.STRATEGIE_GEO, 5)[1]
    kind, text = E.verdict_handbeispiel(_m(False, 7, 1), ohne, C.STRATEGIE_LUBY, 2)
    assert text.startswith("Der Lauf mit Luby-Neustarts (Einheit 2) braucht 7 Konflikte bei 1 Neustart, ohne Neustarts 6 Konflikte;")
    assert E.verdict_handbeispiel(_m(True, 6, 1), ohne, C.STRATEGIE_LUBY, 1)[0] == "error"
    kind, text = E.verdict_handbeispiel(ohne, ohne, C.STRATEGIE_KEINE, 1)
    assert text == "Das Handbeispiel ist unerfüllbar; der Lauf ohne Neustarts braucht 6 Konflikte und lernt 5 Klauseln."


def test_verdict_lauf_alle_zweige():
    assert E.verdict_lauf(_m(None, 20000, 12), C.STRATEGIE_LUBY, 32) == (
        "warning", "Das Budget wurde erreicht: nach 20 000 Konflikten mit Luby-Neustarts (Einheit 32) ist keine Antwort bekannt (die Zahl ist eine untere Schranke).")
    assert E.verdict_lauf(_m(True, 100, 0), C.STRATEGIE_LUBY, 32) == ("info", "Antwort erfüllbar nach 100 Konflikten mit Luby-Neustarts (Einheit 32); es gab keinen Neustart.")
    assert E.verdict_lauf(_m(False, 218, 0), C.STRATEGIE_KEINE, 32)[1] == "Antwort unerfüllbar nach 218 Konflikten ohne Neustarts; es gab keinen Neustart."
    kind, text = E.verdict_lauf(_m(False, 1218, 7), C.STRATEGIE_LUBY, 32)
    assert text.startswith("Antwort unerfüllbar nach 1 218 Konflikten mit Luby-Neustarts (Einheit 32), 7 Neustarts.")
    assert "1 Neustart." in E.verdict_lauf(_m(False, 9, 1), C.STRATEGIE_GEO, 100)[1]


# ---------------------------------------------------------------- Reiter 3
def _daten_mess():
    return {"mess": {C.FAMILIE_FAERBUNG: [
        {"index": 0, "seed": 500, "antwort": "erfüllbar", "abbrueche": 0, "keine": [100, 200, 300], "luby": [40, 50, 60], "geo": [90, 100, 110]},
        {"index": 1, "seed": 501, "antwort": "unerfüllbar", "abbrueche": 0, "keine": [100, 100, 100], "luby": [105, 100, 100], "geo": [100, 150, 150]},
        {"index": 2, "seed": 502, "antwort": "erfüllbar", "abbrueche": 0, "keine": [10, 20, 30], "luby": [30, 30, 30], "geo": [20, 20, 20]},
    ]}}


def test_aufgaben_zeilen_und_zusammenfassung():
    z = E.aufgaben_zeilen(_daten_mess(), C.FAMILIE_FAERBUNG)
    assert [(a["q_luby"], a["klasse_luby"]) for a in z] == [(0.25, E.HILFT), (1.0, E.NEUTRAL), (1.5, E.SCHADET)]
    assert [(a["q_geo"], a["klasse_geo"]) for a in z] == [(0.5, E.HILFT), (1.5, E.SCHADET), (1.0, E.NEUTRAL)]
    assert z[0]["keine"]["median"] == 200 and z[0]["keine"]["p90"] == 300 and z[0]["keine"]["max"] == 300 and z[0]["luby"]["median"] == 50
    # P90 (Rang min(2, int(0,9 · 3)) = 2, also der größte Wert): keine 300 / 100 / 30, Luby 60 / 105 / 30, geometrisch 110 / 150 / 20
    assert [a["p90_q_luby"] for a in z] == [0.2, 1.05, 1.0] and [a["p90_q_geo"] for a in z][2] == pytest.approx(20 / 30)
    s = E.familien_zusammenfassung(z, C.STRATEGIE_LUBY)
    assert s == {"n": 3, "haeufigkeit": {"hilft": 1, "neutral": 1, "schadet": 1}, "median_quotient": 1.0, "min_quotient": 0.25, "max_quotient": 1.5,
                 "p90_kleiner": 1, "median_p90_quotient": 1.0}
    assert E.familien_zusammenfassung(z, C.STRATEGIE_GEO)["p90_kleiner"] == 2


def test_verdict_familien_und_kern():
    zus = {"Färbung": {"n": 10, "haeufigkeit": {"hilft": 8, "neutral": 2, "schadet": 0}, "median_quotient": 0.45, "min_quotient": 0.2, "max_quotient": 0.9, "p90_kleiner": 9, "median_p90_quotient": 0.5},
           "Zufallsformel": {"n": 12, "haeufigkeit": {"hilft": 3, "neutral": 7, "schadet": 2}, "median_quotient": 1.0, "min_quotient": 0.7, "max_quotient": 1.53, "p90_kleiner": 6, "median_p90_quotient": 0.95}}
    kind, text = E.verdict_familien(zus)
    assert kind == "info"
    assert text == ("Luby (Einheit 32) gegen keine Neustarts, je Aufgabe nach der Schwelle ±20 % des Medians: "
                    "Färbung: hilft bei 8, neutral bei 2, schadet bei 0 von 10 Aufgaben (Quotient der Mediane Luby / keine: Median 0,45, kleinster 0,20, größter 0,90); das P90 liegt bei 9 von 10 Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,50); "
                    "Zufallsformel: hilft bei 3, neutral bei 7, schadet bei 2 von 12 Aufgaben (Quotient der Mediane Luby / keine: Median 1,00, kleinster 0,70, größter 1,53); das P90 liegt bei 6 von 12 Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,95).")
    k2, t2 = E.verdict_kern(zus)
    assert t2 == text + " Gemessen an diesen Aufgaben und Größen; keine Aussage über andere Familien." and k2 == "info"


# ---------------------------------------------------------------- Reiter 4
def _daten_kurve():
    a = {"keine": [100, 100], "luby": {"4": [50, 50], "8": [60, 60], "16": [90, 90]}, "geo": {"1.1": [100, 100], "1.5": [110, 110]}}
    b = {"keine": [200, 200], "luby": {"4": [100, 100], "8": [100, 100], "16": [160, 160]}, "geo": {"1.1": [220, 220], "1.5": [200, 200]}}
    return {"meta": {"kurve_einheiten": [4, 8, 16], "kurve_faktoren": [1.1, 1.5]}, "kurve": {C.FAMILIE_ZUFALL: [a, b]}}


def test_kurve_quotienten_und_zeilen():
    q = E.kurve_quotienten(_daten_kurve(), C.FAMILIE_ZUFALL)
    assert q == {"luby:4": [0.5, 0.5], "luby:8": [0.6, 0.5], "luby:16": [0.9, 0.8], "geo:1.1": [1.0, 1.1], "geo:1.5": [1.1, 1.0]}
    z = {r["name"]: r for r in E.kurve_zeilen(_daten_kurve(), C.FAMILIE_ZUFALL)}
    assert (z["luby:8"]["median"], z["luby:8"]["min"], z["luby:8"]["max"], z["luby:8"]["klasse"], z["luby:8"]["hilft"], z["luby:8"]["n"]) == (0.55, 0.5, 0.6, E.HILFT, 2, 2)
    assert z["luby:16"]["klasse"] == E.NEUTRAL and z["luby:16"]["hilft"] == 0       # Median 0,85; 0,8 ist neutral (inklusive)
    assert z["geo:1.1"]["klasse"] == E.NEUTRAL


def _kz(art, werte):
    return [{"name": f"{art}:{k}", "median": m, "min": m, "max": m, "klasse": E.einordnung(m), "hilft": 0, "n": 2} for k, m in werte]


def test_verdict_kurve_flach_ist_inklusive_bei_1_2():
    kind, text = E.verdict_kurve(_kz("luby", [("4", 0.5), ("8", 0.55), ("16", 0.6)]), "luby", "Färbung")
    assert kind == "info"
    assert text == ("Färbung, Luby-Einheit: die Kurve ist flach (größter Median-Quotient 0,60 gegen kleinster 0,50, Verhältnis 1,20 ≤ 1,2): im Median über die Aufgaben ändert sich die Wirkung nur wenig; "
                    "je Aufgabe liegen die Quotienten dieser Kurve zwischen 0,50 und 0,60.")
    kind, text = E.verdict_kurve(_kz("luby", [("4", 0.5), ("8", 0.61), ("16", 0.7)]), "luby", "Färbung")
    assert text == ("Färbung, Luby-Einheit: die Kurve ist nicht flach (Median-Quotient von 0,50 bei 4 bis 0,70 bei 16, Verhältnis 1,40 > 1,2). "
                    "4 liegt in dieser Messung am niedrigsten; als allgemein gültig gilt das nicht.")
    gz = _kz("geo", [("1.1", 0.9), ("1.5", 0.5)]) + _kz("luby", [("4", 0.1)])           # Luby-Zeilen stören die geometrische Kurve nicht
    assert "geometrischer Faktor: die Kurve ist nicht flach (Median-Quotient von 0,50 bei 1,5 bis 0,90 bei 1,1" in E.verdict_kurve(gz, "geo", "Zufallsformel")[1]


def test_tabelle_zeitpunkte_ist_die_tabelle_des_handbeispiels():
    """Handwerte aus hb_04.py; die geometrische Zeile: Grenzen 100, 150, 225, 337, 506, 759, 1 139, 1 708 (Faktor 1,5, abgerundet), kumulativ."""
    assert E.tabelle_zeitpunkte() == [
        ["Luby, Einheit 1", 1, 2, 4, 5, 6, 8, 12, 13],
        ["Luby, Einheit 2", 2, 4, 8, 10, 12, 16, 24, 26],
        ["Luby, Einheit 32", 32, 64, 128, 160, 192, 256, 384, 416],
        ["geometrisch (100, ×1,5)", 100, 250, 475, 812, 1318, 2077, 3216, 4924],
    ]
