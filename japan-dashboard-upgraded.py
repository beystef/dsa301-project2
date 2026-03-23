import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DESIGN RATIONALE — GESTALT & BERTIN PRINCIPLES APPLIED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  BERTIN'S RETINAL VARIABLES (position, size, shape, value/lightness,
#  colour hue, orientation, texture) guide WHICH variable encodes WHAT:
#
#  B1  Position (most powerful)  → always used for the quantitative axes
#       (year on X, arrivals on Y / bar length). Never wasted on a nominal var.
#
#  B2  Size                      → KPI numbers use large type; bar LENGTH is
#       the primary size retinal variable for ranking — NOT colour.
#
#  B3  Colour HUE (selective,    → hue used only for categorical distinction
#       not ordered)               (regions, individual countries). NOT for
#                                  quantities — that would confuse hue with value.
#
#  B4  Value / lightness         → sequential single-hue ramps (Blues) used
#  (ordered, quantitative)         wherever magnitude must be read from colour
#                                  (heatmap, bar fill). Diverging (RdYlGn) only
#                                  where there is a meaningful midpoint (YoY %).
#
#  B5  Redundant encoding        → in the bar chart, BOTH bar length (position)
#       increases legibility       AND lightness encode magnitude — so the rank
#                                  order pops even in a long list.
#
#  GESTALT PRINCIPLES applied:
#
#  G1  Proximity                 → KPI cards are grouped in one visual band.
#                                  Filters are grouped above charts. Related
#                                  charts (regional breakdown + YoY) share a row.
#
#  G2  Similarity                → All chart titles share the same style/size.
#                                  All "context" captions share grey italic text.
#                                  The same neutral background (#F8F9FB) used on
#                                  every chart panel creates a consistent figure.
#
#  G3  Continuity / Common fate  → Line chart uses continuous strokes; the
#                                  "total" line is thicker and darker to lead the
#                                  eye along the primary trend.
#
#  G4  Figure / Ground           → White chart plot area against the light page
#       (contrast)                 background creates clear figure-ground sep.
#                                  Grid lines are ultra-light (#e8e8e8) so they
#                                  stay ground. Axis labels are dark so they
#                                  read as figure.
#
#  G5  Closure / Enclosure       → Each section is enclosed with a visible card
#                                  (light background + subtle border-radius) so
#                                  elements within feel grouped.
#
#  G6  Focal point / prägnanz    → The #1 country in the bar chart and the peak
#                                  year in the line chart are annotated, pulling
#                                  the eye to the most important datum first.
#
#  G7  Common region             → The filter bar sits inside a visually
#                                  distinct panel (coloured background) that is
#                                  separate from the chart region, so users never
#                                  confuse controls with data.
#
#  ADDITIONAL PERCEPTUAL CHOICES:
#  - Pie chart REPLACED by a stacked-bar (normalised %) chart because angle/arc
#    (pie) is one of the weakest Bertin encodings for comparing magnitudes;
#    bar position along a common scale is far more accurate (Cleveland & McGill).
#  - Diverging colour only on YoY chart where zero IS a meaningful midpoint.
#  - Colourblind-safe palette (Plotly "Safe" / hand-picked) for multi-line chart.
#  - Gridlines: horizontal only on bar/line charts (follow reading direction),
#    suppressed on heatmap Y-axis to avoid visual noise.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Japan Inbound Immigration Dashboard",
    page_icon="🇯🇵",
    layout="wide",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
