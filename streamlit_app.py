import streamlit as st
import math
import json # Importieren des json-Moduls
import pandas as pd # Importieren von Pandas

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
st.caption(f"Gemäß URS Version 1.0. Mit Daten für {load_course_data().get('golfclub', 'ausgewählte Clubs')}.")


# --- Input Validation Ranges ---
HCPI_MIN, HCPI_MAX = -5.0, 54.0
# SR, CR, PAR Min/Max werden jetzt weniger relevant für die Lookup-Tabelle, aber für manuelle Eingaben behalten
SLOPE_MIN, SLOPE_MAX = 55, 155
CR_MIN, CR_MAX = 55.0, 85.0
PAR_MIN, PAR_MAX = 60, 78

# --- Tabs ---
tab_club_data, tab_manual_calc, tab_single_match, tab_foursome_match = st.tabs([
    "Club-Daten Lookup (FA-01)",
    "Manuelle Berechnung (FA-01)",
    "Einzel-Matchplay (FA-02)",
    "Vierer-Matchplay (FA-03)"
])

# --- Club-Daten Lookup (Erweiterung für FA-01) ---
with tab_club_data:
    st.header(f"Course Handicap Lookup für: {COURSE_DATA.get('golfclub', 'Fehler beim Laden der Clubdaten')}")
    
    course_data_loaded = load_course_data()

    if course_data_loaded and "courseHandicaps" in course_data_loaded:
        categories = sorted(list(set(ch_info["category"] for ch_info in course_data_loaded["courseHandicaps"])))
        selected_category = st.selectbox("Kategorie wählen:", categories, key="cat_select")

        # Filtere Kurse basierend auf Kategorie
        courses_in_category = [ch_info for ch_info in course_data_loaded["courseHandicaps"] if ch_info["category"] == selected_category]
        
        hole_options = sorted(list(set(ch_info["holes"] for ch_info in courses_in_category)))
        selected_holes_desc = st.selectbox(f"Lochzahl/Platz wählen ({selected_category}):", hole_options, key="holes_select")

        # Finde die genauen Kursinformationen
        current_course_info = next((ch_info for ch_info in courses_in_category if ch_info["holes"] == selected_holes_desc), None)

        if current_course_info and "tees" in current_course_info:
            tee_colors = list(current_course_info["tees"].keys())
            selected_tee_color = st.selectbox(f"Abschlag wählen ({selected_holes_desc}):", tee_colors, key="tee_select")
            
            tee_data = current_course_info["tees"].get(selected_tee_color)

            if tee_data:
                st.write(f"**Daten für {selected_category} - {selected_holes_desc} - Abschlag {selected_tee_color.capitalize()}:**")
                col_data1, col_data2, col_data3 = st.columns(3)
                col_data1.metric("Course Rating", f"{tee_data['CR']:.1f}")
                col_data2.metric("Slope Rating", tee_data['SR'])
                col_data3.metric("Par", tee_data['Par'])

                hcpi_club = st.number_input("Ihr HCPI:",
                                            min_value=HCPI_MIN, max_value=HCPI_MAX, value=18.0, step=0.1, format="%.1f", key="hcpi_club_lookup")

                if st.button("Course Handicap aus Tabelle ermitteln", key="lookup_ch_table"):
                    course_hcp_from_table = "Nicht gefunden"
                    if "handicapRanges" in tee_data:
                        for hcp_range in tee_data["handicapRanges"]:
                            if hcp_range["HCPI_min"] <= hcpi_club <= hcp_range["HCPI_max"]:
                                course_hcp_from_table = hcp_range["CourseHCP"]
                                break
                    
                    if course_hcp_from_table != "Nicht gefunden":
                        st.success(f"Course Handicap aus Tabelle ({selected_tee_color}): **{course_hcp_from_table}**")
                    else:
                        st.warning(f"Für HCPI {hcpi_club} wurde kein direkter Tabelleneintrag gefunden.")

                    # Zusätzliche Berechnung mit Formel für Vergleich oder als Fallback
                    # Die URS 9-Loch Formel ist (HCPI/2) * (SR/113) + (CR-Par)
                    # Die URS 18-Loch Formel ist HCPI * (SR/113) + (CR-Par)
                    
                    hcpi_for_formula = hcpi_club
                    # Anpassung für 9-Loch-Formel gemäß URS FA-01.06
                    # Die JSON "holes" Beschreibung muss geparst werden, um zu entscheiden ob 9 oder 18 Loch
                    # Beispiel: "9-Loch (Platz A 1-9)"
                    is_9_hole_course = "9-Loch" in selected_holes_desc 

                    if is_9_hole_course:
                        hcpi_for_formula = hcpi_club / 2.0
                        # SR, CR, Par sind schon die 9-Loch spezifischen Werte aus der JSON
                        # Der Hinweis aus FA-01.08 ist hier implizit durch die Auswahl abgedeckt

                    calculated_ch_formula = urs_round(hcpi_for_formula * (tee_data['SR'] / 113) + (tee_data['CR'] - tee_data['Par']))
                    st.info(f"Zum Vergleich: Course Handicap per Formel berechnet: **{calculated_ch_formula}**")
                    if is_9_hole_course:
                        st.caption("Formel für 9 Loch: (HCPI / 2) * (Slope Rating / 113) + (Course Rating - Par)")
                    else:
                        st.caption("Formel für 18 Loch: HCPI * (Slope Rating / 113) + (Course Rating - Par)")


            else:
                st.warning(f"Keine Daten für Abschlag '{selected_tee_color}' gefunden.")
        else:
            st.warning(f"Keine Abschlagsdaten für '{selected_holes_desc}' gefunden.")
    else:
        st.error("Kursdaten konnten nicht geladen oder verarbeitet werden.")


