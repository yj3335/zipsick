# config/sources.py
# URLs and metadata for each data ingestion lane.

NIMBLE_TARGET_URL = "https://www.nyc.gov/site/doh/health/health-topics/food-poisoning.page"

NYC_311_ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
NYC_311_LIMIT = 25
NYC_311_FIELDS = [
    "created_date",
    "complaint_type",
    "descriptor",
    "incident_zip",
    "borough",
    "location_type",
]
