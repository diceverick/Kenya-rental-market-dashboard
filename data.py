"""Data loading, cleaning, outlier flagging, filtering and aggregation."""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_FILE = "buyrent_rentals_data.xlsx"
PRICE, BEDS, SIZE = "Price (KSh)", "Bedrooms", "Size (sq ft)"
CITY, NB, PPSF = "City", "Neighborhood", "KSh per sq ft"
REQUIRED = [PRICE, BEDS, CITY, NB]
OUTLIER_Z = 4.0          # modified z-score threshold on log-rent
MIN_LOCAL_GROUP = 15     # bedroom groups smaller than this use the global baseline
INTERNAL = ["Area", "BedLabel", "OutlierZ"]

_SUFFIX = re.compile(r"\s*-\s*(?:image|thumbnail)\s*\d+\s*$", re.I)
_CATEGORY_RULES = [
    (r"office", "Office"),
    (r"\b(?:shop|retail|showroom|restaurant|commercial)\b", "Retail / commercial"),
    (r"warehouse|godown|industrial|factory", "Industrial"),
    (r"\b(?:land|plot)\b", "Land"),
    (r"bedsit", "Bedsitter"),
    (r"maisonette|townhouse|town house|villa|bungalow|mansion|\bhouse\b|duplex|cottage", "House"),
    (r"apartment|flat|penthouse|studio|condo", "Apartment"),
]


# ---------------------------------------------------------------- formatting
def ksh(x) -> str:
    return "–" if pd.isna(x) else f"KSh {x:,.0f}"


def short(x) -> str:
    if pd.isna(x):
        return "–"
    a = abs(x)
    if a >= 1e6:
        return f"{x / 1e6:.2f}".rstrip("0").rstrip(".") + "M"
    if a >= 1e3:
        return f"{x / 1e3:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{x:.0f}"


def bed_label(b) -> str:
    if pd.isna(b):
        return "N/A"
    return "Studio" if b == 0 else f"{b:g} BR"


def data_path() -> Path:
    for p in (Path(__file__).resolve().parent / DATA_FILE, Path.cwd() / DATA_FILE):
        if p.exists():
            return p
    return Path(DATA_FILE)


# ------------------------------------------------------------------ cleaning
def _clean_text(s: pd.Series) -> pd.Series:
    def f(v):
        if pd.isna(v):
            return None
        t = _SUFFIX.sub("", str(v)).strip()
        return None if t.lower() in {"", "n/a", "nan", "none"} else t
    return s.map(f).astype("object")


