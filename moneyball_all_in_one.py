# Moneyball Phil — All-in-One App
# Version: Final (All Modules + Global Parlay + Banner)
# -----------------------------------------------------

import streamlit as st
import base64, os, math, uuid, datetime
import pandas as pd

# ---------------------------
# Page Config (once only)
# ---------------------------
st.set_page_config(page_title="Moneyball Phil — All-in-One", layout="wide")

# ---------------------------
# Fixed Top Banner
# ---------------------------
def _read_banner_bytes():
    candidates = [
        "moneyball_banner.jpg",
        "moneyball_banner.png",
        "banner.jpg",
        "banner.png",
    ]
    for name in candidates:
        if os.path.exists(name):
            try:
                with open(name, "rb") as f:
                    return f.read()
            except Exception:
                pass
    return None

_banner = _read_banner_bytes()
if _banner:
    banner_b64 = base64.b64encode(_banner).decode()
    banner_img_html = f'<img src="data:image/jpeg;base64,{banner_b64}" style="height:120px;object-fit:contain;" />'
else:
    banner_img_html = "<div style='height:120px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;'>Moneyball Phil</div>"

st.markdown(f"""
    <style>
    .fixed-banner {{
        position: fixed; top: 0; left: 0; right: 0;
        height: 120px; background: #000; z-index: 9999;
        display:flex; align-items:center; justify-content:center;
        border-bottom: 1px solid #222;
    }}
    .app-content {{ margin-top: 130px; }}
    </style>
    <div class="fixed-banner">{banner_img_html}</div>
""", unsafe_allow_html=True)

# Open content wrapper so modules render below banner
st.markdown('<div class="app-content">', unsafe_allow_html=True)
# =====================================================
# ============ GLOBAL PARLAY BUILDER ==================
# =====================================================
if "global_parlay" not in st.session_state:
    st.session_state.global_parlay = []

def american_to_prob(odds: float) -> float:
    if odds >= 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)

def american_to_decimal(odds: float) -> float:
    if odds >= 0:
        return 1.0 + (odds / 100.0)
    return 1.0 + (100.0 / abs(odds))

def decimal_to_american(dec: float) -> int:
    if dec <= 1.0: return 0
    if dec >= 2.0: return round((dec - 1.0) * 100)
    return -round(100.0 / (dec - 1.0))

def add_to_global_parlay(sport: str, description: str, odds_american: float, true_prob_frac: float):
    st.session_state.global_parlay.append({
        "id": str(uuid.uuid4())[:8],
        "sport": sport,
        "description": description,
        "odds": float(odds_american),
        "true_prob": float(true_prob_frac),
    })

def render_global_parlay_builder():
    st.markdown("---")
    st.header("🌍 Global Parlay Builder (All Sports)")

    legs = st.session_state.get("global_parlay", [])
    if not legs:
        st.info("No global legs saved yet. Use “Add to Global Parlay” inside any module.")
        return

    # Show table of legs
    for leg in legs:
        c1, c2, c3, c4, c5 = st.columns([1.1, 4, 1.2, 1.2, 0.8])
        c1.write(leg["sport"])
        c2.write(leg["description"])
        c3.write(f"Odds: {int(leg['odds'])}")
        c4.write(f"True: {leg['true_prob']*100:.2f}%")
        with c5:
            if st.button("🗑️", key=f"rm_gl_{leg['id']}"):
                st.session_state.global_parlay = [x for x in legs if x["id"] != leg["id"]]
                st.rerun()

    cc1, cc2 = st.columns([1,1])
    with cc1:
        if st.button("🧹 Clear All Global Legs"):
            st.session_state.global_parlay = []
            st.success("Global parlay cleared.")
            st.rerun()

    # Manual sportsbook parlay odds
    st.markdown("### Sportsbook Parlay Odds (manual)")
    book_odds_str = st.text_input("Enter combined sportsbook odds (American, e.g., +650 or -120):", value="", key="global_book_odds")
    implied_book = None
    if book_odds_str.strip():
        try:
            book_odds_val = float(book_odds_str.replace("+",""))
            implied_book = american_to_prob(book_odds_val)  # [0..1]
        except Exception:
            st.warning("Could not parse the American odds you entered.")

    # Compute true parlay %, auto odds, EV
    true_parlay = 1.0
    dec_product = 1.0
    for leg in legs:
        true_parlay *= max(0.0, min(1.0, float(leg["true_prob"])))
        dec_product *= american_to_decimal(float(leg["odds"]))

    auto_american = decimal_to_american(dec_product)
    implied_auto = american_to_prob(auto_american)

    st.markdown("---")
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Legs", f"{len(legs)}")
    g2.metric("True Parlay %", f"{true_parlay*100:.2f}%")
    g3.metric("Auto Combined Odds", f"{auto_american:+d}")
    g4.metric("Auto Implied %", f"{implied_auto*100:.2f}%")
    if implied_book is not None:
        g5.metric("Book Implied %", f"{implied_book*100:.2f}%")
    else:
        g5.metric("Book Implied %", "—")

    # EV using sportsbook odds if given, otherwise auto odds
    if implied_book is not None:
        used_implied = implied_book
        used_dec = american_to_decimal(book_odds_val)
    else:
        used_implied = implied_auto
        used_dec = dec_product

    edge_pp = (true_parlay - used_implied) * 100.0
    roi_per_dollar = (true_parlay * (used_dec - 1.0)) - (1.0 - true_parlay)
    ev_pct = roi_per_dollar * 100.0

    st.write(f"**Edge (pp):** {edge_pp:.2f} pp  |  **EV % (ROI/$1):** {ev_pct:.2f}%")

    # Parlay Tier
    if ev_pct >= 10.0:
        tier = "🟢 Elite"
    elif ev_pct >= 5.0:
        tier = "🟡 Strong"
    elif ev_pct >= 0.0:
        tier = "🟠 Moderate"
    else:
        tier = "🔴 Risky"
    st.write(f"**Parlay Tier:** {tier}")

    # Copy-ready tracker row
    legs_text = " + ".join([f"{leg['sport']}: {leg['description']}" for leg in legs])
    used_amer_for_text = book_odds_val if implied_book is not None else auto_american
    st.markdown("#### Copy-ready Tracker Row")
    st.code(
        f"{datetime.date.today()} | {legs_text} | {int(used_amer_for_text)} | "
        f"True {true_parlay*100:.2f}% | Implied {used_implied*100:.2f}% | "
        f"EV {ev_pct:.2f}% | Edge {edge_pp:.2f} pp | {tier}",
        language="text"
    )
