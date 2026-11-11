"""Neustarts – dieselbe Aufgabe, andere Reihenfolge - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Neustart eines CDCL-Lösers wirft die Entscheidungen weg und behält die gelernten Klauseln. Vier Experimente: Neustartzeitpunkte lesen,
Streuung gegen Median, Familienvergleich (Färbung gegen Zufallsformeln), Einheit und Faktor.
Aufwand wird in Konflikten, Entscheidungen, Neustarts und gelernten Klauseln gezählt, nie in Sekunden.

Lauffähig mit: streamlit run app.py
"""

import time

import pandas as pd
import streamlit as st

import nst_algorithm as A
import nst_constants as C
import nst_evaluation as E
import nst_instanzen as I
import nst_scenario as S
import nst_visualization as V
from nst_layout import dunkles_design, kopf_css
from nst_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Neustarts – Sebastian Hanisch", layout="wide")

MAX_NEUSTART_ZEILEN = 40


@st.cache_data(show_spinner=False)
def _zeitleiste_hand(strategie, einheit, faktor):
    zl = A.zeitleiste(S.HANDBEISPIEL_G, strategie, einheit, faktor=faktor, feste_regel=True)
    ohne = A.zeitleiste(S.HANDBEISPIEL_G, C.STRATEGIE_KEINE, 1, feste_regel=True)
    voll = A.lauf(S.HANDBEISPIEL_G, strategie, einheit, faktor=faktor, feste_regel=True, trace=True)
    return zl, ohne, A.ereignis_zeilen(voll.spur)


@st.cache_data(show_spinner=False)
def _zeitleiste_seite(familie, n, seed, strategie, einheit, faktor, budget):
    inst = S.aufgabe(familie, n, seed)
    zl = A.zeitleiste(inst, strategie, einheit, faktor=faktor, seed=C.LOESER_SEED_R1, budget=budget)
    modell_ok = None
    if zl.ergebnis.antwort is True:
        modell_ok = I.pruefe_modell(inst.klauseln, zl.ergebnis.modell)
    return inst, zl, modell_ok


@st.cache_data(show_spinner=False)
def _streuung(familie, n, seed, seeds, budget):
    """Konflikte je Löser-Zufalls-Seed (0 bis seeds - 1) für keine, Luby (32), geometrisch (100, ×1,5)."""
    t0 = time.perf_counter()
    inst = S.aufgabe(familie, n, seed)
    konf, antworten, abbr = {}, set(), {}
    konfig = {C.STRATEGIE_KEINE: 1, C.STRATEGIE_LUBY: C.LUBY_EINHEIT_MESSUNG, C.STRATEGIE_GEO: C.GEO_START_MESSUNG}
    for s, einheit in konfig.items():
        konf[s], ans, abbr[s] = A.konflikte_je_seed(inst, s, einheit, range(seeds), budget=budget)
        antworten |= ans
    return inst, konf, abbr, antworten, time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _daten():
    return E.lade_messung()


def _tabelle(daten, spalten):
    st.dataframe(pd.DataFrame(daten, columns=spalten), hide_index=True, width="stretch")


def _neustart_tabelle(zl):
    zeilen = [[i, k, st_, 0, seit, g] for i, (k, st_, seit, g) in enumerate(zl.neustarts, 1)]
    return zeilen[:MAX_NEUSTART_ZEILEN]


NEUSTART_SPALTEN = ["Neustart Nr.", "nach Konflikt Nr.", "Stufe davor", "Stufe danach", "Konflikte seit dem letzten Neustart", "gelernte Klauseln bis dahin"]


def _konflikt_wort(k: int) -> str:
    return f"{k} Konflikt" if k == 1 else f"{k} Konflikte"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in nst_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔁 Neustarts – dieselbe Aufgabe, andere Reihenfolge")
