"""Jede Zahl der README (Abschnitte „Befunde“ und „Befunde und Korrekturen“) wird hier nachgerechnet. Zahl -> Test steht in der Tabelle „Befunde“ der README.

Zwei Arten von Zahlen: (1) exakte Zählungen des deterministischen Lösers (Handbeispiel, Grenzen, Schur-Probe; ganzzahlig, auf jeder Plattform gleich);
(2) die vorgerechneten Messreihen `nst_messung_vorgerechnet.json` (Messung dieses Repos mit `tools/messung_neustarts.py`, Aufgaben mit SplitMix64, Löser-Zufalls-Seeds 0 bis 29
bzw. 0 bis 9). Ein Teil der Zellen wird hier live nachgerechnet, um zu zeigen, dass die Datei dem heutigen Code entspricht; die übrigen werden aus der Datei gezählt.
Die Zahlen der Vormessung der Planung (`out_v6.txt`) stammen von anderen Zufallsfolgen und gelten nicht als Ersatz. Sekunden werden nirgends geprüft."""

import statistics

import pytest

import nst_algorithm as A
import nst_constants as C
import nst_evaluation as E
import nst_instanzen as I
import nst_scenario as S

FAE, ZUF = C.FAMILIE_FAERBUNG, C.FAMILIE_ZUFALL


@pytest.fixture(scope="module")
def daten():
    return E.lade_messung()


@pytest.fixture(scope="module")
def zeilen(daten):
    return {fam: E.aufgaben_zeilen(daten, fam) for fam in C.FAMILIEN}


def _ag(zs, s, feld):
    return statistics.median([z[s][feld] for z in zs])


# ---------------------------------------------------------------- Aufbau der Messreihe
def test_claim_aufbau_der_messreihe(daten, zeilen):
    """10 Färbungen (n = 160, Grad 4,5, 3 Rampen; 6 erfüllbar, 4 unerfüllbar) und 12 Zufallsformeln (n = 150, m = 639; 3 erfüllbar, 9 unerfüllbar), je 30 Löser-Zufalls-Seeds, Budget 200 000,
    **kein Abbruch** in einem der 3 · 22 · 30 = 1 980 Läufe."""
    assert [len(zeilen[f]) for f in C.FAMILIEN] == [10, 12]
    for fam, (sat, unsat) in ((FAE, (6, 4)), (ZUF, (3, 9))):
        assert sum(1 for z in zeilen[fam] if z["antwort"] == "erfüllbar") == sat and sum(1 for z in zeilen[fam] if z["antwort"] == "unerfüllbar") == unsat
        assert all(z["abbrueche"] == 0 for z in zeilen[fam])
    assert sum(len(a[s]) for fam in C.FAMILIEN for a in daten["mess"][fam] for s in C.STRATEGIEN) == 1980
    assert daten["meta"]["budget"] == 200000 and max(max(a[s]) for fam in C.FAMILIEN for a in daten["mess"][fam] for s in C.STRATEGIEN) < 200000


def test_claim_messreihe_stimmt_mit_dem_heutigen_code_ueberein(daten):
    """Live nachgerechnet: Färbung A1 und A3 mit allen drei Strategien und allen 30 Löser-Zufalls-Seeds, Zufallsformel A12 (die schnellste) mit den ersten 5 Seeds."""
    for index in (0, 2):
        inst = S.messaufgabe(FAE, index)
        a = daten["mess"][FAE][index]
        assert A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, range(30))[0] == a["keine"]
        assert A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 32, range(30))[0] == a["luby"]
        assert A.konflikte_je_seed(inst, C.STRATEGIE_GEO, 100, range(30))[0] == a["geo"]
    inst = S.messaufgabe(ZUF, 11)
    a = daten["mess"][ZUF][11]
    assert A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 32, range(5))[0] == a["luby"][:5]


# ---------------------------------------------------------------- Rampen-Färbung
def test_claim_faerbung_luby_hilft_in_jeder_aufgabe(zeilen):
    """Luby (Einheit 32) gegen keine Neustarts, Quotient der Mediane je Aufgabe: Median 0,42, kleinster 0,22, größter 0,59; hilft (< 0,8) bei 10 von 10 Aufgaben,
    neutral bei 0, schadet bei 0; erfüllbare Aufgaben 6 von 6 hilft, unerfüllbare 4 von 4."""
    zs = zeilen[FAE]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_LUBY)
    assert s["haeufigkeit"] == {"hilft": 10, "neutral": 0, "schadet": 0}
    assert (round(s["median_quotient"], 2), round(s["min_quotient"], 2), round(s["max_quotient"], 2)) == (0.42, 0.22, 0.59)
    assert sum(1 for z in zs if z["antwort"] == "erfüllbar" and z["klasse_luby"] == E.HILFT) == 6
    assert sum(1 for z in zs if z["antwort"] == "unerfüllbar" and z["klasse_luby"] == E.HILFT) == 4