# =====================================================
# =============== MODULE: NFL Props ===================
# =====================================================
def nfl_app():
    st.header("🏈 Moneyball Phil: NFL Prop Simulator (v2.5)")

    # ---- Session State ----
    if "nfl_all_props" not in st.session_state:
        st.session_state.nfl_all_props = []
    if "nfl_temp_props" not in st.session_state:
        st.session_state.nfl_temp_props = []

    # ---- Helpers ----
    def implied_prob(odds: float) -> float:
        if odds == 0: return 0.0
        return (abs(odds) / (abs(odds) + 100)) if odds < 0 else (100 / (odds + 100))

    def ev_calc(true_prob_frac: float, odds: float) -> float:
        return round((true_prob_frac - implied_prob(odds)) * 100, 2)

    def get_tier(prob_pct: float) -> str:
        if prob_pct >= 80: return "🟢 Elite"
        elif prob_pct >= 65: return "🟡 Strong"
        elif prob_pct >= 50: return "🟠 Moderate"
        else: return "🔴 Risky"

    def logistic_prob(x_value: float, line_value: float, scale: float = 15.0) -> float:
        try:
            p = 1.0 / (1.0 + math.exp(-(x_value - line_value) / scale))
        except OverflowError:
            p = 0.0 if (x_value - line_value) < 0 else 1.0
        return round(p * 100.0, 2)   # return as %

    def classify_def_tier(yds_allowed: float) -> str:
        if yds_allowed < 210: return "🔴 Tough"
        elif yds_allowed <= 240: return "🟡 Average"
        else: return "🟢 Easy"

    def apply_defense_adjustments(ypg: float, tpg: float, tier: str):
        if tier == "🔴 Tough": return ypg - 10, tpg - 0.2
        elif tier == "🟢 Easy": return ypg + 10, tpg + 0.2
        return ypg, tpg

    def add_temp_play(player: str, prop: str, true_prob_pct: float, odds: float, group: str):
        st.session_state.nfl_temp_props.append({
            "id": str(uuid.uuid4()),
            "Player": player,
            "Prop": prop,
            "True Prob": f"{true_prob_pct:.2f}%",  # format %
            "Odds": odds,
            "Group": group
        })

    # ---- UI Common Helpers ----
    def render_temp_save_controls():
        if not st.session_state.nfl_temp_props:
            return
        st.subheader("📝 Save Plays from Latest Simulation")
        to_save = []
        for p in st.session_state.nfl_temp_props:
            col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])
            with col1:
                st.markdown(f"**{p['Player']} – {p['Prop']}**  \nTrue: `{p['True Prob']}` | Odds: `{p['Odds']}`")
            with col2:
                ev = ev_calc(float(p["True Prob"].replace('%',''))/100.0, p["Odds"])
                st.markdown(f"EV: `{ev}%`")
            with col3:
                tier = get_tier(float(p["True Prob"].replace('%','')))
                st.markdown(f"Tier: {tier}")
            with col4:
                if st.checkbox("Save", key=f"save_{p['id']}"):
                    to_save.append(p)
            with col5:
                if st.button("🌍 Add", key=f"add_gl_{p['id']}"):
                    add_to_global_parlay("NFL", f"{p['Player']} — {p['Prop']}", p["Odds"], float(p["True Prob"].replace('%',''))/100.0)
                    st.success("Added to Global Parlay")
        if st.button("➕ Add Selected to Board"):
            for p in to_save:
                st.session_state.nfl_all_props.append(p)
            st.session_state.nfl_temp_props = []
            st.success("Selected plays added to Top Player Board.")

    def render_board():
        st.markdown("---")
        st.subheader("📊 Top Player Board (Saved Plays)")
        if not st.session_state.nfl_all_props:
            st.info("No saved plays yet.")
            return
        sorted_props = sorted(st.session_state.nfl_all_props, key=lambda x: float(x["True Prob"].replace('%','')), reverse=True)
        for p in sorted_props:
            prob_val = float(p["True Prob"].replace('%',''))
            ev = ev_calc(prob_val/100.0, p["Odds"])
            tier = get_tier(prob_val)
            col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])
            with col1: st.markdown(f"**{p['Player']} – {p['Prop']}**  \nGroup: `{p['Group']}`")
            with col2: st.markdown(f"True: `{p['True Prob']}`")
            with col3: st.markdown(f"Odds: `{p['Odds']}`  \nEV: `{ev}%`")
            with col4: st.markdown(f"Tier: {tier}") 
            with col5:
                if st.button("🌍 Add", key=f"add_gl_board_{p['id']}"):
                    add_to_global_parlay("NFL", f"{p['Player']} — {p['Prop']}", p["Odds"], prob_val/100.0)
                    st.success("Added to Global Parlay")

    # ---- Position Selector ----
    position = st.selectbox("Select Position", ["Quarterback", "Wide Receiver", "Running Back"])

    # ---- QB Module ----
    if position == "Quarterback":
        st.header("🎯 Quarterback Inputs")
        name = st.text_input("Quarterback Name", value="")
        opp = st.text_input("Opponent Team", value="")
        std_line = st.number_input("Standard Passing Yards Line", value=0.0)
        over_std = st.number_input("Odds Over (Standard)", value=0.0)
        under_std = st.number_input("Odds Under (Standard)", value=0.0)
        alt_line = st.number_input("Alt Over Line", value=0.0)
        alt_odds = st.number_input("Odds for Alt Over", value=0.0)
        td_line = st.number_input("Passing TD Line", value=1.5)
        td_under_odds = st.number_input("Odds for Under TDs", value=0.0)
        ypg = st.number_input("QB Yards/Game", value=0.0)
        tds = st.number_input("QB TD/Game", value=0.0)
        def_yds = st.number_input("Defense Pass Yards Allowed/Game", value=0.0)
        def_tds = st.number_input("Defense Pass TDs Allowed/Game", value=0.0)

        if st.button("Simulate QB Props"):
            tier = classify_def_tier(def_yds)
            avg_ypg = (ypg + def_yds) / 2
            avg_tds = (tds + def_tds) / 2
            adj_ypg, adj_tds = apply_defense_adjustments(avg_ypg, avg_tds, tier)
            st.session_state.nfl_temp_props = []
            std_prob = logistic_prob(adj_ypg, std_line)
            alt_prob = logistic_prob(adj_ypg, alt_line)
            td_prob = logistic_prob(adj_tds, td_line, scale=0.5)
            under_td_prob = round(100.0 - td_prob, 2)
            st.info(f"Opponent Defense Tier: **{tier}**")
            st.success(f"📈 Over {std_line} Pass Yds → {std_prob:.2f}%")
            st.success(f"📈 Over {alt_line} Alt Pass Yds → {alt_prob:.2f}%")
            st.success(f"📉 Under {td_line} Pass TDs → {under_td_prob:.2f}%")
            add_temp_play(name, f"Over {std_line} Pass Yds", std_prob, over_std, "QB")
            add_temp_play(name, f"Over {alt_line} Alt Pass Yds", alt_prob, alt_odds, "QB")
            add_temp_play(name, f"Under {td_line} Pass TDs", under_td_prob, td_under_odds, "QB")

    # ---- WR Module ----
    if position == "Wide Receiver":
        st.header("🎯 Wide Receiver Inputs")
        name = st.text_input("Wide Receiver Name", value="")
        opp = st.text_input("Opponent Team", value="")
        std_line = st.number_input("Standard Receiving Yards Line", value=0.0)
        over_std = st.number_input("Odds Over (Standard)", value=0.0)
        under_std = st.number_input("Odds Under (Standard)", value=0.0)
        alt_line = st.number_input("Alt Over Line", value=0.0)
        alt_odds = st.number_input("Odds for Alt Over", value=0.0)
        rec_line = st.number_input("Receptions Line", value=0.0)
        rec_over_odds = st.number_input("Odds for Over Receptions", value=0.0)
        rec_under_odds = st.number_input("Odds for Under Receptions", value=0.0)
        ypg = st.number_input("WR Yards/Game", value=0.0)
        rpg = st.number_input("WR Receptions/Game", value=0.0)
        def_yds = st.number_input("Defense WR Yards Allowed/Game", value=0.0)
        def_rec = st.number_input("Defense WR Receptions Allowed/Game", value=0.0)

        if st.button("Simulate WR Props"):
            tier = classify_def_tier(def_yds)

            # --- League baseline averages for WR scaling ---
            LEAGUE_WR_YDS = 150.0
            LEAGUE_WR_RECS = 12.0

            # --- Scale player production based on defense strength ---
            avg_ypg = ypg * (def_yds / LEAGUE_WR_YDS)
            avg_rpg = rpg * (def_rec / LEAGUE_WR_RECS)

            # --- Apply your existing defensive tier adjustments ---
            adj_ypg, _ = apply_defense_adjustments(avg_ypg, 0.0, tier)

            # --- Run logistic probability simulations ---
            st.session_state.nfl_temp_props = []
            std_prob = logistic_prob(adj_ypg, std_line)
            alt_prob = logistic_prob(adj_ypg, alt_line)
            rec_prob = logistic_prob(avg_rpg, rec_line, scale=1.5)

            # --- Display results ---
            st.info(f"Opponent Defense Tier: **{tier}**")
            st.success(f"📈 Over {std_line} Rec Yds → {std_prob:.2f}%")
            st.success(f"📈 Over {alt_line} Alt Rec Yds → {alt_prob:.2f}%")
            st.success(f"🎯 Over {rec_line} Receptions → {rec_prob:.2f}%")
            st.success(f"📉 Under {rec_line} Receptions → {round(100 - rec_prob, 2):.2f}%")

            # --- Save props to temporary play board ---
            add_temp_play(name, f"Over {std_line} Rec Yds", std_prob, over_std, "WR")
            add_temp_play(name, f"Under {std_line} Rec Yds", round(100 - std_prob, 2), under_std, "WR")
            add_temp_play(name, f"Over {alt_line} Alt Rec Yds", alt_prob, alt_odds, "WR")
            add_temp_play(name, f"Over {rec_line} Receptions", rec_prob, rec_over_odds, "WR")
            add_temp_play(name, f"Under {rec_line} Receptions", round(100 - rec_prob, 2), rec_under_odds, "WR")

    # ---- RB Module ----
    if position == "Running Back":
        st.header("🎯 Running Back Inputs")
        name = st.text_input("Running Back Name", value="")
        opp = st.text_input("Opponent Team", value="")
        std_line = st.number_input("Standard Rushing Yards Line", value=0.0)
        over_std = st.number_input("Odds Over (Standard)", value=0.0)
        under_std = st.number_input("Odds Under (Standard)", value=0.0)
        alt_line = st.number_input("Alt Over Line", value=0.0)
        alt_odds = st.number_input("Odds for Alt Over", value=0.0)
        rec_line = st.number_input("Receptions Line", value=0.0)
        rec_over_odds = st.number_input("Odds for Over Receptions", value=0.0)
        rec_under_odds = st.number_input("Odds for Under Receptions", value=0.0)
        ypg = st.number_input("RB Yards/Game", value=0.0)
        rpg = st.number_input("RB Receptions/Game", value=0.0)
        def_yds = st.number_input("Defense Rush Yards Allowed/Game", value=0.0)
        def_rec = st.number_input("Defense RB Receptions Allowed/Game", value=0.0)

        if st.button("Simulate RB Props"):
            tier = classify_def_tier(def_yds)
            avg_ypg = (ypg + def_yds) / 2
            avg_rpg = (rpg + def_rec) / 2
            adj_ypg, _ = apply_defense_adjustments(avg_ypg, 0.0, tier)
            st.session_state.nfl_temp_props = []
            std_prob = logistic_prob(adj_ypg, std_line)
            alt_prob = logistic_prob(adj_ypg, alt_line)
            rec_prob = logistic_prob(avg_rpg, rec_line, scale=1.5)
            st.info(f"Opponent Defense Tier: **{tier}**")
            st.success(f"📈 Over {std_line} Rush Yds → {std_prob:.2f}%")
            st.success(f"📈 Over {alt_line} Alt Rush Yds → {alt_prob:.2f}%")
            st.success(f"🎯 Over {rec_line} Receptions → {rec_prob:.2f}%")
            st.success(f"📉 Under {rec_line} Receptions → {round(100-rec_prob,2):.2f}%")
            add_temp_play(name, f"Over {std_line} Rush Yds", std_prob, over_std, "RB")
            add_temp_play(name, f"Under {std_line} Rush Yds", round(100-std_prob,2), under_std, "RB")
            add_temp_play(name, f"Over {alt_line} Alt Rush Yds", alt_prob, alt_odds, "RB")
            add_temp_play(name, f"Over {rec_line} Receptions", rec_prob, rec_over_odds, "RB")
            add_temp_play(name, f"Under {rec_line} Receptions", round(100-rec_prob,2), rec_under_odds, "RB")

    # Render lists + global add buttons
    render_temp_save_controls()
    render_board()

