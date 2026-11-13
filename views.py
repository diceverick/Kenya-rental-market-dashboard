"""The five dashboard sections. Each takes (filtered df, full df, meta)."""
from __future__ import annotations

import hashlib

import pandas as pd
import streamlit as st

import charts as ch
import theme as T
from data import BEDS, CITY, INTERNAL, NB, PPSF, PRICE, SIZE, grp_stats, ksh, ranked, short

CFG = {"displayModeBar": False}
NUM = st.column_config.NumberColumn


def panel(title: str, sub: str, fig, note: str = "Not enough data for this view.") -> None:
    with st.container(border=True):
        T.chart_title(title, sub)
        if fig is None:
            st.caption(note)
        else:
            st.plotly_chart(fig, width="stretch", config=CFG, key="p" + hashlib.md5(title.encode()).hexdigest()[:10])


def guard(df: pd.DataFrame) -> None:
    if df.empty:
        T.empty_state()
        st.stop()


def head(title: str, desc: str, df, full) -> None:
    T.page_head(title, desc, len(df), len(full))
    guard(df)


def stat_table(s: pd.DataFrame, key: str, label: str) -> None:
    cols = [key, "Listings", "Median", "Mean", "Min", "Max"]
    st.dataframe(s[cols].rename(columns={key: label}), hide_index=True, width="stretch",
                 column_config={c: NUM(format="localized") for c in cols[1:]})


# --------------------------------------------------------------- 1. OVERVIEW
def overview(df, full, meta):
    T.hero(meta["source"], meta["updated"], len(df), len(full))
    guard(df)
    p = df[PRICE]
    med, avg = p.median(), p.mean()
    at_min, at_max = df.loc[p.idxmin(), "Area"], df.loc[p.idxmax(), "Area"]
    cols = st.columns(4, gap="small")
    big = [("Median rent", T.money(med), f"IQR {short(p.quantile(.25))} – {short(p.quantile(.75))}"),
           ("Average rent", T.money(avg), f"{avg / med - 1:+.0%} vs median"),
           ("Minimum rent", T.money(p.min()), T.e(at_min)),
           ("Maximum rent", T.money(p.max()), T.e(at_max))]
    for c, (l, v, s) in zip(cols, big):
        c.markdown(T.kpi(l, v, s), unsafe_allow_html=True)
    sz = df[SIZE].dropna()
    top_city = df[CITY].value_counts()
    small = [("Listings analysed", f"{len(df):,}", f"{len(df) / len(full):.0%} of {len(full):,} in dataset"),
             ("Average size", f'{sz.mean():,.0f}<span class="unit">sq ft</span>' if len(sz) else "N/A",
              f"{len(sz):,} listings report size"),
             ("Neighbourhoods", f"{df['Area'].nunique():,}", f"Most listings: {T.e(df['Area'].value_counts().index[0])}"),
             ("Regions", f"{df[CITY].nunique():,}", f"Largest: {T.e(top_city.index[0])} ({top_city.iloc[0]:,})")]
    cols = st.columns(4, gap="small")
    for c, (l, v, s) in zip(cols, small):
        c.markdown(T.kpi(l, v, s, "sm"), unsafe_allow_html=True)

    T.section("Market structure")
    a, b = st.columns([7, 5], gap="medium")
    s, used = ranked(df, "Area", 3)
    with a:
        panel("Highest-rent neighbourhoods", f"Median monthly rent · top 10 · neighbourhoods with ≥{used} listings",
              ch.hbar(s, "Median", 10) if not s.empty else None)
    with b:
        panel("Rent distribution", "Number of listings by monthly rent", ch.hist(p, "Rent"))
    bs = grp_stats(df, "BedLabel")
    panel("Rent by bedroom count", "Average vs median monthly rent", ch.grouped(bs, "BedLabel") if len(bs) else None)
    data_notes(meta, full)


