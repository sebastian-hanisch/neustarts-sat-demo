# Neustarts – dieselbe Aufgabe, andere Reihenfolge – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-neustarts-sat-demo.streamlit.app/)**

Stück der **sat-constraint-programming**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, im SAT-Arm. Vorgänger ist [variablenwahl-sat-demo](https://github.com/sebastian-hanisch/variablenwahl-sat-demo) (Variablenwahl nach Aktivität; Kante „fix“: die frühe Wahl bindet den Löser zu lange an einen schlechten Teil des Suchraums), Nachfolger [klauseln-loeschen-demo](https://github.com/sebastian-hanisch/klauseln-loeschen-demo) (was mit den gelernten Klauseln geschieht; hier bleiben sie alle erhalten). Rückgriff: [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo) zählt Knoten der Suche ohne Gedächtnis und ohne Neustarts; hier zählen Konflikte mit Lernen. [graph-coloring-demo](https://github.com/sebastian-hanisch/graph-coloring-demo) hat dasselbe Kernmodell (Färbung) mit anderer Frage. Vehikel sind **Aufträge auf Rampen** (3-Färbung eines Konfliktgraphen) und **Zufalls-3-SAT**; dazu das **Handbeispiel G** (6 Variablen, 11 Klauseln). Der CDCL-Löser ist eine Kopie des Kern-Pakets der Linie (`nst_cdcl.py`, Herkunft und Kern-Version im Modulkopf); die Strategien, die Zeitleiste und alle Messungen sind neuer Code dieses Repos. Die Demo hängt an keiner anderen Demo.

## Warum dieses Problem

**Ein Neustart wirft die Entscheidungen weg, behält aber alle gelernten Klauseln.** Die Kernfrage der Demo: **Was ändert das an der Zahl der Konflikte und an ihrer Streuung, auf strukturierten Aufgaben (Färbung) und auf Zufallsformeln?** Aufwand wird in Konflikten, Entscheidungen, Neustarts und gelernten Klauseln gezählt, nie in Sekunden. Die Antwort steht im Abschnitt „Befunde“; sie gilt für die gemessenen Familien und Größen und nur mit der Schwelle von ±20 % des Medians, die vor der Messung festgelegt wurde.

## Modell

- **Löser.** CDCL mit 1-UIP-Lernen, Aktivität je Variable (VSIDS in der MiniSat-Variante, Zerfall 0,95), Phasenspeicher, ohne Löschen gelernter Klauseln. Im **Handbeispiel** gilt eine feste Entscheidungsregel (kleinste freie Variable, zuerst falsch, kein Phasenspeicher, kein Zufall).
- **Neustart.** Sprung auf Stufe 0. Verworfen werden Entscheidungen und Folgerungen; behalten werden gelernte Klauseln, Aktivitäten und (außer im Handbeispiel) gespeicherte Phasen. Der Neustart wird erst geprüft, wenn die Propagation ohne Konflikt geendet hat, und findet statt, wenn seit dem letzten Neustart mindestens die **Grenze** an Konflikten gezählt wurde und mindestens eine Entscheidung auf dem Stapel liegt. Auf Stufe 0 gibt es nichts zu verwerfen; die Schuld bleibt dann bestehen.
- **Strategien.** **Keine**; **Luby** (Grenze = Einheit mal Luby-Glied 1, 1, 2, 1, 1, 2, 4, …; Messreihen mit Einheit 32); **geometrisch** (erste Grenze, danach mal Faktor, abgerundet; Messreihen mit erster Grenze 100 und Faktor 1,5).
- **Aufgaben.** Färbung: n Aufträge, Konfliktgraph mit mittlerem Grad 4,5 (SplitMix64), 3 Rampen (= 3 Farben, „höchstens eine Farbe“ fehlt bewusst). Zufall: n Variablen, gerundet 4,26 n Klauseln. Der **Zufalls-Seed der Aufgabe** wählt Graph bzw. Formel; die **Löser-Zufalls-Seeds** (zufälliger Start der Aktivitäten, SplitMix64) streuen nur den Löser, nie die Aufgabe.
- **Messgröße.** Konflikte bis zur Antwort; ein Abbruch am Budget zählt mit dem Budget (untere Schranke). Median, P90 (Wert am 90-Prozent-Rang: sortierte Liste, Index min(Länge − 1, ⌊0,9 · Länge⌋)), Maximum.
- Mathematik, Symboltabelle und Quellen: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL (Kopie des Kern-Pakets) | `nst_cdcl.py` | Kern-Version 832b2c10dfdea62d; einzige inhaltliche Änderung: Option `restart_factor` (Standard 1,5 wie im Kern) |
| SplitMix64, Instanzerzeuger (Kopien) | `nst_rng.py`, `nst_instanzen.py` | Kern-Versionen im Modulkopf; Zufall nie über Pythons `random` oder `hash()` |
| Strategien, Läufe, Zeitleiste, Statistik | `nst_algorithm.py` | Grenzen und Zeitpunkte der Strategien, `ZeitleistenLoeser` (verwirft die Folgerungs-Ereignisse, damit die Spur nicht überläuft) |
| Aufgaben, Handbeispiel G | `nst_scenario.py` | Färbung („Rampen“), Zufall, die feste Messreihe |
| Verdikte, Auswertung der Messreihen | `nst_evaluation.py` | alle Verdikte als reine Funktionen |
| Messskript der vorgerechneten Reihen | `tools/messung_neustarts.py` | schreibt `nst_messung_vorgerechnet.json` (**vorgerechnet, nicht live**) |

Vier Reiter in der App: **Neustartzeitpunkte** (Einzellauf mit Zeitleiste; Handbeispiel Schritt für Schritt aus der Spur des Lösers), **Streuung gegen Median** (dieselbe Aufgabe, bis zu 30 Löser-Zufalls-Seeds, Kastendiagramm, live auf Knopfdruck mit Spinner), **Familienvergleich** (vorgerechnet), **Einheit und Faktor** (vorgerechnet). Presets (Schnellstart) und allgemeine Einstellungen stehen in der Seitenleiste, die experimentbezogenen Regler im Hauptbereich.

## Befunde und Korrekturen gegenüber dem Plan

- **Handbeispiel: Formel G statt Schubfach.** Die erste Fassung des Plans beschrieb einen Lauf am Schubfach mit 4 Tauben und 3 Löchern (12 Variablen, Neustarts nach den Konflikten 1, 2, 4, 5). Die Fassung 2 des Plans (2026-11-11) und `hb_04.py` nehmen die Formel G mit 6 Variablen; die Demo auch. Der Kern rechnet das Schubfach mit derselben Regel anders: 6 Konflikte, 5 gelernte Klauseln, ein einziger Neustart nach Konflikt 2, bei Einheit 1 und bei Einheit 2 (Test `test_schubfach_3_im_kern_hat_nur_einen_neustart_nach_konflikt_2`).
- **Tabelle „Neustart nach Konflikt Nr.“ ist der früheste Zeitpunkt, nicht der tatsächliche.** An G folgt bei Einheit 1 der Neustart nach den Konflikten 1 und 4 (die Tabelle nennt 1, 2, 4, 5, …), bei Einheit 2 nach Konflikt 4 (Tabelle: 2, 4, …). Der Neustart wartet, bis die Propagation ohne Konflikt endet und eine Entscheidung steht. Die Annahme des Plans, Einheit 1 erzeuge auf einer Aufgabe ohne Konflikt auf Stufe 0 genau die Tabellenwerte, gilt nur teilweise: Färbung n = 60 mit Zufalls-Seed 707 erreicht sie (1, 2, 4), mit Zufalls-Seed 702 liegen die Neustarts bei 2, 4, 7, 8 statt 1, 2, 4, 5, obwohl kein Konflikt auf Stufe 0 liegt (ein Folgekonflikt verschiebt den Neustart). Geprüft wird deshalb: jeder Neustart liegt auf oder nach dem Tabellenwert (Test `test_neustartabstaende_summieren_sich_zur_kumulativen_tabelle`).
- **Geometrische Grenzen: 506 und 759, nicht 505 und 757.** Der Plan nennt die Grenzen 100, 150, 225, 337, 505, 757; die kumulativen Zeitpunkte 100, 250, 475, 812, 1 318, 2 077 stimmen, und die Grenzen sind 100, 150, 225, 337, 506, 759, weil der Löser den Wert 337,5 ungerundet weiter mit 1,5 multipliziert und erst die Grenze abrundet (Test `test_geometrische_grenzen_und_zeitpunkte_von_hand`).
- **Zahlen der Vormessung reproduzieren sich nicht, die neue Messreihe ersetzt sie.** Die Vormessung nutzte Pythons `random`; die Aufgaben dieser Demo stammen aus SplitMix64 und sind andere Aufgaben. Vormessung: Färbung C5 287,5 → 65, Zufallsformel R2 1 087,5 → 1 661 (+53 %). Hier: Färbung hilft in 10 von 10 Aufgaben (Quotient der Mediane 0,22 bis 0,59), und **in 12 Zufallsformeln gibt es keine einzige Aufgabe oberhalb des Bandes ±20 %** (größter Quotient 1,12). Der „schadet“-Fall der Vormessung zeigt sich in dieser Reihe nicht; die Schwelle würde ihn melden (`tests/test_verdicts.py`).
- **Zufallsformeln: geometrisch liegt unter Luby.** Der Plan sagt, geometrisch liege auf beiden Familien zwischen „keine“ und Luby. Auf Färbung stimmt das (Median der Aufgaben-Mediane 294 / 147,5 / 108,25 für keine / geometrisch / Luby), auf Zufallsformeln nicht: 3 162,75 / 2 394,25 / 2 764,75.
- **Einheit und Faktor jetzt gemessen** (Reiter „Einheit und Faktor“): die Luby-Kurve ist auf Färbung **nicht** flach, auf Zufallsformeln flach (nach der Schwelle 1,2); die Faktor-Kurve ist in beiden Familien flach. Siehe Befunde.
- **Familie Zufallsformel in der Messreihe: n = 150 mit 12 Aufgaben** (die Planungsmessung nutzte n = 100 mit 10 Aufgaben; der Plan lässt „n 100 bis 150“ zu). n = 100 gibt es live im Preset „Zufallsformel“, nicht als vorgerechnete Reihe.
- **Schur als dritte Familie nicht in der App.** Die Probe (Befunde) zeigt, dass Schur Neustarts auslöst; es gibt aber je (n, k) nur eine Aufgabe, also keine Reihe von mindestens zehn Aufgaben. Die Probe steht in der README und im Test, nicht in der App.
- **Faktor-Regler** im Hauptbereich (Plan: Strategie, Einheit, Faktor); er gilt nur geometrisch und ist sonst gesperrt, nicht verborgen. **Kern-Option `restart_factor`** ergänzt (im Kern war der Faktor fest 1,5), mit dem Standard 1,5 rechnet die Kopie wie der Kern (`test_restart_faktor_standard_ist_der_wert_des_kerns`); der Kern-Hash im Modulkopf nennt den Stand vor dieser Änderung.
- **Budget 0 und 1** brechen beide nach dem ersten Konflikt ab (der Kern prüft das Budget nach einem Konflikt); eine Formel ohne Konflikt wird auch mit Budget 0 beantwortet.

## Befunde (gemessen, keine Behauptungen)

Die Messreihen stehen in `nst_messung_vorgerechnet.json` (Messskript `tools/messung_neustarts.py`, vorgerechnet, nicht live). Konflikte bis zur Antwort; „besser“ heißt Quotient Median(mit Neustarts) / Median(keine) unter 0,8, „neutral“ von 0,8 bis 1,2, „schlechter“ über 1,2 (Schwelle vor der Messung festgelegt); der Median wird je Aufgabe über die Löser-Zufalls-Seeds gebildet, dann die Aufgaben gezählt. Keine Zeitmessung, in keinem der 1 980 Läufe der Familienreihe ein Abbruch am Budget von 200 000. Jede Zeile gilt für die genannte Familie, Größe und Zahl der Aufgaben, nicht darüber hinaus.

| Frage | Befund | Test |
|---|---|---|
| **Aufbau der Messreihe** | 10 Färbungen (n = 160, Grad 4,5, 3 Rampen; 6 erfüllbar, 4 unerfüllbar) und 12 Zufallsformeln (n = 150, m = 639; 3 erfüllbar, 9 unerfüllbar), je 30 Löser-Zufalls-Seeds, 3 Strategien: 1 980 Läufe, 0 Abbrüche. | `test_claim_aufbau_der_messreihe` |
| **Stimmt die Datei mit dem heutigen Code überein?** | Färbung A1 und A3 (alle Strategien, 30 Seeds) und die ersten 5 Seeds von Zufallsformel A12 werden live neu gerechnet und sind gleich der Datei; die übrigen Zellen sind nicht live nachgerechnet. | `test_claim_messreihe_stimmt_mit_dem_heutigen_code_ueberein` |
| **Färbung: Luby (Einheit 32) gegen keine** | Besser bei **10 von 10** Aufgaben, neutral 0, schlechter 0; Quotient der Mediane Median 0,42, kleinster 0,22, größter 0,59; erfüllbare 6 von 6 besser, unerfüllbare 4 von 4 (Quotient Median 0,36 gegen 0,53, bei so wenigen Aufgaben keine Regel). | `test_claim_faerbung_luby_hilft_in_jeder_aufgabe`, `test_claim_faerbung_luby_nach_antwort` |
| **Färbung: Median und P90** | Median der Aufgaben-Mediane der Konflikte: keine 294, geometrisch 147,5, Luby 108,25; Median der Aufgaben-P90: 546 / 203,5 / 157,5. | `test_claim_faerbung_median_der_aufgaben_mediane_und_p90` |
| **Färbung: Tail (P90 und Maximum)** | Das P90 liegt mit Luby bei **10 von 10** Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,29), das Maximum über die 30 Seeds ebenfalls bei 10 von 10. | `test_claim_faerbung_tail_p90_und_maximum` |
| **Färbung: geometrisch (100, ×1,5)** | Besser 7, neutral 3 (Aufgaben 1, 3, 5), schlechter 0; Quotient Median 0,61, kleinster 0,43, größter 1,00; P90 bei 10 von 10 Aufgaben kleiner (Median 0,44); Luby hat bei 10 von 10 Aufgaben den kleineren Median als geometrisch. | `test_claim_faerbung_geometrisch` |
| **Zufallsformel: Luby gegen keine** | Besser bei **5 von 12**, neutral bei 7, schlechter bei 0; Quotient Median 0,86, kleinster 0,75, größter 1,12 (Aufgabe 10, erfüllbar); erfüllbar 1 von 3 besser, unerfüllbar 4 von 9. Der Median sinkt dabei bei 11 von 12 Aufgaben (nur Aufgabe 10 liegt darüber); „besser“ gegen „neutral“ hängt an der Schwelle 0,8, denn die fünfte Aufgabe mit „besser“ liegt knapp darunter (Nachrechnung über die 30 Löser-Zufalls-Seeds, nicht Teil der Tests: die Zählung schwankt zwischen 1 und 8). | `test_claim_zufall_luby_zaehlung_je_aufgabe` |
| **Zufallsformel: Median und P90** | Median der Aufgaben-Mediane: keine 3 162,75, geometrisch 2 394,25, Luby 2 764,75; Median der Aufgaben-P90: 4 154 / 2 935 / 3 357,5. | `test_claim_zufall_median_der_aufgaben_mediane_und_p90` |
| **Zufallsformel: Tail** | Das P90 liegt mit Luby bei 11 von 12 Aufgaben unter dem ohne Neustarts (Quotient der P90: Median 0,76; die Ausnahme ist Aufgabe 10 mit 1,21), das Maximum bei 12 von 12. | `test_claim_zufall_tail_p90_und_maximum` |
| **Zufallsformel: geometrisch** | Besser bei 9 von 12, neutral bei 3, schlechter bei 0; Quotient Median 0,78, kleinster 0,72, größter 0,84; P90 bei 12 von 12 kleiner (Median 0,70). | `test_claim_zufall_geometrisch` |
| **Fall „schadet“** | In keiner der 22 Aufgaben liegt Luby oder geometrisch außerhalb des Bandes nach oben (größter Quotient 1,12). Die +53 % der Vormessung (R2) reproduzieren sich an diesen Aufgaben nicht. Bei Aufgabe 10 reicht das Streuungsintervall der 30 Löser-Zufalls-Seeds für Luby bis etwa 1,6 (Nachrechnung, nicht Teil der Tests). | `test_claim_kein_schadet_fall_der_vormessung_reproduziert_sich_nicht` |
| **Verdikt der Kernfrage** | Der Text über den Reitern nennt genau diese Zählungen (Färbung 10 / 0 / 0 von 10, Zufallsformel 5 / 7 / 0 von 12). | `test_claim_kernfrage_verdikt_nennt_die_zaehlungen` |
| **Luby-Einheit, Färbung** (10 Aufgaben × 10 Seeds, Median der Quotienten) | Einheit 4 / 8 / 16 / 32 / 64 / 128 / 256: 0,32 / 0,30 / 0,37 / 0,38 / 0,48 / 0,64 / 0,91; „hilft“ bei 10 / 10 / 10 / 10 / 9 / 7 / 3 Aufgaben. Die Kurve ist **nicht flach** (größter durch kleinsten 3,09 > 1,2). | `test_claim_kurve_faerbung_luby_einheit` |
| **Geometrischer Faktor, Färbung** | Faktor 1,1 / 1,3 / 1,5 / 2: 0,58 / 0,59 / 0,59 / 0,58, jedes Mal „hilft“ bei 7 von 10: flach (1,02). | `test_claim_kurve_faerbung_faktor` |
| **Zufallsformel: Einheit und Faktor** (12 Aufgaben × 10 Seeds) | Luby-Einheit 4 bis 256: 0,89 / 0,86 / 0,87 / 0,85 / 0,81 / 0,80 / 0,79 (flach, 1,12); Faktor 1,1 / 1,3 / 1,5 / 2: 0,78 / 0,77 / 0,79 / 0,76 (flach, 1,04). Je Aufgabe reichen die Quotienten der Luby-Kurve von 0,35 bis 1,32; „flach“ gilt nur für den Median über die Aufgaben. | `test_claim_kurve_zufall` |
| **Kurven: Läufe und Abbrüche** | 22 Aufgaben × 12 Einstellungen × 10 Seeds, 0 Abbrüche; Färbung A1 mit Einheit 4 und 256 und Faktor 2 wird live nachgerechnet und ist gleich der Datei. | `test_claim_kurven_messung_ohne_abbrueche`, `test_claim_kurve_stimmt_mit_dem_heutigen_code_ueberein` |
| **Handbeispiel G** | 6 Konflikte, 5 gelernte Klauseln, Neustarts bei Einheit 1 / 2 / 32: nach den Konflikten 1 und 4 / nach 4 / keiner; die fünf gelernten Klauseln sind jeweils per Einheitspropagation aus den vorigen herleitbar. Geometrisch (100, ×1,5): Grenzen 100, 150, 225, 337, 506, 759. | `test_claim_handbeispiel_g_und_geometrische_grenzen`, `test_handbeispiel_*` (`tests/test_algorithm.py`) |
| **Schur-Probe** (nicht in der App) | Schur n = 40, k = 4 (erfüllbar, eine deterministische Aufgabe, Löser-Zufalls-Seeds 0 bis 4, Budget 20 000): ohne Neustarts 330 / 535 / 2 065 / 7 050 / 14 500 Konflikte, Luby (Einheit 32) 75 / 103 / 109 / 141 / 679 (beide Reihen aufsteigend sortiert, nicht in der Reihenfolge der Seeds); Median 2 065 gegen 109, 3 Neustarts im Lauf mit Seed 0. Eine Aufgabe, eine Größe: keine Aussage über Schur im Allgemeinen. | `test_claim_schur_probe_k4_n40` |
| **Budget 0 und 1** | Beide stoppen nach genau einem Konflikt. | `test_claim_budget_0_und_1_stoppen_nach_dem_ersten_konflikt` |