def test_claim_faerbung_luby_nach_antwort(zeilen):
    """Quotient Median(Luby) / Median(keine), Median über die Aufgaben: erfüllbare Färbungen (6) 0,36, unerfüllbare (4) 0,53; die Zahlen von 4 und 6 Aufgaben sind keine Regel."""
    zs = zeilen[FAE]
    sat = statistics.median([z["q_luby"] for z in zs if z["antwort"] == "erfüllbar"])
    unsat = statistics.median([z["q_luby"] for z in zs if z["antwort"] == "unerfüllbar"])
    assert (E.dezimal(sat, 2), E.dezimal(unsat, 2)) == ("0,36", "0,53")


def test_claim_faerbung_median_der_aufgaben_mediane_und_p90(zeilen):
    """Median der Aufgaben-Mediane: keine 294, Luby 108,25, geometrisch 147,5; Median der Aufgaben-P90: 546 / 157,5 / 203,5."""
    zs = zeilen[FAE]
    assert [_ag(zs, s, "median") for s in C.STRATEGIEN] == [294.0, 108.25, 147.5]
    assert [_ag(zs, s, "p90") for s in C.STRATEGIEN] == [546.0, 157.5, 203.5]


def test_claim_faerbung_tail_p90_und_maximum(zeilen):
    """Das P90 liegt mit Luby in 10 von 10 Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,29), das Maximum über die 30 Seeds ebenfalls in 10 von 10."""
    zs = zeilen[FAE]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_LUBY)
    assert s["p90_kleiner"] == 10 and round(s["median_p90_quotient"], 2) == 0.29
    assert sum(1 for z in zs if z["luby"]["max"] < z["keine"]["max"]) == 10


def test_claim_faerbung_geometrisch(zeilen):
    """Geometrisch (erste Grenze 100, Faktor 1,5) gegen keine: hilft 7, neutral 3 (A1, A3, A5), schadet 0; Median der Quotienten 0,61, kleinster 0,43, größter 1,00;
    P90 in 10 von 10 Aufgaben kleiner (Median 0,44). Luby ist in 10 von 10 Aufgaben besser als geometrisch im Median der Konflikte."""
    zs = zeilen[FAE]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_GEO)
    assert s["haeufigkeit"] == {"hilft": 7, "neutral": 3, "schadet": 0}
    assert [z["index"] + 1 for z in zs if z["klasse_geo"] == E.NEUTRAL] == [1, 3, 5]
    assert (round(s["median_quotient"], 2), round(s["min_quotient"], 2), round(s["max_quotient"], 2)) == (0.61, 0.43, 1.0)
    assert s["p90_kleiner"] == 10 and round(s["median_p90_quotient"], 2) == 0.44
    assert sum(1 for z in zs if z["luby"]["median"] < z["geo"]["median"]) == 10


# ---------------------------------------------------------------- Zufallsformeln
def test_claim_zufall_luby_zaehlung_je_aufgabe(zeilen):
    """Zufallsformeln (n = 150): Luby gegen keine hilft bei 5 von 12 Aufgaben (< 0,8), neutral bei 7, schadet bei 0; Quotient Median 0,86, kleinster 0,75, größter 1,12 (Aufgabe 10, erfüllbar).
    Erfüllbar: 1 von 3 Aufgaben hilft, unerfüllbar 4 von 9."""
    zs = zeilen[ZUF]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_LUBY)
    assert s["haeufigkeit"] == {"hilft": 5, "neutral": 7, "schadet": 0}
    assert (round(s["median_quotient"], 2), round(s["min_quotient"], 2), round(s["max_quotient"], 2)) == (0.86, 0.75, 1.12)
    assert max(zs, key=lambda z: z["q_luby"])["index"] == 9 and zs[9]["antwort"] == "erfüllbar"
    assert sum(1 for z in zs if z["antwort"] == "erfüllbar" and z["klasse_luby"] == E.HILFT) == 1
    assert sum(1 for z in zs if z["antwort"] == "unerfüllbar" and z["klasse_luby"] == E.HILFT) == 4