def data_notes(meta, full):
    T.section("Data treatment")
    with st.expander("How the data was cleaned and how outliers are handled"):
        st.markdown(
            f"- **Source:** `{meta['source']}` · {meta['rows_raw']:,} rows read.\n"
            f"- **Removed:** {meta['invalid_price']:,} rows with a missing or non-positive rent, which cannot be analysed as a price.\n"
            f"- **Kept, not dropped:** rows with missing bedrooms ({meta['beds_missing']:,}), size ({meta['size_missing']:,}), "
            "city or neighbourhood (shown as *N/A* / *Unspecified*).\n"
            f"- **Outliers:** the old fixed KSh 1M cap is replaced by a statistical check. A listing is flagged when its "
            f"log-rent is more than 4 robust deviations (modified z-score, MAD) from the median of its bedroom group "
            f"(whole-dataset baseline for groups under 15). This catches implausible values such as sale prices or typos "
            f"while keeping genuine luxury rentals. **{meta['n_outliers']:,} listings flagged**; "
            "exclusion is controlled by the *Exclude statistical outliers* switch in the sidebar.\n"
            + ("- **Property category:** inferred from title keywords (no category column in the file).\n"
               if meta["category_derived"] else "- **Property category:** taken from the file.\n"))
        fl = full[full["Outlier"]]
        if len(fl):
            keep = [c for c in ("Title", "Area", BEDS, SIZE, PRICE, "OutlierZ") if c in fl.columns]
            st.caption("Flagged listings")
            st.dataframe(fl[keep].rename(columns={"OutlierZ": "Robust z"}).round(1), hide_index=True, width="stretch",
                         column_config={PRICE: NUM("Rent (KSh)", format="localized")})


# --------------------------------------------------------- 2. RENTAL ANALYSIS
def rental(df, full, meta):
    head("Rental Analysis", "Rent levels, distribution and dispersion across neighbourhoods, bedrooms and sizes.", df, full)
    c1, c2, c3, _ = st.columns([1.3, 1.3, 1, 3])
    min_n = c1.number_input("Min. listings per neighbourhood", 1, 50, 3, key="r_min")
    top = c2.selectbox("Neighbourhoods shown", [10, 15, 20, 30], index=1, key="r_top")
    log = c3.toggle("Log rent axis", True, key="r_log")
    s, used = ranked(df, "Area", int(min_n))
    if used != min_n:
        st.caption(f"No neighbourhood has {int(min_n)}+ listings in this view; showing all neighbourhoods.")

    T.section("Neighbourhood rankings")
    a, b = st.columns(2, gap="medium")
    with a:
        panel("Average rent by neighbourhood", f"Top {top} · mean monthly rent", ch.hbar(s, "Mean", top, ch.BLUE) if len(s) else None)
    with b:
        panel("Median rent by neighbourhood", f"Top {top} · median monthly rent", ch.hbar(s, "Median", top) if len(s) else None)

    T.section("Distributions")
    a, b = st.columns(2, gap="medium")
    with a:
        panel("Rent distribution", "Listings by monthly rent; dotted line marks the median", ch.hist(df[PRICE], "Rent", log=log))
    with b:
        panel("Property size distribution", "Listings by size (sq ft)", ch.hist(df[SIZE], "Size", log=False, color=ch.BLUE, fmt=""),
              "No size data in the current view.")

    T.section("Bedrooms")
    bs = grp_stats(df, "BedLabel")
    order = [str(c) for c in bs["BedLabel"]]
    a, b = st.columns(2, gap="medium")
    with a:
        panel("Rent by bedroom count", "Average vs median monthly rent", ch.grouped(bs, "BedLabel"))
    with b:
        panel("Rent dispersion by bedroom count", "Box: interquartile range · line: median · points: outliers",
              ch.box_by(df, "BedLabel", order))

    T.section("Size and price")
    cc1, cc2, _ = st.columns([1.2, 1, 3])
    color_by = cc1.selectbox("Colour by", ["None", "Bedrooms", "Category"], key="r_col")
    lg = cc2.toggle("Log axes", True, key="r_sclog")
    panel("Rent versus property size", "Each point is a listing; dashed line is a log–log fit (slope ≈ rent elasticity to size)",
          ch.scatter(df, {"None": None, "Bedrooms": "BedLabel", "Category": "Category"}[color_by], lg),
          "Fewer than 3 listings report a size in this view.")

    T.section("Price ranges")
    panel("Rent range by neighbourhood", f"Median (diamond), interquartile range (bar) and min–max (line) · top {top} by median",
          ch.range_chart(s, top) if len(s) else None)