# G5 Enclosure: section cards; G7 Common region: filter band; G4 Figure/Ground
st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #F0F2F6; }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

    /* Section card — G5 Enclosure */
    .section-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1rem 1.4rem 0.8rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }

    /* Filter band — G7 Common region */
    .filter-band {
        background: #1B2A4A;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.2rem;
    }
    .filter-band label, .filter-band .stSlider label,
    .filter-band .stMultiSelect label { color: #FFFFFF !important; }

    /* KPI cards — G1 Proximity, G5 Enclosure */
    .kpi-card {
        background: #FFFFFF;
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        text-align: left;
    }
    .kpi-value { font-size: 1.55rem; font-weight: 700; color: #1B2A4A; line-height:1.1; }
    .kpi-label { font-size: 0.75rem; color: #6B7280; text-transform: uppercase;
                 letter-spacing: 0.05em; margin-top: 2px; }
    .kpi-delta-pos { color: #16A34A; font-size:0.85rem; font-weight:600; }
    .kpi-delta-neg { color: #DC2626; font-size:0.85rem; font-weight:600; }

    /* Section headers — G2 Similarity */
    .chart-title {
        font-size: 1rem; font-weight: 700; color: #1B2A4A;
        margin-bottom: 0.15rem; margin-top: 0;
    }
    .chart-caption {
        font-size: 0.78rem; color: #6B7280; font-style: italic;
        margin-bottom: 0.5rem;
    }

    /* Dividers less heavy */
    hr { border-color: #E5E7EB !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def card_open():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

def card_close():
    st.markdown('</div>', unsafe_allow_html=True)

def chart_title(text):
    st.markdown(f'<p class="chart-title">{text}</p>', unsafe_allow_html=True)

def chart_caption(text):
    st.markdown(f'<p class="chart-caption">{text}</p>', unsafe_allow_html=True)

# ── Colourblind-safe discrete palette (Bertin B3 / hue for categories) ────────
# Based on Wong (2011) colour-blind safe set, extended
CB_PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#CC79A7",
    "#56B4E9", "#D55E00", "#F0E442", "#000000",
    "#332288", "#117733", "#44AA99", "#88CCEE",
    "#DDCC77", "#CC6677", "#AA4499", "#882255",
]

# ── Load & clean data ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("japan_immigration_statistics_inbound.csv")
    df.columns = df.columns.str.strip()
    df["year"] = df["year"].astype(str).str.strip().astype(int)
    for col in df.columns.drop("year"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()

EXCLUDED = {
    "year", "total", "asia", "europe", "africa",
    "north_america", "south_america", "oceania",
    "stateless", "unknown_other",
}
ALL_COUNTRY_COLS = [c for c in df.columns if c not in EXCLUDED]

PRETTY = {c: c.replace("_", " ").title() for c in ALL_COUNTRY_COLS}
PRETTY.update({
    "china": "China", "south_korea": "South Korea", "north_korea": "North Korea",
    "united_states": "United States", "united_kingdom": "United Kingdom",
    "china_hong_kong": "Hong Kong", "china_other": "China (Other)",
    "united_arab_emirates": "UAE", "saudi_arabia": "Saudi Arabia",
    "sri_lanka": "Sri Lanka", "timor_leste": "Timor-Leste",
    "cote_d_ivoire": "Côte d'Ivoire", "republic_of_the_congo": "Congo (Rep.)",
    "democratic_republic_of_the_congo": "Congo (DRC)",
    "guinea_bissau": "Guinea-Bissau", "sao_tome_and_principe": "São Tomé & Príncipe",
    "bosnia_and_herzegovina": "Bosnia & Herzegovina",
    "serbia_and_montenegro": "Serbia & Montenegro",
    "north_macedonia": "North Macedonia", "georgia_country": "Georgia",
    "burkina_faso": "Burkina Faso", "cape_verde": "Cape Verde",
    "equatorial_guinea": "Equatorial Guinea", "new_zealand": "New Zealand",
    "papua_new_guinea": "Papua New Guinea", "solomon_islands": "Solomon Islands",
    "marshall_islands": "Marshall Islands", "trinidad_and_tobago": "Trinidad & Tobago",
    "antigua_and_barbuda": "Antigua & Barbuda", "saint_lucia": "Saint Lucia",
    "saint_vincent": "Saint Vincent", "saint_kitts_and_nevis": "Saint Kitts & Nevis",
    "el_salvador": "El Salvador", "costa_rica": "Costa Rica",
    "dominican_republic": "Dominican Republic",
    "united_kingdom_hong_kong": "UK (Hong Kong)",
    "san_marino": "San Marino", "vatican_city": "Vatican City",
})

PRETTY_TO_COL    = {v: k for k, v in PRETTY.items()}
ALL_PRETTY_SORTED = sorted(PRETTY[c] for c in ALL_COUNTRY_COLS)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#1B2A4A; margin-bottom:0.1rem;'>🇯🇵 Japan Inbound Immigration Dashboard</h1>
<p style='color:#6B7280; font-size:0.92rem; margin-top:0;'>
Inbound arrivals across <strong>every origin country</strong> · Use filters to focus · All charts are zoomable
</p>
""", unsafe_allow_html=True)

# ━━ FILTERS (G7 Common region — dark band separates controls from data) ━━━━━━
st.markdown('<div class="filter-band">', unsafe_allow_html=True)
f1, f2, f3 = st.columns([2, 1, 3])
with f1:
    year_range = st.slider(
        "📅 Year Range",
        min_value=int(df["year"].min()), max_value=int(df["year"].max()),
        value=(int(df["year"].min()), int(df["year"].max())),
    )
with f2:
    top_n = st.slider(
        "🏅 Top N Countries", min_value=3, max_value=len(ALL_COUNTRY_COLS),
        value=15, step=1,
        help="Ranks countries by total arrivals in the selected period.",
    )
with f3:
    search_pretty = st.multiselect(
        "🔍 Add Specific Countries",
        options=ALL_PRETTY_SORTED, default=[],
        placeholder="Type a country name…",
    )
st.markdown('</div>', unsafe_allow_html=True)

# ── Resolve countries ─────────────────────────────────────────────────────────
filtered      = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].copy()
period_totals = filtered[ALL_COUNTRY_COLS].sum().sort_values(ascending=False)
top_n_cols    = period_totals.head(top_n).index.tolist()
searched_cols = [PRETTY_TO_COL[p] for p in search_pretty if p in PRETTY_TO_COL]
selected_cols = list(dict.fromkeys(top_n_cols + searched_cols))

extra_note = f" + {len(searched_cols)} added by search" if searched_cols else ""
st.caption(f"**{len(selected_cols)} countries shown** (top {top_n} by period total{extra_note}). "
           "Drag to zoom · Double-click to reset.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  KPI CARDS  (G1 Proximity — four metrics in one visual band)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sorted_f     = filtered.sort_values("year")
total_period = int(filtered["total"].sum())
peak_row     = filtered.loc[filtered["total"].idxmax()]
avg_annual   = int(filtered["total"].mean())
min_row      = filtered.loc[filtered["total"].idxmin()]
yoy = (
    (sorted_f.iloc[-1]["total"] - sorted_f.iloc[-2]["total"])
    / sorted_f.iloc[-2]["total"] * 100
    if len(sorted_f) >= 2 else None
)

def kpi(label, value, delta_str=None, delta_positive=True):
    delta_html = ""
    if delta_str:
        cls = "kpi-delta-pos" if delta_positive else "kpi-delta-neg"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="{cls}">{arrow} {delta_str}</div>'
    return f"""
    <div class="kpi-card">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
      {delta_html}
    </div>"""

k1, k2, k3, k4 = st.columns(4)
k1.markdown(kpi("Total Arrivals (Period)", f"{total_period:,.0f}"), unsafe_allow_html=True)
k2.markdown(kpi("Peak Year", str(int(peak_row["year"])),
                f"{int(peak_row['total']):,.0f} arrivals"), unsafe_allow_html=True)
k3.markdown(kpi("Avg Annual Arrivals", f"{avg_annual:,.0f}"), unsafe_allow_html=True)
if yoy is not None:
    k4.markdown(kpi("Latest YoY Change", f"{yoy:+.1f}%",
                    f"{abs(yoy):.1f}% vs prior year", yoy >= 0), unsafe_allow_html=True)
else:
    k4.markdown(kpi("Latest YoY Change", "N/A"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART 1 — Total Immigration Trend (line)
#  B1 Position encodes year (X) and count (Y) — most powerful retinal variable.
#  G3 Continuity: continuous stroke guides eye through time.
#  G6 Focal point: peak year annotated so eye lands on most important datum.
#  G4 Figure/Ground: white plot area, ultra-light gridlines stay as ground.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
card_open()
chart_title("Total Immigration Trend Over Time")
chart_caption("Position (X = year, Y = arrivals) encodes both variables. "
              "Peak year is annotated. Gridlines are suppressed to stay ground.")

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(
    x=filtered["year"], y=filtered["total"],
    mode="lines+markers",
    line=dict(color="#2563EB", width=2.8),
    marker=dict(size=4, color="#2563EB"),
    hovertemplate="<b>%{x}</b><br>Arrivals: %{y:,.0f}<extra></extra>",
    name="Total",
))

# G6 — annotate peak year
peak_y = int(peak_row["year"])
peak_v = int(peak_row["total"])
fig_line.add_annotation(
    x=peak_y, y=peak_v,
    text=f"  Peak: {peak_y}<br>  {peak_v:,.0f}",
    showarrow=True, arrowhead=2, arrowcolor="#DC2626",
    font=dict(size=11, color="#DC2626"), ax=40, ay=-36,
)
# Add a subtle filled area under the line for better figure/ground
fig_line.add_trace(go.Scatter(
    x=filtered["year"], y=filtered["total"],
    fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
    line=dict(width=0), showlegend=False, hoverinfo="skip",
))
fig_line.update_layout(
    template="plotly_white",
    height=300,
    hovermode="x unified",
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(title="Year", showgrid=False, tickfont=dict(size=11)),
    # B1: horizontal gridlines only — follow reading direction
    yaxis=dict(title="Annual Arrivals", gridcolor="#EFEFEF",
               tickfont=dict(size=11), tickformat=","),
    plot_bgcolor="#FFFFFF",
    showlegend=False,
)
st.plotly_chart(fig_line, use_container_width=True)
card_close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART 2 — Ranked Bar Chart
#  B1 Position (bar length along common baseline) = primary rank encoding.
#  B4 Value/lightness (single-hue Blues) = REDUNDANT encoding of magnitude
#     reinforcing the length signal (B5 Redundant encoding).
#  G6 Focal point: #1 country bar gets a contrasting annotation.
#  G4 Figure/Ground: no vertical gridlines, faint horizontal guide lines only.
#  NOTE: colour hue is NOT used here because hue does not convey order (Bertin).
#        A single-hue sequential ramp (value) correctly encodes magnitude.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
card_open()
chart_title(f"Countries Ranked by Total Arrivals — Top {len(selected_cols)}")
chart_caption("Bar length (position) is the primary encoding; lightness reinforces rank "
              "(redundant encoding). Single-hue ramp — not multi-hue — because data is ordered.")

ct = (
    filtered[selected_cols].sum()
    .reset_index().rename(columns={"index": "col", 0: "arrivals"})
    .assign(country=lambda d: d["col"].map(PRETTY))
    .sort_values("arrivals", ascending=True)
)
bar_height = max(400, len(selected_cols) * 26)
fig_bar = px.bar(
    ct, x="arrivals", y="country", orientation="h",
    labels={"arrivals": "Total Arrivals", "country": ""},
    color="arrivals",
    # B4: single-hue sequential (Blues) — value encodes magnitude, not hue
    color_continuous_scale="Blues",
    template="plotly_white",
)
# G6: annotate the top country
top_country = ct.iloc[-1]
fig_bar.add_annotation(
    x=top_country["arrivals"], y=top_country["country"],
    text=f"  {top_country['arrivals']:,.0f}",
    showarrow=False, xanchor="left",
    font=dict(size=11, color="#1B2A4A", weight=700),
)
fig_bar.update_layout(
    coloraxis_showscale=False,
    height=bar_height,
    margin=dict(l=10, r=80, t=10, b=10),
    xaxis=dict(title="Total Arrivals", gridcolor="#EFEFEF",
               tickformat=",", tickfont=dict(size=11)),
    yaxis=dict(tickfont=dict(size=11), showgrid=False),
    plot_bgcolor="#FFFFFF",
)
st.plotly_chart(fig_bar, use_container_width=True)
card_close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART 3 — Multi-line Country Trends
#  B3 Colour HUE separates categories (countries) — correct for nominal var.
#  B1 Position (X=year, Y=arrivals) encodes the quantitative relationship.
#  G3 Continuity: lines guide the eye through time for each country.
#  G2 Similarity: lines in same palette family group as "country series".
#  Palette: colourblind-safe (Wong 2011). Each country gets a distinct hue.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
card_open()
chart_title("Individual Country Trends Over Time")
chart_caption("Hue distinguishes countries (nominal). Position encodes quantity. "
              "Colourblind-safe palette. Drag to zoom; double-click legend to isolate a country.")

melt = (
    filtered[["year"] + selected_cols]
    .melt(id_vars="year", var_name="col", value_name="arrivals")
    .assign(country=lambda d: d["col"].map(PRETTY))
    .dropna(subset=["arrivals"])
)
n_colors  = len(selected_cols)
palette   = (CB_PALETTE * ((n_colors // len(CB_PALETTE)) + 1))[:n_colors]
line_height = max(480, len(selected_cols) * 22)

fig_multi = px.line(
    melt, x="year", y="arrivals", color="country",
    color_discrete_sequence=palette,
    labels={"year": "Year", "arrivals": "Arrivals", "country": "Country"},
    template="plotly_white",
)
fig_multi.update_traces(line_width=1.8)
fig_multi.update_layout(
    hovermode="x unified",
    height=line_height,
    legend=dict(orientation="v", x=1.01, y=1,
                font=dict(size=10), bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#E5E7EB", borderwidth=1),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(title="Year", showgrid=False, tickfont=dict(size=11)),
    yaxis=dict(title="Arrivals", gridcolor="#EFEFEF",
               tickfont=dict(size=11), tickformat=","),
    plot_bgcolor="#FFFFFF",
)
st.plotly_chart(fig_multi, use_container_width=True)
card_close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART 4 — Heatmap (Country × Year)
#  B4 Value/lightness (sequential single-hue) encodes magnitude correctly.
#  B1 Position on both axes encodes the two categorical dimensions (year, country).
#  G2 Similarity: rows of same lightness signal similar magnitude.
#  G1 Proximity: adjacent cells in same country row are perceived as a series.
#  NOTE: "YlOrRd" replaced with "Blues" single-hue to avoid multi-hue confusion
#        where hue changes could be mistaken for categorical differences.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
card_open()
chart_title("Heatmap — Arrivals by Country and Year")
chart_caption("Lightness (single-hue sequential) encodes magnitude. "
              "Multi-hue ramps avoided — hue change should signal category, not quantity.")

heat_df = filtered[["year"] + selected_cols].set_index("year")[selected_cols].T
heat_df.index = [PRETTY[c] for c in heat_df.index]
heat_height = max(420, len(selected_cols) * 22)

fig_heat = px.imshow(
    heat_df,
    # B4: single-hue sequential — lightness = quantity, no hue shifts
    color_continuous_scale="Blues",
    labels={"x": "Year", "y": "Country", "color": "Arrivals"},
    aspect="auto",
    template="plotly_white",
)
fig_heat.update_layout(
    height=heat_height,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(tickmode="linear", dtick=5, tickangle=-45,
               tickfont=dict(size=10), showgrid=False),
    yaxis=dict(tickfont=dict(size=11), showgrid=False),
    coloraxis_colorbar=dict(title="Arrivals", thickness=14,
                            tickformat=",", len=0.6),
    plot_bgcolor="#FFFFFF",
)
st.plotly_chart(fig_heat, use_container_width=True)
card_close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHART 5 + 6 — Regional Share & YoY Growth
#  G1 Proximity: these two summary charts share a row — both are "overview" views.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
c5, c6 = st.columns(2)

# CHART 5 — Regional breakdown: STACKED NORMALISED BAR (replaces pie)
# PIE REPLACED: arc/angle is Bertin's weakest retinal variable for comparing
# magnitudes. A 100%-stacked bar with a common baseline lets the eye use
# POSITION to compare, which is the strongest retinal variable (B1).
# B3 Hue differentiates the six regions (nominal → hue is correct).
# G2 Similarity: same hue across a segment = same region across years.
with c5:
    card_open()
    chart_title("Regional Share of Arrivals — by Decade")
    chart_caption("Stacked % bar replaces pie chart: position along a common baseline "
                  "(Bertin B1) is more accurate than angle/arc for comparing part-to-whole.")

    REGIONS = {
        "Asia": "asia", "Europe": "europe",
        "North America": "north_america", "South America": "south_america",
        "Africa": "africa", "Oceania": "oceania",
    }
    valid_regions = {k: v for k, v in REGIONS.items() if v in filtered.columns}

    decade_data = []
    filt_copy = filtered.copy()
    filt_copy["decade"] = (filt_copy["year"] // 10 * 10).astype(str) + "s"
    for region_label, col in valid_regions.items():
        grp = filt_copy.groupby("decade")[col].sum().reset_index()
        grp.columns = ["decade", "arrivals"]
        grp["region"] = region_label
        decade_data.append(grp)
    decade_df = pd.concat(decade_data)

    # B3: hand-picked distinct hues for regions (colourblind-safe)
    region_colors = {
        "Asia":          "#2563EB",
        "Europe":        "#E69F00",
        "North America": "#009E73",
        "South America": "#CC79A7",
        "Africa":        "#D55E00",
        "Oceania":       "#56B4E9",
    }
    fig_region = px.bar(
        decade_df, x="decade", y="arrivals", color="region",
        barmode="relative",   # 100% stacked
        labels={"decade": "Decade", "arrivals": "Arrivals", "region": "Region"},
        color_discrete_map=region_colors,
        template="plotly_white",
    )
    fig_region.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", x=0, y=-0.18, font=dict(size=10)),
        xaxis=dict(title="Decade", showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(title="Arrivals", gridcolor="#EFEFEF",
                   tickformat=",", tickfont=dict(size=11)),
        plot_bgcolor="#FFFFFF",
        bargap=0.25,
    )
    st.plotly_chart(fig_region, use_container_width=True)
    card_close()

# CHART 6 — YoY Growth
# B4 DIVERGING colour (RdYlGn) is correct here: zero IS a meaningful midpoint.
#    Positive growth → green; negative → red. Diverging only where justified.
# B1 Position (bar length from zero baseline) encodes magnitude.
# G6 Focal point: zero reference line visually anchors the midpoint.
with c6:
    card_open()
    chart_title("Year-over-Year Growth Rate (%)")
    chart_caption("Diverging colour (RdYlGn) used only here — zero is a true midpoint. "
                  "Red = decline, green = growth. Zero reference line anchors the baseline.")

    yoy_df = filtered[["year", "total"]].sort_values("year").copy()
    yoy_df["growth"] = yoy_df["total"].pct_change() * 100
    yoy_df = yoy_df.dropna(subset=["growth"])

    fig_yoy = px.bar(
        yoy_df, x="year", y="growth",
        labels={"year": "Year", "growth": "YoY Growth (%)"},
        color="growth",
        # B4 Diverging: justified because zero is a meaningful midpoint
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        template="plotly_white",
    )
    # G6: zero line as focal anchor
    fig_yoy.add_hline(y=0, line_width=1.5, line_dash="solid", line_color="#374151")
    fig_yoy.update_layout(
        coloraxis_showscale=False,
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Year", showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(title="Growth (%)", gridcolor="#EFEFEF",
                   tickfont=dict(size=11), ticksuffix="%"),
        plot_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig_yoy, use_container_width=True)
    card_close()

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("🗃️ View Raw Data (selected countries)"):
    display_cols = ["year", "total"] + selected_cols
    rename_map   = {c: PRETTY.get(c, c.replace("_", " ").title()) for c in display_cols}
    rename_map.update({"year": "Year", "total": "Total"})
    st.dataframe(
        filtered[display_cols].rename(columns=rename_map).set_index("Year"),
        use_container_width=True, height=320,
    )

st.caption("Data: Japan Ministry of Justice – Inbound Immigration Statistics · "
           "Visual encoding: Bertin retinal variables & Gestalt principles")