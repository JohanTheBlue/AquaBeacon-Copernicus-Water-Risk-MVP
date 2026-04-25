import json
import os
import csv

SAMPLES_DIR = "samples"
OUTPUT_CSV = "samples/aquabeacon_sample_overview.csv"
OUTPUT_JSON = "samples/aquabeacon_sample_overview.json"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


rows = []

for event_id in sorted(os.listdir(SAMPLES_DIR)):
    event_dir = os.path.join(SAMPLES_DIR, event_id)

    if not os.path.isdir(event_dir):
        continue

    summary_path = os.path.join(event_dir, "aquabeacon_prediction_summary.json")

    if not os.path.exists(summary_path):
        print(f"Skipping {event_id}: no prediction summary")
        continue

    summary = load_json(summary_path)

    indicators = summary.get("indicators", {})
    live_inputs = summary.get("live_inputs", {})
    prediction = summary.get("prediction", {})
    historical = summary.get("historical_risk", {})

    row = {
        "event_id": event_id,
        "aoi_name": summary.get("aoi", {}).get("name"),
        "known_event": summary.get("known_event"),
        "historical_risk": historical.get("label"),
        "historical_score": historical.get("score"),
        "rainfall_mm": live_inputs.get("forecast_rain_mm"),
        "sentinel1_surface_water_change_percent": live_inputs.get(
            "sentinel1_surface_water_change_percent"
        ),
        "delta_ndvi_mean": indicators.get("delta_ndvi", {}).get("mean"),
        "delta_ndmi_mean": indicators.get("delta_ndmi", {}).get("mean"),
        "risk_score": prediction.get("risk_score"),
        "predicted_risk_level": prediction.get("predicted_risk_level"),
        "reasons": " | ".join(prediction.get("reasons", [])),
    }

    rows.append(row)


if not rows:
    raise RuntimeError("No sample summaries found.")

fieldnames = list(rows[0].keys())

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

with open(OUTPUT_JSON, "w") as f:
    json.dump(rows, f, indent=2)

print(f"Saved CSV: {OUTPUT_CSV}")
print(f"Saved JSON: {OUTPUT_JSON}")

print("\nOverview:")
for row in rows:
    print(
        f"{row['event_id']}: "
        f"{row['predicted_risk_level']} "
        f"(score={row['risk_score']}, "
        f"S1={row['sentinel1_surface_water_change_percent']}%, "
        f"rain={row['rainfall_mm']}mm)"
    )