# ------------------------------------------------------ 3. GEOGRAPHIC ANALYSIS
def geographic(df, full, meta):
    head("Geographic Analysis", "How rents differ between regions and neighbourhoods.", df, full)
    st.markdown('<div class="note"><b>No map shown.</b> The dataset has region and neighbourhood names but no coordinates, '
                'so location is compared with rankings, concentration and cross-tabs instead of plotted points.</div>',
                unsafe_allow_html=True)

    T.section("Regions")
    a, b = st.columns([5, 7], gap="medium")
    rs = grp_stats(df, CITY).sort_values("Listings", ascending=False)
    with a:
        with st.container(border=True):
            T.chart_title("Regional summary", "Monthly rent, KSh")
            stat_table(rs, CITY, "Region")
    with b:
        panel("Listing concentration", "Area = listings · colour = median rent · grouped by region", ch.treemap(df))

    T.section("Neighbourhood ranking")
    s, used = ranked(df, "Area", 3)
    a, b = st.columns([6, 6], gap="medium")
    with a:
        with st.container(border=True):
            T.chart_title("Neighbourhood price ranking", f"Ranked by median rent · neighbourhoods with ≥{used} listings")
            r = s.sort_values("Median", ascending=False).reset_index(drop=True)
            r.insert(0, "Rank", r.index + 1)
            r["Share of listings"] = r["Listings"] / len(df)
            st.dataframe(r[["Rank", "Area", "City", "Listings", "Share of listings", "Median", "Mean"]], hide_index=True,
                         width="stretch", height=420, column_config={
                             "Listings": NUM(format="%d"), "Median": NUM(format="localized"), "Mean": NUM(format="localized"),
                             "Share of listings": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=float(r["Share of listings"].max()))})
    with b:
        panel("Average vs median rent", "Most-listed neighbourhoods · a wide gap means high-end listings pull the average up",
              ch.dumbbell(s, 12) if len(s) else None)

    T.section("Neighbourhood × bedrooms")
    panel("Median rent by neighbourhood and bedroom count", "12 most-listed neighbourhoods · blank = no listings", ch.heatmap(df, 12))

    T.section("Region comparison")
    regions = list(df[CITY].value_counts().index)
    cur = [r for r in st.session_state.get("geo_regions", []) if r in regions] or regions[:2]
    st.session_state["geo_regions"] = cur
    sel = st.multiselect("Regions to compare", regions, key="geo_regions")
    if len(sel) < 2:
        st.caption("Select at least two regions to compare.")
        return
    sub = df[df[CITY].isin(sel)]
    a, b = st.columns([6, 6], gap="medium")
    with a:
        panel("Rent dispersion by region", "Box: interquartile range · line: median", ch.box_by(sub, CITY, sel))
    with b:
        with st.container(border=True):
            ref = st.selectbox("Reference region", sel, key="geo_ref")
            T.chart_title("Difference vs reference region", "Median monthly rent")
            t = grp_stats(sub, CITY).set_index(CITY)
            rows = [{"Region": r, "Listings": int(t.loc[r, "Listings"]), "Median": t.loc[r, "Median"],
                     "Δ vs ref (KSh)": t.loc[r, "Median"] - t.loc[ref, "Median"],
                     "Δ vs ref (%)": (t.loc[r, "Median"] / t.loc[ref, "Median"] - 1) * 100}
                    for r in sel if r in t.index]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
                "Median": NUM(format="localized"), "Δ vs ref (KSh)": NUM(format="localized"), "Δ vs ref (%)": NUM(format="%+.1f%%")})


