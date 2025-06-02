import streamlit as st
import math
import json # Importieren des json-Moduls

# Globale Variable für geladene Kursdaten
COURSE_DATA = None

def load_course_data():
    """Lädt die Kursdaten aus der JSON-Datei."""
    global COURSE_DATA
    if COURSE_DATA is None:
        try:
            with open("course_data.json", "r", encoding="utf-8") as f:
                COURSE_DATA = json.load(f)
        except FileNotFoundError:
            st.error("Fehler: course_data.json nicht gefunden. Bitte stellen Sie sicher, dass die Datei im Projektordner liegt und in index.html korrekt referenziert ist.")
            COURSE_DATA = {} # Leeres Dict, um weitere Fehler zu vermeiden
        except json.JSONDecodeError:
            st.error("Fehler: course_data.json enthält ungültiges JSON.")
            COURSE_DATA = {}
    return COURSE_DATA

def urs_round(n):
    return round(n)

st.set_page_config(page_title="Golf-Vorgabe-Rechner", layout="wide")

st.title("Golf-Vorgabe-Rechner ⛳")
# Das Laden hier stellt sicher, dass der Clubname im Titel verfügbar ist, wenn benötigt.
# Und dass die Fehlerbehandlung frühzeitig stattfindet.
club_data_for_title = load_course_data() 
club_name_for_title = club_data_for_title.get('golfclub', 'Clubdaten nicht geladen')

st.caption(f"URS V1.0. Daten für Einzelmatchplay: {club_name_for_title}")


# --- Input Validation Ranges ---
HCPI_MIN, HCPI_MAX = -5.0, 54.0
SLOPE_MIN, SLOPE_MAX = 55, 155
CR_MIN, CR_MAX = 55.0, 85.0 
PAR_MIN, PAR_MAX = 60, 78

# --- Tabs ---
# Nur noch Einzel-Matchplay und Vierer-Matchplay
tab_single_match, tab_foursome_match = st.tabs([
    "Einzel-Matchplay (FA-02)",
    "Vierer-Matchplay (FA-03)"
])

