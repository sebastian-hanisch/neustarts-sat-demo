"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import nst_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_zeitleiste(zl, grenz_zeitpunkte=()):
    """Zeitleiste der Konflikte: je Konflikt die Entscheidungsstufe, auf der er auftrat (Linie) und die Stufe, auf die zurückgesprungen wurde (Punkte);
    jeder Neustart ist eine rote senkrechte Marke mit der Stufe davor. Graue Dreiecke unten: Konfliktzahl, bei der die Grenze der Strategie erreicht ist."""
    k = len(zl.konflikt_stufe)
    xs = list(range(1, k + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=zl.konflikt_stufe, mode="lines+markers", name="Stufe des Konflikts", line=dict(color=C.COLOR_LINE, width=1.5),
                             marker=dict(size=5), hovertemplate="Konflikt %{x}: Stufe %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=zl.lernstufe, mode="markers", name="Rücksprungstufe", marker=dict(size=5, symbol="circle-open", color=C.COLOR_LUBY),
                             hovertemplate="nach Konflikt %{x}: zurück auf Stufe %{y}<extra></extra>"))
    hoch = max(zl.konflikt_stufe + [1])
    for konflikte, stufe, _, _ in zl.neustarts:
        fig.add_shape(type="line", x0=konflikte + 0.5, x1=konflikte + 0.5, y0=0, y1=hoch + 1, line=dict(color=C.COLOR_NEUSTART, width=2, dash="solid"))
    if zl.neustarts:
        fig.add_trace(go.Scatter(x=[n[0] + 0.5 for n in zl.neustarts], y=[hoch + 1] * len(zl.neustarts), mode="markers", name="Neustart (davor: Stufe)",
                                 marker=dict(size=9, color=C.COLOR_NEUSTART, symbol="x"), customdata=[n[1] for n in zl.neustarts],
                                 hovertemplate="Neustart nach Konflikt %{x:.0f}: Stufe davor %{customdata}<extra></extra>"))
    sicht = [g for g in grenz_zeitpunkte if g <= k]
    if sicht:
        fig.add_trace(go.Scatter(x=sicht, y=[0] * len(sicht), mode="markers", name="Grenze der Strategie erreicht", marker=dict(size=8, color="#888", symbol="triangle-up"),
                                 hovertemplate="Grenze erreicht nach %{x} Konflikten<extra></extra>"))
    fig.update_xaxes(title_text="Konflikt Nr.", range=[0, max(k, 1) + 1])
    fig.update_yaxes(title_text="Entscheidungsstufe", range=[-0.5, hoch + 1.8])
    return _base(fig, 380)


def build_box(konflikte_je_strategie: dict, abbrueche: dict | None = None):
    """Kastendiagramm der Konflikte über die Löser-Zufalls-Seeds, eine Spur je Strategie, alle Punkte sichtbar."""
    fig = go.Figure()
    for s, werte in konflikte_je_strategie.items():
        fig.add_trace(go.Box(y=werte, name=C.STRATEGIE_NAMEN[s], boxpoints="all", jitter=0.4, pointpos=0, marker=dict(color=C.STRATEGIE_FARBEN[s], size=5),
                             line=dict(color=C.STRATEGIE_FARBEN[s]), boxmean=False, hovertemplate="%{y} Konflikte<extra></extra>"))
    fig.update_yaxes(title_text="Konflikte bis zur Antwort", rangemode="tozero")
    fig.update_layout(showlegend=False)
    return _base(fig, 380)


def build_quotienten(zeilen: list, familie_kurz: str):
    """Je Aufgabe der Messreihe der Quotient Median(mit Neustarts) / Median(keine) für Luby und geometrisch; das Band 0,8 bis 1,2 ist „neutral“."""
    fig = go.Figure()
    xs = [f"A{z['index'] + 1}" for z in zeilen]
    for s, name in ((C.STRATEGIE_LUBY, "Luby (Einheit 32)"), (C.STRATEGIE_GEO, "geometrisch (100, ×1,5)")):
        fig.add_trace(go.Bar(x=xs, y=[z["q_" + s] for z in zeilen], name=name, marker_color=C.STRATEGIE_FARBEN[s],
                             hovertemplate="%{x}: Quotient %{y:.2f}<extra></extra>"))
    fig.add_hrect(y0=1 - C.NEUTRAL_BAND, y1=1 + C.NEUTRAL_BAND, fillcolor="rgba(128,128,128,0.18)", line_width=0)
    fig.add_hline(y=1.0, line_dash="dot", line_color="gray")
    fig.update_xaxes(title_text=f"Aufgabe der Reihe ({familie_kurz})", type="category")
    fig.update_yaxes(title_text="Median mit / Median ohne Neustarts", rangemode="tozero")
    fig.update_layout(barmode="group")
    return _base(fig, 340)


def build_kurve(zeilen: list, art: str, familie_kurz: str):
    """Kurve des Median-Quotienten über die Einstellung (Luby-Einheit oder geometrischer Faktor); Fehlerbalken: kleinster und größter Quotient über die Aufgaben."""
    kurve = [z for z in zeilen if z["name"].startswith(art + ":")]
    xs = [z["name"].split(":")[1] for z in kurve]
    meds = [z["median"] for z in kurve]
    fig = go.Figure()
    fig.add_hrect(y0=1 - C.NEUTRAL_BAND, y1=1 + C.NEUTRAL_BAND, fillcolor="rgba(128,128,128,0.18)", line_width=0)
    fig.add_hline(y=1.0, line_dash="dot", line_color="gray")
    farbe = C.COLOR_LUBY if art == "luby" else C.COLOR_GEO
    fig.add_trace(go.Scatter(x=xs, y=meds, mode="lines+markers", name=f"Median über die Aufgaben ({familie_kurz})", line=dict(color=farbe, width=2), marker=dict(size=8),
                             error_y=dict(type="data", symmetric=False, array=[z["max"] - z["median"] for z in kurve], arrayminus=[z["median"] - z["min"] for z in kurve], color=farbe),
                             hovertemplate="%{x}: Median-Quotient %{y:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Luby-Einheit" if art == "luby" else "geometrischer Faktor (erste Grenze 100)", type="category")
    fig.update_yaxes(title_text="Median mit / Median ohne Neustarts", rangemode="tozero")
    return _base(fig, 340)
