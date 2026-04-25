import json
import os
import rasterio
import numpy as np


EVENTS_FILE = "events.json"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def make_summary(event):
    event_id = event["event_id"]

    output_dir = f"samples/{event_id}/sentinel1"
    delta_tif = f"{output_dir}/openEO.tif"
    mask_tif = f"{output_dir}/sentinel1_surface_water_mask.tif"
    summary_json = f"{output_dir}/sentinel1_surface_water_summary.json"

    if not os.path.exists(delta_tif):
        print(f"Skipping Sentinel-1 summary for {event_id}: missing {delta_tif}")
        return

    with rasterio.open(delta_tif) as src:
        arr = src.read(1).astype("float32")
        nodata = src.nodata
        profile = src.profile.copy()
        bounds = src.bounds
        crs = src.crs
        width = src.width
        height = src.height

    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    valid_mask = ~np.isnan(arr)
    valid_values = arr[valid_mask]

    threshold = float(np.nanpercentile(valid_values, 5))
    candidate_mask = (arr <= threshold) & valid_mask

    candidate_percent = float(np.sum(candidate_mask) / np.sum(valid_mask) * 100)
    mean_candidate_change = float(np.nanmean(arr[candidate_mask]))
    min_candidate_change = float(np.nanmin(arr[candidate_mask]))

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0,
    )

    with rasterio.open(mask_tif, "w", **profile) as dst:
        dst.write(candidate_mask.astype(np.uint8), 1)

    summary = {
        "event_id": event_id,
        "aoi": {
            "name": event["aoi_name"],
            "bbox": event["bbox"],
        },
        "collection": "SENTINEL1_GRD",
        "indicator": "Sentinel-1 VV backscatter change",
        "before_period": event["sentinel1_before_period"],
        "after_period": event["sentinel1_after_period"],
        "threshold_method": "5th percentile of VV delta",
        "threshold_value": threshold,
        "possible_surface_water_change_percent": candidate_percent,
        "mean_candidate_change": mean_candidate_change,
        "min_candidate_change": min_candidate_change,
        "outputs": {
            "delta_raster": delta_tif,
            "candidate_mask": mask_tif,
            "summary_json": summary_json,
        },
        "raster": {
            "width": int(width),
            "height": int(height),
            "bounds": {
                "left": float(bounds.left),
                "bottom": float(bounds.bottom),
                "right": float(bounds.right),
                "top": float(bounds.top),
            },
            "crs": str(crs),
        },
        "explanation": (
            "Pixels with the strongest negative Sentinel-1 VV backscatter change "
            "between the before and after periods are flagged as possible surface-water-change "
            "candidates. This is not a confirmed flood map."
        ),
    }

    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved {summary_json}")


def main():
    with open(EVENTS_FILE, "r") as f:
        events = json.load(f)

    for event in events:
        make_summary(event)


if __name__ == "__main__":
    main()