st.markdown(
    """
**Ein Neustart wirft die Entscheidungen des Lösers weg, behält aber alle gelernten Klauseln.** Die Demo misst an **Aufträgen auf Rampen** (3-Färbung eines Konfliktgraphen) und an
**Zufalls-3-SAT**, was das für die Zahl der Konflikte und vor allem für ihre **Streuung** bedeutet: Neustarts nach **Luby** oder **geometrisch** gegen **keine**. Der Aufwand wird in
**Konflikten, Entscheidungen, Neustarts und gelernten Klauseln** gezählt, nie in Sekunden.

Weiter unten: vier Experimente (Reiter), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktionieren Neustarts", expanded=True):
    st.markdown(
        """
Ein CDCL-Löser entscheidet eine Variable nach der anderen, folgert daraus (Propagation) und lernt bei jedem Konflikt eine Klausel. Ein **Neustart** springt auf Stufe 0 zurück:
**verworfen** werden alle Entscheidungen und ihre Folgerungen, **behalten** werden alle gelernten Klauseln, die Aktivitäten der Variablen und (in den Aufgaben der Seitenleiste) die gespeicherten Phasen.
Danach entscheidet der Löser wieder von vorn, mit den inzwischen geänderten Aktivitäten; so kann er in einen anderen Teil des Suchraums geraten (Deutung, nicht gemessen). Wann ein Neustart fällig ist, bestimmt die **Strategie**:

| Strategie | Grenze: Konflikte bis zum nächsten Neustart | Stellschraube | Was sie erzeugt |
|---|---|---|---|
| **keine** | – | – | Die Suche läuft ohne Unterbrechung; Entscheidungen bleiben, bis ein Konflikt sie zurücknimmt. |
| **Luby** | Einheit mal Luby-Glied: 1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8, … mal Einheit | die Einheit (hier 1 bis 100; Messreihen: 32) | Viele kurze Läufe, dazwischen immer seltener ein langer; die Folge ist nach Luby, Sinclair und Zuckerman (1993) eine universelle Strategie für Las-Vegas-Algorithmen. |
| **geometrisch** | erste Grenze, danach jede mit 1,5 multipliziert und abgerundet | die erste Grenze (hier 1 bis 100; Messreihen: 100) und der Faktor (Reiter 4) | Wachsende Läufe: 100, 150, 225, 337, 506, 759, … |

**Wann der Neustart stattfindet:** erst, wenn die Propagation ohne Konflikt geendet hat. Er folgt, sobald seit dem letzten Neustart mindestens die Grenze an Konflikten gezählt wurde
**und** mindestens eine Entscheidung auf dem Stapel liegt. Auf Stufe 0 gibt es nichts zu verwerfen; die „Schuld“ bleibt dann bestehen und wird eingelöst, sobald wieder eine Entscheidung steht.
        """
    )

load_permalink_settings()
init_session_state_defaults()
st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Aufgabe** (Reiter „Neustartzeitpunkte“ mit der Aufgabe der Seitenleiste und Reiter „Streuung gegen Median“)")
    familie = st.selectbox("Aufgabenfamilie", C.FAMILIEN, key="familie_select",
                           help="Färbung: n Aufträge, mittlerer Grad 4,5 im Konfliktgraphen, 3 Rampen. Zufalls-3-SAT: n Variablen, 4,26 Klauseln je Variable.")
    n = st.slider("Größe n (Aufträge bzw. Variablen)", *bounds("n_slider"), step=C.N_SCHRITT, key="n_slider",
                  help="Bei Zufallsformeln mit großem n können die Läufe des Reiters „Streuung gegen Median“ länger dauern.")
    st.markdown("**Zufall und Budget**")
    seed = st.number_input("Zufalls-Seed der Aufgabe", *bounds("seed_input"), key="seed_input", step=1,
                           help="Bestimmt die Aufgabe (SplitMix64): den Konfliktgraphen bzw. die Formel. Die Löser-Zufalls-Seeds sind davon getrennt.")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)
    budget = st.select_slider("Konfliktbudget", options=C.BUDGET_OPTIONEN, key="budget_slider",
                              help="Nach so vielen Konflikten bricht ein Lauf ab; die Konfliktzahl ist dann eine untere Schranke.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was ändern Neustarts an den Konflikten und an ihrer Streuung?")
daten = _daten()
zusammen = {}
for fam in C.FAMILIEN:
    zusammen[C.FAMILIE_KURZ[fam]] = E.familien_zusammenfassung(E.aufgaben_zeilen(daten, fam), C.STRATEGIE_LUBY)
kind, text = E.verdict_kern(zusammen)
getattr(st, kind)(text)
st.caption("Die Zählung stammt aus den vorgerechneten Messreihen (Reiter „Familienvergleich“), nicht aus einem Lauf dieser Sitzung.")
kopfzahlen = st.container()

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🔬 Neustartzeitpunkte", "🔬 Streuung gegen Median", "🔬 Familienvergleich", "🔬 Einheit und Faktor"])

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

with tab1:
    st.subheader("🔬 Neustartzeitpunkte lesen")
    st.caption("Ein Einzellauf mit Zeitleiste: jeder Konflikt mit seiner Entscheidungsstufe, jeder Neustart als rote Marke. Das Handbeispiel hat eine feste Entscheidungsregel "
               "(kleinste freie Variable, zuerst falsch) und keinen Zufall; die Aufgabe der Seitenleiste läuft mit Aktivität, Phasenspeicher und Löser-Zufalls-Seed 0.")
    aufgabe = st.radio("Aufgabe", C.AUFGABEN_R1, key="aufgabe_radio", horizontal=True)
    c1, c2, c3 = st.columns([1.2, 1.4, 1])
    strategie = c1.radio("Strategie", C.STRATEGIEN, key="strategie_radio", format_func=lambda s: C.STRATEGIE_NAMEN[s])
    einheit = c2.select_slider("Einheit (Luby) bzw. erste Grenze (geometrisch)", options=C.EINHEITEN, key="einheit_select", disabled=strategie == C.STRATEGIE_KEINE,
                               help="Grenze = Einheit mal Luby-Glied; geometrisch: erste Grenze, danach mal Faktor. Ohne Neustarts ohne Wirkung (der Regler ist dann gesperrt).")
    faktor = c3.select_slider("Faktor (geometrisch)", options=C.KURVE_FAKTOREN, key="faktor_select", disabled=strategie != C.STRATEGIE_GEO,
                              format_func=lambda f: str(f).replace(".", ","), help="Gilt nur für die geometrische Strategie; sonst gesperrt.")
    if aufgabe == C.AUFGABE_HAND:
        inst = S.HANDBEISPIEL_G
        zl, ohne_zl, zeilen_spur = _zeitleiste_hand(strategie, einheit, faktor)
        mit = A.messung(zl.ergebnis)
        ohne = A.messung(ohne_zl.ergebnis)
        modell_ok = None
    else:
        inst, zl, modell_ok = _zeitleiste_seite(familie, n, int(seed), strategie, einheit, faktor, budget)
        mit = A.messung(zl.ergebnis)
    st.markdown(f"**Aufgabe:** {S.beschreibung(inst)}.")
    if aufgabe == C.AUFGABE_HAND:
        kind, text = E.verdict_handbeispiel(mit, ohne, strategie, einheit)
    else:
        kind, text = E.verdict_lauf(mit, strategie, einheit)
    getattr(st, kind)(text)
    if modell_ok is True:
        st.caption("Das Modell des Lösers wurde gegen jede Klausel geprüft (unabhängig vom Löser).")
    elif modell_ok is False:
        st.error("Das Modell des Lösers verletzt eine Klausel: das darf nicht vorkommen.")

    grenz_zp = A.zeitpunkte(strategie, einheit, 60, faktor) if strategie != C.STRATEGIE_KEINE else []
    st.plotly_chart(V.build_zeitleiste(zl, grenz_zp), width="stretch", key="zeitleiste")
    st.caption("Blau: Stufe, auf der der Konflikt auftrat. Grüne Kreise: Stufe, auf die nach dem Lernen zurückgesprungen wurde. Rote Kreuze und Linien: Neustart (Sprung auf Stufe 0). "
               "Graue Dreiecke: die Konfliktzahl, bei der die Grenze der Strategie erreicht ist; der Neustart folgt erst, wenn eine Entscheidung steht.")

    links, rechts = st.columns(2)
    with links:
        st.markdown("**Grenze erreicht nach Konflikt Nr. (kumulativ)**")
        zeilen_zp = E.tabelle_zeitpunkte()
        _tabelle(zeilen_zp, ["Strategie"] + [f"{i}." for i in range(1, C.TABELLEN_ZEILEN + 1)])
        st.caption("Die erste Luby-Zeile (Einheit 1) ist die Tabelle des Handbeispiels. Der tatsächliche Neustart folgt, sobald keine Konflikte mehr offen sind und eine Entscheidung steht.")
    with rechts:
        st.markdown("**Luby-Folge** (Glieder 1 bis 15)")
        _tabelle([A.luby_folge(C.LUBY_ZEILEN)], [str(i) for i in range(1, C.LUBY_ZEILEN + 1)])
        st.caption("Jedes Glied ist die Zahl der Einheiten bis zum nächsten Neustart; das Glied $2^{k-1}$ steht an der Stelle $2^k - 1$ (4 an Stelle 7, 8 an Stelle 15), dazwischen wiederholt sich die Folge davor.")

    st.markdown(f"**Neustarts dieses Laufs** ({zl.ergebnis.stat['neustarts']})")
    if zl.neustarts:
        _tabelle(_neustart_tabelle(zl), NEUSTART_SPALTEN)
        if len(zl.neustarts) > MAX_NEUSTART_ZEILEN:
            st.caption(f"Gezeigt sind die ersten {MAX_NEUSTART_ZEILEN} von {len(zl.neustarts)} Neustarts.")
        st.caption("„Stufe davor“ ist die Zahl der Entscheidungen, die der Neustart verwirft; danach steht der Löser immer auf Stufe 0, und die Zahl der gelernten Klauseln ist nicht kleiner geworden.")
    else:
        st.info("In diesem Lauf gab es keinen Neustart.")

    if aufgabe == C.AUFGABE_HAND:
        st.markdown("**Schritt für Schritt (Spur des Lösers)**")
        schritt = st.slider("Ereignis", 1, len(zeilen_spur), len(zeilen_spur), key=f"ereignis_{strategie}_{einheit}",
                            help="Zeigt die Ereignisse des Laufs bis zum gewählten; das letzte ist hervorgehoben.")
        st.markdown(f"**Ereignis {schritt}:** {zeilen_spur[schritt - 1][2]}")
        with st.expander("Alle Ereignisse bis hierher", expanded=False):
            for nr, _, t in zeilen_spur[:schritt]:
                st.markdown(f"{nr}. {t}")
        st.caption("Handbeispiel G (von Hand nachgerechnet, in den Tests): 6 Variablen, 11 Klauseln, unerfüllbar; die fünf gelernten Klauseln sind jeweils aus den vorigen per Einheitspropagation herleitbar.")

with kopfzahlen:
    st.markdown(f"**Der Lauf aus Reiter „Neustartzeitpunkte“:** {S.beschreibung(inst)}")
    z1, z2, z3, z4, z5 = st.columns([1.6, 1, 1.3, 1, 1.4])
    z1.metric("Antwort", mit.antwort_text)
    z2.metric("Konflikte", E.zahl(mit.konflikte))
    z3.metric("Entscheidungen", E.zahl(mit.entscheidungen))
    z4.metric("Neustarts", E.zahl(mit.neustarts))
    z5.metric("gelernte Klauseln", E.zahl(mit.gelernt))

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

with tab2:
    st.subheader("🔬 Streuung gegen Median: dieselbe Aufgabe, viele Löser-Zufalls-Seeds")
    st.caption("Die Aufgabe bleibt gleich; die Löser-Zufalls-Seeds 0 bis (Zahl − 1) streuen nur den zufälligen Start der Aktivitäten. Je Strategie ein Kastendiagramm der Konflikte: "
               "Median, P90 (Wert am 90-Prozent-Rang), Maximum und Abbrüche am Budget. Verglichen werden keine Neustarts, Luby (Einheit 32) und geometrisch (erste Grenze 100, Faktor 1,5).")
    seeds = st.slider("Löser-Zufalls-Seeds", *bounds("seeds_slider"), key="seeds_slider", help="Je Strategie so viele Läufe derselben Aufgabe.")
    st.markdown(f"**Aufgabe:** {S.beschreibung(S.aufgabe(familie, n, int(seed)))}.")
    schluessel = (familie, n, int(seed), seeds, budget)
    if familie == C.FAMILIE_ZUFALL and n >= 140:
        st.caption(f"Bei Zufallsformeln dieser Größe können 3 × {seeds} Läufe länger als eine Minute dauern; weniger Seeds oder ein kleineres n wählen, wenn es schneller gehen soll.")
    if st.button("▶ Läufe rechnen", key="streuung_rechnen"):
        with st.spinner(f"Rechne 3 × {seeds} Läufe, je bis zu {E.zahl(budget)} Konflikte …"):
            st.session_state["streuung_ergebnis"] = (schluessel, *_streuung(*schluessel))
    erg = st.session_state.get("streuung_ergebnis")
    if erg is None or erg[0] != schluessel:
        st.info("Für diese Einstellung ist noch nichts gerechnet. Mit „Läufe rechnen“ starten.")
    else:
        _, inst2, konf, abbr, antworten, sek = erg
        zeilen = {s: E.zeile_streuung(konf[s], abbr[s]) for s in C.STRATEGIEN}
        kind, text = E.verdict_streuung(zeilen, C.FAMILIE_KURZ[familie])
        getattr(st, kind)(text)
        antwort_text = "Abbruch" if not antworten else ("erfüllbar" if antworten == {True} else "unerfüllbar" if antworten == {False} else "widersprüchlich (Fehler)")
        st.markdown(f"**Antwort der Aufgabe in allen Läufen, die eine Antwort fanden:** {antwort_text}.")
        _tabelle([[C.STRATEGIE_NAMEN[s], E.zahl(zeilen[s]["median"]), E.zahl(zeilen[s]["p90"]), E.zahl(zeilen[s]["max"]), E.zahl(zeilen[s]["min"]),
                   f"{zeilen[s]['abbrueche']} von {zeilen[s]['n']}"] for s in C.STRATEGIEN],
                 ["Strategie", "Median", "P90", "Maximum", "Minimum", "Abbrüche am Budget"])
        st.plotly_chart(V.build_box(konf), width="stretch", key="streuung_box")
        st.caption(f"Jeder Punkt ist ein Lauf. Abbrüche zählen mit dem Budget ({E.zahl(budget)} Konflikte); die Zahlen sind dann untere Schranken. "
                   f"Rechenzeit dieser Läufe: {sek:.1f} s (nur Anzeige, kein Befund). Ein einzelner Zufalls-Seed der Aufgabe sagt nichts über die Familie: dafür gibt es den Reiter „Familienvergleich“.")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("🔬 Familienvergleich: Färbung gegen Zufallsformeln")
    meta = daten["meta"]
    st.caption(f"Vorgerechnet mit `{meta['skript']}` (Datei `{C.MESSUNG_DATEI}`), **nicht live**: je Aufgabe {meta['mess_seeds']} Löser-Zufalls-Seeds, Konfliktbudget {E.zahl(meta['budget'])}, "
               f"Luby mit Einheit {meta['luby_einheit']}, geometrisch mit erster Grenze {meta['geo_start']} und Faktor {str(meta['geo_faktor']).replace('.', ',')}. "
               f"Färbung: {len(meta['faerbung']['seeds'])} Aufgaben (n = {meta['faerbung']['n']}, Grad {str(meta['faerbung']['grad']).replace('.', ',')}); "
               f"Zufalls-3-SAT: {len(meta['zufall']['seeds'])} Aufgaben (n = {meta['zufall']['n']}, m = {meta['zufall']['m']}). Unabhängig von den Reglern der Seitenleiste.")
    kind, text = E.verdict_familien(zusammen)
    getattr(st, kind)(text)
    st.caption("„neutral“ heißt: der Quotient liegt im Band 0,8 bis 1,2 (±20 % des Medians ohne Neustarts); die Schwelle stand vor der Messung fest.")
    for fam in C.FAMILIEN:
        kurz = C.FAMILIE_KURZ[fam]
        zeilen_f = E.aufgaben_zeilen(daten, fam)
        st.markdown(f"**{kurz}**")
        st.plotly_chart(V.build_quotienten(zeilen_f, kurz), width="stretch", key=f"quot_{kurz}")
        with st.expander(f"Alle Zahlen je Aufgabe ({kurz}): Median / P90 der Konflikte"):
            _tabelle([[f"A{z['index'] + 1}", z["antwort"],
                       f"{E.zahl(z['keine']['median'])} / {E.zahl(z['keine']['p90'])}",
                       f"{E.zahl(z['luby']['median'])} / {E.zahl(z['luby']['p90'])}", E.dezimal(z["q_luby"], 2), z["klasse_luby"],
                       f"{E.zahl(z['geo']['median'])} / {E.zahl(z['geo']['p90'])}", E.dezimal(z["q_geo"], 2), z["klasse_geo"]] for z in zeilen_f],
                     ["Aufgabe", "Antwort", "keine", "Luby", "Quotient Luby", "Luby: Einordnung", "geometrisch", "Quotient geom.", "geom.: Einordnung"])
            st.caption("Quotient = Median mit Neustarts durch Median ohne Neustarts, je Aufgabe über alle Löser-Zufalls-Seeds.")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

with tab4:
    st.subheader("🔬 Einheit und Faktor: wie viel hängt an den Stellschrauben?")
    st.caption(f"Vorgerechnet mit `{meta['skript']}`, **nicht live**: je Aufgabe und Einstellung {meta['kurve_seeds']} Löser-Zufalls-Seeds. Die Kurve zeigt je Einstellung den Median der Quotienten "
               "Median(mit Neustarts) / Median(keine) über die Aufgaben der Familie; die Balken reichen vom kleinsten bis zum größten Quotienten einer Aufgabe. Grauer Streifen: das Band „neutral“ (0,8 bis 1,2).")
    kurve_fam = st.selectbox("Familie", C.FAMILIEN, key="kurve_select")
    kurz = C.FAMILIE_KURZ[kurve_fam]
    zeilen_k = E.kurve_zeilen(daten, kurve_fam)
    for art in ("luby", "geo"):
        kind, text = E.verdict_kurve(zeilen_k, art, kurz)
        getattr(st, kind)(text)
    ca, cb = st.columns(2)
    ca.plotly_chart(V.build_kurve(zeilen_k, "luby", kurz), width="stretch", key="kurve_luby")
    cb.plotly_chart(V.build_kurve(zeilen_k, "geo", kurz), width="stretch", key="kurve_geo")
    with st.expander("Alle Zahlen der Kurven"):
        _tabelle([[z["name"].replace("luby:", "Luby, Einheit ").replace("geo:", "geometrisch, Faktor ").replace(".", ","), E.dezimal(z["median"], 2), E.dezimal(z["min"], 2),
                   E.dezimal(z["max"], 2), z["klasse"], f"{z['hilft']} von {z['n']}"] for z in zeilen_k],
                 ["Einstellung", "Median-Quotient", "kleinster", "größter", "Einordnung des Medians", "Aufgaben mit „hilft“"])

sync_query_params({k: st.session_state.get(k, spec.default) for k, spec in SETTING_SPECS.items()})

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Zwei Aufgabenfamilien** (Färbung n = 160, Zufalls-3-SAT n = 150, je 10 bis 12 Aufgaben) | Die Aussage gilt für diese Familien und Größen. Schur und Schubfach, industrielle Formeln und andere Größen sind nicht gemessen. |
| **Die Löser-Zufalls-Seeds streuen nur den Start der Aktivitäten** | Die Streuung über die Seeds ist nicht die Streuung über Aufgaben; Median und P90 eines Reiters gelten für die eine Aufgabe. |
| **Einheit 32 und Faktor 1,5 sind nicht abgestimmt** | Reiter „Einheit und Faktor“ misst die Kurve; ob ein anderer Wert besser ist, steht dort, gilt aber nur für diese Familien. |
| **Zählgrößen statt Sekunden** | Gezählt werden Konflikte, Entscheidungen, Neustarts und gelernte Klauseln. Konflikte sind nicht gleich teuer; eine Aussage über die Laufzeit machen die Zahlen nicht. |
| **Ein Löser (CDCL mit Aktivität, Phasenspeicher, ohne Löschen)** | Rephasing, Wechsel stabil/fokussiert, adaptive Neustarts nach Glucose-Art und Neustarts mit teilweiser Wiederverwendung des Stapels sind nicht Teil der Demo und nicht gemessen. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel in konjunktiver Normalform mit Variablen $x_1, \dots, x_n$ und Klauseln aus Literalen. Gesucht ist eine erfüllende Belegung oder der Beweis, dass es keine gibt.
Der Löser zählt die Konflikte $c = 1, 2, 3, \dots$ bis zur Antwort; ein Neustart ist ein Sprung auf Stufe 0 ohne Verlust gelernter Klauseln.

| Symbol | Bedeutung |
|---|---|
| $c$ | laufende Zahl der Konflikte seit Beginn des Laufs |
| $t_i$ | $i$-tes Glied der Luby-Folge ($i = 1, 2, \dots$) |
| $u$ | Einheit der Luby-Strategie, zugleich erste Grenze der geometrischen Strategie |
| $g_i$ | Grenze vor dem $i$-ten Neustart: Konflikte, die seit dem vorigen Neustart gezählt sein müssen |
| $f$ | Faktor der geometrischen Strategie (hier 1,5; in Reiter 4 variiert) |
| $T_i$ | Konfliktzahl, bei der die $i$-te Grenze erreicht ist (kumulativ) |

**Luby-Folge** (Luby, Sinclair und Zuckerman 1993): für $i \ge 1$ gilt

$$t_i = 2^{k-1} \quad \text{falls } i = 2^k - 1,$$

$$t_i = t_{\,i - 2^{k-1} + 1} \quad \text{falls } 2^{k-1} \le i < 2^k - 1.$$

Das ergibt $1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8, \dots$. Die Strategie lässt den $i$-ten Lauf höchstens $g_i = u \cdot t_i$ Konflikte dauern.

**Geometrische Folge.** Mit der ersten Grenze $u$ und dem Faktor $f$ ist

$$g_i = \lfloor u \cdot f^{\,i-1} \rfloor,$$

wobei der Löser die Zahl $u f^{\,i-1}$ ungerundet fortschreibt und erst die Grenze abrundet (für $u = 100$, $f = 1{,}5$: 100, 150, 225, 337, 506, 759).

**Zeitpunkte.** Die $i$-te Grenze ist nach

$$T_i = \sum_{j=1}^{i} g_j$$

Konflikten erreicht. Der Neustart selbst folgt erst, wenn die Propagation ohne Konflikt endet und mindestens eine Entscheidung auf dem Stapel liegt; deshalb liegt der tatsächliche Neustart nicht immer genau bei $T_i$.

**Einordnung in „hilft“, „neutral“, „schadet“** (Schwelle vor der Messung festgelegt): mit $m_\text{mit}$ und $m_\text{ohne}$ als Median der Konflikte über die Löser-Zufalls-Seeds einer Aufgabe ist

$$q = \frac{m_\text{mit}}{m_\text{ohne}}, \qquad \text{hilft: } q < 0{,}8, \qquad \text{neutral: } 0{,}8 \le q \le 1{,}2, \qquad \text{schadet: } q > 1{,}2.$$

**Annahmen der Messung.**

| Annahme | Wert |
|---|---|
| Aufgabenfamilien | 3-Färbung eines Zufallsgraphen (n = 160, mittlerer Grad 4,5, 3 Rampen), Zufalls-3-SAT (n = 150, m = 639, also 4,26 Klauseln je Variable) |
| Löser-Zufalls-Seeds | zufälliger Start der Aktivitäten aus dem SplitMix64; 30 je Aufgabe (Reiter 3), 10 je Einstellung (Reiter 4) |
| Löser | CDCL mit 1-UIP, Aktivität (VSIDS in der MiniSat-Variante, Zerfall 0,95), Phasenspeicher, ohne Löschen |
| Budget | 200 000 Konflikte; ein Abbruch zählt mit dem Budget |
| Messgröße | Konflikte bis zur Antwort |

**Literatur.** M. Luby, A. Sinclair, D. Zuckerman: Optimal speedup of Las Vegas algorithms. Information Processing Letters 47(4), 1993, S. 173–180 (Volltext gelesen: die universelle Strategie $1, 1, 2, 1, 1, 2, 4, \dots$ ist unter den universellen Strategien, die die Verteilung der Laufzeiten nicht kennen, bis auf einen konstanten Faktor optimal; gegenüber der besten Strategie für eine bekannte Verteilung gilt das nur bis auf einen logarithmischen Faktor; das Papier handelt von Las-Vegas-Algorithmen, nicht von SAT).
G. Audemard, L. Simon: Predicting learnt clauses quality in modern SAT solvers. IJCAI 2009 (Volltext gelesen: nennt MiniSat mit Luby-Neustarts, Start 32, und Phasenspeicher als Grundlage von Glucose).
M. Moskewicz u. a.: Chaff: engineering an efficient SAT solver. DAC 2001 (Volltext gelesen: Neustarts verwerfen alle Entscheidungen; die Autoren vermerken, dass sich ähnliche Ergebnisse oft oder zumindest manchmal auch ohne Neustarts erzielen lassen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
