# streamlit_app.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# AquaBeacon Command Center Frontend
# - Uses existing AquaBeacon JSON/PNG sample outputs
# - Adds Bubble-inspired dummy command-center pages/features
# - No new model logic, APIs, databases, or live routing
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

MAP_FILES = {
    "Water risk composite": "sentinel1_surface_water_mask.png",
    "Sentinel-1 water candidates": "sentinel1_surface_water_mask.png",
    "NDVI vegetation change": "delta_ndvi.png",
    "NDMI moisture change": "delta_ndmi.png",
}

PAGES = [
    "🗺 Dashboard",
    "⚠ Incidents",
    "🕯 Alerts",
    "📸 Monitoring Stations",
    "🚩 Evacuation Routes",
    "🗎 Historical Records",
    "📍 Regions",
    "⚙ AOI Settings",
]

EXPECTED_ASSET_FILES = [
    "aquabeacon_prediction_summary.json",
    "delta_ndmi.png",
    "delta_ndvi.png",
    "sentinel1_surface_water_mask.png",
]

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Moderate": 2, "Low": 3}
RISK_TO_SEVERITY = {"Low": "Low", "Medium": "Moderate", "High": "High", "Unknown": "Low"}

RISK_STYLE = {
    "Low": {"emoji": "🟢", "label": "Low", "action": "Routine monitoring"},
    "Medium": {"emoji": "🟡", "label": "Medium", "action": "Review local conditions"},
    "High": {"emoji": "🔴", "label": "High", "action": "Prioritize monitoring"},
    "Unknown": {"emoji": "⚪", "label": "Unknown", "action": "Check backend outputs"},
}

DUMMY_REGIONS = [
    {
        "region": "Coastal Surge Zone Alpha",
        "risk": "Critical",
        "status": "Active response",
        "population": "42,000",
        "notes": "Dense low-lying coastal area with storm-surge exposure.",
    },
    {
        "region": "Northern Delta Basin",
        "risk": "High",
        "status": "Heightened monitoring",
        "population": "31,500",
        "notes": "River-adjacent basin with floodplain exposure.",
    },
    {
        "region": "Highland Watershed District",
        "risk": "Moderate",
        "status": "Watch",
        "population": "18,200",
        "notes": "Watershed and landslide-prone terrain.",
    },
    {
        "region": "Southern Lowland Plains",
        "risk": "Low",
        "status": "Routine monitoring",
        "population": "25,800",
        "notes": "Baseline control region for non-emergency comparison.",
    },
]

DUMMY_INCIDENTS = [
    {"type": "Water Contamination", "severity": "Critical", "region": "Coastal Surge Zone Alpha", "reported": "13:48", "status": "Uncontained"},
    {"type": "Flash Flood", "severity": "High", "region": "Coastal Surge Zone Alpha", "reported": "13:48", "status": "Active"},
    {"type": "Flood", "severity": "High", "region": "Northern Delta Basin", "reported": "13:55", "status": "Active"},
    {"type": "Storm Surge", "severity": "Moderate", "region": "Highland Watershed District", "reported": "13:55", "status": "Monitoring"},
    {"type": "Drought", "severity": "Low", "region": "Southern Lowland Plains", "reported": "13:55", "status": "Advisory"},
    {"type": "Landslide", "severity": "Low", "region": "Southern Lowland Plains", "reported": "13:48", "status": "Monitoring"},
]

DUMMY_ALERTS = [
    {
        "level": "Emergency",
        "title": "Dam Breach Active Response",
        "message": "Evacuation route published. Follow designated route and report to assembly points.",
        "incident": "Dam Breach",
        "region": "Northern Delta Basin",
        "issued": "13:48",
    },
    {
        "level": "Emergency",
        "title": "Active Flood Response",
        "message": "Residents in low-lying areas should evacuate immediately via designated routes.",
        "incident": "Flood",
        "region": "Northern Delta Basin",
        "issued": "13:55",
    },
    {
        "level": "Warning",
        "title": "Storm Surge Infrastructure Watch",
        "message": "Infrastructure assessment ongoing. Avoid damaged road sections.",
        "incident": "Storm Surge",
        "region": "Highland Watershed District",
        "issued": "13:48",
    },
    {
        "level": "Advisory",
        "title": "Drought Conditions Persist",
        "message": "Conserve water resources and follow rationing guidance from local authorities.",
        "incident": "Drought",
        "region": "Southern Lowland Plains",
        "issued": "13:48",
    },
]

