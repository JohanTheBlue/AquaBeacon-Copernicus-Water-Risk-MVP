# streamlit_app.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# AquaBeacon — Stable Native Streamlit Dashboard
# Existing backend outputs only. No new model logic.
# No custom HTML layout, so no visible </div> bugs.
# ============================================================

SAMPLES_DIR = Path("samples")
OVERVIEW_JSON = SAMPLES_DIR / "aquabeacon_sample_overview.json"
OVERVIEW_CSV = SAMPLES_DIR / "aquabeacon_sample_overview.csv"
LOGO_PATH = Path("logo.png")

EVENT_ORDER = [
    "budapest_parliament_aug_2024_no_flood_control",
    "budapest_parliament_sep_2024",
    "houston_jun_2024_no_flood_control",
    "houston_beryl_jul_2024",
]

FRIENDLY_NAMES = {
    "budapest_parliament_aug_2024_no_flood_control": "Budapest Parliament — Control",
    "budapest_parliament_sep_2024": "Budapest Parliament — Flood event",
    "houston_jun_2024_no_flood_control": "Houston — Control",
    "houston_beryl_jul_2024": "Houston — Beryl impact",
}

AOI_NAMES = {
    "budapest_parliament_aug_2024_no_flood_control": "Budapest Parliament",
    "budapest_parliament_sep_2024": "Budapest Parliament",
    "houston_jun_2024_no_flood_control": "Houston AOI",
    "houston_beryl_jul_2024": "Houston AOI",
}

SHORT_DESCRIPTIONS = {
    "budapest_parliament_aug_2024_no_flood_control": "Same Danube-side AOI during a no-flood control window.",
    "budapest_parliament_sep_2024": "Known Danube flood context near the Hungarian Parliament.",
    "houston_jun_2024_no_flood_control": "Same Houston AOI before Hurricane Beryl.",
    "houston_beryl_jul_2024": "Storm-impact sample with extreme rainfall input.",
}

MAP_FILES = {
    "Water risk composite": "sentinel1_surface_water_mask.png",
    "Sentinel-1 water candidates": "sentinel1_surface_water_mask.png",
    "NDVI vegetation change": "delta_ndvi.png",
    "NDMI moisture change": "delta_ndmi.png",
}

PAGES = [
    "⌂ Overview",
    "▱ Map Layers",
    "▥ Evidence",
    "▤ Reports",
    "⚙ AOI Settings",
]

EXPECTED_ASSET_FILES = [
    "aquabeacon_prediction_summary.json",
    "delta_ndmi.png",
    "delta_ndvi.png",
    "sentinel1_surface_water_mask.png",
]

RISK_STYLE = {
    "Low": {"emoji": "🟢", "label": "Low", "action": "Routine monitoring"},
    "Medium": {"emoji": "🟡", "label": "Medium", "action": "Review local conditions"},
    "High": {"emoji": "🔴", "label": "High", "action": "Prioritize monitoring"},
    "Unknown": {"emoji": "⚪", "label": "Unknown", "action": "Check backend outputs"},
}


