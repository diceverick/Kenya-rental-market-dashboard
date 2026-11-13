"""Plotly figure builders. Each returns a styled figure."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from data import PRICE, SIZE, short
from theme import ACCENT, AMBER, BG, BLUE, BORDER, CAT, GREY, MUTED, SEQ, TEAL, TEXT, style

RENT_AXIS = "Monthly rent (KSh)"


def hbar(s: pd.DataFrame, col: str, top: int = 15, color: str = ACCENT):
    d = s.sort_values(col, ascending=False).head(top).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d[col], y=d["Area"], orientation="h", marker_color=color,
        text=[short(v) for v in d[col]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT, size=11),
        customdata=d[["Listings", "Median", "Mean", "City"]].to_numpy(),
        hovertemplate="<b>%{y}</b> · %{customdata[3]}<br>Median: KSh %{customdata[1]:,.0f}"
                      "<br>Average: KSh %{customdata[2]:,.0f}<br>Listings: %{customdata[0]}<extra></extra>"))
    style(fig, height=max(240, 27 * len(d) + 70), grid="x")
    fig.update_xaxes(title_text=RENT_AXIS, tickformat="~s", range=[0, float(d[col].max()) * 1.16])
    return fig


def bar_counts(df: pd.DataFrame, col: str, top: int = 10, color: str = BLUE):
    c = df[col].astype(str).value_counts().head(top).iloc[::-1]
    fig = go.Figure(go.Bar(x=c.values, y=c.index, orientation="h", marker_color=color,
                           text=[f"{v:,}" for v in c.values], textposition="outside", cliponaxis=False,
                           textfont=dict(color=TEXT, size=11),
                           hovertemplate="<b>%{y}</b><br>Listings: %{x:,}<extra></extra>"))
    style(fig, height=max(240, 27 * len(c) + 70), grid="x")
    fig.update_xaxes(title_text="Listings", range=[0, float(c.max()) * 1.16])
    return fig


def hist(x, label: str, log: bool | None = None, bins: int = 36, color: str = ACCENT, fmt: str = "KSh"):
    x = pd.Series(x).dropna()
    x = x[x > 0]
    if x.empty:
        return None
    lo, hi = float(x.min()), float(x.max())
    if log is None:
        log = hi / lo > 30
    if lo == hi:
        edges = np.array([lo * 0.95, hi * 1.05])
    elif log:
        edges = np.geomspace(lo, hi, min(bins, max(5, x.nunique())) + 1)
    else:
        edges = np.linspace(lo, hi, min(bins, max(5, x.nunique())) + 1)
    cnt, _ = np.histogram(x, bins=edges)
    tx = np.log10 if log else (lambda v: v)
    ctr, w = tx(edges[:-1]) / 2 + tx(edges[1:]) / 2, np.diff(tx(edges))
    prefix = "KSh " if fmt == "KSh" else ""
    fig = go.Figure(go.Bar(
        x=ctr, y=cnt, width=w * 0.92, marker_color=color, customdata=np.c_[edges[:-1], edges[1:]],
        hovertemplate=f"{label}: {prefix}%{{customdata[0]:,.0f}} – %{{customdata[1]:,.0f}}"
                      "<br>Listings: %{y:,}<extra></extra>"))
    med = float(x.median())
    fig.add_vline(x=float(tx(med)), line=dict(color=AMBER, width=1.2, dash="dot"),
                  annotation_text=f"Median {short(med)}", annotation_font=dict(color=AMBER, size=11),
                  annotation_position="top right")
    style(fig, height=330)
    if log:
        cand = [v for v in (500, 1e3, 2e3, 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6) if lo * 0.8 <= v <= hi * 1.25]
        fig.update_xaxes(tickvals=[np.log10(v) for v in cand], ticktext=[short(v) for v in cand])
    else:
        fig.update_xaxes(tickformat="~s")
    fig.update_xaxes(title_text=label + (" · log scale" if log else ""))
    fig.update_yaxes(title_text="Listings")
    return fig


def grouped(s: pd.DataFrame, key: str):
    s = s.copy()
    cats = [f"{k}<br><span style='color:#5D666E'>n={int(n)}</span>" for k, n in zip(s[key], s["Listings"])]
    fig = go.Figure()
    for col, name, colr in (("Mean", "Average", BLUE), ("Median", "Median", ACCENT)):
        fig.add_bar(x=cats, y=s[col], name=name, marker_color=colr, customdata=np.c_[s[key].astype(str), s["Listings"]],
                    hovertemplate=f"<b>%{{customdata[0]}}</b><br>{name}: KSh %{{y:,.0f}}"
                                  "<br>Listings: %{customdata[1]}<extra></extra>")
    style(fig, height=330, legend=True)
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.06)
    fig.update_yaxes(title_text=RENT_AXIS, tickformat="~s")
    return fig


def box_by(df: pd.DataFrame, key: str, order: list | None = None, horizontal: bool = False, height: int = 330):
    groups = order or list(df[key].astype(str).value_counts().index)
    fig = go.Figure()
    for i, g in enumerate(groups):
        v = df.loc[df[key].astype(str) == g, PRICE]
        if v.empty:
            continue
        c = CAT[i % len(CAT)] if len(groups) <= 6 else ACCENT
        kw = dict(x=v, y=[g] * len(v)) if horizontal else dict(y=v, x=[g] * len(v))
        fig.add_trace(go.Box(name=g, boxpoints="outliers", marker=dict(color=c, size=4, opacity=.6),
                             line=dict(color=c, width=1.3), fillcolor="rgba(255,255,255,0.03)",
                             orientation="h" if horizontal else "v", showlegend=False, **kw))
    style(fig, height=height, grid="x" if horizontal else "y")
    (fig.update_xaxes if horizontal else fig.update_yaxes)(title_text=RENT_AXIS, tickformat="~s")
    return fig


def scatter(df: pd.DataFrame, color_by: str | None = None, log: bool = True):
    d = df[[SIZE, PRICE, "Area", "BedLabel", "Category"]].dropna(subset=[SIZE, PRICE])
    d = d[d[SIZE] > 0]
    if len(d) < 3:
        return None
    fig = go.Figure()
    groups = [(None, d)] if not color_by else [(str(k), g) for k, g in d.groupby(color_by, observed=True)]
    for i, (name, g) in enumerate(groups):
        fig.add_trace(go.Scatter(
            x=g[SIZE], y=g[PRICE], mode="markers", name=name or "Listings", showlegend=bool(name),
            marker=dict(size=7, opacity=.65, color=CAT[i % len(CAT)] if name else ACCENT, line=dict(width=0)),
            customdata=np.c_[g["Area"], g["BedLabel"].astype(str), g["Category"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}"
                          "<br>Size: %{x:,.0f} sq ft<br>Rent: KSh %{y:,.0f}<extra></extra>"))
    if len(d) >= 8 and d[SIZE].nunique() > 2:
        a, b = np.polyfit(np.log(d[SIZE]), np.log(d[PRICE]), 1)
        xs = np.geomspace(d[SIZE].min(), d[SIZE].max(), 60)
        fig.add_trace(go.Scatter(x=xs, y=np.exp(b + a * np.log(xs)), mode="lines", hoverinfo="skip",
                                 name=f"Log–log trend (slope {a:.2f})", line=dict(color=AMBER, width=1.5, dash="dash")))
    style(fig, height=440, grid="y", legend=True)
    fig.update_xaxes(title_text="Size (sq ft)", tickformat="~s", type="log" if log else "linear")
    fig.update_yaxes(title_text=RENT_AXIS, tickformat="~s", type="log" if log else "linear")
    return fig


def range_chart(s: pd.DataFrame, top: int = 15):
    d = s.sort_values("Median").tail(top)
    ys = d["Area"].tolist()

    def seg(a, b):
        xs, yy = [], []
        for lo, hi, y in zip(d[a], d[b], ys):
            xs += [lo, hi, None]
            yy += [y, y, None]
        return xs, yy

    fig = go.Figure()
    x, y = seg("Min", "Max")
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color="#3A434B", width=1.5), hoverinfo="skip", name="Min – max"))
    x, y = seg("Q1", "Q3")
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=TEAL, width=8), hoverinfo="skip", name="Interquartile range"))
    fig.add_trace(go.Scatter(
        x=d["Median"], y=ys, mode="markers", name="Median",
        marker=dict(symbol="diamond", size=10, color=ACCENT, line=dict(color=BG, width=1)),
        customdata=d[["Q1", "Q3", "Min", "Max", "Listings"]].to_numpy(),
        hovertemplate="<b>%{y}</b><br>Median: KSh %{x:,.0f}<br>IQR: %{customdata[0]:,.0f} – %{customdata[1]:,.0f}"
                      "<br>Range: %{customdata[2]:,.0f} – %{customdata[3]:,.0f}<br>Listings: %{customdata[4]}<extra></extra>"))
    style(fig, height=max(260, 30 * len(d) + 80), grid="x", legend=True)
    fig.update_yaxes(categoryorder="array", categoryarray=ys)
    fig.update_xaxes(title_text=RENT_AXIS, tickformat="~s")
    return fig


def dumbbell(s: pd.DataFrame, top: int = 15):
    d = s.sort_values("Listings", ascending=False).head(top).sort_values("Median")
    ys = d["Area"].tolist()
    xs, yy = [], []
    for a, b, y in zip(d["Median"], d["Mean"], ys):
        xs += [a, b, None]
        yy += [y, y, None]
    fig = go.Figure(go.Scatter(x=xs, y=yy, mode="lines", line=dict(color="#3A434B", width=2), hoverinfo="skip", showlegend=False))
    for col, name, c in (("Median", "Median", ACCENT), ("Mean", "Average", BLUE)):
        fig.add_trace(go.Scatter(x=d[col], y=ys, mode="markers", name=name, marker=dict(size=9, color=c),
                                 customdata=d["Listings"],
                                 hovertemplate=f"<b>%{{y}}</b><br>{name}: KSh %{{x:,.0f}}<br>Listings: %{{customdata}}<extra></extra>"))
    style(fig, height=max(260, 28 * len(d) + 80), grid="x", legend=True)
    fig.update_yaxes(categoryorder="array", categoryarray=ys)
    fig.update_xaxes(title_text=RENT_AXIS, tickformat="~s")
    return fig


def treemap(df: pd.DataFrame):
    leaf = df.groupby(["City", "Area"])[PRICE].agg(n="size", med="median").reset_index()
    city = df.groupby("City")[PRICE].agg(n="size", med="median").reset_index()
    ids = list(city["City"]) + [f"{c}||{a}" for c, a in zip(leaf["City"], leaf["Area"])]
    colors = list(city["med"]) + list(leaf["med"])
    fig = go.Figure(go.Treemap(
        ids=ids, labels=list(city["City"]) + list(leaf["Area"]), parents=[""] * len(city) + list(leaf["City"]),
        values=list(city["n"]) + list(leaf["n"]), branchvalues="total", customdata=colors, pathbar_visible=False,
        marker=dict(colors=colors, colorscale=SEQ, cmin=float(leaf["med"].min()), cmax=float(leaf["med"].max()),
                    line=dict(color=BG, width=2),
                    colorbar=dict(title=dict(text="Median", font=dict(size=10)), thickness=8, outlinewidth=0, tickformat="~s")),
        texttemplate="<b>%{label}</b><br>%{value} listings", textfont=dict(color=TEXT, size=12),
        hovertemplate="<b>%{label}</b><br>Listings: %{value}<br>Median rent: KSh %{customdata:,.0f}<extra></extra>"))
    style(fig, height=380, grid=None)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig


def heatmap(df: pd.DataFrame, top: int = 12):
    areas = list(df["Area"].value_counts().head(top).index)
    g = df[df["Area"].isin(areas)].groupby(["Area", "BedLabel"], observed=True)[PRICE].agg(["median", "size"]).reset_index()
    if g.empty:
        return None
    med = g.pivot(index="Area", columns="BedLabel", values="median").reindex(areas)
    cnt = g.pivot(index="Area", columns="BedLabel", values="size").reindex(areas)
    med = med.dropna(axis=1, how="all")
    cnt = cnt[med.columns]
    text = [["" if pd.isna(v) else short(v) for v in row] for row in med.to_numpy()]
    fig = go.Figure(go.Heatmap(
        z=med.to_numpy(), x=[str(c) for c in med.columns], y=areas, text=text, texttemplate="%{text}",
        customdata=cnt.to_numpy(), colorscale=SEQ, xgap=2, ygap=2, hoverongaps=False,
        textfont=dict(size=11, color=TEXT),
        colorbar=dict(title=dict(text="Median", font=dict(size=10)), thickness=8, outlinewidth=0, tickformat="~s"),
        hovertemplate="<b>%{y}</b> · %{x}<br>Median rent: KSh %{z:,.0f}<br>Listings: %{customdata:.0f}<extra></extra>"))
    style(fig, height=max(260, 30 * len(areas) + 80), grid=None)
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top")
    return fig