DUMMY_STATIONS = [
    {"station": "Station A-01", "region": "Coastal Surge Zone Alpha", "type": "Water level", "status": "Online", "last": "2 min ago", "value": "High"},
    {"station": "Station B-14", "region": "Northern Delta Basin", "type": "Rain gauge", "status": "Online", "last": "5 min ago", "value": "80 mm"},
    {"station": "Station C-08", "region": "Highland Watershed District", "type": "Soil moisture", "status": "Delayed", "last": "24 min ago", "value": "Moderate"},
    {"station": "Station D-22", "region": "Southern Lowland Plains", "type": "Field camera", "status": "Online", "last": "3 min ago", "value": "Normal"},
]

DUMMY_RECORDS = [
    {"date": "2024-09-21", "event": "Budapest Danube flood context", "risk": "Medium", "source": "AquaBeacon sample"},
    {"date": "2024-08-15", "event": "Budapest no-flood control", "risk": "Low", "source": "AquaBeacon sample"},
    {"date": "2024-07-08", "event": "Houston Hurricane Beryl impact", "risk": "High", "source": "AquaBeacon sample"},
    {"date": "2024-06-20", "event": "Houston no-flood control", "risk": "Low", "source": "AquaBeacon sample"},
]


st.set_page_config(
    page_title="AquaBeacon Command Center",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Minimal safe styling only. Avoid complex custom HTML layouts.
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1450px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .ab-small {
            color: #64748b;
            font-size: 0.9rem;
        }
        .ab-title-note {
            color: #475569;
            font-size: 1rem;
            margin-top: -0.5rem;
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


def make_incidents_from_aquabeacon(overview: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, row in overview.iterrows():
        event_id = row.get("event_id", "")
        risk = row.get("predicted_risk_level", "Unknown")
        severity = RISK_TO_SEVERITY.get(str(risk), "Low")
        rows.append({
            "type": "AquaBeacon AOI Risk",
            "severity": severity,
            "region": AOI_NAMES.get(event_id, event_id),
            "reported": "sample output",
            "status": f"{risk} risk",
            "source": FRIENDLY_NAMES.get(event_id, event_id),
        })
    return rows


def severity_filter_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if "severity" in df.columns:
        df["_order"] = df["severity"].map(lambda x: SEVERITY_ORDER.get(str(x), 9))
        df = df.sort_values("_order").drop(columns=["_order"])
    return df


# -----------------------------
# Load app data
# -----------------------------

overview = load_overview()
events = ordered_events(overview)

if not events:
    st.error("No demo events found in overview.")
    st.stop()


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=170)
    else:
        st.title("🌊 AquaBeacon")

    page = st.radio("Command Navigation", PAGES)

    current_event_id = normalize_event_id(st.session_state.get("selected_event_id", events[0]))
    selected_event_id = st.selectbox(
        "AquaBeacon sample",
        events,
        index=events.index(current_event_id) if current_event_id in events else 0,
        format_func=lambda event_id: FRIENDLY_NAMES.get(event_id, event_id),
    )
    st.session_state["selected_event_id"] = selected_event_id

    st.info("Monitor water risk, routes, alerts, and response context. Dummy command-center features are clearly separated from AquaBeacon outputs.")


summary = get_summary(selected_event_id)
risk, score = get_risk(summary)
risk_style = RISK_STYLE.get(risk, RISK_STYLE["Unknown"])


# -----------------------------
# Header
# -----------------------------

st.title("🌊 AquaBeacon Command Center")
st.markdown(
    "<div class='ab-title-note'>COMMAND CENTER · LIVE FEED · Copernicus-based water-risk MVP</div>",
    unsafe_allow_html=True,
)

h1, h2, h3, h4 = st.columns([0.28, 0.32, 0.2, 0.2])
with h1:
    st.write(f"**AOI:** {AOI_NAMES.get(selected_event_id, 'Selected AOI')}")
with h2:
    st.write(f"**Sample:** {FRIENDLY_NAMES.get(selected_event_id, selected_event_id)}")
with h3:
    st.write(f"**Risk:** {risk_style['emoji']} {risk}")
with h4:
    st.write(f"**Score:** {score}")

st.divider()


# -----------------------------
# Shared render functions
# -----------------------------

def render_kpis() -> None:
    active_events = len(DUMMY_INCIDENTS) + len(make_incidents_from_aquabeacon(overview))
    emergency_count = sum(1 for a in DUMMY_ALERTS if a["level"] == "Emergency")
    affected_regions = len({r["region"] for r in DUMMY_REGIONS})
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Active Events", active_events, help="Dummy command-center incidents plus AquaBeacon sample incidents.")
    with k2:
        st.metric("Emergency Alerts", emergency_count)
    with k3:
        st.metric("Affected Regions", affected_regions)
    with k4:
        st.metric("Selected AOI Risk", f"{risk_style['emoji']} {risk}", delta=f"Score {score}", delta_color="off")


def render_map_view(default_layer: str = "Water risk composite") -> None:
    layer = st.radio(
        "Map layer",
        list(MAP_FILES.keys()),
        index=list(MAP_FILES.keys()).index(default_layer),
        horizontal=True,
    )
    image_path = SAMPLES_DIR / selected_event_id / MAP_FILES[layer]

    st.subheader(f"🗺 Live Risk Map — {layer}")
    st.caption("Existing PNG evidence-layer viewer. This is not a live GIS service.")

    if image_path.exists():
        st.image(str(image_path), width="stretch")
    else:
        st.warning(f"Missing map layer: {image_path}")

    st.caption("Low / Moderate / High / Critical labels in the command center are UI status categories. AquaBeacon's real score is the selected AOI risk above.")


def render_aquabeacon_risk_panel() -> None:
    left, right = st.columns([0.45, 0.55])

    with left:
        st.subheader("AquaBeacon Risk Output")
        st.metric(
            label="Risk level",
            value=f"{risk_style['emoji']} {risk}",
            delta=f"Score {score}",
            delta_color="off",
        )
        st.info(risk_interpretation(risk))

    with right:
        st.subheader("Key Signals")
        k1, k2 = st.columns(2)
        with k1:
            st.metric("Rainfall input", f"{safe_get(summary, ['live_inputs', 'forecast_rain_mm'], '—')} mm")
            st.metric("NDVI mean", safe_get(summary, ["indicators", "delta_ndvi", "mean"], "—"))
        with k2:
            st.metric("S1 candidates", f"{safe_get(summary, ['live_inputs', 'sentinel1_surface_water_change_percent'], '—')}%")
            st.metric("NDMI mean", safe_get(summary, ["indicators", "delta_ndmi", "mean"], "—"))


def render_recent_incidents() -> None:
    st.subheader("Recent Active Incidents")
    rows = make_incidents_from_aquabeacon(overview) + DUMMY_INCIDENTS
    df = severity_filter_df(rows)
    st.dataframe(df, hide_index=True, width="stretch")

    selected_incident = st.selectbox(
        "Select incident for route request",
        [f"{r['type']} — {r['region']}" for r in rows],
    )
    if st.button("Request AI Evacuation Routes", width="stretch"):
        st.success(f"Dummy route request generated for: {selected_incident}")


def render_alert_cards() -> None:
    st.subheader("Active Alerts")
    st.caption("Unresolved advisories, watches, warnings, and emergencies. These are dummy operational UI items.")

    for alert in DUMMY_ALERTS:
        with st.container(border=True):
            c1, c2 = st.columns([0.72, 0.28])
            with c1:
                st.write(f"**{alert['level']}: {alert['title']}**")
                st.write(alert["message"])
                st.caption(f"Linked Incident: {alert['incident']} · Linked Region: {alert['region']} · Issued {alert['issued']}")
            with c2:
                st.button("Resolve", key=f"resolve_{alert['title']}", width="stretch")
                st.button("Escalate", key=f"escalate_{alert['title']}", width="stretch")


def render_evidence() -> None:
    st.subheader("AquaBeacon Evidence")
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
    st.subheader("Decision-Maker Report")
    st.write(f"**AOI label:** {get_label(summary)}")
    st.write(f"**Observation window:** {get_window(summary)}")
    st.write(f"**Risk summary:** {risk_interpretation(risk)}")
    st.write(f"**Suggested action:** {recommended_action(risk)}")
    st.warning(
        "Prototype note: AquaBeacon is an early-warning MVP. It is not a confirmed flood-extent map and not a hydrological forecast model."
    )

    st.download_button(
        "⬆ Export AquaBeacon Report",
        data=build_report(selected_event_id, summary),
        file_name=f"{selected_event_id}_aquabeacon_report.md",
        mime="text/markdown",
        width="stretch",
    )


def render_stations() -> None:
    st.subheader("Monitoring Stations")
    st.caption("Dummy field-monitoring feature based on the teammate frontend concept.")
    st.dataframe(pd.DataFrame(DUMMY_STATIONS), hide_index=True, width="stretch")

    with st.expander("Add station — dummy form"):
        with st.form("station_form"):
            st.text_input("Station name")
            st.selectbox("Station type", ["Water level", "Rain gauge", "Soil moisture", "Field camera"])
            st.selectbox("Region", [r["region"] for r in DUMMY_REGIONS])
            submitted = st.form_submit_button("Save dummy station")
            if submitted:
                st.success("Dummy station saved for presentation purposes.")


def render_routes() -> None:
    st.subheader("AI Evacuation Routes")
    st.caption("Dummy route-generation UI. No live routing API is connected.")

    incidents = make_incidents_from_aquabeacon(overview) + DUMMY_INCIDENTS
    selected = st.selectbox(
        "Active incident",
        [f"{i['type']} — {i['region']} ({i['severity']})" for i in incidents],
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Primary route", "Route A")
    with col2:
        st.metric("Estimated clearance", "24 min")
    with col3:
        st.metric("Status", "Draft")

    st.info(f"Dummy route generated for {selected}. In a future version, this could connect to routing and road-closure data.")
    if st.button("Publish route as alert", width="stretch"):
        st.success("Dummy route published to alert feed.")


def render_records() -> None:
    st.subheader("Historical Records")
    st.caption("AquaBeacon sample history plus dummy command-center records.")
    records = DUMMY_RECORDS + [
        {"date": "demo", "event": r["type"], "risk": r["severity"], "source": "Dummy command-center incident"}
        for r in DUMMY_INCIDENTS
    ]
    st.dataframe(pd.DataFrame(records), hide_index=True, width="stretch")


def render_regions() -> None:
    st.subheader("Regions")
    st.caption("Dummy region registry used by the command-center UI.")
    st.dataframe(pd.DataFrame(DUMMY_REGIONS), hide_index=True, width="stretch")


def render_settings() -> None:
    st.subheader("AOI Settings")
    st.caption("Read-only demo settings. No model configuration is changed here.")
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        st.write(f"**AOI:** {AOI_NAMES.get(selected_event_id, 'Selected AOI')}")
        st.write(f"**Sample:** {FRIENDLY_NAMES.get(selected_event_id, selected_event_id)}")
        st.write(f"**Label:** {get_label(summary)}")
        st.write(f"**Window:** {get_window(summary)}")
        st.write(f"**Risk:** {risk} / Score {score}")
    with c2:
        st.write("**Demo health check**")
        st.dataframe(health_check(overview), hide_index=True, width="stretch")


# -----------------------------
# Pages
# -----------------------------

if page == "🗺 Dashboard":
    st.subheader("Risk Monitoring Dashboard")
    st.caption("Real-time situational awareness style view using AquaBeacon sample outputs plus dummy command-center features.")

    render_kpis()

    c_left, c_right = st.columns([0.55, 0.45], gap="large")
    with c_left:
        render_map_view()
    with c_right:
        render_aquabeacon_risk_panel()
        st.divider()
        render_recent_incidents()

    st.divider()
    render_alert_cards()

elif page == "⚠ Incidents":
    render_recent_incidents()

elif page == "🕯 Alerts":
    render_alert_cards()

elif page == "📸 Monitoring Stations":
    render_stations()

elif page == "🚩 Evacuation Routes":
    render_routes()

elif page == "🗎 Historical Records":
    render_records()

elif page == "📍 Regions":
    render_regions()

elif page == "⚙ AOI Settings":
    render_settings()


st.divider()

with st.expander("AquaBeacon evidence"):
    render_evidence()

with st.expander("Decision-maker report"):
    render_report()

with st.expander("Compare AquaBeacon demo samples"):
    st.dataframe(overview_table(overview), hide_index=True, width="stretch")

with st.expander("Data sources and prototype scope"):
    st.write(
        "Data sources: Copernicus Sentinel-1 GRD, Copernicus Sentinel-2 L2A, rainfall input, "
        "historical AOI exposure, and AquaBeacon rule-based scoring outputs."
    )
    st.write(
        "Scope: The command-center pages include dummy UI features. The real MVP output is the AquaBeacon "
        "risk score, JSON summaries, and PNG evidence layers."
    )