# -------------------------------------------------------- 4. PROPERTY INSIGHTS
def insights(df, full, meta):
    head("Property Insights", "Patterns computed directly from the filtered listings. No figures are hard-coded.", df, full)
    min_n = st.slider("Minimum listings per group", 1, 20, 3, key="ins_min",
                      help="Groups smaller than this are ignored so a single listing cannot top a ranking.")
    beds = grp_stats(df, "BedLabel", min_n)
    beds = beds[beds["BedLabel"].astype(str) != "N/A"]
    areas, cats = grp_stats(df, "Area", min_n), grp_stats(df, "Category", min_n)
    none = "Not enough listings per group at this threshold."
    cards = []

    if len(beds):
        r = beds.loc[beds["Mean"].idxmax()]
        cards.append(("Highest-rent bedroom category", T.e(r["BedLabel"]),
                      f"Average <b>{ksh(r['Mean'])}</b> across {int(r['Listings']):,} listings (median {ksh(r['Median'])})."))
    else:
        cards.append(("Highest-rent bedroom category", "–", none))
    lo, hi = areas.nsmallest(3, "Mean"), areas.nlargest(3, "Median")
    fmt = lambda d, c: "<br>".join(f"<b>{T.e(a)}</b> · {ksh(v)}" for a, v in zip(d["Area"], d[c]))
    cards.append(("Lowest average rent", T.e(lo["Area"].iloc[0]) if len(lo) else "–", fmt(lo, "Mean") if len(lo) else none))
    cards.append(("Highest median rent", T.e(hi["Area"].iloc[0]) if len(hi) else "–", fmt(hi, "Median") if len(hi) else none))

    sp = df[[SIZE, PRICE]].dropna()
    if len(sp) >= 8 and sp[SIZE].nunique() > 1:
        rho = sp[SIZE].rank().corr(sp[PRICE].rank())  # Spearman = Pearson on ranks (no scipy needed)
        strength = "strong" if abs(rho) >= .7 else "moderate" if abs(rho) >= .4 else "weak"
        cards.append(("Size vs rent", f"ρ = {rho:.2f}",
                      f"A <b>{strength} {'positive' if rho >= 0 else 'negative'}</b> rank correlation across {len(sp):,} listings "
                      f"with size. Median rent per sq ft: <b>{ksh(df[PPSF].median())}</b>."))
    else:
        cards.append(("Size vs rent", "–", "Fewer than 8 listings report a size."))
    cv = areas.dropna(subset=["CV"])
    if len(cv):
        r = cv.loc[cv["CV"].idxmax()]
        cards.append(("Widest rent variation", T.e(r["Area"]),
                      f"Rents vary by <b>{r['CV']:.0%}</b> of the mean (std {ksh(r['Std'])}, mean {ksh(r['Mean'])}, {int(r['Listings'])} listings)."))
    else:
        cards.append(("Widest rent variation", "–", none))
    if len(cats) >= 2:
        h, l = cats.loc[cats["Median"].idxmax()], cats.loc[cats["Median"].idxmin()]
        cards.append(("Property category pricing", T.e(h["Category"]),
                      f"Highest median at <b>{ksh(h['Median'])}</b>; lowest is <b>{T.e(l['Category'])}</b> at {ksh(l['Median'])}."))
    elif len(cats):
        cards.append(("Property category pricing", T.e(cats["Category"].iloc[0]), "Only one category in this view."))
    else:
        cards.append(("Property category pricing", "–", none))

    for i in (0, 3):
        for c, (l, h_, d) in zip(st.columns(3, gap="small"), cards[i:i + 3]):
            c.markdown(T.insight(l, h_, d), unsafe_allow_html=True)
        st.write("")

    T.section("Supporting analysis")
    if True:
        top = cv.nlargest(12, "CV")
        if len(top):
            import plotly.graph_objects as go
            d = top.iloc[::-1]
            fig = go.Figure(go.Bar(x=d["CV"], y=d["Area"], orientation="h", marker_color=ch.AMBER,
                                   customdata=d[["Mean", "Std", "Listings"]].to_numpy(),
                                   hovertemplate="<b>%{y}</b><br>Variation: %{x:.0%}<br>Mean: KSh %{customdata[0]:,.0f}"
                                                 "<br>Std: KSh %{customdata[1]:,.0f}<br>Listings: %{customdata[2]}<extra></extra>"))
            T.style(fig, height=max(240, 27 * len(d) + 70), grid="x")
            fig.update_xaxes(title_text="Coefficient of variation (std ÷ mean)", tickformat=".0%")
        else:
            fig = None
        panel("Rent variation by neighbourhood", "Higher = wider spread of rents within the area", fig)

    T.section("Summary tables")
    a, b = st.columns(2, gap="medium")
    with a:
        with st.container(border=True):
            T.chart_title("By bedroom count", "Monthly rent, KSh")
            stat_table(grp_stats(df, "BedLabel"), "BedLabel", "Bedrooms")
    with b:
        with st.container(border=True):
            T.chart_title("By property category", "Monthly rent, KSh")
            stat_table(grp_stats(df, "Category").sort_values("Median", ascending=False), "Category", "Category")


