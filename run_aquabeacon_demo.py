import json
import os
import time
import subprocess
from pathlib import Path

import openeo


OPENEO_ENDPOINT = "https://openeofed.dataspace.copernicus.eu"
EVENTS_FILE = "events.json"

POLL_SECONDS = 20
MAX_POLLS = 60  # 60 * 20 sec = 20 min max per job


def load_events():
    with open(EVENTS_FILE, "r") as f:
        return json.load(f)


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def file_exists(path):
    return Path(path).exists()


def save_job_id(path, job_id):
    ensure_dir(Path(path).parent)
    with open(path, "w") as f:
        f.write(job_id)


def load_job_id(path):
    if not file_exists(path):
        return None
    return Path(path).read_text().strip()


def poll_job(job, label):
    print(f"\nPolling job: {label}")
    print(f"Job ID: {job.job_id}")

    for i in range(MAX_POLLS):
        info = job.describe_job()
        status = info.get("status")
        progress = info.get("progress")

        print(f"[{i}] status={status}, progress={progress}")

        if status == "finished":
            return True

        if status in ["error", "canceled"]:
            print(json.dumps(info, indent=2))
            return False

        time.sleep(POLL_SECONDS)

    print(f"Timed out waiting for {label}. Job may still finish server-side.")
    return False


def download_job(connection, job_id, output_dir):
    ensure_dir(output_dir)

    print(f"\nDownloading job {job_id} to {output_dir}")
    job = connection.job(job_id)
    results = job.get_results()
    results.download_files(output_dir)

    return file_exists(f"{output_dir}/openEO.tif")


def create_sentinel1_job(connection, event):
    event_id = event["event_id"]
    output_dir = f"samples/{event_id}/sentinel1"
    ensure_dir(output_dir)

    target_tif = f"{output_dir}/openEO.tif"
    job_id_file = f"{output_dir}/job_id.txt"

    if file_exists(target_tif):
        print(f"Sentinel-1 already exists for {event_id}, skipping.")
        return

    existing_job_id = load_job_id(job_id_file)
    if existing_job_id:
        job = connection.job(existing_job_id)
        info = job.describe_job()
        status = info.get("status")

        print(f"Existing Sentinel-1 job for {event_id}: {existing_job_id}, status={status}")

        if status == "finished":
            download_job(connection, existing_job_id, output_dir)
            return

        if status in ["created", "queued", "running"]:
            if poll_job(job, f"Sentinel-1 {event_id}"):
                download_job(connection, existing_job_id, output_dir)
            return

    def load_vv(period):
        cube = connection.load_collection(
            "SENTINEL1_GRD",
            spatial_extent=event["bbox"],
            temporal_extent=period,
            bands=["VV"],
        )
        vv = cube.band("VV")
        return vv.reduce_dimension(dimension="t", reducer="median")

    before_vv = load_vv(event["sentinel1_before_period"])
    after_vv = load_vv(event["sentinel1_after_period"])
    delta_vv = after_vv - before_vv

    job = delta_vv.create_job(
        title=f"AquaBeacon Sentinel-1 VV Change - {event_id}",
        out_format="GTiff",
    )

    save_job_id(job_id_file, job.job_id)

    print(f"\nCreated Sentinel-1 job for {event_id}: {job.job_id}")
    job.start()

    if poll_job(job, f"Sentinel-1 {event_id}"):
        download_job(connection, job.job_id, output_dir)


def create_sentinel2_job(connection, event, indicator):
    event_id = event["event_id"]

    if indicator == "ndvi":
        output_dir = f"samples/{event_id}/delta_ndvi"
        bands = ["B04", "B08"]
        title = f"AquaBeacon Delta NDVI - {event_id}"
    elif indicator == "ndmi":
        output_dir = f"samples/{event_id}/delta_ndmi"
        bands = ["B08", "B11"]
        title = f"AquaBeacon Delta NDMI - {event_id}"
    else:
        raise ValueError(f"Unknown indicator: {indicator}")

    ensure_dir(output_dir)

    target_tif = f"{output_dir}/openEO.tif"
    job_id_file = f"{output_dir}/job_id.txt"

    if file_exists(target_tif):
        print(f"{indicator.upper()} already exists for {event_id}, skipping.")
        return

    existing_job_id = load_job_id(job_id_file)
    if existing_job_id:
        job = connection.job(existing_job_id)
        info = job.describe_job()
        status = info.get("status")

        print(f"Existing {indicator.upper()} job for {event_id}: {existing_job_id}, status={status}")

        if status == "finished":
            download_job(connection, existing_job_id, output_dir)
            return

        if status in ["created", "queued", "running"]:
            if poll_job(job, f"{indicator.upper()} {event_id}"):
                download_job(connection, existing_job_id, output_dir)
            return

    def load_cube(period):
        return connection.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=event["bbox"],
            temporal_extent=period,
            bands=bands,
            max_cloud_cover=60,
        )

    baseline_cube = load_cube(event["baseline_period"])
    recent_cube = load_cube(event["recent_period"])

    if indicator == "ndvi":
        def compute(cube):
            red = cube.band("B04")
            nir = cube.band("B08")
            return ((nir - red) / (nir + red)).reduce_dimension(
                dimension="t",
                reducer="median",
            )
    else:
        def compute(cube):
            nir = cube.band("B08")
            swir = cube.band("B11")
            return ((nir - swir) / (nir + swir)).reduce_dimension(
                dimension="t",
                reducer="median",
            )

    baseline = compute(baseline_cube)
    recent = compute(recent_cube)
    delta = recent - baseline

    job = delta.create_job(
        title=title,
        out_format="GTiff",
    )

    save_job_id(job_id_file, job.job_id)

    print(f"\nCreated {indicator.upper()} job for {event_id}: {job.job_id}")
    job.start()

    if poll_job(job, f"{indicator.upper()} {event_id}"):
        download_job(connection, job.job_id, output_dir)


def run_script(script):
    print(f"\nRunning {script}")
    subprocess.run(["python3", script], check=True)


def main():
    events = load_events()

    connection = openeo.connect(OPENEO_ENDPOINT)
    connection.authenticate_oidc()

    for event in events:
        event_id = event["event_id"]
        print(f"\n==============================")
        print(f"Processing event: {event_id}")
        print(f"==============================")

        create_sentinel1_job(connection, event)
        create_sentinel2_job(connection, event, "ndvi")
        create_sentinel2_job(connection, event, "ndmi")

    # These scripts read existing files only.
    run_script("make_sentinel1_summaries_all.py")
    run_script("recompute_prediction_from_files.py")
    run_script("make_sample_overview.py")
    run_script("make_sample_maps.py")

    print("\nAquaBeacon demo pipeline finished.")


if __name__ == "__main__":
    main()