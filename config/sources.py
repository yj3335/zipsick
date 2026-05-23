# config/sources.py
# URLs and metadata for each data ingestion lane.

NIMBLE_TARGET_URLS = [
    "https://www.nyc.gov/site/doh/health/health-topics/food-poisoning.page",
    "https://www.nyc.gov/site/doh/health/health-topics/bedbugs.page",
    "https://www.nyc.gov/site/doh/health/health-topics/flu.page",
    "https://www.nyc.gov/site/doh/health/health-topics/measles.page",
    "https://www.nyc.gov/site/doh/health/health-topics/rsv.page"
]

NYC_311_ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
NYC_311_LIMIT = 200
NYC_311_FIELDS = [
    "created_date",
    "complaint_type",
    "descriptor",
    "incident_zip",
    "borough",
    "location_type",
]

REDDIT_SUBREDDITS = ["nyc", "AskNYC", "newyorkcity"]
HEALTH_KEYWORDS = "food poisoning OR stomach bug OR norovirus OR diarrhea OR sick OR covid OR flu OR rsv OR measles OR legionnaires OR bedbug OR bedbugs OR scabies OR rat OR rats OR roach OR roaches OR cockroach OR rodent OR mouse"
YELP_SEARCH_URL = "https://www.yelp.com/search?find_desc=food+poisoning+OR+bedbugs+OR+sick+OR+roaches+OR+rats&find_loc=10036"

