import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Japan Inbound Immigration Dashboard",
    page_icon="🇯🇵",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

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

# ── Build country list (exclude aggregate/regional columns) ───────────────────
EXCLUDED = {
    "year", "total", "asia", "europe", "africa",
    "north_america", "south_america", "oceania",
    "stateless", "unknown_other",
}
ALL_COUNTRY_COLS = [c for c in df.columns if c not in EXCLUDED]

# Pretty-name map
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

PRETTY_TO_COL = {v: k for k, v in PRETTY.items()}
ALL_PRETTY_SORTED = sorted(PRETTY[c] for c in ALL_COUNTRY_COLS)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🇯🇵 Japan Inbound Immigration Dashboard")
st.markdown(
    f"Explore inbound immigration to Japan across **every origin country** "
    f"({len(ALL_COUNTRY_COLS)} countries) from **{df['year'].min()}** to **{df['year'].max()}**. "
    "Use the **Top N slider** to surface the biggest senders, or **search by name** to add any specific country. "
    "All charts support drag-to-zoom and double-click to reset."
)
st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
st.subheader("🔧 Filters")
f1, f2, f3 = st.columns([2, 1, 3])

with f1:
    year_range = st.slider(
        "📅 Year Range",
        min_value=int(df["year"].min()),
        max_value=int(df["year"].max()),
        value=(int(df["year"].min()), int(df["year"].max())),
    )

with f2:
    top_n = st.slider(
        "🏅 Top N Countries",
        min_value=3,
        max_value=len(ALL_COUNTRY_COLS),
        value=15,
        step=1,
        help="Ranks countries by total arrivals within the selected year range.",
    )

with f3:
    search_pretty = st.multiselect(
        "🔍 Add / Override Specific Countries",
        options=ALL_PRETTY_SORTED,
        default=[],
        placeholder="Type any country name to search and add it…",
    )

# ── Resolve selected countries ────────────────────────────────────────────────
filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].copy()

period_totals = filtered[ALL_COUNTRY_COLS].sum().sort_values(ascending=False)
top_n_cols = period_totals.head(top_n).index.tolist()

searched_cols = [PRETTY_TO_COL[p] for p in search_pretty if p in PRETTY_TO_COL]
# Deduplicate while preserving order
selected_cols = list(dict.fromkeys(top_n_cols + searched_cols))

extra_note = f" + {len(searched_cols)} searched" if searched_cols else ""
st.caption(
    f"**{len(selected_cols)} countries selected** (top {top_n} by period total{extra_note}). "
    "Charts resize automatically — increase Top N to see more."
)
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
total_period = int(filtered["total"].sum())
peak_row     = filtered.loc[filtered["total"].idxmax()]
avg_annual   = int(filtered["total"].mean())
sorted_f     = filtered.sort_values("year")
yoy = (
    (sorted_f.iloc[-1]["total"] - sorted_f.iloc[-2]["total"]) / sorted_f.iloc[-2]["total"] * 100
    if len(sorted_f) >= 2 else None
)

k1.metric("Total Arrivals (Period)", f"{total_period:,.0f}")
k2.metric("Peak Year", f"{int(peak_row['year'])} — {int(peak_row['total']):,.0f}")
k3.metric("Avg Annual Arrivals", f"{avg_annual:,.0f}")
k4.metric("Latest YoY Change", f"{yoy:+.1f}%" if yoy else "N/A", delta=f"{yoy:+.1f}%" if yoy else None)
st.divider()

# ── Chart 1: Total trend ──────────────────────────────────────────────────────
st.subheader("📈 Total Immigration Trend")
fig_line = px.line(
    filtered, x="year", y="total", markers=True,
    labels={"year": "Year", "total": "Total Arrivals"},
    template="plotly_white", color_discrete_sequence=["#E63946"],
)
fig_line.update_traces(line_width=2.5, marker_size=4)
fig_line.update_layout(hovermode="x unified", height=300, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig_line, use_container_width=True)
st.divider()