st.set_page_config(
    page_title="AquaBeacon Water Risk Overview",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Minimal safe CSS only. Do not hide the Streamlit header/sidebar controls.
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1400px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Data helpers
# -----------------------------

@st.cache_data(show_spinner=False)
def read_json(path: str) -> dict[str, Any] | list[Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_overview() -> pd.DataFrame:
    if OVERVIEW_CSV.exists():
        df = pd.read_csv(OVERVIEW_CSV)
    elif OVERVIEW_JSON.exists():
        data = read_json(str(OVERVIEW_JSON))
        df = pd.DataFrame(data)
    else:
        st.error("Missing sample overview. Run make_sample_overview.py first.")
        st.stop()

    if "event_id" not in df.columns:
        st.error("Overview file is missing event_id.")
        st.stop()

    return df


def normalize_event_id(event_id: Any) -> str:
    if isinstance(event_id, tuple):
        return str(event_id[0])
    return str(event_id)


@st.cache_data(show_spinner=False)
def get_summary(event_id: str) -> dict[str, Any]:
    event_id = normalize_event_id(event_id)
    data = read_json(str(SAMPLES_DIR / event_id / "aquabeacon_prediction_summary.json"))
    return data if isinstance(data, dict) else {}


def ordered_events(overview: pd.DataFrame) -> list[str]:
    existing = set(overview["event_id"].tolist())
    ordered = [event_id for event_id in EVENT_ORDER if event_id in existing]
    ordered += [event_id for event_id in overview["event_id"].tolist() if event_id not in ordered]
    return ordered


def safe_get(obj: dict[str, Any], path: list[str], fallback: Any = "—") -> Any:
    value: Any = obj
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return fallback
        value = value[key]
    if isinstance(value, float):
        return round(value, 4)
    return value


def get_risk(summary: dict[str, Any]) -> tuple[str, Any]:
    prediction = summary.get("prediction", {})
    return prediction.get("predicted_risk_level", "Unknown"), prediction.get("risk_score", "—")


def get_label(summary: dict[str, Any]) -> str:
    event_label = summary.get("event_label", {})
    if isinstance(event_label, dict) and event_label.get("display_label"):
        return str(event_label["display_label"])
    if summary.get("known_event") is True:
        return "Known flood / impact event"
    if summary.get("known_event") is False:
        return "No-flood control"
    return "Unlabelled sample"


def get_window(summary: dict[str, Any]) -> str:
    recent = summary.get("recent_period")
    if isinstance(recent, list) and len(recent) == 2:
        return f"{recent[0]} → {recent[1]}"
    event_date = summary.get("event_date")
    return str(event_date) if event_date else "Selected event window"


def risk_interpretation(risk: str) -> str:
    if risk == "Low":
        return "Low active water-risk for the selected observation window. This is useful as a control or baseline case."
    if risk == "Medium":
        return "Medium water-risk awareness signal. Review local conditions and compare with official warnings."
    if risk == "High":
        return "High water-risk signal. Prioritize monitoring of exposed areas and validate with local reports."
    return "Risk classification unavailable from the current output."


def recommended_action(risk: str) -> str:
    return RISK_STYLE.get(risk, RISK_STYLE["Unknown"])["action"]


def build_report(event_id: str, summary: dict[str, Any]) -> str:
    risk, score = get_risk(summary)
    event_name = FRIENDLY_NAMES.get(event_id, event_id)
    return f"""# AquaBeacon Decision-Maker Report

**AOI / event:** {event_name}  
**AOI label:** {get_label(summary)}  
**Risk level:** {risk}  
**Risk score:** {score}  
**Observation window:** {get_window(summary)}  

## Main detected signals

- Rainfall input: {safe_get(summary, ["live_inputs", "forecast_rain_mm"], "—")} mm
- Historical exposure: {safe_get(summary, ["historical_risk", "label"], "—")}
- Sentinel-1 surface-water-change candidates: {safe_get(summary, ["live_inputs", "sentinel1_surface_water_change_percent"], "—")}%
- Sentinel-2 NDVI mean change: {safe_get(summary, ["indicators", "delta_ndvi", "mean"], "—")}
- Sentinel-2 NDMI mean change: {safe_get(summary, ["indicators", "delta_ndmi", "mean"], "—")}

## Plain-English interpretation

{risk_interpretation(risk)}

## Recommended next action

{recommended_action(risk)}

## Limitations / confidence note

AquaBeacon is an early-warning MVP. It does not claim confirmed flood extent and is not a hydrological forecast model. The maps are satellite evidence layers that support local risk awareness.

## Data sources used

Copernicus Sentinel-1, Copernicus Sentinel-2, rainfall input, historical AOI exposure, AquaBeacon rule-based scoring outputs.
"""


def overview_table(overview: pd.DataFrame) -> pd.DataFrame:
    cols = [
        c for c in [
            "event_id",
            "rainfall_mm",
            "sentinel1_surface_water_change_percent",
            "delta_ndvi_mean",
            "delta_ndmi_mean",
            "risk_score",
            "predicted_risk_level",
        ] if c in overview.columns
    ]
    df = overview[cols].copy()
    if "event_id" in df.columns:
        df["Sample"] = df["event_id"].map(lambda x: FRIENDLY_NAMES.get(x, x))
        df = df.drop(columns=["event_id"])
        df = df[["Sample"] + [c for c in df.columns if c != "Sample"]]
    return df.rename(columns={
        "rainfall_mm": "Rainfall (mm)",
        "sentinel1_surface_water_change_percent": "S1 candidates (%)",
        "delta_ndvi_mean": "NDVI",
        "delta_ndmi_mean": "NDMI",
        "risk_score": "Score",
        "predicted_risk_level": "Risk",
    })


def health_check(overview: pd.DataFrame) -> pd.DataFrame:
    overview_ids = set(overview["event_id"].tolist())
    rows: list[dict[str, str]] = []
    for event_id in EVENT_ORDER:
        sample_dir = SAMPLES_DIR / event_id
        missing = [name for name in EXPECTED_ASSET_FILES if not (sample_dir / name).exists()]
        rows.append({
            "Sample": FRIENDLY_NAMES.get(event_id, event_id),
            "In overview": "yes" if event_id in overview_ids else "missing",
            "Folder": "yes" if sample_dir.exists() else "missing",
            "Assets": "ready" if not missing else ", ".join(missing),
        })
    return pd.DataFrame(rows)


# -----------------------------
# Sidebar
# -----------------------------

overview = load_overview()
events = ordered_events(overview)

if not events:
    st.error("No demo events found in overview.")
    st.stop()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=170)
    else:
        st.title("🌊 AquaBeacon")

    page = st.radio("Navigation", PAGES)

    current_event_id = normalize_event_id(st.session_state.get("selected_event_id", events[0]))
    selected_event_id = st.selectbox(
        "Demo sample",
        events,
        index=events.index(current_event_id) if current_event_id in events else 0,
        format_func=lambda event_id: FRIENDLY_NAMES.get(event_id, event_id),
    )
    st.session_state["selected_event_id"] = selected_event_id

    st.info("AquaBeacon is a Copernicus-based water-risk MVP for decision support.")


summary = get_summary(selected_event_id)
risk, score = get_risk(summary)
risk_style = RISK_STYLE.get(risk, RISK_STYLE["Unknown"])


# -----------------------------
# Header
# -----------------------------

st.title("🌊 AquaBeacon — Water Risk Overview")

header_cols = st.columns([0.34, 0.26, 0.2, 0.2])
with header_cols[0]:
    st.write(f"**AOI:** {AOI_NAMES.get(selected_event_id, 'Selected AOI')}")
with header_cols[1]:
    st.write(f"**Sample:** {FRIENDLY_NAMES.get(selected_event_id, selected_event_id)}")
with header_cols[2]:
    st.write(f"**Window:** {get_window(summary)}")
with header_cols[3]:
    st.write(f"**Label:** {get_label(summary)}")

st.caption(SHORT_DESCRIPTIONS.get(selected_event_id, "Selected AquaBeacon sample."))

st.divider()


# -----------------------------
# Shared render functions
# -----------------------------

def render_risk_panel() -> None:
    left, right = st.columns([0.45, 0.55])

    with left:
        st.subheader("Current Risk Level")
        st.metric(
            label="Risk",
            value=f"{risk_style['emoji']} {risk}",
            delta=f"Score {score}",
            delta_color="off",
        )
        st.info(risk_interpretation(risk))

    with right:
        st.subheader("Key indicators")
        k1, k2 = st.columns(2)
        with k1:
            st.metric("Rainfall input", f"{safe_get(summary, ['live_inputs', 'forecast_rain_mm'], '—')} mm")
            st.metric("NDVI mean", safe_get(summary, ["indicators", "delta_ndvi", "mean"], "—"))
        with k2:
            st.metric("S1 candidates", f"{safe_get(summary, ['live_inputs', 'sentinel1_surface_water_change_percent'], '—')}%")
            st.metric("NDMI mean", safe_get(summary, ["indicators", "delta_ndmi", "mean"], "—"))


def render_map_view(default_layer: str = "Water risk composite") -> None:
    layer = st.radio(
        "Map layer",
        list(MAP_FILES.keys()),
        index=list(MAP_FILES.keys()).index(default_layer),
        horizontal=True,
    )
    image_path = SAMPLES_DIR / selected_event_id / MAP_FILES[layer]

    st.subheader(f"▱ Map View — {layer}")
    st.caption("Lightweight evidence-layer viewer from existing PNG outputs. This is not a live GIS map.")

    if image_path.exists():
        st.image(str(image_path), width="stretch")
    else:
        st.warning(f"Missing map layer: {image_path}")

    st.caption("Evidence layers support the score but do not represent confirmed flood extent.")


def render_evidence() -> None:
    st.subheader("▥ Evidence")

    reasons = summary.get("prediction", {}).get("reasons", [])
    if reasons:
        for reason in reasons:
            st.write(f"• {reason}")
    else:
        st.write("No scoring reasons found in the current summary.")

    st.markdown("### Evidence previews")
    preview_cols = st.columns(3)
    previews = {
        "Sentinel-1 candidates": "sentinel1_surface_water_mask.png",
        "NDVI change": "delta_ndvi.png",
        "NDMI change": "delta_ndmi.png",
    }
    for col, (title, filename) in zip(preview_cols, previews.items()):
        with col:
            st.write(f"**{title}**")
            image_path = SAMPLES_DIR / selected_event_id / filename
            if image_path.exists():
                st.image(str(image_path), width="stretch")
            else:
                st.info(f"Missing: {filename}")


def render_report() -> None:
    st.subheader("▤ Decision-Maker Report")
    st.write(f"**Risk summary:** {risk_interpretation(risk)}")
    st.write(f"**Suggested action:** {recommended_action(risk)}")
    st.write(
        "**Limitations:** AquaBeacon is an early-warning MVP. "
        "It is not a confirmed flood-extent map and not a hydrological forecast model."
    )

    st.download_button(
        "⬆ Export Report",
        data=build_report(selected_event_id, summary),
        file_name=f"{selected_event_id}_aquabeacon_report.md",
        mime="text/markdown",
        width="stretch",
    )


# -----------------------------
# Pages
# -----------------------------

if page == "⌂ Overview":
    top_left, top_right = st.columns([0.52, 0.48], gap="large")
    with top_left:
        render_map_view()
    with top_right:
        render_risk_panel()
        render_report()

elif page == "▱ Map Layers":
    render_map_view()

elif page == "▥ Evidence":
    render_risk_panel()
    render_evidence()

elif page == "▤ Reports":
    render_report()

elif page == "⚙ AOI Settings":
    st.subheader("⚙ AOI Settings")
    st.caption("Read-only demo settings. No model configuration is changed here.")
    st.write(f"**AOI:** {AOI_NAMES.get(selected_event_id, 'Selected AOI')}")
    st.write(f"**Sample:** {FRIENDLY_NAMES.get(selected_event_id, selected_event_id)}")
    st.write(f"**Label:** {get_label(summary)}")
    st.write(f"**Window:** {get_window(summary)}")
    st.write(f"**Risk:** {risk} / Score {score}")
    st.dataframe(health_check(overview), hide_index=True, width="stretch")


st.divider()

with st.expander("Compare all demo samples"):
    st.dataframe(overview_table(overview), hide_index=True, width="stretch")

with st.expander("Demo health check"):
    st.dataframe(health_check(overview), hide_index=True, width="stretch")

with st.expander("Data sources and prototype scope"):
    st.write(
        "Data sources: Copernicus Sentinel-1 GRD, Copernicus Sentinel-2 L2A, rainfall input, "
        "historical AOI exposure, and AquaBeacon rule-based scoring outputs."
    )
    st.write(
        "Scope: This MVP is a transparent early-warning prototype. It does not ingest river gauges, "
        "perform hydrological routing, or provide confirmed flood-extent mapping."
    )
