"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import nst_constants as C
import nst_presets as P


def test_jedes_preset_hat_einen_hilfetext_und_nur_bekannte_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]
    assert list(C.PRESETS) == ["Handbeispiel", "Rampen-Färbung", "Zufallsformel", "Streuung groß"]


def test_preset_werte_liegen_in_den_reglergrenzen():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.options is not None:
                assert wert in spec.options, (name, key)
            else:
                assert spec.lo <= wert <= spec.hi, (name, key)


def test_standard_preset_entspricht_den_standardeinstellungen():
    """Das erste Preset (Handbeispiel) nennt nur Werte, die den Standardwerten der Regler gleichen: beim Start ist es hervorgehoben."""
    for key, wert in C.PRESETS["Handbeispiel"].items():
        assert wert == P.SETTING_SPECS[P.PRESET_KEYS[key]].default, key


def test_presets_unterscheiden_sich_paarweise_in_mindestens_einem_regler():
    def voll(preset):
        return {sk: preset.get(k, P.SETTING_SPECS[sk].default) for k, sk in P.PRESET_KEYS.items()}
    namen = list(C.PRESETS)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            assert voll(C.PRESETS[a]) != voll(C.PRESETS[b]), (a, b)


def test_setting_specs_decken_jeden_preset_schluessel():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_preset_namen_beschreiben_die_werte():
    """Vertauschte Beschriftungen: „Rampen-Färbung“ setzt die Färbung mit n = 160, „Zufallsformel“ Zufalls-3-SAT mit n = 100, „Streuung groß“ dieselbe Färbung mit 30 statt 10 Seeds, „Handbeispiel“ Einheit 1."""
    assert C.PRESETS["Rampen-Färbung"]["familie"] == C.FAMILIE_FAERBUNG and C.PRESETS["Rampen-Färbung"]["n"] == C.N_MAX == 160 and C.PRESETS["Rampen-Färbung"]["seeds"] == 10
    assert C.PRESETS["Zufallsformel"]["familie"] == C.FAMILIE_ZUFALL and C.PRESETS["Zufallsformel"]["n"] == 100
    assert C.PRESETS["Streuung groß"]["familie"] == C.FAMILIE_FAERBUNG and C.PRESETS["Streuung groß"]["n"] == 160 and C.PRESETS["Streuung groß"]["seeds"] == 30 == C.SEEDS_MAX
    assert C.PRESETS["Handbeispiel"]["aufgabe"] == C.AUFGABE_HAND and C.PRESETS["Handbeispiel"]["einheit"] == 1


def test_permalink_bereinigung_begrenzt_und_verwirft_unbekanntes():
    n = P.SETTING_SPECS["n_slider"]
    assert P._bereinige(n, 5) == C.N_MIN and P._bereinige(n, 10 ** 6) == C.N_MAX and P._bereinige(n, 90) == 90
    b = P.SETTING_SPECS["budget_slider"]
    assert P._bereinige(b, 5000) == 5000 and P._bereinige(b, 7) is None
    f = P.SETTING_SPECS["familie_select"]
    assert P._bereinige(f, "Unsinn") is None and P._bereinige(f, C.FAMILIE_ZUFALL) == C.FAMILIE_ZUFALL