# --- FA-01: Manuelle Berechnung des Course Handicaps ---
with tab_manual_calc:
    st.header("FA-01: Manuelle Berechnung des Course Handicaps")
    st.info("Hinweis (FA-01.08): Für eine 9-Loch-Berechnung tragen Sie bitte die spezifischen 9-Loch-Platzdaten (Slope, CR, Par der gespielten 9 Löcher) in die allgemeinen Eingabefelder ein.")

    col1_1, col1_2 = st.columns(2)
    with col1_1:
        hcpi_allg = st.number_input("Ihr HCPI (FA-01.01):",
                                    min_value=HCPI_MIN, max_value=HCPI_MAX, value=18.0, step=0.1, format="%.1f", key="hcpi_allg_manual")
        slope_allg = st.number_input("Slope Rating (Platz) (FA-01.02):",
                                     min_value=SLOPE_MIN, max_value=SLOPE_MAX, value=125, step=1, key="slope_allg_manual")
    with col1_2:
        cr_allg = st.number_input("Course Rating (Platz) (FA-01.03):",
                                  min_value=CR_MIN, max_value=CR_MAX, value=71.0, step=0.1, format="%.1f", key="cr_allg_manual")
        par_allg = st.number_input("Par (Platz) (FA-01.04):",
                                   min_value=PAR_MIN, max_value=PAR_MAX, value=72, step=1, key="par_allg_manual")

    if st.button("Berechne Course Handicaps (manuell)", key="calc_allg_ch_manual"):
        # FA-01.05: 18-Loch
        course_handicap_18 = urs_round(hcpi_allg * (slope_allg / 113) + (cr_allg - par_allg))
        st.success(f"Berechnetes 18-Loch Course Handicap (FA-01.07): **{course_handicap_18}**")

        # FA-01.06: 9-Loch
        course_handicap_9 = urs_round((hcpi_allg / 2) * (slope_allg / 113) + (cr_allg - par_allg))
        st.success(f"Berechnetes 9-Loch Course Handicap (FA-01.07): **{course_handicap_9}**")
        st.caption("(Stellen Sie sicher, dass die Platzdaten (SR, CR, Par) für diese 9-Loch-Berechnung korrekt sind!)")