# --- FA-02: Berechnung der Vorgabe im Einzel-Matchplay ---
# (Code aus der Antwort vom [Mon Jun 2 17:10:02 2025], leicht angepasst für globale course_data_loaded)
with tab_single_match:
    st.header("FA-02: Einzel-Matchplay Vorgabe")

    # course_data_loaded wird jetzt am Anfang der App geladen und hier verwendet
    # Die Variable club_name wurde bereits oben als club_name_for_title initialisiert
    st.info(f"Daten für: {club_name_for_title}. Pro Spieler wird Geschlecht und ein Abschlag gewählt. Daraus werden die Vorgaben für 18-Loch und 9-Loch Runden ermittelt.")

    if not club_data_for_title or "courseHandicaps" not in club_data_for_title:
        st.error("Clubdaten konnten nicht geladen werden. Matchplay-Berechnung mit Clubdaten nicht möglich.")
    else:
        name_col1, name_col2 = st.columns(2)
        player1_name = name_col1.text_input("Name Spieler 1:", "Spieler 1", key="p1_name_v2_main") # Keys angepasst
        player2_name = name_col2.text_input("Name Spieler 2:", "Spieler 2", key="p2_name_v2_main") # Keys angepasst
        st.markdown("---")

        col_p1, col_p2 = st.columns(2)

        player1_results = {"ch_18": None, "ch_9": None}
        player2_results = {"ch_18": None, "ch_9": None}

        # Helper function to get CH and details for single player (innerhalb des Tabs, um Kapselung zu wahren oder global definieren)
        # Diese Funktion ist die Version aus der Einzel-Matchplay-Anpassung
        def get_player_handicaps_single(player_label_prefix, sex, hcpi, selected_tee_color):
            results = {"ch_18": None, "ch_9": None, "desc_18": "", "desc_9": ""}
            
            # 18-Loch Logik
            course_info_18 = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex and "18-Loch" in c["holes"]), None)
            if course_info_18 and selected_tee_color in course_info_18["tees"]:
                tee_data_18 = course_info_18["tees"][selected_tee_color]
                results["desc_18"] = f"18-Loch ({course_info_18['holes']}), Abschlag {selected_tee_color.capitalize()}: SR {tee_data_18['SR']}, CR {tee_data_18['CR']:.1f}, Par {tee_data_18['Par']}"
                ch18 = None
                if "handicapRanges" in tee_data_18:
                    for r in tee_data_18["handicapRanges"]:
                        if r["HCPI_min"] <= hcpi <= r["HCPI_max"]: ch18 = r["CourseHCP"]; break
                if ch18 is None: ch18 = urs_round(hcpi * (tee_data_18['SR'] / 113) + (tee_data_18['CR'] - tee_data_18['Par']))
                results["ch_18"] = ch18
            else: results["desc_18"] = f"Keine 18-Loch Daten für {sex}, Abschlag {selected_tee_color.capitalize()} gefunden."

            # 9-Loch Logik
            course_info_9 = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex and "9-Loch" in c["holes"]), None)
            if course_info_9 and selected_tee_color in course_info_9["tees"]:
                tee_data_9 = course_info_9["tees"][selected_tee_color]
                results["desc_9"] = f"9-Loch ({course_info_9['holes']}), Abschlag {selected_tee_color.capitalize()}: SR {tee_data_9['SR']}, CR {tee_data_9['CR']:.1f}, Par {tee_data_9['Par']}"
                results["ch_9"] = urs_round((hcpi / 2.0) * (tee_data_9['SR'] / 113) + (tee_data_9['CR'] - tee_data_9['Par']))
                ch9_table = None
                if "handicapRanges" in tee_data_9:
                    for r in tee_data_9["handicapRanges"]:
                        if r["HCPI_min"] <= hcpi <= r["HCPI_max"]: ch9_table = r["CourseHCP"]; break
                if ch9_table is not None: results["desc_9"] += f" (CH Tabelle: {ch9_table})"
            else: results["desc_9"] = f"Keine 9-Loch Daten für {sex}, Abschlag {selected_tee_color.capitalize()} gefunden."
            return results

        # --- Spieler 1 ---
        with col_p1:
            st.subheader(player1_name)
            sex_p1 = st.radio(f"Geschlecht {player1_name}:", ("Herren", "Damen"), key="sex_p1_v2_main", horizontal=True) # Key angepasst
            
            tees_18_p1 = []
            course_info_18_p1_s = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_p1 and "18-Loch" in c["holes"]), None) # s für single
            if course_info_18_p1_s: tees_18_p1 = list(course_info_18_p1_s["tees"].keys())
            
            tees_9_p1 = []
            course_info_9_p1_s = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_p1 and "9-Loch" in c["holes"]), None)
            if course_info_9_p1_s: tees_9_p1 = list(course_info_9_p1_s["tees"].keys())
            
            common_tees_p1 = sorted(list(set(tees_18_p1) & set(tees_9_p1)))

            if not common_tees_p1:
                st.warning(f"Keine gemeinsamen Abschläge für 18- und 9-Loch für {sex_p1} gefunden.")
            else:
                default_tee_p1 = "gelb" if sex_p1 == "Herren" else "rot"
                default_tee_p1_idx = common_tees_p1.index(default_tee_p1) if default_tee_p1 in common_tees_p1 else 0
                selected_tee_p1 = st.selectbox(f"Abschlag {player1_name}:", common_tees_p1, index=default_tee_p1_idx, key="tee_p1_v2_main") # Key angepasst
                
                hcpi_p1 = st.number_input(f"HCPI {player1_name}:",
                                          min_value=HCPI_MIN, max_value=HCPI_MAX, value=10.0, step=0.1, format="%.1f", key="hcpi_p1_match_v2_main") # Key angepasst

                p1_data = get_player_handicaps_single("p1", sex_p1, hcpi_p1, selected_tee_p1)
                player1_results["ch_18"] = p1_data["ch_18"]
                player1_results["ch_9"] = p1_data["ch_9"]
                
                if p1_data["ch_18"] is not None:
                    st.metric(label="Course HCP 18-Loch", value=p1_data["ch_18"])
                    st.caption(p1_data["desc_18"])
                if p1_data["ch_9"] is not None:
                    st.metric(label="Course HCP 9-Loch (Formel)", value=p1_data["ch_9"])
                    st.caption(p1_data["desc_9"])

        # --- Spieler 2 ---
        with col_p2:
            st.subheader(player2_name)
            sex_p2 = st.radio(f"Geschlecht {player2_name}:", ("Herren", "Damen"), key="sex_p2_v2_main", horizontal=True) # Key angepasst

            tees_18_p2 = []
            course_info_18_p2_s = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_p2 and "18-Loch" in c["holes"]), None)
            if course_info_18_p2_s: tees_18_p2 = list(course_info_18_p2_s["tees"].keys())
            
            tees_9_p2 = []
            course_info_9_p2_s = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_p2 and "9-Loch" in c["holes"]), None)
            if course_info_9_p2_s: tees_9_p2 = list(course_info_9_p2_s["tees"].keys())

            common_tees_p2 = sorted(list(set(tees_18_p2) & set(tees_9_p2)))

            if not common_tees_p2:
                st.warning(f"Keine gemeinsamen Abschläge für 18- und 9-Loch für {sex_p2} gefunden.")
            else:
                default_tee_p2 = "gelb" if sex_p2 == "Herren" else "rot"
                default_tee_p2_idx = common_tees_p2.index(default_tee_p2) if default_tee_p2 in common_tees_p2 else 0
                selected_tee_p2 = st.selectbox(f"Abschlag {player2_name}:", common_tees_p2, index=default_tee_p2_idx, key="tee_p2_v2_main") # Key angepasst

                hcpi_p2 = st.number_input(f"HCPI {player2_name}:",
                                          min_value=HCPI_MIN, max_value=HCPI_MAX, value=20.5, step=0.1, format="%.1f", key="hcpi_p2_match_v2_main") # Key angepasst

                p2_data = get_player_handicaps_single("p2", sex_p2, hcpi_p2, selected_tee_p2)
                player2_results["ch_18"] = p2_data["ch_18"]
                player2_results["ch_9"] = p2_data["ch_9"]

                if p2_data["ch_18"] is not None:
                    st.metric(label="Course HCP 18-Loch", value=p2_data["ch_18"])
                    st.caption(p2_data["desc_18"])
                if p2_data["ch_9"] is not None:
                    st.metric(label="Course HCP 9-Loch (Formel)", value=p2_data["ch_9"])
                    st.caption(p2_data["desc_9"])
        
        st.markdown("---")
        st.subheader("Ergebnis Matchplay-Vorgabe (Formel: |CH₁ - CH₂| * 2/3)")
        
        def display_matchplay_calculation(ch_p1, ch_p2, p1_name, p2_name, round_type_label): # Definition hier, falls nicht global
            if ch_p1 is not None and ch_p2 is not None:
                abs_diff = abs(ch_p1 - ch_p2); intermediate_result = abs_diff * (2/3); final_vorgabe = urs_round(intermediate_result)
                st.markdown(f"**Für eine {round_type_label}-Runde:**")
                with st.expander("Berechnungsschritte anzeigen"):
                    st.markdown(f"Formel: `|CH {p1_name} - CH {p2_name}| * (2/3)`")
                    st.markdown(f"Einsetzen: `|{ch_p1} - {ch_p2}| * (2/3)` `= |{ch_p1 - ch_p2}| * (2/3)` `= {abs_diff} * (2/3)` `= {intermediate_result:.3f}`")
                    st.markdown(f"Gerundet = **{final_vorgabe}**")
                st.success(f"Zu gewährende Vorgabeschläge: **{final_vorgabe}**")
                if ch_p1 == ch_p2: st.info("Keine Vorgabeschläge.")
                elif ch_p1 > ch_p2: st.info(f"{p1_name} (CH {ch_p1}) erhält die Schläge von {p2_name} (CH {ch_p2}).")
                else: st.info(f"{p2_name} (CH {ch_p2}) erhält die Schläge von {p1_name} (CH {ch_p1}).")
            else: st.markdown(f"**Für {round_type_label}:**"); st.warning(f"CH für {round_type_label} nicht für beide Spieler ermittelt.")

        display_matchplay_calculation(player1_results["ch_18"], player2_results["ch_18"], player1_name, player2_name, "18-Loch")
        st.markdown("---")
        display_matchplay_calculation(player1_results["ch_9"], player2_results["ch_9"], player1_name, player2_name, "9-Loch")

