"""Kenya Real Estate Market Intelligence · launch with: streamlit run app.py"""
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Kenya Real Estate · Market Intelligence", layout="wide",
                   initial_sidebar_state="expanded")

import data as D  # noqa: E402
import theme as T  # noqa: E402
import views  # noqa: E402

T.inject_css()

path = D.data_path()
if not path.exists():
    st.error(f"Dataset not found: `{D.DATA_FILE}`. Place it next to app.py (or run Streamlit from its folder).")
    st.stop()
try:
    df, meta = D.load_data(str(path), path.stat().st_mtime)
except Exception as exc:  # surfaced to the user rather than a stack trace
    st.error(f"Could not read `{path.name}`: {exc}")
    st.stop()
meta["source"] = path.name
meta["updated"] = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d %b %Y")


def sidebar(df):
    ss, sb = st.session_state, st.sidebar
    bounds = D.slider_bounds(df)
    defaults = {"f_city": [], "f_nb": [], "f_bed": [], "f_cat": [], "f_price": bounds["price"],
                "f_size": bounds["size"] or (0, 0), "f_nosize": True, "f_excl": True}
    for k, v in defaults.items():
        ss.setdefault(k, v)

    def reset():
        for k, v in defaults.items():
            ss[k] = v
    # keep stored ranges valid if the dataset changed between runs
    lo, hi = bounds["price"]
    ss["f_price"] = (max(lo, ss["f_price"][0]), min(hi, ss["f_price"][1]))

    sb.markdown('<div class="side-t">Filters</div>', unsafe_allow_html=True)
    slot = sb.empty()
    sb.button("Reset filters", on_click=reset, width="stretch")

    sb.markdown('<div class="side-l">Region</div>', unsafe_allow_html=True)
    sb.multiselect("Region", sorted(df[D.CITY].unique()), key="f_city", placeholder="All regions", label_visibility="collapsed")
    avail = df[df[D.CITY].isin(ss["f_city"])] if ss["f_city"] else df
    nb_opts = sorted(avail["Area"].unique())
    ss["f_nb"] = [v for v in ss["f_nb"] if v in nb_opts]
    sb.markdown('<div class="side-l">Neighbourhood</div>', unsafe_allow_html=True)
    sb.multiselect("Neighbourhood", nb_opts, key="f_nb", placeholder="All neighbourhoods", label_visibility="collapsed")
    sb.markdown('<div class="side-l">Bedrooms</div>', unsafe_allow_html=True)
    sb.multiselect("Bedrooms", list(df["BedLabel"].cat.categories), key="f_bed", placeholder="Any", label_visibility="collapsed")
    sb.markdown('<div class="side-l">Property category</div>', unsafe_allow_html=True)
    sb.multiselect("Category", sorted(df["Category"].unique()), key="f_cat", placeholder="All categories", label_visibility="collapsed")
    sb.markdown('<div class="side-l">Monthly rent (KSh)</div>', unsafe_allow_html=True)
    sb.slider("Rent", lo, hi, key="f_price", step=bounds["step"], label_visibility="collapsed")
    if bounds["size"]:
        sb.markdown('<div class="side-l">Property size (sq ft)</div>', unsafe_allow_html=True)
        sb.slider("Size", *bounds["size"], key="f_size", step=50, label_visibility="collapsed")
        sb.checkbox("Include listings with no size", key="f_nosize")
    sb.markdown('<div class="side-l">Data quality</div>', unsafe_allow_html=True)
    sb.toggle("Exclude statistical outliers", key="f_excl")
    sb.caption(f"{meta['n_outliers']:,} listings flagged. Rent and size ranges ignore flagged listings until moved.")

    f = {k[2:]: ss[k] for k in defaults}
    out = D.apply_filters(df, f, bounds)
    slot.markdown(f'<div class="cnt"><b>{len(out):,}</b><span>of {len(df):,} listings match</span></div>', unsafe_allow_html=True)
    return out


fdf = sidebar(df)


def page(fn, title, slug, default=False):
    def run():
        fn(fdf, df, meta)
    run.__name__ = slug
    return st.Page(run, title=title, url_path=slug, default=default)


pages = [page(views.overview, "Market Overview", "overview", True),
         page(views.rental, "Rental Analysis", "rental"),
         page(views.geographic, "Geographic Analysis", "geographic"),
         page(views.insights, "Property Insights", "insights"),
         page(views.explorer, "Data Explorer", "explorer")]
try:
    nav = st.navigation(pages, position="top")
except TypeError:  # older Streamlit without top navigation
    nav = st.navigation(pages)
nav.run()