def test_claim_zufall_median_der_aufgaben_mediane_und_p90(zeilen):
    """Median der Aufgaben-Mediane: keine 3 162,75, Luby 2 764,75, geometrisch 2 394,25; der Aufgaben-P90: 4 154 / 3 357,5 / 2 935."""
    zs = zeilen[ZUF]
    assert [_ag(zs, s, "median") for s in C.STRATEGIEN] == [3162.75, 2764.75, 2394.25]
    assert [_ag(zs, s, "p90") for s in C.STRATEGIEN] == [4154.0, 3357.5, 2935.0]


def test_claim_zufall_tail_p90_und_maximum(zeilen):
    """Das P90 liegt mit Luby bei 11 von 12 Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,76; die Ausnahme ist Aufgabe 10 mit 1,21), das Maximum bei 12 von 12."""
    zs = zeilen[ZUF]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_LUBY)
    assert s["p90_kleiner"] == 11 and round(s["median_p90_quotient"], 2) == 0.76
    assert [z["index"] + 1 for z in zs if z["p90_q_luby"] >= 1.0] == [10] and round(zs[9]["p90_q_luby"], 2) == 1.21
    assert sum(1 for z in zs if z["luby"]["max"] < z["keine"]["max"]) == 12


def test_claim_zufall_geometrisch(zeilen):
    """Geometrisch gegen keine: hilft bei 9 von 12 Aufgaben, neutral bei 3, schadet bei 0; Quotient Median 0,78, kleinster 0,72, größter 0,84; P90 bei 12 von 12 kleiner (Median 0,70).
    Auf Zufallsformeln liegt geometrisch damit unter Luby (Median der Aufgaben-Mediane 2 394,25 gegen 2 764,75), auf Färbung darüber."""
    zs = zeilen[ZUF]
    s = E.familien_zusammenfassung(zs, C.STRATEGIE_GEO)
    assert s["haeufigkeit"] == {"hilft": 9, "neutral": 3, "schadet": 0}
    assert (round(s["median_quotient"], 2), round(s["min_quotient"], 2), round(s["max_quotient"], 2)) == (0.78, 0.72, 0.84)
    assert s["p90_kleiner"] == 12 and round(s["median_p90_quotient"], 2) == 0.70


def test_claim_kein_schadet_fall_der_vormessung_reproduziert_sich_nicht(zeilen):
    """Die Vormessung der Planung (Formel R2, 1 087,5 -> 1 661, +53 %) hatte andere Zufallsformeln. In den 12 Aufgaben dieser Reihe ist der größte Quotient 1,12: kein Fall außerhalb
    des Bandes. Die Schwelle würde einen solchen Fall melden (Test in tests/test_verdicts.py)."""
    assert max(z["q_luby"] for z in zeilen[ZUF]) < 1 + C.NEUTRAL_BAND
    assert sum(1 for fam in C.FAMILIEN for z in zeilen[fam] if z["klasse_luby"] == E.SCHADET or z["klasse_geo"] == E.SCHADET) == 0


def test_claim_kernfrage_verdikt_nennt_die_zaehlungen(zeilen):
    zus = {C.FAMILIE_KURZ[f]: E.familien_zusammenfassung(zeilen[f], C.STRATEGIE_LUBY) for f in C.FAMILIEN}
    kind, text = E.verdict_kern(zus)
    assert "Färbung: hilft bei 10, neutral bei 0, schadet bei 0 von 10 Aufgaben" in text
    assert "Zufallsformel: hilft bei 5, neutral bei 7, schadet bei 0 von 12 Aufgaben" in text


# ---------------------------------------------------------------- Handbeispiel, Plan-Korrekturen
def test_claim_handbeispiel_g_und_geometrische_grenzen():
    """G: 6 Konflikte, 5 gelernte Klauseln; Neustarts 2 / 1 / 0 bei Einheit 1 / 2 / 32 (nach Konflikt 1 und 4 / nach 4 / keiner). Geometrisch (100, 1,5): Grenzen 100, 150, 225, 337, 506, 759
    (der Plan nannte 505 und 757), kumulativ 100, 250, 475, 812, 1 318, 2 077."""
    g = S.HANDBEISPIEL_G
    for einheit, erwartet in ((1, [1, 4]), (2, [4]), (32, [])):
        zl = A.zeitleiste(g, C.STRATEGIE_LUBY, einheit, feste_regel=True)
        assert (zl.ergebnis.stat["konflikte"], zl.ergebnis.stat["gelernt"], [n[0] for n in zl.neustarts]) == (6, 5, erwartet)
    assert A.grenzen(C.STRATEGIE_GEO, 100, 6) == [100, 150, 225, 337, 506, 759] and A.zeitpunkte(C.STRATEGIE_GEO, 100, 6) == [100, 250, 475, 812, 1318, 2077]