# ── Chart 2: Horizontal bar (scrollable) ─────────────────────────────────────
st.subheader(f"🏆 Countries Ranked by Period Total — Top {len(selected_cols)}")
ct = (
    filtered[selected_cols].sum()
    .reset_index().rename(columns={"index": "col", 0: "arrivals"})
    .assign(country=lambda d: d["col"].map(PRETTY))
    .sort_values("arrivals", ascending=True)
)
bar_height = max(400, len(selected_cols) * 24)
fig_bar = px.bar(
    ct, x="arrivals", y="country", orientation="h",
    labels={"arrivals": "Total Arrivals", "country": ""},
    template="plotly_white",
    color="arrivals", color_continuous_scale="Reds",
)
fig_bar.update_layout(
    coloraxis_showscale=False,
    height=bar_height,
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis=dict(tickfont=dict(size=11)),
)
st.plotly_chart(fig_bar, use_container_width=True)
st.divider()

# ── Chart 3: Multi-line (scroll/zoom) ────────────────────────────────────────
st.subheader("📉 Country Trends Over Time")
melt = (
    filtered[["year"] + selected_cols]
    .melt(id_vars="year", var_name="col", value_name="arrivals")
    .assign(country=lambda d: d["col"].map(PRETTY))
    .dropna(subset=["arrivals"])
)
line_height = max(450, len(selected_cols) * 20)
fig_multi = px.line(
    melt, x="year", y="arrivals", color="country",
    labels={"year": "Year", "arrivals": "Arrivals", "country": "Country"},
    template="plotly_white",
)
fig_multi.update_traces(line_width=1.5)
fig_multi.update_layout(
    hovermode="x unified",
    height=line_height,
    legend=dict(orientation="v", x=1.01, y=1, font=dict(size=10)),
    margin=dict(l=0, r=60, t=10, b=0),
)
st.plotly_chart(fig_multi, use_container_width=True)
st.divider()

# ── Chart 4: Heatmap — every country × every year ────────────────────────────
st.subheader("🌡️ Heatmap — Country × Year")
st.caption("Rows = countries · Columns = years · Colour = arrivals. Drag to zoom, scroll inside the chart.")

heat_df = filtered[["year"] + selected_cols].set_index("year")[selected_cols].T
heat_df.index = [PRETTY[c] for c in heat_df.index]

heat_height = max(400, len(selected_cols) * 22)
fig_heat = px.imshow(
    heat_df,
    color_continuous_scale="YlOrRd",
    labels={"x": "Year", "y": "Country", "color": "Arrivals"},
    aspect="auto",
    template="plotly_white",
)
fig_heat.update_layout(
    height=heat_height,
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(tickmode="linear", dtick=5, tickangle=-45, tickfont=dict(size=10)),
    yaxis=dict(tickfont=dict(size=11)),
    coloraxis_colorbar=dict(title="Arrivals", thickness=12),
)
st.plotly_chart(fig_heat, use_container_width=True)
st.divider()

# ── Chart 5 + 6: Regional pie + YoY ──────────────────────────────────────────
c5, c6 = st.columns(2)

with c5:
    st.subheader("🌏 Regional Share of Arrivals")
    REGIONS = {
        "Asia": "asia", "Europe": "europe",
        "North America": "north_america", "South America": "south_america",
        "Africa": "africa", "Oceania": "oceania",
    }
    valid = {k: v for k, v in REGIONS.items() if v in filtered.columns}
    rtotals = {k: filtered[v].sum() for k, v in valid.items()}
    fig_pie = px.pie(
        values=list(rtotals.values()), names=list(rtotals.keys()),
        hole=0.4, template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with c6:
    st.subheader("📊 Year-over-Year Growth Rate (%)")
    yoy_df = filtered[["year", "total"]].sort_values("year").copy()
    yoy_df["growth"] = yoy_df["total"].pct_change() * 100
    yoy_df = yoy_df.dropna(subset=["growth"])
    fig_yoy = px.bar(
        yoy_df, x="year", y="growth",
        labels={"year": "Year", "growth": "YoY Growth (%)"},
        template="plotly_white",
        color="growth", color_continuous_scale="RdYlGn",
    )
    fig_yoy.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_yoy.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_yoy, use_container_width=True)

st.divider()

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("🗃️ View Raw Data (selected countries)"):
    display_cols = ["year", "total"] + selected_cols
    rename_map = {c: PRETTY.get(c, c.replace("_", " ").title()) for c in display_cols}
    rename_map.update({"year": "Year", "total": "Total"})
    st.dataframe(
        filtered[display_cols].rename(columns=rename_map).set_index("Year"),
        use_container_width=True,
        height=320,
    )

st.caption("Data: Japan Ministry of Justice – Inbound Immigration Statistics")