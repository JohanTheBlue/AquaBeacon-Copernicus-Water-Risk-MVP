# AquaBeacon

## Dashboard Preview

![AquaBeacon dashboard](screenshots/aquabeacon_dashboard.png)

AquaBeacon is a lightweight Copernicus-based early-warning MVP for water-related environmental risk.

It combines existing backend outputs from Sentinel-1, Sentinel-2, rainfall input, and historical AOI exposure into a simple, explainable Low / Medium / High risk signal shown in a Streamlit dashboard.

## What this MVP demonstrates

- A working Python/openEO backend pipeline that produces JSON summaries and PNG evidence maps.
- A Streamlit dashboard that presents the output in a decision-maker-friendly way.
- Four final demo samples:
  - Budapest Parliament — no-flood control: Low
  - Budapest Parliament — September 2024 flood event: Medium
  - Houston — no-flood control: Low
  - Houston — Hurricane Beryl impact: High
- A downloadable quick report for each AOI/event.

## MVP scope

AquaBeacon is not a full hydrological forecast model and does not claim confirmed flood extent.

The current prototype is intentionally rule-based and transparent. The satellite layers are evidence layers, not final flood maps.

## Required files

Expected project structure:

```text
streamlit_app.py
requirements.txt
logo.png
cover.png / cover2.png optional
samples/
  aquabeacon_sample_overview.csv
  aquabeacon_sample_overview.json
  budapest_parliament_aug_2024_no_flood_control/
  budapest_parliament_sep_2024/
  houston_jun_2024_no_flood_control/
  houston_beryl_jul_2024/
```

Each sample folder should contain:

```text
aquabeacon_prediction_summary.json
delta_ndmi.png
delta_ndvi.png
sentinel1_surface_water_mask.png
```

## Run the dashboard

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Final demo flow

1. Show the hero section and four sample cards.
2. Open Houston — Beryl impact and show High risk.
3. Open Houston — Control and show Low risk.
4. Open Budapest Parliament — Flood event and explain why it is Medium:
   the event was significant in reality, but the MVP does not ingest river gauge or upstream hydrology.
5. Show the quick report export.
6. Mention that AquaBeacon is an early-warning prototype, not a hydrological forecast model.

## Do not add before submission

- New APIs
- Snow model
- River gauges
- Hydrological routing
- 20-day prediction
- Extra indicators
- Complex hydrological forecasting
