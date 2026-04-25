import json
import os
import rasterio
import numpy as np


EVENTS_FILE = "events.json"


def read_raster_stats(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        nodata = src.nodata
        bounds = src.bounds
        crs = src.crs
        width = src.width
        height = src.height

    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    valid = arr[~np.isnan(arr)]

    return {
        "file": path,
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "mean": float(np.nanmean(arr)),
        "std": float(np.nanstd(arr)),
        "p05": float(np.nanpercentile(valid, 5)),
        "p50": float(np.nanpercentile(valid, 50)),
        "p95": float(np.nanpercentile(valid, 95)),
        "width": int(width),
        "height": int(height),
        "bounds": {
            "left": float(bounds.left),
            "bottom": float(bounds.bottom),
            "right": float(bounds.right),
            "top": float(bounds.top),
        },
        "crs": str(crs),
    }


def calculate_risk_score(
    historical_risk_score,
    historical_risk_label,
    ndvi_delta_mean,
    ndmi_delta_mean,
    forecast_rain_mm,
    sentinel1_surface_water_change_percent,
):
    risk_score = 0
    risk_reasons = []

    historical_score = int(historical_risk_score)
    forecast_rain_mm = float(forecast_rain_mm or 0.0)
    s1_percent = float(sentinel1_surface_water_change_percent or 0.0)

    # Historical risk is AOI vulnerability, not active event evidence by itself.
    if historical_score >= 2:
        risk_reasons.append(
            "AOI has high historical flood exposure, but this only increases concern when active triggers are present."
        )
    elif historical_score == 1:
        risk_reasons.append(
            "AOI has medium historical flood exposure, but this only increases concern when active triggers are present."
        )
    else:
        risk_reasons.append(
            "AOI has low historical flood exposure."
        )

    # Rainfall trigger
    rain_trigger = False

    if forecast_rain_mm >= 20:
        risk_score += 1
        rain_trigger = True
        risk_reasons.append("Rainfall exceeds 20 mm, indicating a possible water-risk trigger.")

    if forecast_rain_mm >= 40:
        risk_score += 1
        risk_reasons.append("Rainfall exceeds 40 mm, indicating a stronger water-risk trigger.")

    if forecast_rain_mm >= 75:
        risk_score += 1
        risk_reasons.append("Rainfall exceeds 75 mm, indicating an extreme rainfall trigger.")

    # Only activate historical vulnerability if an active rainfall trigger exists.
    if rain_trigger:
        risk_score += historical_score
        risk_reasons.append(
            f"Historical AOI exposure contributes {historical_score} points because an active rainfall trigger is present."
        )

    # Sentinel-1 evidence.
    # Because the S1 mask is percentile-based, do not use the 5% value alone unless a rainfall trigger exists.
    if rain_trigger and s1_percent >= 5:
        risk_score += 1
        risk_reasons.append(
            "Sentinel-1 shows possible surface-water-change candidates during a rainfall-triggered event window."
        )

    if rain_trigger and s1_percent >= 20:
        risk_score += 1
        risk_reasons.append(
            "Sentinel-1 shows widespread possible surface-water-change candidates."
        )

    # Sentinel-2 evidence.
    # NDVI/NDMI are supporting indicators, not standalone flood proof.
    if rain_trigger and ndvi_delta_mean < -0.05:
        risk_score += 1
        risk_reasons.append("NDVI is lower than baseline during an active trigger window.")

    if rain_trigger and ndmi_delta_mean < -0.05:
        risk_score += 1
        risk_reasons.append("NDMI is lower than baseline during an active trigger window.")

    # Add explicit no-trigger explanation.
    if not rain_trigger:
        risk_reasons.append(
            "No rainfall trigger is present, so historical exposure and satellite changes are treated as context rather than active flood-risk evidence."
        )

    # Final class
    if risk_score <= 1:
        predicted_risk_level = "Low"
    elif risk_score <= 4:
        predicted_risk_level = "Medium"
    else:
        predicted_risk_level = "High"

    return risk_score, predicted_risk_level, risk_reasons

with open(EVENTS_FILE, "r") as f:
    events = json.load(f)

for event in events:
    event_id = event["event_id"]
    output_dir = f"samples/{event_id}"

    ndvi_path = f"{output_dir}/delta_ndvi/openEO.tif"
    ndmi_path = f"{output_dir}/delta_ndmi/openEO.tif"
    sentinel1_path = f"{output_dir}/sentinel1/sentinel1_surface_water_summary.json"
    summary_path = f"{output_dir}/aquabeacon_prediction_summary.json"

    print(f"\nRecomputing prediction for {event_id}")
    
    if not os.path.exists(ndvi_path):
        print(f"Skipping {event_id}: missing {ndvi_path}")
        continue

    if not os.path.exists(ndmi_path):
        print(f"Skipping {event_id}: missing {ndmi_path}")
        continue

    ndvi_stats = read_raster_stats(ndvi_path)
    ndmi_stats = read_raster_stats(ndmi_path)

    sentinel1_percent = event.get("sentinel1_surface_water_change_percent", 0.0)

    if os.path.exists(sentinel1_path):
        print(f"Reading Sentinel-1 summary: {sentinel1_path}")
        with open(sentinel1_path, "r") as f:
            sentinel1_summary = json.load(f)

        sentinel1_percent = sentinel1_summary.get(
            "possible_surface_water_change_percent",
            sentinel1_percent
        )
    else:
        print("No Sentinel-1 summary found; using fallback.")

    historical_risk = event["historical_risk"]
    forecast_rain_mm = event.get("rainfall_mm", 0.0)

    risk_score, risk_level, reasons = calculate_risk_score(
        historical_risk_score=historical_risk["score"],
        historical_risk_label=historical_risk["label"],
        ndvi_delta_mean=ndvi_stats["mean"],
        ndmi_delta_mean=ndmi_stats["mean"],
        forecast_rain_mm=forecast_rain_mm,
        sentinel1_surface_water_change_percent=sentinel1_percent,
    )

    prediction = {
        "event_id": event_id,
        "aoi": {
            "name": event["aoi_name"],
            "bbox": event["bbox"],
        },
        "prediction_type": "historical-plus-live rule-based water-risk prediction prototype",
        "collection": "SENTINEL2_L2A",
        "baseline_period": event["baseline_period"],
        "recent_period": event["recent_period"],
        "historical_risk": {
            "label": historical_risk["label"],
            "score": historical_risk["score"],
            "source": historical_risk.get("source", "Unknown"),
        },
        "live_inputs": {
            "forecast_rain_mm": forecast_rain_mm,
            "sentinel1_surface_water_change_percent": sentinel1_percent,
        },
        "indicators": {
            "delta_ndvi": {
                "description": "Recent NDVI minus baseline NDVI",
                "mean": ndvi_stats["mean"],
                "stats": ndvi_stats,
            },
            "delta_ndmi": {
                "description": "Recent NDMI minus baseline NDMI",
                "mean": ndmi_stats["mean"],
                "stats": ndmi_stats,
            },
        },
        "prediction": {
            "risk_score": risk_score,
            "predicted_risk_level": risk_level,
            "reasons": reasons,
        },
        "outputs": {
            "delta_ndvi_tif": ndvi_path,
            "delta_ndmi_tif": ndmi_path,
            "sentinel1_summary_json": sentinel1_path,
            "summary_json": summary_path,
        },
        "known_event": event.get("known_event", None),
        "explanation": (
            "This prototype combines a historical AOI risk baseline with live/recent "
            "Copernicus-derived vegetation and moisture anomalies, rainfall input, and "
            "Sentinel-1 surface-water-change evidence. It outputs a Low/Medium/High "
            "rule-based predicted water-risk level."
        ),
    }

    with open(summary_path, "w") as f:
        json.dump(prediction, f, indent=2)

    print(json.dumps(prediction["live_inputs"], indent=2))
    print(json.dumps(prediction["prediction"], indent=2))
    print(f"Updated {summary_path}")