# ------------------------------------------------------------ 5. DATA EXPLORER
def explorer(df, full, meta):
    head("Data Explorer", "Search, sort and export the listings behind every chart.", df, full)
    q = st.text_input("Search", placeholder="Search title, neighbourhood or region", key="ex_q", label_visibility="collapsed")
    d = df
    if q.strip():
        hay_cols = [c for c in ("Title", NB, CITY) if c in d.columns]
        hay = d[hay_cols].fillna("").agg(" ".join, axis=1).str.lower()
        m = pd.Series(True, index=d.index)
        for tok in q.lower().split():
            m &= hay.str.contains(tok, regex=False)
        d = d[m]

    front = [c for c in ("Title", "Category", NB, CITY, BEDS, SIZE, PRICE, PPSF, "Outlier") if c in d.columns]
    rest = [c for c in d.columns if c not in front and c not in INTERNAL]
    d = d[front + rest].copy()
    d[PPSF] = d[PPSF].round(0)
    c1, c2, c3 = st.columns([2, 1, 2])
    sort_by = c1.selectbox("Sort by", front, index=front.index(PRICE), key="ex_sort")
    asc = c2.radio("Order", ["Descending", "Ascending"], horizontal=True, key="ex_order") == "Ascending"
    d = d.sort_values(sort_by, ascending=asc, na_position="last")
    c3.markdown(f'<div class="meta" style="padding-top:26px">Showing<span>{len(d):,} of {len(df):,} listings</span></div>', unsafe_allow_html=True)

    cfg = {PRICE: NUM("Rent (KSh)", format="localized"), SIZE: NUM("Size (sq ft)", format="localized"),
           BEDS: NUM("Bedrooms", format="%d"), PPSF: NUM("Rent per sq ft (KSh)", format="localized"),
           "Outlier": st.column_config.CheckboxColumn("Flagged outlier"), NB: "Neighbourhood", CITY: "Region"}
    st.dataframe(d, hide_index=True, width="stretch", height=560, column_config=cfg)
    st.download_button("Download filtered data (CSV)", d.to_csv(index=False).encode("utf-8"),
                       file_name="kenya_rentals_filtered.csv", mime="text/csv", disabled=d.empty)