# =====================================================
# ============ MODULE: ATS & Totals (v3.5) ============
# (Restored projections + tier color labels + adj fix)
# =====================================================
def ats_totals_app():
    st.header("📊 Moneyball Phil — ATS & Totals (v3.5)")

    # ----------------- State -----------------
    def init_state():
        defaults = {
            "home": "", "away": "",
            "home_pf": 0.0, "home_pa": 0.0,
            "away_pf": 0.0, "away_pa": 0.0,
            "spread_line_home": 0.0,
            "spread_odds_home": -110.0, "spread_odds_away": -110.0,
            "total_line": 0.0,
            "over_odds": -110.0, "under_odds": -110.0,
            "ml_home": -110.0, "ml_away": -110.0,  # 🆕 Moneyline odds
            "stake": 0.0,
            "results_df": None,
        }
        for k,v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    init_state()

    # ----------------- Helpers -----------------
    def american_to_implied(odds: float) -> float:
        return (100 / (odds + 100)) if odds > 0 else (abs(odds) / (abs(odds) + 100))

    def calculate_ev_pct(true_prob_pct: float, odds: float):
        implied = american_to_implied(odds) * 100
        return (true_prob_pct - implied), implied

    def _std_norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def get_sport_sigmas(sport: str):
        if sport == "MLB": return 3.5, 3.0
        if sport == "NFL": return 10.0, 9.0
        if sport == "NCAA Football": return 12.0, 10.0
        if sport == "NBA": return 15.0, 12.0
        if sport == "NCAA Basketball": return 18.0, 14.0
        return 12.0, 10.0

    def suggested_volatility(sport: str) -> float:
        mapping = {"NFL": 10.0, "NCAA Football": 12.0, "NBA": 12.0, "NCAA Basketball": 15.0, "MLB": 8.0}
        return mapping.get(sport, 10.0)

    def project_scores_base(H_pf: float, H_pa: float, A_pf: float, A_pa: float):
        return (H_pf + A_pa) / 2.0, (A_pf + H_pa) / 2.0

    def tier_label(ev):
        if ev >= 20: return "🟢 Elite"
        if ev >= 10: return "🟡 Strong"
        if ev >= 0: return "🟠 Moderate"
        return "🔴 Risky"

    # ----------------- UI -----------------
    sport = st.selectbox("Select Sport", ["MLB", "NFL", "NBA", "NCAA Football", "NCAA Basketball"])

    col_inputs, col_results = st.columns([1,2])
    with col_inputs:
        with st.form("inputs_form_ats"):
            n1, n2 = st.columns(2)
            with n1: st.session_state.home = st.text_input("Home Team", value=st.session_state.home)
            with n2: st.session_state.away = st.text_input("Away Team", value=st.session_state.away)

            h_col, a_col = st.columns(2)
            with h_col:
                st.session_state.home_pf = st.number_input("Home: Avg Scored", step=0.01, format="%.2f", value=float(st.session_state.home_pf))
                st.session_state.home_pa = st.number_input("Home: Avg Allowed", step=0.01, format="%.2f", value=float(st.session_state.home_pa))
            with a_col:
                st.session_state.away_pf = st.number_input("Away: Avg Scored", step=0.01, format="%.2f", value=float(st.session_state.away_pf))
                st.session_state.away_pa = st.number_input("Away: Avg Allowed", step=0.01, format="%.2f", value=float(st.session_state.away_pa))

            s1, s2 = st.columns(2)
            with s1:
                st.session_state.spread_line_home = st.number_input("Home Spread (negative if favorite)", step=0.01, format="%.2f", value=float(st.session_state.spread_line_home))
            with s2:
                st.caption(f"Away Spread (auto): {(-st.session_state.spread_line_home):+.2f}")

            so1, so2 = st.columns(2)
            with so1:
                st.session_state.spread_odds_home = st.number_input("Home Spread Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.spread_odds_home))
            with so2:
                st.session_state.spread_odds_away = st.number_input("Away Spread Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.spread_odds_away))

            t_row1, t_row2 = st.columns(2)
            with t_row1:
                st.session_state.total_line = st.number_input("Total Line", step=0.01, format="%.2f", value=float(st.session_state.total_line))
                st.session_state.over_odds = st.number_input("Over Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.over_odds))
            with t_row2:
                st.session_state.stake = st.number_input("Stake ($)", min_value=0.0, step=1.0, format="%.2f", value=float(st.session_state.stake))
                st.session_state.under_odds = st.number_input("Under Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.under_odds))

            # 🆕 Moneyline inputs
            ml_row1, ml_row2 = st.columns(2)
            with ml_row1:
                st.session_state.ml_home = st.number_input("Home ML Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.ml_home))
            with ml_row2:
                st.session_state.ml_away = st.number_input("Away ML Odds (American)", step=1.0, format="%.0f", value=float(st.session_state.ml_away))

            # ⚙️ Advanced Adjustments
            with st.expander("⚙️ Advanced adjustments (optional)", expanded=False):
                st.markdown("**Universal**")
                u1, u2, u3 = st.columns(3)
                with u1:
                    home_edge_pts = st.number_input("Home edge (pts)", value=0.0, step=0.25, format="%.2f")
                    form_H_pct = st.number_input("Home form (±% PF)", value=0.0, step=1.0, format="%.0f")
                    injury_H_pct = st.number_input("Home injuries (±% PF)", value=0.0, step=1.0, format="%.0f")
                with u2:
                    away_edge_pts = st.number_input("Away edge (pts)", value=0.0, step=0.25, format="%.2f")
                    form_A_pct = st.number_input("Away form (±% PF)", value=0.0, step=1.0, format="%.0f")
                    injury_A_pct = st.number_input("Away injuries (±% PF)", value=0.0, step=1.0, format="%.0f")
                with u3:
                    auto_volatility = st.checkbox("Auto volatility by sport", value=True)
                    pace_pct_global = st.number_input("Global pace (±% total)", value=0.0, step=1.0, format="%.0f")
                    variance_pct_manual = st.number_input("Volatility tweak (±% SD)", value=0.0, step=5.0, format="%.0f")

                if sport in ["NFL", "NCAA Football"]:
                    st.markdown("**Football specifics**")
                    f1, f2, f3 = st.columns(3)
                    with f1:
                        plays_pct = st.number_input("Plays/pace (±% total)", value=0.0, step=1.0, format="%.0f")
                        to_margin_pts = st.number_input("Turnover margin (pts to Home)", value=0.0, step=0.5, format="%.2f")
                    with f2:
                        redzone_H_pct = st.number_input("Home red zone (±% PF)", value=0.0, step=1.0, format="%.0f")
                    with f3:
                        redzone_A_pct = st.number_input("Away red zone (±% PF)", value=0.0, step=1.0, format="%.0f")
                else:
                    plays_pct = redzone_H_pct = redzone_A_pct = to_margin_pts = 0.0

                if sport in ["NBA", "NCAA Basketball"]:
                    st.markdown("**Basketball specifics**")
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        pace_pct_hoops = st.number_input("Pace (±% total)", value=0.0, step=1.0, format="%.0f")
                        rest_H_pct = st.number_input("Home rest/fatigue (±% PF)", value=0.0, step=1.0, format="%.0f")
                    with b2:
                        ortg_H_pct = st.number_input("Home ORtg (±% PF)", value=0.0, step=1.0, format="%.0f")
                        rest_A_pct = st.number_input("Away rest/fatigue (±% PF)", value=0.0, step=1.0, format="%.0f")
                    with b3:
                        ortg_A_pct = st.number_input("Away ORtg (±% PF)", value=0.0, step=1.0, format="%.0f")
                        drtg_H_pct = st.number_input("Home DRtg (±% opp PF)", value=0.0, step=1.0, format="%.0f")
                    drtg_A_pct = st.number_input("Away DRtg (±% opp PF)", value=0.0, step=1.0, format="%.0f")
                else:
                    pace_pct_hoops = ortg_H_pct = ortg_A_pct = drtg_H_pct = drtg_A_pct = rest_H_pct = rest_A_pct = 0.0

                if sport == "MLB":
                    st.markdown("**MLB specifics**")
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        sp_H_runs = st.number_input("SP impact (Home, runs)", value=0.0, step=0.1, format="%.1f")
                        bullpen_H_runs = st.number_input("Bullpen (Home, runs)", value=0.0, step=0.1, format="%.1f")
                    with m2:
                        sp_A_runs = st.number_input("SP impact (Away, runs)", value=0.0, step=0.1, format="%.1f")
                        bullpen_A_runs = st.number_input("Bullpen (Away, runs)", value=0.0, step=0.1, format="%.1f")
                    with m3:
                        park_total_pct = st.number_input("Park factor (±% total)", value=0.0, step=1.0, format="%.0f")
                        weather_total_pct = st.number_input("Weather (±% total)", value=0.0, step=1.0, format="%.0f")
                else:
                    sp_H_runs = sp_A_runs = bullpen_H_runs = bullpen_A_runs = 0.0
                    park_total_pct = weather_total_pct = 0.0

            # 🔮 Run + ♻️ Reset (keys to avoid conflicts)
            btn1, btn2 = st.columns(2)
            with btn1:
                run_projection = st.form_submit_button("🔮 Run Projection", key="run_projection_btn_v35")
            with btn2:
                reset_inputs = st.form_submit_button("♻️ Reset Inputs", key="reset_inputs_btn_v35")

            # Safe reset: only clear known inputs + results
            if reset_inputs:
                for key in ["home","away","home_pf","home_pa","away_pf","away_pa",
                            "spread_line_home","spread_odds_home","spread_odds_away",
                            "total_line","over_odds","under_odds","ml_home","ml_away",
                            "stake","results_df"]:
                    if key in ["home","away"]:
                        st.session_state[key] = ""
                    else:
                        st.session_state[key] = 0.0 if key != "results_df" else None
                st.success("Inputs reset.")
                st.stop()  # stop to avoid running results on same submit

    # ----------------- Results -----------------
    with col_results:
        if run_projection:
            S = st.session_state

            # ===== Base from averages =====
            home_pts, away_pts = project_scores_base(S.home_pf, S.home_pa, S.away_pf, S.away_pa)

            # ===== Universal additive adjustments =====
            home_pts += home_edge_pts
            away_pts += away_edge_pts

            # ===== Universal % adjustments =====
            home_pts *= (1 + form_H_pct/100.0) * (1 + injury_H_pct/100.0)
            away_pts *= (1 + form_A_pct/100.0) * (1 + injury_A_pct/100.0)

            # ===== Football specifics =====
            if sport in ["NFL", "NCAA Football"]:
                home_pts += to_margin_pts/2.0
                away_pts -= to_margin_pts/2.0
                home_pts *= (1 + redzone_H_pct/100.0)
                away_pts *= (1 + redzone_A_pct/100.0)
                scale = 1 + plays_pct/100.0
                home_pts *= scale; away_pts *= scale

            # ===== Basketball specifics =====
            if sport in ["NBA", "NCAA Basketball"]:
                home_pts *= (1 + pace_pct_hoops/100.0) * (1 + ortg_H_pct/100.0) * (1 + rest_H_pct/100.0)
                away_pts *= (1 + ortg_A_pct/100.0) * (1 + rest_A_pct/100.0)
                home_pts *= (1 + drtg_A_pct/100.0)
                away_pts *= (1 + drtg_H_pct/100.0)

            # ===== MLB specifics =====
            if sport == "MLB":
                home_pts += sp_H_runs + bullpen_H_runs
                away_pts += sp_A_runs + bullpen_A_runs
                factor = (1 + park_total_pct/100.0) * (1 + weather_total_pct/100.0)
                home_pts *= factor; away_pts *= factor

            # ===== Global pace/volatility tweaks =====
            home_pts *= (1 + pace_pct_global/100.0)
            away_pts *= (1 + pace_pct_global/100.0)

            # ===== Final totals =====
            proj_total = home_pts + away_pts
            proj_margin = home_pts - away_pts

            auto_vol_used = suggested_volatility(sport) if auto_volatility else float(variance_pct_manual)
            sd_total, sd_margin = get_sport_sigmas(sport)
            sd_total *= (1 + auto_vol_used/100.0)
            sd_margin *= (1 + auto_vol_used/100.0)

            rows, inline_summaries = [], []

            # Spread probs
            if S.spread_line_home < 0:
                z_spread_home = (proj_margin - abs(S.spread_line_home)) / sd_margin
                true_home = _std_norm_cdf(z_spread_home) * 100.0
            else:
                z_spread_home = (proj_margin + abs(S.spread_line_home)) / sd_margin
                true_home = _std_norm_cdf(z_spread_home) * 100.0

            ev_home, impl_home = calculate_ev_pct(true_home, S.spread_odds_home)
            rows.append([f"{S.home} {S.spread_line_home:+.2f}", S.spread_odds_home,
                         f"{true_home:.2f}%", f"{impl_home:.2f}%", f"{ev_home:.2f}%"])
            inline_summaries.append((f"{S.home} {S.spread_line_home:+.2f}", true_home, impl_home, ev_home))

            true_away = 100.0 - true_home
            ev_away, impl_away = calculate_ev_pct(true_away, S.spread_odds_away)
            rows.append([f"{S.away} {(-S.spread_line_home):+.2f}", S.spread_odds_away,
                         f"{true_away:.2f}%", f"{impl_away:.2f}%", f"{ev_away:.2f}%"])
            inline_summaries.append((f"{S.away} {(-S.spread_line_home):+.2f}", true_away, impl_away, ev_away))

            # Totals
            z_total_over = (proj_total - S.total_line) / sd_total
            true_over = _std_norm_cdf(z_total_over) * 100.0
            ev_over, impl_over = calculate_ev_pct(true_over, S.over_odds)
            rows.append([f"Over {S.total_line:.2f}", S.over_odds,
                         f"{true_over:.2f}%", f"{impl_over:.2f}%", f"{ev_over:.2f}%"])
            inline_summaries.append((f"Over {S.total_line:.2f}", true_over, impl_over, ev_over))

            true_under = max(0.0, 100.0 - true_over)
            ev_under, impl_under = calculate_ev_pct(true_under, S.under_odds)
            rows.append([f"Under {S.total_line:.2f}", S.under_odds,
                         f"{true_under:.2f}%", f"{impl_under:.2f}%", f"{ev_under:.2f}%"])
            inline_summaries.append((f"Under {S.total_line:.2f}", true_under, impl_under, ev_under))

            # 🆕 Moneyline (win prob from margin distribution)
            true_home_ml = _std_norm_cdf(proj_margin / sd_margin) * 100.0
            ev_home_ml, impl_home_ml = calculate_ev_pct(true_home_ml, S.ml_home)
            rows.append([f"{S.home} ML", S.ml_home,
                         f"{true_home_ml:.2f}%", f"{impl_home_ml:.2f}%", f"{ev_home_ml:.2f}%"])
            inline_summaries.append((f"{S.home} ML", true_home_ml, impl_home_ml, ev_home_ml))

            true_away_ml = 100.0 - true_home_ml
            ev_away_ml, impl_away_ml = calculate_ev_pct(true_away_ml, S.ml_away)
            rows.append([f"{S.away} ML", S.ml_away,
                         f"{true_away_ml:.2f}%", f"{impl_away_ml:.2f}%", f"{ev_away_ml:.2f}%"])
            inline_summaries.append((f"{S.away} ML", true_away_ml, impl_away_ml, ev_away_ml))

            df = pd.DataFrame(rows, columns=["Bet Type", "Odds", "True %", "Implied %", "EV %"])
            st.session_state.results_df = df

            # Projections + Inline Summaries
            st.subheader("Projected Game Outcome")
            st.markdown(f"**Projected Home:** {home_pts:.2f} | **Projected Away:** {away_pts:.2f} | "
                        f"**Projected Total:** {proj_total:.2f} | **Projected Margin:** {proj_margin:.2f}")

            for bet, tp, ip, ev in inline_summaries:
                st.markdown(f"🔹 **{bet} → True {tp:.2f}% | Implied {ip:.2f}% | EV {ev:.2f}% | {tier_label(ev)}**")

        # Results Table + Details
        if st.session_state.get("results_df") is not None:
            df = st.session_state.results_df
            st.subheader("Bet Results")
            st.dataframe(df, use_container_width=True)

            if len(df) > 0:
                choice = st.selectbox("Select a bet:", options=list(df["Bet Type"]))
                selected = df[df["Bet Type"] == choice].iloc[0]

                st.subheader("Bet Details")
                st.markdown(f"Tier: {tier_label(float(selected['EV %'].replace('%','')))}")

                st.progress(float(selected['True %'].replace("%",""))/100.0, text=f"True Probability: {selected['True %']}")
                st.progress(float(selected['Implied %'].replace("%",""))/100.0, text=f"Implied Probability: {selected['Implied %']}")
                st.progress((float(selected['EV %'].replace("%",""))+100)/200, text=f"EV%: {selected['EV %']}")

                colA, colB = st.columns(2)
                with colA:
                    if st.button("💾 Save Straight Bet"):
                        st.success("Bet saved locally (straight bet).")
                with colB:
                    if st.button("🌍 Send to Parlay Slip"):
                        add_to_global_parlay("ATS/Totals", str(selected["Bet Type"]),
                                             float(selected["Odds"]),
                                             float(selected["True %"].replace("%",""))/100.0)
                        st.success("Added to Global Parlay")





# =====================================================
# ======== MODULE: MLB HIT SIMULATOR (Final) ==========
# =====================================================
def mlb_hits_app():
    st.header("⚾ Moneyball Phil: Hit Probability Simulator")

    if "saved_players" not in st.session_state:
        st.session_state.saved_players = []
    if "last_player_result" not in st.session_state:
        st.session_state.last_player_result = None
    if "id_counter" not in st.session_state:
        st.session_state.id_counter = 1

    def next_id():
        st.session_state.id_counter += 1
        return st.session_state.id_counter

    def _to_float(txt: str, *, allow_empty=False, default=0.0):
        s = str(txt).strip()
        if allow_empty and s == "":
            return default
        return float(s)

    def american_to_implied_from_text(txt: str) -> float:
        s = str(txt).strip()
        am = float(s.replace("+", ""))
        return abs(am) / (abs(am) + 100.0) if am < 0 else 100.0 / (am + 100.0)

    def calculate_weighted_avg(season, last7, split_, hand, pitcher):
        return round(0.2 * season + 0.3 * last7 + 0.2 * split_ + 0.2 * hand + 0.1 * pitcher, 4)

    def binomial_hit_probability(avg, ab=4):
        return 1 - (1 - avg) ** ab

    def classify_zone(prob):
        if prob >= 0.8:
            return "🟩 Elite"
        elif prob >= 0.7:
            return "🟨 Strong"
        elif prob >= 0.6:
            return "🟧 Moderate"
        else:
            return "🟥 Risky"

    st.subheader("📥 Player Stat Entry")
    with st.form("player_input"):
        name = st.text_input("Player Name", key="name")
        season_avg_txt  = st.text_input("Season AVG", placeholder="0.285", key="season_avg")
        last7_avg_txt   = st.text_input("Last 7 Days AVG", placeholder="0.310", key="last7_avg")
        split_avg_txt   = st.text_input("Split AVG (Home/Away)", placeholder="0.295", key="split_avg")
        hand_avg_txt    = st.text_input("AVG vs Handedness", placeholder="0.305", key="hand_avg")
        pitcher_avg_txt = st.text_input("AVG vs Pitcher", placeholder="0.270", key="pitcher_avg")

        ab_vs_pitcher = st.number_input("At-Bats vs Pitcher", min_value=0, step=1, key="ab_vs_pitcher")
        pitcher_hand = st.selectbox("Pitcher Handedness", ["Right", "Left"], key="pitcher_hand")

        pitcher_era_txt  = st.text_input("Pitcher ERA", placeholder="3.75", key="pitcher_era")
        pitcher_whip_txt = st.text_input("Pitcher WHIP", placeholder="1.20", key="pitcher_whip")
        pitcher_k9_txt   = st.text_input("Pitcher K/9", placeholder="9.3", key="pitcher_k9")

        batting_order = st.selectbox("Batting Order Position", list(range(1, 10)), key="batting_order")
        odds_txt = st.text_input("Sportsbook Odds (American)", placeholder="-115", key="odds_txt")
        submit = st.form_submit_button("Simulate Player")

    if submit:
        try:
            season_avg  = _to_float(season_avg_txt)
            last7_avg   = _to_float(last7_avg_txt)
            split_avg   = _to_float(split_avg_txt)
            hand_avg    = _to_float(hand_avg_txt)
            pitcher_avg = _to_float(pitcher_avg_txt)
            pitcher_era  = _to_float(pitcher_era_txt)
            pitcher_whip = _to_float(pitcher_whip_txt)
            pitcher_k9   = _to_float(pitcher_k9_txt)
            odds_implied = american_to_implied_from_text(odds_txt)
        except Exception as e:
            st.error(f"Input error: {e}")
        else:
            weighted_avg = calculate_weighted_avg(season_avg, last7_avg, split_avg, hand_avg, pitcher_avg)

            # Pitcher difficulty adjustments
            if pitcher_whip >= 1.40 or pitcher_era >= 5.00:
                adjustment = 0.020
                tier_pitcher = "🟢 Easy Pitcher"
            elif pitcher_whip < 1.10 or pitcher_era < 3.50:
                adjustment = -0.020
                tier_pitcher = "🔴 Tough Pitcher"
            else:
                adjustment = 0.000
                tier_pitcher = "🟨 Average Pitcher"

            adj_weighted_avg = max(0.0, min(1.0, weighted_avg + adjustment))

            ab_lookup = {1: 4.6, 2: 4.5, 3: 4.4, 4: 4.3, 5: 4.2, 6: 4.0, 7: 3.8, 8: 3.6, 9: 3.4}
            est_ab = ab_lookup.get(batting_order, 4.0)

            true_prob = binomial_hit_probability(adj_weighted_avg, ab=round(est_ab))
            implied_prob = odds_implied
            ev = (true_prob - implied_prob) * 100.0
            zone = classify_zone(true_prob)

            st.session_state.last_player_result = {
                "id": next_id(), "name": name or "Player",
                "true_prob": true_prob, "implied_prob": implied_prob,
                "ev": ev, "odds_txt": odds_txt.strip(),
                "batting_order": batting_order,
                "pitcher_hand": pitcher_hand,
                "ab_vs_pitcher": ab_vs_pitcher,
                "weighted_avg": weighted_avg,
                "adj_avg": adj_weighted_avg,
                "est_ab": est_ab,
                "pitcher_tier": tier_pitcher,
                "zone": zone
            }

    if st.session_state.last_player_result:
        r = st.session_state.last_player_result
        st.markdown("---")
        st.subheader("🧪 Latest Simulation (Preview)")

        c1, c2, c3 = st.columns(3)
        c1.metric("Adjusted AVG", f"{r['adj_avg']:.3f}")
        c2.metric("Est. AB", f"{r['est_ab']:.1f}")
        c3.metric("Pitcher Tier", r["pitcher_tier"])

        st.write(f"**Player:** {r['name']} | **Pitcher Hand:** {r['pitcher_hand']} | "
                 f"**Batting Order:** {r['batting_order']} | **AB vs Pitcher:** {r['ab_vs_pitcher']}")
        st.write(f"**Weighted AVG (pre-adj):** `{r['weighted_avg']}` → **Adjusted:** `{r['adj_avg']}`")
        st.write(f"**True Hit %:** {r['true_prob']*100:.1f}% | **Implied %:** {r['implied_prob']*100:.1f}% | "
                 f"**EV %:** {r['ev']:+.1f}% | **Odds:** {r['odds_txt']} | **Zone:** {r['zone']}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save to Board (Hit)"):
                st.session_state.saved_players.append(r)
                st.success("Saved to board.")
        with c2:
            if st.button("🌍 Add to Global Parlay (Hit)"):
                try:
                    odds = float(r["odds_txt"].replace("+",""))
                    add_to_global_parlay("MLB Hit", f"{r['name']} — 1+ Hit", odds, r["true_prob"])
                    st.success("Added to Global Parlay")
                except Exception:
                    st.warning("Couldn't parse odds for global parlay.")

    st.markdown("---")
    st.header("📌 Saved Player Board")
    if not st.session_state.saved_players:
        st.info("No saved players yet.")
    else:
        df = pd.DataFrame([
            {
                "Player": p["name"],
                "True %": f"{p['true_prob']*100:.2f}%",
                "Implied %": f"{p['implied_prob']*100:.2f}%",
                "EV %": f"{p['ev']:.1f}%",
                "Zone": p["zone"],
                "Odds": p["odds_txt"]
            }
            for p in st.session_state.saved_players
        ])
        st.dataframe(df, use_container_width=True)




# =====================================================
# ======= MODULE: Pitcher ER & K Simulator ============
# (Final: Explanations + True Prob Tiers + Delete Support + xERA + WHIP restored)
# =====================================================
def pitcher_app():
    st.header("👨‍⚾ Pitcher Earned Runs & Strikeouts Simulator")

    import math as _m

    # --- Init session state ---
    if "player_board" not in st.session_state: 
        st.session_state.player_board = []
    if "er_result" not in st.session_state: 
        st.session_state.er_result = None
    if "k_result" not in st.session_state: 
        st.session_state.k_result = None

    PA_PER_INNING = 4.3

    # --- Helpers ---
    def american_to_prob_local(odds: float) -> float:
        if odds >= 0: return 100.0 / (odds + 100.0)
        return abs(odds) / (abs(odds) + 100.0)

    def expected_bf(expected_ip, pa_per_inning=PA_PER_INNING):
        return max(1, int(round(expected_ip * pa_per_inning)))

    def parse_pct(s: str) -> float:
        x = float(str(s).strip())
        if x > 1.0: x = x / 100.0
        if x < 0: raise ValueError("Percentage cannot be negative.")
        return x

    # Poisson pmf/cdf
    def poisson_pmf(k: int, lam: float) -> float:
        try:
            return _m.exp(-lam) * (lam**k) / _m.factorial(k)
        except Exception:
            return 0.0

    def poisson_cdf(k: int, lam: float) -> float:
        return sum(poisson_pmf(i, lam) for i in range(0, k+1))

    # Binomial helpers
    def binom_pmf(n, k, p):
        if k < 0 or k > n: return 0.0
        return _m.exp(_m.lgamma(n+1) - _m.lgamma(k+1) - _m.lgamma(n-k+1) +
                      k*_m.log(max(p,1e-12)) + (n-k)*_m.log(max(1-p,1e-12)))

    def binom_cdf(n, k, p):
        return sum(binom_pmf(n, i, p) for i in range(0, k+1))

    def estimate_pK(pitcher_K_rate, opp_K_rate_vs_hand, park_factor=1.0, ump_factor=1.0, recent_factor=1.0):
        base = 0.6*pitcher_K_rate + 0.4*opp_K_rate_vs_hand
        adj = base * park_factor * ump_factor * recent_factor
        return max(0.10, min(0.45, adj))

    # --- Tiering (True Probability) ---
    def get_tier_prob(prob):
        if prob >= 80: return "🟢 Elite"
        if prob >= 65: return "🟡 Strong"
        if prob >= 50: return "🟠 Moderate"
        return "🔴 Risky"

    # --- UI Tabs ---
    tabs = st.tabs(["Earned Runs (U2.5)", "Strikeouts (K)"])

    # ---------------------------
    # Tab 1: Earned Runs
    # ---------------------------
    with tabs[0]:
        with st.form("er_form_glob"):
            c1, c2 = st.columns(2)
            with c1:
                er_pitcher = st.text_input("Pitcher Name", key="er_pitcher")
                er_era = st.text_input("ERA", key="er_era")
                er_total_ip = st.text_input("Total Innings Pitched", key="er_total_ip")
                er_games = st.number_input("Games Started", value=15, step=1, key="er_games")
                er_last3 = st.text_input("Last 3 Game IP (e.g. 5.2,6.1,5.0)", key="er_last3")
                er_xera = st.text_input("xERA (optional, overrides ERA)", key="er_xera")
                er_whip = st.text_input("WHIP (optional)", key="er_whip")
            with c2:
                er_oppops = st.text_input("Opponent OPS", key="er_oppops")
                er_lgops = st.text_input("League Average OPS", key="er_lgops")
                er_ballpark = st.selectbox("Ballpark Factor", ["Neutral","Pitcher-Friendly","Hitter-Friendly"], key="er_ballpark")
                er_under_odds = st.text_input("Sportsbook Odds (U2.5 ER)", key="er_under_odds")
            simulate_er = st.form_submit_button("▶ Simulate Player")
            reset_er = st.form_submit_button("🧹 Reset Form")

        if reset_er:
            st.session_state.er_result = None
            st.experimental_rerun()

        if simulate_er:
            try:
                pitcher_name   = er_pitcher or "Pitcher"
                era            = float(er_era)
                total_ip       = float(er_total_ip)
                games_started  = int(er_games)
                last_3_ip      = er_last3
                xera_txt       = er_xera.strip()
                whip_txt       = er_whip.strip()
                opponent_ops   = float(er_oppops)
                league_avg_ops = float(er_lgops)
                ballpark       = er_ballpark
                under_odds     = float(str(er_under_odds).replace("+",""))

                xera = float(xera_txt) if xera_txt else 0.0
                whip = float(whip_txt) if whip_txt else 0.0

                ip_values = [float(i.strip()) for i in last_3_ip.split(",") if i.strip()]
                trend_ip  = sum(ip_values) / len(ip_values)
            except Exception:
                st.error("Enter valid numerics for ERA/IP/OPS/xERA/WHIP and odds.")
                st.stop()

            base_ip = total_ip / max(1, games_started)
            park_adj = 0.2 if ballpark=="Pitcher-Friendly" else (-0.2 if ballpark=="Hitter-Friendly" else 0.0)
            expected_ip = round(((base_ip + trend_ip) / 2) + park_adj, 2)

            used_era = xera if xera > 0 else era
            adjusted_era = round(used_era * (opponent_ops / max(league_avg_ops, 1e-6)), 3)
            lam_er = round(adjusted_era * (expected_ip / 9), 3)  # 👈 mean earned runs

            # P(X ≤ 2 ER)
            true_prob = round(poisson_cdf(2, lam_er) * 100, 2)
            implied_prob = american_to_prob_local(under_odds) * 100
            ev = round(true_prob - implied_prob, 2)
            tier = get_tier_prob(true_prob)

            warning_msg = "⚠️ ERA may be misleading due to high WHIP. Consider xERA." if (whip > 1.45 and era < 3.20 and xera == 0) else ""

            st.session_state.er_result = {
                "pitcher": pitcher_name, "expected_ip": expected_ip,
                "proj_er": lam_er,  # 👈 store mean ER
                "true_prob": true_prob, "implied_prob": implied_prob,
                "odds": under_odds, "ev": ev, "tier": tier, "warning": warning_msg
            }

        er = st.session_state.er_result
        if er:
            st.subheader("📊 Earned Runs Projection Explanation")
            st.markdown(f"- **Expected IP:** {er['expected_ip']}")
            st.markdown(f"- **Projected Earned Runs (mean):** {er['proj_er']}")
            st.markdown(f"- **True Probability U2.5 ER:** {er['true_prob']}%")
            st.markdown(f"- **Implied Probability:** {er['implied_prob']:.2f}%")
            st.markdown(f"- **EV:** {er['ev']:.2f}%")
            st.markdown(f"- **Tier:** {er['tier']}")
            if er["warning"]: st.warning(er["warning"])
            st.success(f"{er['pitcher']} — U2.5 ER True {er['true_prob']:.2f}% | Odds {int(er['odds'])}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save to Board: U2.5 ER"):
                    st.session_state.player_board.append({
                        "Market":"ER","Description":f"{er['pitcher']} U2.5 ER",
                        "Odds":er["odds"],"True Prob":f"{er['true_prob']:.2f}%",
                        "EV":f"{er['ev']:.2f}%","Tier":er['tier']
                    })
                    st.success("Saved.")
            with c2:
                if st.button("🌍 Add to Global Parlay: U2.5 ER"):
                    add_to_global_parlay("Pitcher", f"{er['pitcher']} U2.5 ER", er["odds"], er["true_prob"]/100)
                    st.success("Added to Global Parlay")

    # ---------------------------
    # Tab 2: Strikeouts
    # ---------------------------
    with tabs[1]:
        with st.form("k_form_glob"):
            c1, c2, c3 = st.columns(3)
            with c1:
                k_pitcher_name = st.text_input("Pitcher Name (K)", key="k_pitcher_name")
                k_total_ip = st.text_input("Total Innings Pitched (season)", key="k_total_ip")
                k_games_started = st.number_input("Games Started (season)", value=17, step=1, key="k_games_started")
                k_last3 = st.text_input("Last 3 Game IP (e.g., 5.2,6.1,5.0)", key="k_last3")
            with c2:
                k_pct = st.text_input("Pitcher K% (24.3 or 0.243)", key="k_pct")
                k_opp_pct = st.text_input("Opponent K% vs Hand (23.0 or 0.23)", key="k_opp_pct")
                k_line = st.text_input("K Line (e.g., 5.5)", key="k_line")
            with c3:
                k_odds_over = st.text_input("Over Odds (American)", key="k_odds_over")
                k_odds_under = st.text_input("Under Odds (American)", key="k_odds_under")
                k_park = st.text_input("Park Factor (K)", value="1.00", key="k_park")
                k_ump = st.text_input("Ump Factor (K)", value="1.00", key="k_ump")
                k_recent = st.text_input("Recent Form Factor", value="1.00", key="k_recent")
            calc_k = st.form_submit_button("▶ Calculate Strikeouts")
            reset_k = st.form_submit_button("🧹 Reset Form")

        if reset_k:
            st.session_state.k_result = None
            st.experimental_rerun()

        if calc_k:
            try:
                k_pitcher = k_pitcher_name or "Pitcher"
                total_ip_k = float(k_total_ip); games_started_k = int(k_games_started)
                last_3_ip_k = k_last3
                pitcher_k_pct = parse_pct(k_pct); opp_k_vs_hand = parse_pct(k_opp_pct)
                k_line_v = float(k_line)
                odds_over_f = float(str(k_odds_over).replace("+",""))
                odds_under_f = float(str(k_odds_under).replace("+",""))
                park_factor = float(k_park); ump_factor = float(k_ump); recent_factor = float(k_recent)

                ip_values_k = [float(i.strip()) for i in last_3_ip_k.split(",") if i.strip()]
                trend_ip_k  = sum(ip_values_k) / len(ip_values_k)
            except Exception as e:
                st.error(f"Bad input: {e}")
                st.stop()

            base_ip_k = total_ip_k / max(1, games_started_k)
            expected_ip_k = round(((base_ip_k + trend_ip_k) / 2), 2)

            pK   = estimate_pK(pitcher_k_pct, opp_k_vs_hand, park_factor, ump_factor, recent_factor)
            n_bf = expected_bf(expected_ip_k)
            expected_ks = round(n_bf * pK, 2)

            k_under = int(_m.floor(k_line_v))
            k_over  = k_under + 1

            p_under = binom_cdf(n_bf, k_under, pK) * 100
            p_over  = (1.0 - binom_cdf(n_bf, k_over-1, pK)) * 100

            implied_over = american_to_prob_local(odds_over_f) * 100
            implied_under = american_to_prob_local(odds_under_f) * 100
            ev_over = round(p_over - implied_over, 2)
            ev_under = round(p_under - implied_under, 2)
            tier_over = get_tier_prob(p_over)
            tier_under = get_tier_prob(p_under)

            st.session_state.k_result = {
                "pitcher": k_pitcher, "k_line": k_line_v, "expected_ip": expected_ip_k,
                "n_bf": n_bf, "pK": round(pK,3), "expected_ks": expected_ks,
                "p_over": p_over, "p_under": p_under,
                "odds_over": odds_over_f, "odds_under": odds_under_f,
                "ev_over": ev_over, "ev_under": ev_under,
                "tier_over": tier_over, "tier_under": tier_under
            }

        kr = st.session_state.k_result
        if kr:
            st.subheader("📊 Strikeout Simulation Results")
            st.markdown(f"- **Expected IP:** {kr['expected_ip']} innings")
            st.markdown(f"- **Estimated Batters Faced (BF):** {kr['n_bf']} (PA/IP = 4.3)")
            st.markdown(f"- **Per-PA Strikeout Probability (pK):** {kr['pK']}")
            st.markdown(f"- **Expected Strikeouts (mean Ks):** {kr['expected_ks']}")
            st.markdown(f"- **K Line:** {kr['k_line']}")
            st.markdown(f"- **True Over %:** {kr['p_over']:.2f}% (Implied {american_to_prob_local(kr['odds_over'])*100:.2f}%) | EV {kr['ev_over']}% | {kr['tier_over']}")
            st.markdown(f"- **True Under %:** {kr['p_under']:.2f}% (Implied {american_to_prob_local(kr['odds_under'])*100:.2f}%) | EV {kr['ev_under']}% | {kr['tier_under']}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save to Board: Over K"):
                    st.session_state.player_board.append({
                        "Market":"K","Description":f"{kr['pitcher']} O{kr['k_line']} K",
                        "Odds":kr["odds_over"],"True Prob":f"{kr['p_over']:.2f}%",
                        "EV":f"{kr['ev_over']:.2f}%","Tier":kr['tier_over']
                    })
                    st.success("Saved.")
            with c2:
                if st.button("💾 Save to Board: Under K"):
                    st.session_state.player_board.append({
                        "Market":"K","Description":f"{kr['pitcher']} U{kr['k_line']} K",
                        "Odds":kr["odds_under"],"True Prob":f"{kr['p_under']:.2f}%",
                        "EV":f"{kr['ev_under']:.2f}%","Tier":kr['tier_under']
                    })
                    st.success("Saved.")

            d1, d2 = st.columns(2)
            with d1:
                if st.button("🌍 Add to Global Parlay: Over K"):
                    add_to_global_parlay("Pitcher", f"{kr['pitcher']} O{kr['k_line']} K", kr["odds_over"], kr["p_over"]/100)
                    st.success("Added Over leg.")
            with d2:
                if st.button("🌍 Add to Global Parlay: Under K"):
                    add_to_global_parlay("Pitcher", f"{kr['pitcher']} U{kr['k_line']} K", kr["odds_under"], kr["p_under"]/100)
                    st.success("Added Under leg.")

    # ================= Saved Pitcher Board =================
    st.markdown("---")
    st.header("📌 Saved Pitcher Board")
    if not st.session_state.player_board:
        st.info("No pitcher props saved yet.")
    else:
        for idx, p in enumerate(st.session_state.player_board):
            cols = st.columns([3, 2, 2, 2, 2, 1])
            cols[0].markdown(f"**{p.get('Market','—')}** — {p.get('Description','—')}")
            cols[1].write(f"Odds: {p.get('Odds','—')}")
            cols[2].write(f"True Prob: {p.get('True Prob','—')}")
            cols[3].write(f"EV: {p.get('EV','—')}")
            cols[4].write(f"Tier: {p.get('Tier','—')}")
            with cols[5]:
                if st.button("🗑️", key=f"del_pitch_{idx}"):
                    st.session_state.player_board.pop(idx)
                    st.rerun()







def nba_app():
    import math
    import pandas as pd
    import streamlit as st

    # ---------------- Header ----------------
    st.header("🏀 NBA Simulator")

    # ---------------- Session defaults ----------------
    st.session_state.setdefault("nba_board", [])
    st.session_state.setdefault("nba_saved_plays", [])
    st.session_state.setdefault("last_result_nba", None)

    # ---------------- Helpers ----------------
    def american_to_prob(odds_text):
        if not odds_text:
            return None
        try:
            o = int(str(odds_text).replace("+", ""))
            return abs(o) / (abs(o) + 100) if o < 0 else 100 / (o + 100)
        except Exception:
            return None

    def defense_tier(rank: int):
        if rank <= 5:   return ("Elite Defense", "🟥", 0.92, "-8%")
        if rank <= 10:  return ("Strong Defense", "🟧", 0.95, "-5%")
        if rank <= 20:  return ("Moderate Defense", "🟨", 1.00, "0%")
        if rank <= 25:  return ("Favorable Defense", "🟩", 1.05, "+5%")
        return ("Very Favorable Defense", "🟩", 1.08, "+8%")

    def readiness_badge(gp: int, w_new: float):
        if gp >= 10 and abs(w_new - 1.0) < 1e-9: return "🟢 Current-season stable"
        if w_new > 0.0:                           return "🟡 Blended (LY + Current)"
        return "🔴 Last-season only"

    def auto_blend_weight(gp: int, pre_g: int, pre_mpg: float) -> float:
        if gp <= 0:
            return 0.10 if (pre_g >= 3 and pre_mpg >= 15) else 0.0
        if 1 <= gp <= 3:  return 0.10
        if 4 <= gp <= 6:  return 0.20
        if 7 <= gp <= 9:  return 0.30
        return 1.0

    def apply_lm_scale(x: float, lm_profile: str, custom_pct: float) -> float:
        if lm_profile == "None":   return x
        if lm_profile == "Light":  return x * 0.95
        if lm_profile == "Heavy":  return x * 0.90
        return x * max(0.70, min(1.20, 1.0 + custom_pct / 100.0))

    def defense_logit_shift(rank: int) -> float:
        slope = 0.25 / 14.5
        return max(-0.25, min(0.25, slope * (rank - 15.5)))

    def true_prob_from_line(stat_type: str, projection: float, line: float, def_rank: int) -> float:
        if line <= 0: return 0.10
        scale = 6.5 if stat_type == "Points Only" else 8.0
        diff  = (projection - line) / scale
        logit = diff + defense_logit_shift(def_rank)
        p = 1.0 / (1.0 + math.exp(-logit))
        return float(max(0.10, min(0.90, round(p, 4))))

    def ev_symbol(ev):
        if ev is None: return ""
        if ev > 0.5:   return "🟩"
        if ev < -0.5:  return "🟥"
        return "🟨"

    # Reset inputs quickly
    def _reset_inputs():
        keys = [
            "nba_player","nba_team","nba_pos","nba_stat","nba_line",
            "nba_odds_over","nba_odds_under","nba_opp","nba_def_rank",
            "nba_pts","nba_reb","nba_ast","nba_recent","nba_alt_line","nba_alt_odds",
            "nba_usage","nba_gp","nba_pre_g","nba_pre_mpg","nba_lm","nba_lm_custom"
        ]
        for k in keys:
            if k in st.session_state: del st.session_state[k]
        st.success("Inputs cleared.")
        st.experimental_rerun()

    # ---------------- Inputs (compact for wide mode) ----------------
    r1c1, r1c2, r1c3, r1c4 = st.columns([1.2, 1.0, 1.0, 1.0])
    with r1c1:
        player_name = st.text_input("Player", key="nba_player")
        team        = st.text_input("Team", key="nba_team")
        position    = st.selectbox("Position", ["PG","SG","SF","PF","C"], key="nba_pos")
        opponent    = st.text_input("Opponent", key="nba_opp")
    with r1c2:
        stat_type       = st.radio("Stat Type", ["PRA","Points Only"], horizontal=True, key="nba_stat")
        sportsbook_line = st.number_input("Sportsbook Line (Pts or PRA)", min_value=0.0, step=0.5, key="nba_line")
        odds_over       = st.text_input("Over Odds", key="nba_odds_over")
        odds_under      = st.text_input("Under Odds", key="nba_odds_under")
    with r1c3:
        base_pts   = st.number_input("Model Base – Pts", min_value=0.0, step=0.1, key="nba_pts")
        base_reb   = st.number_input("Model Base – Reb", min_value=0.0, step=0.1, key="nba_reb")
        base_ast   = st.number_input("Model Base – Ast", min_value=0.0, step=0.1, key="nba_ast")
        recent_avg = st.number_input("Current-Season Avg (Pts/PRA)", min_value=0.0, step=0.1, key="nba_recent")
    with r1c4:
        defense_rank = st.number_input("DEF Rank vs Pos (1–30)", 1, 30, key="nba_def_rank")
        usage        = st.number_input("Usage % (est.)", 0.0, 100.0, step=0.1, key="nba_usage")
        alt_line     = st.number_input("Alt Line (optional)", min_value=0.0, step=0.5, key="nba_alt_line")
        alt_odds     = st.text_input("Alt Over Odds", key="nba_alt_odds")

    r2c1, r2c2, r2c3, r2c4 = st.columns([1.0, 0.9, 0.9, 1.2])
    with r2c1:
        gp_current = st.number_input("Games Played (this season)", min_value=0, step=1, key="nba_gp")
    with r2c2:
        pre_games  = st.number_input("Preseason Games", min_value=0, step=1, key="nba_pre_g")
    with r2c3:
        pre_mpg    = st.number_input("Preseason MPG", min_value=0.0, step=0.5, key="nba_pre_mpg")
    with r2c4:
        lm_profile    = st.selectbox("Load Management", ["None","Light","Heavy","Custom %"], key="nba_lm")
        custom_lm_pct = st.number_input("Custom Role/Minutes % (±)", value=0.0, step=1.0, key="nba_lm_custom")

    act1, act2 = st.columns([1,1])
    with act1:
        simulate_clicked = st.button("Simulate (NBA)", use_container_width=True)
    with act2:
        if st.button("Reset Inputs", use_container_width=True):
            _reset_inputs()

    # ---------------- Simulate ----------------
    if simulate_clicked:
        # Baselines
        if stat_type == "PRA":
            model_sum = base_pts + base_reb + base_ast
            last_season_base = model_sum
            current_estimate = recent_avg if recent_avg > 0 else model_sum
        else:
            last_season_base = base_pts
            current_estimate = recent_avg if recent_avg > 0 else base_pts

        # Blending & LM
        w_new = auto_blend_weight(int(gp_current), int(pre_games), float(pre_mpg))
        w_old = 1.0 - w_new
        blended = w_new * current_estimate + w_old * last_season_base
        blended = apply_lm_scale(blended, lm_profile, custom_lm_pct)

        # Defense tier & weighting
        tier_label, tier_emoji, def_factor, def_pct_txt = defense_tier(int(defense_rank))
        blended *= def_factor

        # Main line probs
        true_p = true_prob_from_line(stat_type, blended, sportsbook_line, int(defense_rank))
        imp_over = american_to_prob(odds_over)
        implied_for_ev = imp_over if imp_over is not None else None
        ev_pct = None if implied_for_ev is None else (true_p - implied_for_ev) * 100.0
        readiness = readiness_badge(int(gp_current), w_new)

        # ------- Compact result row (side-by-side) -------
        left, right = st.columns([0.62, 0.38])

        with left:
            st.markdown(
                f"### **{player_name or 'Player'} — "
                f"{('Points' if stat_type=='Points Only' else 'PRA')} Line: {sportsbook_line:g}**"
            )
            st.markdown(f"**Projected:** {blended:.2f}")
            st.markdown(f"**Matchup Difficulty:** {tier_emoji} **{tier_label}** (Rank {defense_rank}, {def_pct_txt})")
            if implied_for_ev is not None:
                st.markdown(f"**True Probability:** {true_p*100:.2f}% | **Implied Probability:** {implied_for_ev*100:.2f}%")
                st.markdown(f"**EV:** {ev_symbol(ev_pct)} {ev_pct:+.2f}%")
            else:
                st.markdown(f"**True Probability:** {true_p*100:.2f}% | **Implied Probability:** —")
                st.markdown("**EV:** — (enter Over odds)")
            st.caption(f"**Blend:** {int(w_old*100)}/{int(w_new*100)} (LY/Current) | **Readiness:** {readiness}")

        with right:
            st.markdown("#### EV Analysis")
            true_val = int(round(true_p * 100))
            st.write(f"True: {true_val:.0f}%")
            st.progress(min(true_val, 100))
            if implied_for_ev is not None:
                imp_val = int(round(implied_for_ev * 100))
                st.write(f"Implied: {imp_val:.0f}%")
                st.progress(min(imp_val, 100))
            else:
                st.write("Implied: —")
                st.progress(0)

        # ------- Alt line full analysis -------
        if alt_line and alt_line > 0:
            alt_true = true_prob_from_line(stat_type, blended, alt_line, int(defense_rank))
            alt_imp  = american_to_prob(alt_odds)
            alt_ev   = None if alt_imp is None else (alt_true - alt_imp) * 100.0
            st.markdown("---")
            st.markdown(f"**Alt Line {alt_line:g}:**  "
                        f"True {alt_true*100:.2f}%"
                        + (f" | Implied {alt_imp*100:.2f}% | EV {ev_symbol(alt_ev)} {alt_ev:+.2f}%" if alt_imp is not None else "")
                        + (f"  *(Odds {alt_odds})*" if alt_odds else ""))
            alt_c1, alt_c2 = st.columns([1,1])
            with alt_c1:
                st.write(f"True: {alt_true*100:.1f}%")
                st.progress(min(int(round(alt_true*100)), 100))
            with alt_c2:
                if alt_imp is not None:
                    st.write(f"Implied: {alt_imp*100:.1f}%")
                    st.progress(min(int(round(alt_imp*100)), 100))
                else:
                    st.write("Implied: —")
                    st.progress(0)

        # Row for boards & buttons
        row = {
            "Player": player_name or "Player",
            "Type": "Points" if stat_type == "Points Only" else "PRA",
            "Line": float(sportsbook_line),
            "Proj": round(blended, 2),
            "True %": f"{true_p*100:.2f}%",
            "TrueFrac": float(true_p),
            "OverOdds": odds_over,
            "UnderOdds": odds_under,
            "Opponent": opponent,
            "DefenseRank": int(defense_rank),
            "MatchupTier": f"{tier_emoji} {tier_label} ({def_pct_txt})",
            "Blend": f"{int(w_old*100)}/{int(w_new*100)}",
            "Readiness": readiness,
        }
        st.session_state.last_result_nba = row
        st.session_state.nba_board.append(row)

        # ------- 3 buttons (functional) -------
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💾 Save Play (NBA)", use_container_width=True):
                st.session_state.nba_saved_plays.append(row)
                st.success("✅ Saved play to NBA board.")
        with b2:
            if st.button("🌍 Add Over to Global Parlay (NBA)", use_container_width=True):
                try:
                    odds_val = int(str(row["OverOdds"]).replace("+",""))
                    try:
                        add_to_global_parlay("NBA",
                                             f"{row['Player']} Over {row['Line']} ({row['Type']})",
                                             odds_val, float(row["TrueFrac"]))
                        st.success("✅ Added Over leg to Global Parlay.")
                    except NameError:
                        st.warning("Global parlay function not found: add_to_global_parlay.")
                except Exception:
                    st.warning("Could not parse Over odds.")
        with b3:
            if st.button("🌍 Add Under to Global Parlay (NBA)", use_container_width=True):
                try:
                    odds_val = int(str(row["UnderOdds"]).replace("+",""))
                    try:
                        add_to_global_parlay("NBA",
                                             f"{row['Player']} Under {row['Line']} ({row['Type']})",
                                             odds_val, 1.0 - float(row["TrueFrac"]))
                        st.success("✅ Added Under leg to Global Parlay.")
                    except NameError:
                        st.warning("Global parlay function not found: add_to_global_parlay.")
                except Exception:
                    st.warning("Could not parse Under odds.")

    # ---------------- Board (collapsed) ----------------
    st.markdown("---")
    with st.expander("📈 Top Player Board (NBA)", expanded=False):
        if st.session_state.nba_board:
            st.dataframe(pd.DataFrame(st.session_state.nba_board), use_container_width=True)
        else:
            st.caption("No results yet — run a simulation to populate the board.")



# =========================
# Soccer EV Module (v3.2) with Global Parlay Button
# =========================

def soccer_app():
    import math
    from typing import Dict, Tuple
    import numpy as np
    import pandas as pd
    import streamlit as st

    # =========================
    # --------- Utils ---------
    # =========================

    def american_to_decimal(odds: float) -> float:
        """Convert American odds to Decimal odds."""
        if odds == 0:
            raise ValueError("American odds cannot be 0.")
        return 1.0 + (odds / 100.0) if odds > 0 else 1.0 + (100.0 / abs(odds))

    def parse_odds(odds_input: str) -> Tuple[float, float]:
        """
        Accept American like '-120' / '+110' or Decimal like '1.83'.
        Returns (implied_prob [0..1], decimal_odds). Raises on invalid input.
        """
        s = str(odds_input).strip()
        if not s:
            raise ValueError("Odds field is empty.")
        # American?
        if s.startswith(('+', '-')):
            am = float(s)
            dec = american_to_decimal(am)
            if dec <= 1.0 or not np.isfinite(dec):
                raise ValueError("Invalid American odds → decimal ≤ 1.")
            return 1.0 / dec, dec
        # Decimal
        dec = float(s)
        if dec <= 1.0 or not np.isfinite(dec):
            raise ValueError("Decimal odds must be > 1.0")
        return 1.0 / dec, dec

    def roi_per_dollar(true_p: float, dec_odds: float) -> float:
        """
        EV per $1 stake. If >0 you're +EV.
        EV_per_$ = true_p*(dec - 1) - (1 - true_p)
        """
        return true_p * (dec_odds - 1.0) - (1.0 - true_p)

    def pct(x: float) -> str:
        try:
            return f"{float(x)*100:.2f}%"
        except Exception:
            return "—"

    # ---- Tiers driven by True Probability (market-specific cutoffs) ----
    def tier_from_true(true_p: float, market_key: str) -> tuple[str, str]:
        if true_p is None:
            return "—", "⚪"
        thresholds = {
            "O1.5": [
                (0.75, "Elite",    "🟢"),
                (0.65, "Strong",   "🟡"),
                (0.55, "Moderate", "🟠"),
                (0.00, "Risky",    "🔴"),
            ],
            "O2.5": [
                (0.60, "Elite",    "🟢"),
                (0.50, "Strong",   "🟡"),
                (0.45, "Moderate", "🟠"),
                (0.00, "Risky",    "🔴"),
            ],
            "BTTS": [
                (0.58, "Elite",    "🟢"),
                (0.52, "Strong",   "🟡"),
                (0.47, "Moderate", "🟠"),
                (0.00, "Risky",    "🔴"),
            ],
        }
        for cutoff, name, icon in thresholds.get(market_key, thresholds["O2.5"]):
            if true_p >= cutoff:
                return name, icon
        return "Risky", "🔴"

    def tier_from_ev_simple(ev_roi: float):
        if ev_roi is None:
            return "—", "⚪"
        if ev_roi >= 0.20:   return "Elite", "🟩"
        if ev_roi >= 0.10:   return "Strong", "🟨"
        if ev_roi >= 0.05:   return "Moderate", "🟧"
        return "Risky", "🟥"

    def poisson_pmf(k: int, lam: float) -> float:
        if not np.isfinite(lam) or lam < 0:
            return np.nan
        try:
            return math.exp(-lam) * lam**k / math.factorial(k)
        except OverflowError:
            return np.nan

    def safe_goal_matrix(lam_home: float, lam_away: float, max_goals: int = 10) -> np.ndarray:
        for name, lam in [("λ_home", lam_home), ("λ_away", lam_away)]:
            if not np.isfinite(lam):
                raise ValueError(f"{name} is not finite. Check your inputs.")
            if lam < 0:
                raise ValueError(f"{name} is negative. xG/xGA must be ≥ 0.")
        lam_home = float(np.clip(lam_home, 0.0, 4.0))
        lam_away = float(np.clip(lam_away, 0.0, 4.0))
        h = np.array([poisson_pmf(i, lam_home) for i in range(max_goals + 1)], dtype=float)
        a = np.array([poisson_pmf(j, lam_away) for j in range(max_goals + 1)], dtype=float)
        if np.isnan(h).any() or np.isnan(a).any():
            raise ValueError("Poisson PMF produced NaN. Check your λ values and inputs.")
        M = np.outer(h, a)
        total = M.sum()
        if not np.isfinite(total) or total <= 0:
            raise ValueError("Distribution could not be normalized (sum ≤ 0).")
        return M / total

    def market_probs_from_matrix(M: np.ndarray) -> Dict[str, float]:
        if np.isnan(M).any():
            raise ValueError("Probability matrix contains NaN.")
        over15 = over25 = btts = 0.0
        H, A = M.shape
        for i in range(H):
            for j in range(A):
                p = M[i, j]
                if i + j >= 2: over15 += p
                if i + j >= 3: over25 += p
                if i >= 1 and j >= 1: btts += p
        return {"O1.5": over15, "O2.5": over25, "BTTS": btts}

    def is_num(x) -> bool:
        try:
            return np.isfinite(float(x))
        except:
            return False

    # =========================
    # ----- Session Setup -----
    # =========================

    def init_state():
        st.session_state.setdefault("matches", [])
        st.session_state.setdefault("saved_bets", [])
        st.session_state.setdefault("id_counter", 1)

    def next_id():
        st.session_state["id_counter"] += 1
        return st.session_state["id_counter"]

    # =========================
    # --------- App -----------
    # =========================

    st.subheader("⚽ Soccer EV App (v3.2)")
    init_state()

    # ---------------- Inputs ----------------
    st.subheader("➕ Add / Compute a Match (Season totals only)")

    if "reset_seed" not in st.session_state:
        st.session_state["reset_seed"] = 0

    def reset_inputs():
        st.session_state["reset_seed"] += 1
        st.rerun()

    seed = st.session_state["reset_seed"]

    def per_match(total_str, games_str):
        try:
            total = float(str(total_str).strip())
            games = float(str(games_str).strip())
            if games <= 0:
                return None
            return total / games
        except:
            return None

    # ---- HOME TEAM ----
    st.markdown("### Home Team — Season Totals")
    hcol1, hcol2, hcol3 = st.columns(3)
    with hcol1:
        home_team = st.text_input("Home Team", value="", key=f"home_team_name_{seed}")
    with hcol2:
        home_xg_total  = st.text_input("Home xG (SEASON TOTAL)",  value="", key=f"home_xg_total_{seed}")
        home_xga_total = st.text_input("Home xGA (SEASON TOTAL)", value="", key=f"home_xga_total_{seed}")
    with hcol3:
        home_season_matches = st.text_input("Matches Played (SEASON TOTAL)", value="", key=f"home_matches_total_{seed}")

    _home_xg_for_val = per_match(home_xg_total, home_season_matches)
    _home_xga_ag_val = per_match(home_xga_total, home_season_matches)
    home_xg_for = f"{_home_xg_for_val:.3f}" if _home_xg_for_val is not None else ""
    home_xga_ag = f"{_home_xga_ag_val:.3f}" if _home_xga_ag_val is not None else ""
    st.caption(f"Home per-match → xG={(_home_xg_for_val or 0):.3f}, xGA={(_home_xga_ag_val or 0):.3f}")

    # ---- AWAY TEAM ----
    st.markdown("### Away Team — Season Totals")
    acol1, acol2, acol3 = st.columns(3)
    with acol1:
        away_team = st.text_input("Away Team", value="", key=f"away_team_name_{seed}")
    with acol2:
        away_xg_total  = st.text_input("Away xG (SEASON TOTAL)",  value="", key=f"away_xg_total_{seed}")
        away_xga_total = st.text_input("Away xGA (SEASON TOTAL)", value="", key=f"away_xga_total_{seed}")
    with acol3:
        away_season_matches = st.text_input("Matches Played (SEASON TOTAL)", value="", key=f"away_matches_total_{seed}")

    _away_xg_for_val = per_match(away_xg_total, away_season_matches)
    _away_xga_ag_val = per_match(away_xga_total, away_season_matches)
    away_xg_for = f"{_away_xg_for_val:.3f}" if _away_xg_for_val is not None else ""
    away_xga_ag = f"{_away_xga_ag_val:.3f}" if _away_xga_ag_val is not None else ""
    st.caption(f"Away per-match → xG={(_away_xg_for_val or 0):.3f}, xGA={(_away_xga_ag_val or 0):.3f}")

    # ---- ODDS INPUTS ----
    st.markdown("### Odds (American or Decimal)")
    ocol1, ocol2, ocol3 = st.columns(3)
    with ocol1:
        odds_o15  = st.text_input("Over 1.5 Odds", value="", key=f"odds_o15_{seed}")
    with ocol2:
        odds_o25  = st.text_input("Over 2.5 Odds", value="", key=f"odds_o25_{seed}")
    with ocol3:
        odds_btts = st.text_input("BTTS Odds",     value="", key=f"odds_btts_{seed}")

    # ---- Actions ----
    btn_cols = st.columns([1,1,2])
    with btn_cols[0]:
        compute_only = st.button("Compute Only", key=f"btn_compute_only_{seed}")
    with btn_cols[1]:
        compute_and_save = st.button("Compute & Save Match", key=f"btn_compute_save_{seed}")
    with btn_cols[2]:
        if st.button("Reset Inputs", key=f"btn_reset_inputs_{seed}"):
            reset_inputs()

    # =========================
    # ------ Compute Core -----
    # =========================

    def compute_match(label: str,
                      home_xg_for_s: str, away_xga_s: str,
                      away_xg_for_s: str, home_xga_s: str,
                      odds_dict: Dict[str, str]):
        fields = {
            "Home xG For": home_xg_for_s, "Away xGA Against": away_xga_s,
            "Away xG For": away_xg_for_s, "Home xGA Against": home_xga_s
        }
        for name, val in fields.items():
            if not is_num(val):
                raise ValueError(f"{name} invalid: '{val}'")
            if float(val) < 0:
                raise ValueError(f"{name} cannot be negative.")

        hxf, axga, axf, hxga = float(home_xg_for_s), float(away_xga_s), float(away_xg_for_s), float(home_xga_s)
        DEF_FACTOR = 1.2
        lam_home = (hxf * axga) / DEF_FACTOR
        lam_away = (axf * hxga) / DEF_FACTOR

        M = safe_goal_matrix(lam_home, lam_away, max_goals=10)
        probs = market_probs_from_matrix(M)

        imp15, dec15 = parse_odds(odds_dict["O1.5"])
        imp25, dec25 = parse_odds(odds_dict["O2.5"])
        impBT, decBT = parse_odds(odds_dict["BTTS"])

        st.markdown(f"### Results for {label}")
        results = []
        markets = [
            ("O1.5", "Over 1.5", imp15, dec15, odds_dict["O1.5"]),
            ("O2.5", "Over 2.5", imp25, dec25, odds_dict["O2.5"]),
            ("BTTS", "BTTS",     impBT, decBT, odds_dict["BTTS"]),
        ]
        for key, label_mkt, imp, dec, odds_str in markets:
            true_p = probs[key]
            ev = roi_per_dollar(true_p, dec)
            tier, badge = tier_from_true(true_p, key)
            results.append({
                "key": key, "label": label_mkt, "true": true_p, "imp": imp,
                "ev": ev, "dec": dec, "odds_str": odds_str, "tier": tier, "badge": badge
            })
            st.write(f"{label_mkt}: True {pct(true_p)}, Implied {pct(imp)}, EV {pct(ev)} → **{tier}** {badge}")

        st.markdown("---")
        best_value = max(results, key=lambda r: r["ev"])
        if best_value["ev"] >= 0.05:
            st.success(f"Value Play: {best_value['label']} ({best_value['odds_str']}) • EV {pct(best_value['ev'])} • True {pct(best_value['true'])}")
        else:
            st.warning("No value play (all EV < 5%).")

        eligible_safe = [r for r in results if r['ev'] >= 0.05]
        if eligible_safe:
            best_safe = max(eligible_safe, key=lambda r: r["true"])
            st.info(f"Safe Play: {best_safe['label']} ({best_safe['odds_str']}) • EV {pct(best_safe['ev'])} • True {pct(best_safe['true'])}")
        else:
            st.info("No safe play.")

        odds_parsed = {
            "O1.5": {"imp": imp15, "dec": dec15, "str": odds_dict["O1.5"]},
            "O2.5": {"imp": imp25, "dec": dec25, "str": odds_dict["O2.5"]},
            "BTTS": {"imp": impBT, "dec": decBT, "str": odds_dict["BTTS"]},
        }
        return probs, odds_parsed, (lam_home, lam_away)

    odds_dict = {"O1.5": odds_o15, "O2.5": odds_o25, "BTTS": odds_btts}
    label = f"{home_team} vs {away_team}"

    if compute_only or compute_and_save:
        try:
            probs, odds_parsed, (lam_h, lam_a) = compute_match(
                label, home_xg_for, away_xga_ag, away_xg_for, home_xga_ag, odds_dict
            )
            if compute_and_save:
                rec = {
                    "id": next_id(),
                    "label": label,
                    "lambda_home": lam_h,
                    "lambda_away": lam_a,
                    "probs": probs,
                    "odds": {
                        "O1.5": odds_parsed["O1.5"],
                        "O2.5": odds_parsed["O2.5"],
                        "BTTS": odds_parsed["BTTS"],
                    }
                }
                st.session_state["matches"].append(rec)
                st.success("Match saved.")
        except Exception as e:
            st.error(f"⚠️ Compute error: {e}")

    # ---------------- Saved Matches ----------------
    st.markdown("---")
    st.subheader("📚 Saved Matches")
    if not st.session_state["matches"]:
        st.info("No matches saved yet.")
    else:
        for match in list(st.session_state["matches"]):
            st.markdown(f"#### {match['label']}")
            lam_cols = st.columns([1,1,1,1,1.2])
            lam_cols[0].metric("λ Home",  f"{match['lambda_home']:.2f}")
            lam_cols[1].metric("λ Away",  f"{match['lambda_away']:.2f}")
            lam_cols[2].metric("Total λ", f"{match['lambda_home']+match['lambda_away']:.2f}")
            with lam_cols[4]:
                if st.button("🗑️ Delete Match", key=f"btn_del_match_{match['id']}"):
                    st.session_state["matches"] = [m for m in st.session_state["matches"] if m["id"] != match["id"]]
                    st.session_state["saved_bets"] = [b for b in st.session_state.get("saved_bets", []) if b.get("match_id") != match["id"]]
                    st.rerun()

            head = st.columns([1.2,1,1,1,1,1,1])
            head[0].write("**Market**")
            head[1].write("**True %**")
            head[2].write("**Implied %**")
            head[3].write("**Edge**")
            head[4].write("**EV %**")
            head[5].write("**Tier**")
            head[6].write("**Save**")
            for mkt_key, mkt_label in [("O1.5","Over 1.5"),("O2.5","Over 2.5"),("BTTS","BTTS")]:
                true_p = match["probs"][mkt_key]
                imp = match["odds"][mkt_key]["imp"]
                dec = match["odds"][mkt_key]["dec"]
                ev = roi_per_dollar(true_p, dec)
                edge_pp = (true_p - imp)
                tier, badge = tier_from_true(true_p, mkt_key)
                row = st.columns([1.2,1,1,1,1,1,1])
                row[0].write(mkt_label)
                row[1].write(pct(true_p))
                row[2].write(pct(imp))
                row[3].write(f"{edge_pp*100:.2f} pp")
                row[4].write(pct(ev))
                row[5].write(f"{tier} {badge}")
                if row[6].button(f"💾 Save {mkt_label}", key=f"save_{match['id']}_{mkt_key}"):
                    bet_id = next_id()
                    st.session_state["saved_bets"].append({
                        "id": bet_id,
                        "match_id": match["id"],
                        "match_label": match["label"],
                        "market": mkt_key,
                        "market_label": mkt_label,
                        "true_p": true_p,
                        "implied_p": imp,
                        "dec": dec,
                        "odds_str": match["odds"][mkt_key]["str"],
                    })
                    st.success(f"Saved bet: {match['label']} — {mkt_label}")

    # ---------------- Saved Bets ----------------
    st.markdown("---")
    st.subheader("💾 Saved Bets")
    bets = st.session_state.get("saved_bets", [])
    if not bets:
        st.info("No saved bets yet.")
    else:
        h = st.columns([0.6,2.8,1,1,1,1,1.2,0.8])
        h[0].write("**Bet ID**")
        h[1].write("**Match | Market**")
        h[2].write("**True %**")
        h[3].write("**Implied %**")
        h[4].write("**EV %**")
        h[5].write("**Odds**")
        h[6].write("**Tier**")
        h[7].write("**Delete**")
        for b in list(bets):
            true_p, dec = float(b["true_p"]), float(b["dec"])
            implied_p = float(b.get("implied_p", 1.0/dec if dec>0 else 0.0))
            ev = roi_per_dollar(true_p, dec)
            r = st.columns([0.6,2.8,1,1,1,1,1.2,0.8])
            r[0].write(str(b["id"]))
            r[1].write(f"{b['match_label']} | {b['market_label']}")
            r[2].write(pct(true_p))
            r[3].write(pct(implied_p))
            r[4].write(pct(ev))
            r[5].write(b["odds_str"])
            tname, ticon = tier_from_true(true_p, b["market"])
            r[6].write(f"{tname} {ticon}")
            with r[7]:
                if st.button("🗑️", key=f"del_bet_{b['id']}"):
                    st.session_state["saved_bets"] = [x for x in bets if x["id"] != b["id"]]
                    st.rerun()

        # 🌍 Global Parlay Button
        if st.button("🌍 Add ALL Saved Bets to Global Parlay", key="btn_add_all_soccer_global_parlay"):
            for b in st.session_state["saved_bets"]:
                add_to_global_parlay("Soccer", f"{b['match_label']} — {b['market_label']}", float(b["dec"]), float(b["true_p"]))
            st.success("✅ All saved soccer bets added to Global Parlay!")

    # ---------------- N-Leg Parlay Builder ----------------
    st.markdown("---")
    st.subheader("🎛️ Parlay Builder (any number of legs)")
    saved = st.session_state.get("saved_bets", [])
    if len(saved) < 2:
        st.info("Save at least two bets.")
    else:
        def bet_label(b): return f"{b['id']} | {b['match_label']} | {b['market_label']} ({b['odds_str']})"
        legs = st.multiselect("Choose parlay legs (2+):", options=saved, format_func=bet_label, key="parlay_legs_sel")
        if len(legs) >= 2:
            from math import prod
            p_trues = [float(b["true_p"]) for b in legs]
            decs = [float(b["dec"]) for b in legs]
            true_parlay, fallback_dec = prod(p_trues), prod(decs)
            book_parlay_odds_str = st.text_input("Sportsbook Parlay Odds", value="", key="parlay_book_odds_any")
            dec_parlay, imp_parlay, using_book_price = None, None, False
            if book_parlay_odds_str.strip():
                try:
                    imp_parlay, dec_parlay = parse_odds(book_parlay_odds_str.strip())
                    using_book_price = True
                except: st.warning("Could not parse book odds.")
            if dec_parlay is None:
                dec_parlay = fallback_dec
                imp_parlay = 1.0 / dec_parlay if dec_parlay > 0 else 0.0
            ev_parlay = roi_per_dollar(true_parlay, dec_parlay)
            p_tier, p_badge = tier_from_ev_simple(ev_parlay)
            g1,g2,g3,g4,g5,g6 = st.columns(6)
            g1.metric("# Legs", f"{len(legs)}")
            g2.metric("Parlay Decimal", f"{dec_parlay:.3f}")
            g3.metric("True %", f"{true_parlay*100:.2f}%")
            g4.metric("Implied %", f"{imp_parlay*100:.2f}%")
            g5.metric("Edge", f"{(true_parlay-imp_parlay)*100:.2f} pp")
            g6.metric("EV %", f"{ev_parlay*100:.2f}%")
            st.write(f"Parlay Tier: {p_tier} {p_badge}")







# =====================================================
# ================== Router / Layout ==================
# =====================================================
with st.sidebar:
    st.header("Navigation")
    page = st.selectbox("Choose App", [
        "NFL Prop Simulator",
        "ATS & Totals",
        "MLB — Hit Simulator",
        "Pitcher ER & K",
        "NBA Simulator",
        "Soccer EV",
        "🌍 Global Parlay Builder"
    ])

if page == "NFL Prop Simulator":
    nfl_app()
elif page == "ATS & Totals":
    ats_totals_app()
elif page == "MLB — Hit Simulator":
    mlb_hits_app()
elif page == "Pitcher ER & K":
    pitcher_app()
elif page == "NBA Simulator":
    nba_app()
elif page == "Soccer EV":
    soccer_app()
else:
    render_global_parlay_builder()

# Close content div (after banner spacing)
st.markdown('</div>', unsafe_allow_html=True)