def test_claim_budget_0_und_1_stoppen_nach_dem_ersten_konflikt():
    for budget in (0, 1):
        erg = A.lauf(S.HANDBEISPIEL_G, C.STRATEGIE_LUBY, 1, budget=budget, feste_regel=True)
        assert erg.antwort is None and erg.stat["konflikte"] == 1


# ---------------------------------------------------------------- Schur-Probe (nicht in der App)
def test_claim_schur_probe_k4_n40():
    """Schur n = 40, k = 4 (erfüllbar; eine deterministische Aufgabe, Löser-Zufalls-Seeds 0 bis 4, Budget 20 000): ohne Neustarts 330 / 535 / 2 065 / 7 050 / 14 500 Konflikte,
    Luby (Einheit 32) 75 / 103 / 109 / 141 / 679; Median 2 065 gegen 109. Luby löst dabei Neustarts aus (3 im Lauf mit Seed 0)."""
    inst = I.schur(40, 4)
    keine = A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, range(5), budget=20000)
    luby = A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 32, range(5), budget=20000)
    assert sorted(keine[0]) == [330, 535, 2065, 7050, 14500] and sorted(luby[0]) == [75, 103, 109, 141, 679]
    assert keine[2] == luby[2] == 0 and statistics.median(keine[0]) == 2065 and statistics.median(luby[0]) == 109
    assert len(A.zeitleiste(inst, C.STRATEGIE_LUBY, 32, budget=20000).neustarts) == 3


# ---------------------------------------------------------------- Einheit und Faktor (Reiter 4)
def _kurve(daten, fam):
    return {z["name"]: z for z in E.kurve_zeilen(daten, fam)}


def test_claim_kurve_faerbung_luby_einheit(daten):
    """Färbung, 10 Aufgaben, 10 Löser-Seeds: Median-Quotient Median(Luby-Einheit u) / Median(keine) über die Aufgaben bei u = 4 / 8 / 16 / 32 / 64 / 128 / 256: 0,32 / 0,30 / 0,37 / 0,38 / 0,48 / 0,64 / 0,91.
    Die Kurve ist **nicht flach** (Verhältnis 3,09); bei u = 256 hilft Luby nur noch bei 3 von 10 Aufgaben, bei u = 4 und 8 bei 10 von 10."""
    z = _kurve(daten, FAE)
    assert [E.dezimal(z[f"luby:{u}"]["median"], 2) for u in C.KURVE_EINHEITEN] == ["0,32", "0,30", "0,37", "0,38", "0,48", "0,64", "0,91"]
    assert [z[f"luby:{u}"]["hilft"] for u in C.KURVE_EINHEITEN] == [10, 10, 10, 10, 9, 7, 3]
    assert E.dezimal(E.kurven_spreizung([z[f"luby:{u}"]["median"] for u in C.KURVE_EINHEITEN]), 2) == "3,09"
    assert "nicht flach" in E.verdict_kurve(list(z.values()), "luby", "Färbung")[1]


def test_claim_kurve_faerbung_faktor(daten):
    """Färbung, geometrisch (erste Grenze 100), Faktor 1,1 / 1,3 / 1,5 / 2: Median-Quotient 0,58 / 0,59 / 0,59 / 0,58, jedes Mal 7 von 10 Aufgaben mit „hilft“: die Kurve ist flach (Verhältnis 1,02)."""
    z = _kurve(daten, FAE)
    assert [E.dezimal(z[f"geo:{f}"]["median"], 2) for f in C.KURVE_FAKTOREN] == ["0,58", "0,59", "0,59", "0,58"]
    assert [z[f"geo:{f}"]["hilft"] for f in C.KURVE_FAKTOREN] == [7, 7, 7, 7]
    assert E.dezimal(E.kurven_spreizung([z[f"geo:{f}"]["median"] for f in C.KURVE_FAKTOREN]), 2) == "1,02"
    assert "die Kurve ist flach" in E.verdict_kurve(list(z.values()), "geo", "Färbung")[1]


