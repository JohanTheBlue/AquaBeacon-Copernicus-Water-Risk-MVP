import openeo

connection = openeo.connect("https://openeofed.dataspace.copernicus.eu")
connection.authenticate_oidc()

job_id = "cdse-j-26042517572847719bf4997836bd474a"
output_dir = "samples/houston_beryl_jul_2024/delta_ndvi"

job = connection.job(job_id)
results = job.get_results()
results.download_files(output_dir)

print(f"Downloaded results to {output_dir}")