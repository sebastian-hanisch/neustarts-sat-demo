"""Konstanten: Regler-Grenzen, feste Annahmen, Aufgabenfamilien, Schwellen der Verdikte, Farben und Presets."""

# --- Aufgabenfamilien --------------------------------------------------------------------------------------------------------------------
FAMILIE_FAERBUNG = "3-Färbung (Aufträge auf Rampen)"
FAMILIE_ZUFALL = "Zufalls-3-SAT"
FAMILIEN = (FAMILIE_FAERBUNG, FAMILIE_ZUFALL)
FAMILIE_KURZ = {FAMILIE_FAERBUNG: "Färbung", FAMILIE_ZUFALL: "Zufallsformel"}
GRAD = 4.5                       # mittlerer Grad des Konfliktgraphen (3-Färbung nahe der Schwelle, mehrheitlich erfüllbar)
RAMPEN = 3                       # Zahl der Rampen = Zahl der Farben
KLAUSEL_VERHAELTNIS = 4.26       # Klauseln je Variable bei Zufalls-3-SAT (Nähe des Phasenübergangs)

# --- Aufgabe in Reiter 1 -----------------------------------------------------------------------------------------------------------------
AUFGABE_HAND = "Handbeispiel (6 Variablen, 11 Klauseln)"
AUFGABE_SEITE = "Aufgabe aus der Seitenleiste"
AUFGABEN_R1 = (AUFGABE_HAND, AUFGABE_SEITE)

# --- Neustart-Strategien ---------------------------------------------------------------------------------------------------------------
STRATEGIE_KEINE, STRATEGIE_LUBY, STRATEGIE_GEO = "keine", "luby", "geo"
STRATEGIEN = (STRATEGIE_KEINE, STRATEGIE_LUBY, STRATEGIE_GEO)
STRATEGIE_NAMEN = {STRATEGIE_KEINE: "keine Neustarts", STRATEGIE_LUBY: "Luby", STRATEGIE_GEO: "geometrisch"}
EINHEITEN = (1, 2, 4, 8, 32, 100)   # Luby: Einheit u (Grenze = u mal Luby-Glied); geometrisch: erste Grenze
DEFAULT_EINHEIT_HAND = 1
DEFAULT_EINHEIT = 32
LUBY_EINHEIT_MESSUNG = 32          # Einheit der Messreihen (Reiter 2, 3)
GEO_START_MESSUNG = 100            # erste Grenze der geometrischen Strategie in den Messreihen
GEO_FAKTOR = 1.5                   # Faktor der geometrischen Strategie (Messreihen)
KURVE_EINHEITEN = (4, 8, 16, 32, 64, 128, 256)   # Reiter 4: Luby-Einheit
KURVE_FAKTOREN = (1.1, 1.3, 1.5, 2.0)            # Reiter 4: geometrischer Faktor (erste Grenze 100); zugleich die Auswahl des Reglers in Reiter 1
DEFAULT_FAKTOR = GEO_FAKTOR
LUBY_ZEILEN = 15                   # Länge der angezeigten Luby-Folge
TABELLEN_ZEILEN = 8                # Zahl der Neustartzeitpunkte in der Tabelle

# --- Regler ----------------------------------------------------------------------------------------------------------------------------
N_MIN, N_MAX, N_SCHRITT, DEFAULT_N = 40, 160, 10, 120
SEED_MAX, DEFAULT_SEED = 999999, 500
BUDGET_OPTIONEN = (1000, 5000, 20000, 200000)
DEFAULT_BUDGET = 20000
BUDGET_MESSUNG = 200000            # Budget der vorgerechneten Messreihen
SEEDS_MIN, SEEDS_MAX, DEFAULT_SEEDS = 5, 30, 30
LOESER_SEED_R1 = 0                 # Löser-Zufalls-Seed der Einzelläufe in Reiter 1 (Start der Aktivitäten)