# --- FA-02: Berechnung der Vorgabe im Einzel-Matchplay ---
# --- FA-02: Berechnung der Vorgabe im Einzel-Matchplay ---
with tab_single_match:
    st.header("FA-02: Einzel-Matchplay Vorgabe")

    course_data_loaded = load_course_data()
    club_name = course_data_loaded.get('golfclub', 'Clubdaten nicht geladen')
    st.info(f"Daten für: {club_name}. Pro Spieler wird Geschlecht und ein Abschlag gewählt. Daraus werden die Vorgaben für 18-Loch und 9-Loch Runden ermittelt.")

    if not course_data_loaded or "courseHandicaps" not in course_data_loaded:
        st.error("Clubdaten konnten nicht geladen werden. Matchplay-Berechnung mit Clubdaten nicht möglich.")
    else:
        name_col1, name_col2 = st.columns(2)
        player1_name = name_col1.text_input("Name Spieler 1:", "Spieler 1", key="p1_name_v2")
        player2_name = name_col2.text_input("Name Spieler 2:", "Spieler 2", key="p2_name_v2")
        st.markdown("---")

        col_p1, col_p2 = st.columns(2)

        player1_results = {"ch_18": None, "ch_9": None}
        player2_results = {"ch_18": None, "ch_9": None}

        # Helper function to get CH and details
        def get_player_handicaps(player_idx_str, sex, hcpi, selected_tee_color):
            results = {"ch_18": None, "ch_9": None, "desc_18": "", "desc_9": ""}
            
            # --- 18-Loch Logik ---
            course_info_18 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex and "18-Loch" in c["holes"]), None)
            if course_info_18 and selected_tee_color in course_info_18["tees"]:
                tee_data_18 = course_info_18["tees"][selected_tee_color]
                results["desc_18"] = f"18-Loch ({course_info_18['holes']}), Abschlag {selected_tee_color.capitalize()}: SR {tee_data_18['SR']}, CR {tee_data_18['CR']:.1f}, Par {tee_data_18['Par']}"
                
                ch18 = None
                # Primär: Tabellen-Lookup für 18-Loch
                if "handicapRanges" in tee_data_18:
                    for r in tee_data_18["handicapRanges"]:
                        if r["HCPI_min"] <= hcpi <= r["HCPI_max"]:
                            ch18 = r["CourseHCP"]
                            break
                if ch18 is None: # Fallback auf Formel für 18-Loch
                    ch18 = urs_round(hcpi * (tee_data_18['SR'] / 113) + (tee_data_18['CR'] - tee_data_18['Par']))
                results["ch_18"] = ch18
            else:
                results["desc_18"] = f"Keine 18-Loch Daten für {sex}, Abschlag {selected_tee_color.capitalize()} gefunden."

            # --- 9-Loch Logik ---
            # Annahme: Wir suchen nach einem "9-Loch" Eintrag, z.B. "9-Loch (Platz A 1-9)"
            course_info_9 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex and "9-Loch" in c["holes"]), None)
            if course_info_9 and selected_tee_color in course_info_9["tees"]:
                tee_data_9 = course_info_9["tees"][selected_tee_color]
                results["desc_9"] = f"9-Loch ({course_info_9['holes']}), Abschlag {selected_tee_color.capitalize()}: SR {tee_data_9['SR']}, CR {tee_data_9['CR']:.1f}, Par {tee_data_9['Par']}"

                # Primär: URS Formel für 9-Loch (um "zu hohe" Werte aus Tabellen zu vermeiden, falls diese anders kalibriert sind)
                ch9_formula = urs_round((hcpi / 2.0) * (tee_data_9['SR'] / 113) + (tee_data_9['CR'] - tee_data_9['Par']))
                results["ch_9"] = ch9_formula
                
                # Informativer Tabellen-Lookup für 9-Loch, falls vorhanden
                ch9_table = None
                if "handicapRanges" in tee_data_9:
                    for r in tee_data_9["handicapRanges"]:
                        if r["HCPI_min"] <= hcpi <= r["HCPI_max"]: # Voller HCPI für Tabellen-Lookup
                            ch9_table = r["CourseHCP"]
                            break
                if ch9_table is not None:
                    results["desc_9"] += f" (CH Tabelle: {ch9_table})"
            else:
                results["desc_9"] = f"Keine 9-Loch Daten für {sex}, Abschlag {selected_tee_color.capitalize()} gefunden."
            
            return results

        # --- Spieler 1 ---
        with col_p1:
            st.subheader(player1_name)
            sex_p1 = st.radio(f"Geschlecht {player1_name}:", ("Herren", "Damen"), key="sex_p1_v2", horizontal=True)
            
            # Gemeinsame Abschlagsfarben finden, die für die gewählte Kategorie für 18 UND 9 Loch existieren
            tees_18_p1 = []
            course_info_18_p1 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex_p1 and "18-Loch" in c["holes"]), None)
            if course_info_18_p1: tees_18_p1 = list(course_info_18_p1["tees"].keys())
            
            tees_9_p1 = []
            course_info_9_p1 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex_p1 and "9-Loch" in c["holes"]), None)
            if course_info_9_p1: tees_9_p1 = list(course_info_9_p1["tees"].keys())
            
            common_tees_p1 = sorted(list(set(tees_18_p1) & set(tees_9_p1)))

            if not common_tees_p1:
                st.warning(f"Keine gemeinsamen Abschläge für 18- und 9-Loch für {sex_p1} gefunden.")
            else:
                default_tee_p1 = "gelb" if sex_p1 == "Herren" else "rot"
                default_tee_p1_idx = common_tees_p1.index(default_tee_p1) if default_tee_p1 in common_tees_p1 else 0
                selected_tee_p1 = st.selectbox(f"Abschlag {player1_name}:", common_tees_p1, index=default_tee_p1_idx, key="tee_p1_v2")
                
                hcpi_p1 = st.number_input(f"HCPI {player1_name}:",
                                          min_value=HCPI_MIN, max_value=HCPI_MAX, value=10.0, step=0.1, format="%.1f", key="hcpi_p1_match_v2")

                p1_data = get_player_handicaps("p1", sex_p1, hcpi_p1, selected_tee_p1)
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
            sex_p2 = st.radio(f"Geschlecht {player2_name}:", ("Herren", "Damen"), key="sex_p2_v2", horizontal=True)

            tees_18_p2 = []
            course_info_18_p2 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex_p2 and "18-Loch" in c["holes"]), None)
            if course_info_18_p2: tees_18_p2 = list(course_info_18_p2["tees"].keys())
            
            tees_9_p2 = []
            course_info_9_p2 = next((c for c in course_data_loaded["courseHandicaps"] if c["category"] == sex_p2 and "9-Loch" in c["holes"]), None)
            if course_info_9_p2: tees_9_p2 = list(course_info_9_p2["tees"].keys())

            common_tees_p2 = sorted(list(set(tees_18_p2) & set(tees_9_p2)))

            if not common_tees_p2:
                st.warning(f"Keine gemeinsamen Abschläge für 18- und 9-Loch für {sex_p2} gefunden.")
            else:
                default_tee_p2 = "gelb" if sex_p2 == "Herren" else "rot"
                default_tee_p2_idx = common_tees_p2.index(default_tee_p2) if default_tee_p2 in common_tees_p2 else 0
                selected_tee_p2 = st.selectbox(f"Abschlag {player2_name}:", common_tees_p2, index=default_tee_p2_idx, key="tee_p2_v2")

                hcpi_p2 = st.number_input(f"HCPI {player2_name}:",
                                          min_value=HCPI_MIN, max_value=HCPI_MAX, value=20.5, step=0.1, format="%.1f", key="hcpi_p2_match_v2")

                p2_data = get_player_handicaps("p2", sex_p2, hcpi_p2, selected_tee_p2)
                player2_results["ch_18"] = p2_data["ch_18"]
                player2_results["ch_9"] = p2_data["ch_9"]

                if p2_data["ch_18"] is not None:
                    st.metric(label="Course HCP 18-Loch", value=p2_data["ch_18"])
                    st.caption(p2_data["desc_18"])
                if p2_data["ch_9"] is not None:
                    st.metric(label="Course HCP 9-Loch (Formel)", value=p2_data["ch_9"])
                    st.caption(p2_data["desc_9"])
        
        # --- Ergebnis Matchplay-Vorgabe ---
        st.markdown("---")
        st.subheader("Ergebnis Matchplay-Vorgabe (Formel: |CH1 - CH2| * 2/3)")

        # 18-Loch Matchplay
        if player1_results["ch_18"] is not None and player2_results["ch_18"] is not None:
            ch_p1_18, ch_p2_18 = player1_results["ch_18"], player2_results["ch_18"]
            vorgabe_18 = urs_round(abs(ch_p1_18 - ch_p2_18) * (2/3))
            st.markdown(f"**Für eine 18-Loch Runde:**")
            st.success(f"Zu gewährende Vorgabeschläge: **{vorgabe_18}**")
            if ch_p1_18 == ch_p2_18:
                st.info("Keine Vorgabeschläge.")
            elif ch_p1_18 > ch_p2_18:
                st.info(f"{player1_name} (CH {ch_p1_18}) erhält die Schläge von {player2_name} (CH {ch_p2_18}).")
            else:
                st.info(f"{player2_name} (CH {ch_p2_18}) erhält die Schläge von {player1_name} (CH {ch_p1_18}).")
        else:
            st.markdown("**Für eine 18-Loch Runde:**")
            st.warning("Course Handicaps für 18-Loch konnten nicht für beide Spieler vollständig ermittelt werden.")

        # 9-Loch Matchplay
        if player1_results["ch_9"] is not None and player2_results["ch_9"] is not None:
            ch_p1_9, ch_p2_9 = player1_results["ch_9"], player2_results["ch_9"]
            vorgabe_9 = urs_round(abs(ch_p1_9 - ch_p2_9) * (2/3))
            st.markdown(f"**Für eine 9-Loch Runde:**")
            st.success(f"Zu gewährende Vorgabeschläge: **{vorgabe_9}**")
            if ch_p1_9 == ch_p2_9:
                st.info("Keine Vorgabeschläge.")
            elif ch_p1_9 > ch_p2_9:
                st.info(f"{player1_name} (CH {ch_p1_9}) erhält die Schläge von {player2_name} (CH {ch_p2_9}).")
            else:
                st.info(f"{player2_name} (CH {ch_p2_9}) erhält die Schläge von {player1_name} (CH {ch_p1_9}).")
        else:
            st.markdown("**Für eine 9-Loch Runde:**")
            st.warning("Course Handicaps für 9-Loch konnten nicht für beide Spieler vollständig ermittelt werden.")
            