Zahl-zu-Test: jede Zahl der Tabelle steht in dem genannten Test (exakt für Zählungen, auf zwei Stellen gerundet für Quotienten). Alle Aussagen gelten für diesen Löser (CDCL mit Aktivität, Phasenspeicher, ohne Löschen), diese Aufgabenfamilien und Größen, Einheit 32 und die erste Grenze 100.

## Ehrliche Grenzen

- **Zwei Familien, je 10 und 12 Aufgaben.** Die Zählungen gelten für diese Familien und Größen (Färbung n = 160, Zufallsformel n = 150, 4,26 Klauseln je Variable). „Strukturiert gegen Zufall“ ist hier eine Familie (Färbung) gegen eine zweite (Zufalls-3-SAT), nicht „Struktur im Allgemeinen“. Industrielle Formeln und andere Größen sind nicht gemessen; die Schur-Probe ist eine Aufgabe.
- **Die Löser-Zufalls-Seeds streuen nur den Start der Aktivitäten**, nicht die Aufgabe. Median und P90 im Reiter „Streuung gegen Median“ gelten für die eine Aufgabe; die Streuung über Aufgaben zeigt der Familienvergleich. Wie wenig eine Aufgabe mit wenigen Seeds sagt, zeigt das Preset „Zufallsformel“ (n = 100, Zufalls-Seed der Aufgabe 500): mit 10 Löser-Zufalls-Seeds steigt der Median von 94,5 auf 158 (+67 %, außerhalb des Bandes), mit 30 Seeds sinkt er von 93,5 auf 72 (Test `test_claim_streuung_einzelaufgabe_haengt_an_der_seedzahl`).
- **„Neutral“ ist eine Zählung je Aufgabe mit der Schwelle ±20 %**, keine Aussage über Zufallsformeln allgemein.
- **Die Kurven über Einheit und Faktor haben je Aufgabe nur 10 Löser-Zufalls-Seeds.** Der Median je Aufgabe schwankt bei so wenigen Läufen, besonders auf Zufallsformeln (je Aufgabe 0,35 bis 1,32 in der Luby-Kurve). „Flach“ heißt: der Median der Quotienten über die Aufgaben schwankt höchstens um das 1,2-Fache; es heißt nicht, dass jede Aufgabe die Einheit nicht spürt. Die beste Einheit der Messung (Färbung: 8) wird nicht als allgemein gültig bezeichnet. Die geometrische Kurve hat eine feste erste Grenze von 100; auf Färbungen mit wenigen hundert Konflikten greift der Faktor erst nach den ersten Neustarts (Deutung, nicht gemessen), die flache Faktor-Kurve ist daher kein Beleg, dass die geometrische Strategie unempfindlich wäre.
- **Der Neustart des Kerns wartet auf eine stehende Entscheidung** (Schuld bleibt bestehen). Würde ein Neustart auch auf Stufe 0 zählen, änderten sich die Neustartzahlen; die Demo misst die Fassung des Kerns.
- **Zählgrößen, keine Zeit.** Konflikte sind nicht gleich teuer; die Demo sagt nichts über die Laufzeit. Die Rechenzeit wird in der App nach dem Lauf angezeigt, ist aber nie ein Befund.
- **Der Löser ist ein lesbarer Python-CDCL** für kleine Aufgaben, kein Wettbewerbslöser; Rephasing, Wechsel stabil/fokussiert, adaptive Neustarts nach Glucose-Art und Teil-Neustarts sind nicht Teil der Demo.
- **Quellen.** Luby, Sinclair und Zuckerman (1993) behandeln Las-Vegas-Algorithmen allgemein, nicht SAT; die Übertragung auf CDCL-Löser nennt das Glucose-Papier (Audemard und Simon 2009: MiniSat mit Luby-Neustarts, Start 32, als Grundlage). Das Papier, das das dort zitiert, wurde nicht gelesen; Jahresangaben zur Geschichte der Neustarts stehen deshalb nicht in der Demo. Chaff (Moskewicz u. a. 2001) vermerkt selbst, dass sich ähnliche Ergebnisse oft oder zumindest manchmal auch ohne Neustarts erzielen lassen; das passt zum Befund auf Zufallsformeln (5 von 12 Aufgaben besser, 7 neutral), belegt ihn aber nicht.
- **Vorgerechnet, nicht live:** Familienvergleich und Kurven stammen aus `nst_messung_vorgerechnet.json`; live gerechnet werden Handbeispiel, Zeitleiste und der Reiter „Streuung gegen Median“.