# --- Vorgerechnete Messreihen (Dateien und Aufgabenlisten) -----------------------------------------------------------------------------
MESSUNG_DATEI = "nst_messung_vorgerechnet.json"
MESSSKRIPT = "tools/messung_neustarts.py"
FAERBUNG_N, FAERBUNG_AUFGABEN = 160, tuple(500 + i for i in range(10))       # Zufalls-Seeds der Aufgaben (Färbung n = 160, Grad 4,5)
ZUFALL_N, ZUFALL_M, ZUFALL_AUFGABEN = 150, 639, tuple(2000 + i for i in range(12))   # Zufalls-3-SAT n = 150, m = 639 (m/n = 4,26)
MESS_SEEDS = 30                    # Löser-Zufalls-Seeds je Aufgabe (Reiter 3)
KURVE_SEEDS = 10                   # Löser-Zufalls-Seeds je Aufgabe und Einstellung (Reiter 4)

# --- Schwellen der Verdikte (vor der Messung festgelegt, im Test festgeschrieben) -------------------------------------------------------
NEUTRAL_BAND = 0.20                # |Median(mit) / Median(ohne) - 1| <= 0,2: „neutral“; darunter „hilft“, darüber „schadet“
FLACH_VERHAELTNIS = 1.2            # Kurve „flach“: größter Median-Quotient höchstens das 1,2-Fache des kleinsten

# --- Farben ------------------------------------------------------------------------------------------------------------------------
COLOR_KEINE = "#8d8d8d"
COLOR_LUBY = "#2F6B65"
COLOR_GEO = "#d68a2b"
COLOR_NEUSTART = "#c0392b"
COLOR_LINE = "#4c78a8"
STRATEGIE_FARBEN = {STRATEGIE_KEINE: COLOR_KEINE, STRATEGIE_LUBY: COLOR_LUBY, STRATEGIE_GEO: COLOR_GEO}

# --- Presets --------------------------------------------------------------------------------------------------------------------------
PRESETS = {
    "Handbeispiel": {"aufgabe": AUFGABE_HAND, "strategie": STRATEGIE_LUBY, "einheit": DEFAULT_EINHEIT_HAND},
    "Rampen-Färbung": {"aufgabe": AUFGABE_SEITE, "familie": FAMILIE_FAERBUNG, "n": 160, "strategie": STRATEGIE_LUBY, "einheit": DEFAULT_EINHEIT, "seeds": 10},
    "Zufallsformel": {"aufgabe": AUFGABE_SEITE, "familie": FAMILIE_ZUFALL, "n": 100, "strategie": STRATEGIE_LUBY, "einheit": DEFAULT_EINHEIT, "seeds": 10},
    "Streuung groß": {"aufgabe": AUFGABE_SEITE, "familie": FAMILIE_FAERBUNG, "n": 160, "strategie": STRATEGIE_LUBY, "einheit": DEFAULT_EINHEIT, "seeds": 30},
}
PRESET_HELP = {
    "Handbeispiel": "Die Formel G aus dem Handbeispiel (6 Variablen, 11 Klauseln, unerfüllbar): feste Entscheidungsregel, Luby mit Einheit 1. Zeigt nur die Mechanik der Neustarts.",
    "Rampen-Färbung": "Aufträge auf Rampen (3-Färbung eines Konfliktgraphen mit 160 Aufträgen, mittlerer Grad 4,5), Luby mit Einheit 32, 10 Löser-Zufalls-Seeds im Reiter „Streuung gegen Median“.",
    "Zufallsformel": "Zufalls-3-SAT mit 100 Variablen und 426 Klauseln (4,26 Klauseln je Variable), Luby mit Einheit 32, 10 Löser-Zufalls-Seeds im Reiter „Streuung gegen Median“.",
    "Streuung groß": "Wie „Rampen-Färbung“, aber mit 30 Löser-Zufalls-Seeds im Reiter „Streuung gegen Median“ (die Läufe starten auf Knopfdruck).",
}