def _num(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce")
    t = (s.astype("string").str.lower().str.replace("studio", "0", regex=False)
         .str.replace(r"[^\d.]", "", regex=True))
    return pd.to_numeric(t.replace("", pd.NA), errors="coerce")


def _category(df: pd.DataFrame) -> tuple[pd.Series, bool]:
    for col in ("Property Type", "Property type", "Type", "Category"):
        if col in df.columns:
            return df[col].fillna("Unspecified"), False
    if "Title" not in df.columns:
        return pd.Series("Unspecified", index=df.index), False
    t = df["Title"].fillna("").str.lower()
    out = pd.Series("Other", index=df.index)
    for pat, lab in reversed(_CATEGORY_RULES):  # earlier rules take precedence
        out[t.str.contains(pat, regex=True)] = lab
    return out, True


def _flag_outliers(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Modified z-score (MAD) on log-rent, within bedroom group when the group
    is large enough, otherwise against the whole dataset. Two-sided."""
    lp = np.log(df[PRICE])
    key = df[BEDS].fillna(-1)
    n = lp.groupby(key).transform("size")
    med = lp.groupby(key).transform("median")
    mad = (lp - med).abs().groupby(key).transform("median")
    g_med = lp.median()
    g_mad = (lp - g_med).abs().median()
    small = n < MIN_LOCAL_GROUP
    med, mad = med.where(~small, g_med), mad.where(~small, g_mad)
    z = 0.6745 * (lp - med) / mad.where(mad > 0)
    return z.abs().gt(OUTLIER_Z), z


@st.cache_data(show_spinner="Loading dataset…")
def load_data(path: str, mtime: float) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(path)
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}. "
                         f"Columns found: {', '.join(raw.columns)}")
    df = raw.copy()
    for c in df.columns:
        if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
            df[c] = _clean_text(df[c])
    df[PRICE], df[BEDS] = _num(df[PRICE]), _num(df[BEDS])
    df[SIZE] = _num(df[SIZE]) if SIZE in df.columns else np.nan
    df[CITY], df[NB] = df[CITY].fillna("Unspecified"), df[NB].fillna("Unspecified")

    valid = df[PRICE].gt(0)
    meta = {"rows_raw": len(df), "invalid_price": int((~valid).sum())}
    df = df[valid].copy()

    df["Category"], meta["category_derived"] = _category(df)
    cities_per_nb = df.groupby(NB)[CITY].nunique()
    dup = cities_per_nb[cities_per_nb > 1].index
    df["Area"] = np.where(df[NB].isin(dup), df[NB] + " · " + df[CITY], df[NB])
    order = [bed_label(b) for b in sorted(df[BEDS].dropna().unique())]
    if df[BEDS].isna().any():
        order.append("N/A")
    df["BedLabel"] = pd.Categorical(df[BEDS].map(bed_label), categories=order, ordered=True)
    df[PPSF] = df[PRICE] / df[SIZE].where(df[SIZE] > 0)
    df["Outlier"], df["OutlierZ"] = _flag_outliers(df)

    meta.update(n_outliers=int(df["Outlier"].sum()), size_missing=int(df[SIZE].isna().sum()),
                beds_missing=int(df[BEDS].isna().sum()), rows=len(df))
    return df.reset_index(drop=True), meta


# ----------------------------------------------------------------- filtering
def apply_filters(df: pd.DataFrame, f: dict, bounds: dict) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    if f["excl"]:
        m &= ~df["Outlier"]
    if f["city"]:
        m &= df[CITY].isin(f["city"])
    if f["nb"]:
        m &= df["Area"].isin(f["nb"])
    if f["bed"]:
        m &= df["BedLabel"].astype(str).isin(f["bed"])
    if f["cat"]:
        m &= df["Category"].isin(f["cat"])
    if tuple(f["price"]) != tuple(bounds["price"]):
        m &= df[PRICE].between(*f["price"])
    if bounds["size"] and tuple(f["size"]) != tuple(bounds["size"]):
        m &= df[SIZE].between(*f["size"]) | (df[SIZE].isna() & f["nosize"])
    return df[m]


def slider_bounds(df: pd.DataFrame) -> dict:
    """Slider ranges ignore flagged outliers so one bad listing cannot stretch them."""
    core = df[~df["Outlier"]] if (~df["Outlier"]).any() else df
    span = core[PRICE].max() - core[PRICE].min()
    step = 1000 if span > 20000 else 100
    lo = int(math.floor(core[PRICE].min() / step) * step)
    hi = max(int(math.ceil(core[PRICE].max() / step) * step), lo + step)
    sizes = core[SIZE].dropna()
    sb = None
    if len(sizes):
        s0, s1 = int(math.floor(sizes.min() / 50) * 50), int(math.ceil(sizes.max() / 50) * 50)
        sb = (s0, max(s1, s0 + 50))
    return {"price": (lo, hi), "size": sb, "step": step}


# --------------------------------------------------------------- aggregation
def grp_stats(df: pd.DataFrame, key: str, min_n: int = 1) -> pd.DataFrame:
    cols = [key, "Listings", "Mean", "Median", "Min", "Max", "Std", "Q1", "Q3", "CV"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    s = df.groupby(key, observed=True)[PRICE].agg(
        Listings="size", Mean="mean", Median="median", Min="min", Max="max", Std="std",
        Q1=lambda x: x.quantile(0.25), Q3=lambda x: x.quantile(0.75))
    s["CV"] = s["Std"] / s["Mean"]
    if key == "Area":
        s["City"] = df.groupby("Area")[CITY].first()
    return s[s["Listings"] >= min_n].reset_index()


def ranked(df: pd.DataFrame, key: str = "Area", min_n: int = 3) -> tuple[pd.DataFrame, int]:
    s = grp_stats(df, key, min_n)
    if s.empty and min_n > 1:
        return grp_stats(df, key, 1), 1
    return s, min_n