## Verifikation

- **Handbeispiel von Hand gerechnet:** Luby-Folge 1 bis 15, Tabelle „Neustart nach Konflikt Nr.“ (Einheit 1, 2, 32; geometrisch), Lauf an G mit Einheit 1, 2, 32 (Konflikte, gelernte Klauseln, Rücksprungstufen, Neustarts), `tests/test_algorithm.py`; Sollwerte aus `hb_04.py` der Planung.
- **Orakel** (`tests/test_oracle_neustarts_sat.py`, anderer Rechenweg): Luby-Folge gegen **Reluctant Doubling** und gegen die **rekursive Definition der Veröffentlichung** (200 Glieder), geometrische Grenzen gegen **exakte Bruchrechnung**; Antwort jeder Strategie gegen **Brute Force** (60 Formeln mit 10 Variablen, beide Antworten vertreten) und gegen **OR-Tools CP-SAT** (14 Zufallsformeln, 10 Färbungen, nur Test-venv), jedes Modell gegen jede Klausel geprüft; Neustartzeitpunkte aus der Spur gegen die Konfliktzähler (Abstände mindestens so groß wie die Grenzen, Summe der Abstände gleich der Konfliktzahl); jede gelernte Klausel per **RUP-Prüfer** (eigene Schleife in `conftest.py`) aus den vorigen herleitbar. Ein größerer Scratch-Lauf (nicht Teil des Repos) rechnete 240 Formeln (Zufalls-3-SAT mit 30 bis 60 Variablen und Färbungen mit 30 bis 62 Aufträgen; 127 erfüllbar) mit fünf Einstellungen (keine, Luby 1 und 32, geometrisch 3 und 100), 1 200 Läufe mit zusammen 3 372 Neustarts: 0 Abweichungen von CP-SAT, jedes Modell gegen jede Klausel geprüft. Im Repo steht die kleine Fassung.
- **Eigenschaften und Zweig-Tests** (`tests/test_properties.py`): die Antwort hängt nicht von der Strategie ab; ohne Neustarts keine Neustart-Ereignisse; nach jedem Neustart folgt „Sprung auf Stufe 0“, die Zahl der gelernten Klauseln wird nicht kleiner; derselbe Zufalls-Seed gibt dieselbe Konfliktzahl; jede Strategie und jede Einstellung der Kurven weicht in der Messreihe von ihrer Nachbarin ab (Luby gegen keine, geometrisch gegen Luby und keine: in jeder der 22 Aufgaben); keine Nullspalte.
- **Randfälle** (`tests/test_edge_cases.py`): Formel ohne Konflikt (nie ein Neustart), Konflikt vor der ersten Entscheidung, Konflikt auf Stufe 0, n = 1, Einheit 1, Budget 0 und 1, ein einziger Lauf, Quotient bei null Konflikten.
- **Kern-Kopien** (`tests/test_kern_kopie.py`): Regressionswerte der kopierten Module (SplitMix64, Instanzerzeuger, Luby, Propagation, 1-UIP, Rücksprung, Budget, Schubfach 7 / 28 / 159 Konflikte); `restart_factor` mit dem Standard 1,5 gleich dem Kern.
- **Verdikte** (`tests/test_verdicts.py`): jede Schwelle (Quotient 0,79 / 0,8 / 1,2 / 1,21; Kurve flach bei 1,2) und jede genannte Zahl an handgesetzten Zeilen, auch ein R2-artiger „schadet“-Fall.
- **Claims** (`tests/test_claims.py`): jede Zahl der Tabelle „Befunde“; Zahl-zu-Test steht in der Tabelle.
- **Presets, Layout, Oberfläche:** `tests/test_presets.py`, `tests/test_layout.py` (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben, jede Regleränderung hebt die Markierung auf; gesperrte statt verborgene Regler), `tests/test_app.py` (AppTest-Smoke), `tests/test_app_inhalt.py` (Verdikte je Preset, Expander nach Titel, Mathe-Blöcke), Footer, Laufzeit-Importe.
- **Zufall:** nur SplitMix64; der Quelltext enthält weder `import random` noch Aufrufe von `hash()` (`tests/test_rng_scenario.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `nst_cdcl.py` | CDCL-Löser (Kopie des Kern-Pakets, Kern-Version im Kopf) |
| `nst_rng.py` | SplitMix64 (Kopie des Kern-Pakets) |
| `nst_instanzen.py` | Instanzerzeuger (Kopie des Kern-Pakets): Zufalls-3-SAT, Färbung, Rampen, Schubfach, Schur |
| `nst_algorithm.py` | Neustart-Strategien, Läufe, Zeitleiste, Statistik |
| `nst_scenario.py` | Handbeispiel G, Aufgaben, die feste Messreihe |
| `nst_constants.py` | Regler-Grenzen, Schwellen der Verdikte, Aufgabenlisten, Farben, Presets |
| `nst_evaluation.py` | Verdikte (reine Funktionen), Auswertung der vorgerechneten Messreihen |
| `nst_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `nst_layout.py` | Fester Kopf (Stylesheet) |
| `nst_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Knopf |
| `nst_messung_vorgerechnet.json` | vorgerechnete Messreihen (Messung dieses Repos) |
| `tools/messung_neustarts.py` | Messskript der Reihen |
| `requirements.txt` | Laufzeit-Bibliotheken: streamlit, pandas, plotly (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe in den Tests) |
| `tests/` | Kern-Kopien, Handbeispiel, Orakel, Eigenschaften, Zweig-Tests, Randfälle, Claims, Verdikte, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Rephasing, Wechsel stabil/fokussiert, adaptive Neustarts nach Glucose-Art** (gleitender LBD-Mittelwert), **Neustarts mit teilweiser Wiederverwendung des Stapels**: nicht gemessen, nicht erklärt.
- **Löschen gelernter Klauseln** (Stück „klauseln-loeschen-demo“): hier bleiben alle erhalten.
- **Schur und Schubfach als Aufgabenfamilie** in der App (nur die Schur-Probe in der README), **industrielle Formeln**, **Zeitmessungen**, **Jahresangaben zur Geschichte der Neustarts** und die Aussage „alle modernen Löser nutzen Neustarts“ (keine gelesene Quelle).
- **Messreihe auf Knopfdruck** für den Familienvergleich: die Reihe ist vorgerechnet; nur der Reiter „Streuung gegen Median“ rechnet live.
- **PDF-Export** (der Plan nennt keinen).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