# --- FA-03: Berechnung der Vorgabe im Vierer-Matchplay (Foursomes) ---
with tab_foursome_match:
    st.header("FA-03: Vierer-Matchplay Vorgabe (Foursomes)")

    # club_data_for_title ist global verfügbar (Ergebnis von load_course_data())
    
    # FESTGELEGTE STANDARDWERTE FÜR DIE TEAM-CH BERECHNUNG IM VIERER
    DEFAULT_FOURSOME_MATCH_CATEGORY = "Herren"
    DEFAULT_FOURSOME_MATCH_TEE_COLOR = "gelb" 
    DEFAULT_18_HOLE_COURSE_NAME_KEY_F = "18-Loch (Platz 1-18 AB)" 
    DEFAULT_9_HOLE_COURSE_NAME_KEY_F = "9-Loch (Platz A 1-9)" 

    st.info(f"Für jeden Spieler können Geschlecht und Abschlag für eine informative Einzel-CH-Anzeige gewählt werden. Die Berechnung der Team-Vorgaben für '{club_name_for_title}' basiert fest auf: Kategorie '{DEFAULT_FOURSOME_MATCH_CATEGORY}', Abschlag '{DEFAULT_FOURSOME_MATCH_TEE_COLOR.capitalize()}'.")

    if not club_data_for_title or "courseHandicaps" not in club_data_for_title:
        st.error("Clubdaten konnten nicht geladen werden. Vierer-Matchplay-Berechnung nicht möglich.")
    else:
        # Lade die festen Platzdaten für die Team-CH-Berechnung
        tee_data_18_match_default = None
        course_info_18_match_f = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == DEFAULT_FOURSOME_MATCH_CATEGORY and c["holes"] == DEFAULT_18_HOLE_COURSE_NAME_KEY_F), None)
        if course_info_18_match_f and DEFAULT_FOURSOME_MATCH_TEE_COLOR in course_info_18_match_f["tees"]:
            tee_data_18_match_default = course_info_18_match_f["tees"][DEFAULT_FOURSOME_MATCH_TEE_COLOR]

        tee_data_9_match_default = None
        course_info_9_match_f = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == DEFAULT_FOURSOME_MATCH_CATEGORY and c["holes"] == DEFAULT_9_HOLE_COURSE_NAME_KEY_F), None)
        if course_info_9_match_f and DEFAULT_FOURSOME_MATCH_TEE_COLOR in course_info_9_match_f["tees"]:
            tee_data_9_match_default = course_info_9_match_f["tees"][DEFAULT_FOURSOME_MATCH_TEE_COLOR]

        if not tee_data_18_match_default or not tee_data_9_match_default:
            st.error(f"Fehler: Die Standard-Platzdaten für Vierer ({DEFAULT_FOURSOME_MATCH_CATEGORY}, {DEFAULT_FOURSOME_MATCH_TEE_COLOR.capitalize()}) für 18 & 9 Loch konnten nicht in course_data.json gefunden werden.")
        else:
            with st.expander("Details zu den Standard-Platzdaten für Team-Berechnung (Vierer)", expanded=False):
                st.markdown(f"**18-Loch:** SR {tee_data_18_match_default['SR']}, CR {tee_data_18_match_default['CR']:.1f}, Par {tee_data_18_match_default['Par']}")
                st.markdown(f"**9-Loch:** SR {tee_data_9_match_default['SR']}, CR {tee_data_9_match_default['CR']:.1f}, Par {tee_data_9_match_default['Par']}")
            
            st.markdown("---")
            # --- Teamnamen und Spielereingaben ---
            tn_col1, tn_col2 = st.columns(2)
            team1_name = tn_col1.text_input("Name Team 1:", "Team Alpha", key="t1_name_v7")
            team2_name = tn_col2.text_input("Name Team 2:", "Team Bravo", key="t2_name_v7")
            st.markdown("---")

            player_inputs_f = {} # Store HCPIs for Team HCPI calculation

            # Helper function for individual player CH display (leicht modifizierte Version von get_player_handicaps_single)
            def get_individual_ch_details(player_label_prefix, sex_val, hcpi_val, selected_tee_color_val):
                # Diese Funktion sollte global oder hier zugreifbar sein, und club_data_for_title verwenden
                results_ind = {"ch_18": None, "ch_9": None, "desc_18": "", "desc_9": ""}
                if not selected_tee_color_val: return results_ind

                # 18-Loch
                ci_18_ind = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_val and DEFAULT_18_HOLE_COURSE_NAME_KEY_F in c["holes"]), None)
                if ci_18_ind and selected_tee_color_val in ci_18_ind["tees"]:
                    td_18_ind = ci_18_ind["tees"][selected_tee_color_val]
                    results_ind["desc_18"] = f"SR {td_18_ind['SR']}, CR {td_18_ind['CR']:.1f}, Par {td_18_ind['Par']}"
                    ch18_ind = None
                    if "handicapRanges" in td_18_ind:
                        for r_ind in td_18_ind["handicapRanges"]:
                            if r_ind["HCPI_min"] <= hcpi_val <= r_ind["HCPI_max"]: ch18_ind = r_ind["CourseHCP"]; break
                    if ch18_ind is None: ch18_ind = urs_round(hcpi_val * (td_18_ind['SR'] / 113) + (td_18_ind['CR'] - td_18_ind['Par']))
                    results_ind["ch_18"] = ch18_ind
                
                # 9-Loch
                ci_9_ind = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex_val and DEFAULT_9_HOLE_COURSE_NAME_KEY_F in c["holes"]), None)
                if ci_9_ind and selected_tee_color_val in ci_9_ind["tees"]:
                    td_9_ind = ci_9_ind["tees"][selected_tee_color_val]
                    results_ind["desc_9"] = f"SR {td_9_ind['SR']}, CR {td_9_ind['CR']:.1f}, Par {td_9_ind['Par']}"
                    results_ind["ch_9"] = urs_round((hcpi_val / 2.0) * (td_9_ind['SR'] / 113) + (td_9_ind['CR'] - td_9_ind['Par']))
                    ch9_table_ind = None
                    if "handicapRanges" in td_9_ind:
                        for r_ind in td_9_ind["handicapRanges"]:
                            if r_ind["HCPI_min"] <= hcpi_val <= r_ind["HCPI_max"]: ch9_table_ind = r_ind["CourseHCP"]; break
                    if ch9_table_ind is not None: results_ind["desc_9"] += f" (Tabelle: {ch9_table_ind})"
                return results_ind

            def display_player_input_foursome(player_id_letter, team_name_str, col_to_use):
                with col_to_use:
                    st.markdown(f"**Spieler {player_id_letter} ({team_name_str})**")
                    hcpi = st.number_input(f"HCPI Spieler {player_id_letter}:", min_value=HCPI_MIN, max_value=HCPI_MAX, value=10.0, step=0.1, format="%.1f", key=f"hcpi_{player_id_letter}_f7")
                    sex = st.radio(f"Geschlecht Spieler {player_id_letter}:", ("Herren", "Damen"), key=f"sex_{player_id_letter}_f7", horizontal=True)
                    
                    available_tees = []
                    ci18 = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex and DEFAULT_18_HOLE_COURSE_NAME_KEY_F in c["holes"]), None)
                    ci9 = next((c for c in club_data_for_title["courseHandicaps"] if c["category"] == sex and DEFAULT_9_HOLE_COURSE_NAME_KEY_F in c["holes"]), None)
                    if ci18 and ci9: # Nur wenn für beide Kurstypen Daten da sind
                        available_tees = sorted(list(set(ci18["tees"].keys()) & set(ci9["tees"].keys())))
                    
                    selected_tee = None
                    if available_tees:
                        default_player_tee = "gelb" if sex == "Herren" else "rot"
                        player_tee_idx = available_tees.index(default_player_tee) if default_player_tee in available_tees else 0
                        selected_tee = st.selectbox(f"Abschlag Info-CH Spieler {player_id_letter}:", available_tees, index=player_tee_idx, key=f"tee_{player_id_letter}_f7")
                        
                        if selected_tee:
                            ind_data = get_individual_ch_details(f"P{player_id_letter}", sex, hcpi, selected_tee)
                            if ind_data["ch_18"] is not None: st.caption(f"Info CH18 ({selected_tee.capitalize()}): {ind_data['ch_18']} ({ind_data['desc_18']})")
                            if ind_data["ch_9"] is not None: st.caption(f"Info CH9 ({selected_tee.capitalize()}): {ind_data['ch_9']} ({ind_data['desc_9']})")
                    else:
                        st.caption(f"Keine passenden Info-Abschläge für Spieler {player_id_letter} ({sex}) gefunden.")
                return hcpi

            # Spieler Eingaben sammeln
            p_cols = st.columns(4)
            player_inputs_f["A"] = display_player_input_foursome("A", team1_name, p_cols[0])
            player_inputs_f["B"] = display_player_input_foursome("B", team1_name, p_cols[1])
            player_inputs_f["C"] = display_player_input_foursome("C", team2_name, p_cols[2])
            player_inputs_f["D"] = display_player_input_foursome("D", team2_name, p_cols[3])
            st.markdown("---")

            # Team HCPIs
            team_hcpi_t1 = (min(player_inputs_f["A"], player_inputs_f["B"]) * 0.6) + (max(player_inputs_f["A"], player_inputs_f["B"]) * 0.4)
            team_hcpi_t2 = (min(player_inputs_f["C"], player_inputs_f["D"]) * 0.6) + (max(player_inputs_f["C"], player_inputs_f["D"]) * 0.4)
            st.subheader("Team Handicap Indizes (Team-HCPI)")
            thcp_col1, thcp_col2 = st.columns(2)
            thcp_col1.metric(label=f"Team-HCPI {team1_name}", value=f"{team_hcpi_t1:.2f}")
            thcp_col2.metric(label=f"Team-HCPI {team2_name}", value=f"{team_hcpi_t2:.2f}")
            st.markdown("---")

            # Team Course Handicaps (mit Standard-Platzdaten)
            team_ch_t1_18, team_ch_t1_9 = None, None
            team_ch_t2_18, team_ch_t2_9 = None, None
            
            # Team 1
            ch18_t1 = None
            if "handicapRanges" in tee_data_18_match_default:
                for r in tee_data_18_match_default["handicapRanges"]:
                    if r["HCPI_min"] <= team_hcpi_t1 <= r["HCPI_max"]: ch18_t1 = r["CourseHCP"]; break
            if ch18_t1 is None: ch18_t1 = urs_round(team_hcpi_t1 * (tee_data_18_match_default['SR'] / 113) + (tee_data_18_match_default['CR'] - tee_data_18_match_default['Par']))
            team_ch_t1_18 = ch18_t1
            team_ch_t1_9 = urs_round((team_hcpi_t1 / 2.0) * (tee_data_9_match_default['SR'] / 113) + (tee_data_9_match_default['CR'] - tee_data_9_match_default['Par']))
            
            # Team 2
            ch18_t2 = None
            if "handicapRanges" in tee_data_18_match_default:
                for r in tee_data_18_match_default["handicapRanges"]:
                    if r["HCPI_min"] <= team_hcpi_t2 <= r["HCPI_max"]: ch18_t2 = r["CourseHCP"]; break
            if ch18_t2 is None: ch18_t2 = urs_round(team_hcpi_t2 * (tee_data_18_match_default['SR'] / 113) + (tee_data_18_match_default['CR'] - tee_data_18_match_default['Par']))
            team_ch_t2_18 = ch18_t2
            team_ch_t2_9 = urs_round((team_hcpi_t2 / 2.0) * (tee_data_9_match_default['SR'] / 113) + (tee_data_9_match_default['CR'] - tee_data_9_match_default['Par']))

            st.subheader("Team Course Handicaps (Team-CH)")
            st.caption(f"Berechnet basierend auf Standard-Platzdaten: {DEFAULT_FOURSOME_MATCH_CATEGORY}, Abschlag {DEFAULT_FOURSOME_MATCH_TEE_COLOR.capitalize()}")
            tch_col1, tch_col2 = st.columns(2)
            with tch_col1:
                st.markdown(f"**{team1_name}**")
                st.metric("Team-CH 18-Loch", value=f"{team_ch_t1_18}")
                st.metric("Team-CH 9-Loch (Formel)", value=f"{team_ch_t1_9}")
                # Informativer 9-Loch Tabellenwert für Team 1
                ch9_t1_table_info = None
                if "handicapRanges" in tee_data_9_match_default:
                    for r_info in tee_data_9_match_default["handicapRanges"]:
                        if r_info["HCPI_min"] <= team_hcpi_t1 <= r_info["HCPI_max"]: ch9_t1_table_info = r_info["CourseHCP"]; break
                if ch9_t1_table_info is not None: st.caption(f"9-Loch CH (Tabelle): {ch9_t1_table_info}")
            with tch_col2:
                st.markdown(f"**{team2_name}**")
                st.metric("Team-CH 18-Loch", value=f"{team_ch_t2_18}")
                st.metric("Team-CH 9-Loch (Formel)", value=f"{team_ch_t2_9}")
                ch9_t2_table_info = None
                if "handicapRanges" in tee_data_9_match_default:
                    for r_info in tee_data_9_match_default["handicapRanges"]:
                        if r_info["HCPI_min"] <= team_hcpi_t2 <= r_info["HCPI_max"]: ch9_t2_table_info = r_info["CourseHCP"]; break
                if ch9_t2_table_info is not None: st.caption(f"9-Loch CH (Tabelle): {ch9_t2_table_info}")

            st.markdown("---")
            st.subheader("Ergebnis Vorgabeschläge Vierer (Formel: |Team CH₁ - Team CH₂|)")
            
            def display_foursome_allowance(tch1, tch2, team1_n, team2_n, round_label):
                if tch1 is not None and tch2 is not None:
                    abs_diff = abs(tch1 - tch2); final_vorgabe = urs_round(abs_diff)
                    st.markdown(f"**Für eine {round_label}-Runde:**")
                    with st.expander("Berechnungsschritte anzeigen"):
                        st.markdown(f"Formel: `Runde( |Team CH {team1_n} - Team CH {team2_n}| )`")
                        st.markdown(f"Einsetzen: `Runde( |{tch1} - {tch2}| )` `= Runde( |{tch1 - tch2}| )` `= Runde( {abs_diff} )` `= **{final_vorgabe}**`")
                    st.success(f"Zu gewährende Vorgabeschläge: **{final_vorgabe}**")
                    if tch1 == tch2: st.info("Keine Vorgabeschläge.")
                    elif tch1 > tch2: st.info(f"{team1_n} (Team CH {tch1}) erhält die Schläge von {team2_n} (Team CH {tch2}).")
                    else: st.info(f"{team2_n} (Team CH {tch2}) erhält die Schläge von {team1_n} (Team CH {tch1}).")
                else: st.markdown(f"**Für {round_label}:**"); st.warning(f"Team CH für {round_label} nicht für beide Teams ermittelt.")
            
            display_foursome_allowance(team_ch_t1_18, team_ch_t2_18, team1_name, team2_name, "18-Loch")
            st.markdown("---")
            display_foursome_allowance(team_ch_t1_9, team_ch_t2_9, team1_name, team2_name, "9-Loch")

st.markdown("---")
st.caption("Diese App ist eine reine Offline-Anwendung (PWA) und speichert keine Daten.")