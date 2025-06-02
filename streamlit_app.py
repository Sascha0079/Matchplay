import streamlit as st
import math

# Gemäß URS: "Ergebnis gerundet auf eine ganze Zahl" für Course Handicaps.
# Python's round() rundet .5 zur nächsten geraden Zahl.
# Viele Golfsysteme runden .5 immer auf.
# Für dieses Beispiel verwenden wir Python's round(), da "Runde()" in der URS nicht näher spezifiziert ist
# und round() die gängigste Interpretation von "auf ganze Zahl runden" ist.
def urs_round(n):
    return round(n)

st.set_page_config(page_title="Golf-Vorgabe-Rechner", layout="wide")

st.title("Golf-Vorgabe-Rechner ⛳")
st.caption(f"Gemäß URS Version 1.0. Reine Offline-App.")

# --- Input Validation Ranges (Optional aber empfohlen für FA-04.04) ---
HCPI_MIN, HCPI_MAX = -5.0, 54.0
SLOPE_MIN, SLOPE_MAX = 55, 155
CR_MIN, CR_MAX = 55.0, 85.0 # Etwas erweiterte Bereiche für Flexibilität
PAR_MIN, PAR_MAX = 60, 78

tab1, tab2, tab3 = st.tabs([
    "Allgemeines Course Handicap",
    "Einzel-Matchplay Vorgabe",
    "Vierer-Matchplay Vorgabe"
])

# --- FA-01: Allgemeine Berechnung des Course Handicaps ---
with tab1:
    st.header("FA-01: Allgemeine Berechnung des Course Handicaps")
    st.info("Hinweis (FA-01.08): Für eine 9-Loch-Berechnung tragen Sie bitte die spezifischen 9-Loch-Platzdaten (Slope, CR, Par der gespielten 9 Löcher) in die allgemeinen Eingabefelder ein.")

    col1_1, col1_2 = st.columns(2)
    with col1_1:
        hcpi_allg = st.number_input("Ihr HCPI (FA-01.01):",
                                    min_value=HCPI_MIN, max_value=HCPI_MAX, value=18.0, step=0.1, format="%.1f", key="hcpi_allg")
        slope_allg = st.number_input("Slope Rating (Platz) (FA-01.02):",
                                     min_value=SLOPE_MIN, max_value=SLOPE_MAX, value=125, step=1, key="slope_allg")
    with col1_2:
        cr_allg = st.number_input("Course Rating (Platz) (FA-01.03):",
                                  min_value=CR_MIN, max_value=CR_MAX, value=71.0, step=0.1, format="%.1f", key="cr_allg")
        par_allg = st.number_input("Par (Platz) (FA-01.04):",
                                   min_value=PAR_MIN, max_value=PAR_MAX, value=72, step=1, key="par_allg")

    if st.button("Berechne Course Handicaps (FA-01.05 & FA-01.06)", key="calc_allg_ch"):
        # FA-04.04: Grundlegende Validierung (st.number_input macht schon viel)
        
        # FA-01.05: 18-Loch
        course_handicap_18 = urs_round(hcpi_allg * (slope_allg / 113) + (cr_allg - par_allg))
        st.success(f"Berechnetes 18-Loch Course Handicap (FA-01.07): **{course_handicap_18}**")

        # FA-01.06: 9-Loch
        course_handicap_9 = urs_round((hcpi_allg / 2) * (slope_allg / 113) + (cr_allg - par_allg))
        st.success(f"Berechnetes 9-Loch Course Handicap (FA-01.07): **{course_handicap_9}**")
        st.caption("(Stellen Sie sicher, dass die Platzdaten (SR, CR, Par) für diese 9-Loch-Berechnung korrekt sind!)")

# --- FA-02: Berechnung der Vorgabe im Einzel-Matchplay ---
with tab2:
    st.header("FA-02: Einzel-Matchplay Vorgabe")
    col2_1, col2_2, col2_3 = st.columns(3)
    with col2_1:
        hcpi_p1 = st.number_input("HCPI Spieler 1 (FA-02.01):",
                                  min_value=HCPI_MIN, max_value=HCPI_MAX, value=10.0, step=0.1, format="%.1f", key="hcpi_p1")
        hcpi_p2 = st.number_input("HCPI Spieler 2 (FA-02.02):",
                                  min_value=HCPI_MIN, max_value=HCPI_MAX, value=20.5, step=0.1, format="%.1f", key="hcpi_p2")
    with col2_2:
        slope_match = st.number_input("Slope Rating (Platz) (FA-02.03):",
                                      min_value=SLOPE_MIN, max_value=SLOPE_MAX, value=130, step=1, key="slope_match_single")
        cr_match = st.number_input("Course Rating (Platz) (FA-02.04):",
                                   min_value=CR_MIN, max_value=CR_MAX, value=72.1, step=0.1, format="%.1f", key="cr_match_single")
    with col2_3:
        par_match = st.number_input("Par (Platz) (FA-02.05):",
                                    min_value=PAR_MIN, max_value=PAR_MAX, value=72, step=1, key="par_match_single")

    if st.button("Berechne Einzel-Matchplay Vorgabe (FA-02.08)", key="calc_single_match"):
        ch_p1 = urs_round(hcpi_p1 * (slope_match / 113) + (cr_match - par_match))
        st.write(f"18-Loch Course Handicap Spieler 1 (FA-02.06): **{ch_p1}**")

        ch_p2 = urs_round(hcpi_p2 * (slope_match / 113) + (cr_match - par_match))
        st.write(f"18-Loch Course Handicap Spieler 2 (FA-02.07): **{ch_p2}**")

        vorgabeschlaege_einzel = urs_round(abs(ch_p1 - ch_p2) * (2/3))
        st.success(f"Zu gewährende Vorgabeschläge (FA-02.08): **{vorgabeschlaege_einzel}**")

        if ch_p1 == ch_p2:
            st.info("Beide Spieler haben das gleiche Course Handicap. Keine Vorgabeschläge. (FA-02.09)")
        elif ch_p1 > ch_p2:
            st.info("Spieler 1 (mit dem höheren CH) erhält die Schläge von Spieler 2. (FA-02.09)")
        else: # ch_p2 > ch_p1
            st.info("Spieler 2 (mit dem höheren CH) erhält die Schläge von Spieler 1. (FA-02.09)")

# --- FA-03: Berechnung der Vorgabe im Vierer-Matchplay (Foursomes) ---
with tab3:
    st.header("FA-03: Vierer-Matchplay Vorgabe (Foursomes)")
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
        # Team HCPI Team 1 (FA-03.08)
        team_hcpi_t1 = (min(hcpi_a, hcpi_b) * 0.6) + (max(hcpi_a, hcpi_b) * 0.4)
        st.write(f"Team HCPI Team 1 (FA-03.08): **{team_hcpi_t1:.2f}**")

        # Team HCPI Team 2 (FA-03.09)
        team_hcpi_t2 = (min(hcpi_c, hcpi_d) * 0.6) + (max(hcpi_c, hcpi_d) * 0.4)
        st.write(f"Team HCPI Team 2 (FA-03.09): **{team_hcpi_t2:.2f}**")

        # Team Course Handicap Team 1 (FA-03.10)
        team_ch_t1 = urs_round(team_hcpi_t1 * (slope_vierer / 113) + (cr_vierer - par_vierer))
        st.write(f"Team Course Handicap Team 1 (FA-03.10): **{team_ch_t1}**")

        # Team Course Handicap Team 2 (FA-03.11)
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