# --- FA-03: Berechnung der Vorgabe im Vierer-Matchplay (Foursomes) ---
with tab_foursome_match: # Alter Name: tab3
    st.header("FA-03: Vierer-Matchplay Vorgabe (Foursomes)")
    st.info("Hierfür werden CR, SR und Par des gespielten Platzes manuell eingegeben.")
    st.subheader("Team 1")
    t1_col1, t1_col2 = st.columns(2)
    hcpi_a = t1_col1.number_input("HCPI Spieler A (Team 1) (FA-03.01):", min_value=HCPI_MIN, max_value=HCPI_MAX, value=8.0, step=0.1, format="%.1f", key="hcpi_a")
    hcpi_b = t1_col2.number_input("HCPI Spieler B (Team 1) (FA-03.02):", min_value=HCPI_MIN, max_value=HCPI_MAX, value=15.0, step=0.1, format="%.1f", key="hcpi_b")

    st.subheader("Team 2")
    t2_col1, t2_col2 = st.columns(2)
    hcpi_c = t2_col1.number_input("HCPI Spieler C (Team 2) (FA-03.03):", min_value=HCPI_MIN, max_value=HCPI_MAX, value=12.0, step=0.1, format="%.1f", key="hcpi_c")
    hcpi_d = t2_col2.number_input("HCPI Spieler D (Team 2) (FA-03.04):", min_value=HCPI_MIN, max_value=HCPI_MAX, value=22.0, step=0.1, format="%.1f", key="hcpi_d")

    st.subheader("Platzdaten für Vierer-Matchplay")
    p_col1, p_col2, p_col3 = st.columns(3)
    slope_vierer = p_col1.number_input("Slope Rating (Platz) (FA-03.05):", min_value=SLOPE_MIN, max_value=SLOPE_MAX, value=128, step=1, key="slope_vierer")
    cr_vierer = p_col2.number_input("Course Rating (Platz) (FA-03.06):", min_value=CR_MIN, max_value=CR_MAX, value=71.5, step=0.1, format="%.1f", key="cr_vierer")
    par_vierer = p_col3.number_input("Par (Platz) (FA-03.07):", min_value=PAR_MIN, max_value=PAR_MAX, value=72, step=1, key="par_vierer")

    if st.button("Berechne Vierer-Matchplay Vorgabe (FA-03.12)", key="calc_foursome_match"):
        team_hcpi_t1 = (min(hcpi_a, hcpi_b) * 0.6) + (max(hcpi_a, hcpi_b) * 0.4)
        st.write(f"Team HCPI Team 1 (FA-03.08): **{team_hcpi_t1:.2f}**")

        team_hcpi_t2 = (min(hcpi_c, hcpi_d) * 0.6) + (max(hcpi_c, hcpi_d) * 0.4)
        st.write(f"Team HCPI Team 2 (FA-03.09): **{team_hcpi_t2:.2f}**")

        team_ch_t1 = urs_round(team_hcpi_t1 * (slope_vierer / 113) + (cr_vierer - par_vierer))
        st.write(f"Team Course Handicap Team 1 (FA-03.10): **{team_ch_t1}**")

        team_ch_t2 = urs_round(team_hcpi_t2 * (slope_vierer / 113) + (cr_vierer - par_vierer))
        st.write(f"Team Course Handicap Team 2 (FA-03.11): **{team_ch_t2}**")

        vorgabeschlaege_vierer = urs_round(abs(team_ch_t1 - team_ch_t2))
        st.success(f"Zu gewährende Vorgabeschläge (FA-03.12): **{vorgabeschlaege_vierer}**")

        if team_ch_t1 == team_ch_t2:
            st.info("Beide Teams haben das gleiche Team Course Handicap. Keine Vorgabeschläge. (FA-03.13)")
        elif team_ch_t1 > team_ch_t2:
            st.info("Team 1 (mit dem höheren Team CH) erhält die Schläge von Team 2. (FA-03.13)")
        else: # team_ch_t2 > team_ch_t1
            st.info("Team 2 (mit dem höheren Team CH) erhält die Schläge von Team 1. (FA-03.13)")

st.markdown("---")
st.caption("Diese App ist eine reine Offline-Anwendung (PWA) und speichert keine Daten.")