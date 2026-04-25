import os
import json
import rasterio
import numpy as np
import matplotlib.pyplot as plt

SAMPLES_DIR = "samples"


def load_summary(event_dir):
    path = os.path.join(event_dir, "aquabeacon_prediction_summary.json")
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def read_raster(path, clip_index=False):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        nodata = src.nodata

    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    # NDVI / NDMI should normally be around -1..1.
    # This removes extreme artifacts from visualization.
    if clip_index:
        arr = np.where((arr < -1) | (arr > 1), np.nan, arr)

    return arr


def save_raster_png(arr, title, output_png):
    plt.figure(figsize=(8, 8))
    plt.imshow(arr)
    plt.title(title)
    plt.axis("off")
    plt.colorbar(shrink=0.7)
    plt.savefig(output_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_png}")


def save_mask_png(arr, title, output_png):
    plt.figure(figsize=(8, 8))
    plt.imshow(arr)
    plt.title(title)
    plt.axis("off")
    plt.savefig(output_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {output_png}")


for event_id in sorted(os.listdir(SAMPLES_DIR)):
    event_dir = os.path.join(SAMPLES_DIR, event_id)

    if not os.path.isdir(event_dir):
        continue

    summary = load_summary(event_dir)
    if summary is None:
        print(f"Skipping {event_id}: no prediction summary")
        continue

    risk_level = summary.get("prediction", {}).get("predicted_risk_level", "Unknown")
    risk_score = summary.get("prediction", {}).get("risk_score", "NA")

    ndvi_path = os.path.join(event_dir, "delta_ndvi", "openEO.tif")
    ndmi_path = os.path.join(event_dir, "delta_ndmi", "openEO.tif")
    s1_mask_path = os.path.join(event_dir, "sentinel1", "sentinel1_surface_water_mask.tif")

    if os.path.exists(ndvi_path):
        ndvi = read_raster(ndvi_path, clip_index=True)
        save_raster_png(
            ndvi,
            f"{event_id} - Delta NDVI - Risk {risk_level} ({risk_score})",
            os.path.join(event_dir, "delta_ndvi.png")
        )

    if os.path.exists(ndmi_path):
        ndmi = read_raster(ndmi_path, clip_index=True)
        save_raster_png(
            ndmi,
            f"{event_id} - Delta NDMI - Risk {risk_level} ({risk_score})",
            os.path.join(event_dir, "delta_ndmi.png")
        )

    if os.path.exists(s1_mask_path):
        s1_mask = read_raster(s1_mask_path, clip_index=False)
        save_mask_png(
            s1_mask,
            f"{event_id} - Sentinel-1 Surface-Water Candidates",
            os.path.join(event_dir, "sentinel1_surface_water_mask.png")
        )