def test_claim_kurve_zufall(daten):
    """Zufallsformel (n = 150, 12 Aufgaben): Median-Quotient bei Luby-Einheit 4 / 8 / 16 / 32 / 64 / 128 / 256: 0,89 / 0,86 / 0,87 / 0,85 / 0,81 / 0,80 / 0,79 (Verhältnis 1,12: flach);
    geometrisch Faktor 1,1 / 1,3 / 1,5 / 2: 0,78 / 0,77 / 0,79 / 0,76 (Verhältnis 1,04: flach). Je Aufgabe streuen die Quotienten der Luby-Kurve dennoch von 0,35 bis 1,32."""
    z = _kurve(daten, ZUF)
    assert [E.dezimal(z[f"luby:{u}"]["median"], 2) for u in C.KURVE_EINHEITEN] == ["0,89", "0,86", "0,87", "0,85", "0,81", "0,80", "0,79"]
    assert [E.dezimal(z[f"geo:{f}"]["median"], 2) for f in C.KURVE_FAKTOREN] == ["0,78", "0,77", "0,79", "0,76"]
    assert E.dezimal(E.kurven_spreizung([z[f"luby:{u}"]["median"] for u in C.KURVE_EINHEITEN]), 2) == "1,12"
    assert E.dezimal(E.kurven_spreizung([z[f"geo:{f}"]["median"] for f in C.KURVE_FAKTOREN]), 2) == "1,04"
    luby = [z[f"luby:{u}"] for u in C.KURVE_EINHEITEN]
    assert (E.dezimal(min(r["min"] for r in luby), 2), E.dezimal(max(r["max"] for r in luby), 2)) == ("0,35", "1,32")
    zeilen = list(z.values())
    assert "die Kurve ist flach" in E.verdict_kurve(zeilen, "luby", "Zufallsformel")[1] and "die Kurve ist flach" in E.verdict_kurve(zeilen, "geo", "Zufallsformel")[1]


def test_claim_kurven_messung_ohne_abbrueche(daten):
    assert all(a["abbrueche"] == 0 for fam in C.FAMILIEN for a in daten["kurve"][fam])
    assert sum(len(v) for fam in C.FAMILIEN for a in daten["kurve"][fam] for v in [a["keine"]] + list(a["luby"].values()) + list(a["geo"].values())) == 22 * 12 * 10


def test_claim_kurve_stimmt_mit_dem_heutigen_code_ueberein(daten):
    """Live nachgerechnet: Färbung A1, Luby-Einheit 4 und 256 sowie geometrisch Faktor 2 (10 Seeds)."""
    inst = S.messaufgabe(FAE, 0)
    a = daten["kurve"][FAE][0]
    assert A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 4, range(10))[0] == a["luby"]["4"]
    assert A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 256, range(10))[0] == a["luby"]["256"]
    assert A.konflikte_je_seed(inst, C.STRATEGIE_GEO, 100, range(10), faktor=2.0)[0] == a["geo"]["2.0"]


def test_claim_streuung_einzelaufgabe_haengt_an_der_seedzahl():
    """Preset „Zufallsformel“ (n = 100, Zufalls-Seed der Aufgabe 500, Budget 20 000): mit 10 Löser-Zufalls-Seeds ist der Median der Konflikte ohne Neustarts 94,5 und mit Luby 158 (+67 %, schadet);
    mit 30 Seeds 93,5 und 72 (besser). Eine Aufgabe und wenige Seeds sagen nichts über die Familie."""
    inst = S.aufgabe(ZUF, 100, 500)
    for seeds, (keine, luby) in ((10, (94.5, 158.0)), (30, (93.5, 72.0))):
        mk = statistics.median(A.konflikte_je_seed(inst, C.STRATEGIE_KEINE, 1, range(seeds), budget=20000)[0])
        ml = statistics.median(A.konflikte_je_seed(inst, C.STRATEGIE_LUBY, 32, range(seeds), budget=20000)[0])
        assert (mk, ml) == (keine, luby)
    assert E.einordnung(158 / 94.5) == E.SCHADET and E.einordnung(72 / 93.5) == E.HILFT and E.prozent(158 / 94.5) == "+67 %"
