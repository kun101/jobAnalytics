import pymongo
from pymongo import MongoClient
import os

def get_data(locations=["India"], job_title="Data Analyst", limit=2):
    import logging
    from linkedin_jobs_scraper import LinkedinScraper
    from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
    from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
    from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters, \
        OnSiteOrRemoteFilters, SalaryBaseFilters

    # Change root logger level (default is WARN)
    logging.basicConfig(level=logging.WARN)

    all_data = []


    # Fired once for each successfully processed job
    def on_data(data: EventData):
        all_data.append({
            "job_id": data.job_id,
            "title": data.title,
            "company": data.company,
            "place": data.place,
            "date": data.date,
            "description": data.description,
            "link": data.link
        })


    # Fired once for each page (25 jobs)
    # def on_metrics(metrics: EventMetrics):
    #     print('[ON_METRICS]', str(metrics))


    def on_end():
        print('[ON_END]')

    scraper = LinkedinScraper(
        headless=True,  # Overrides headless mode only if chrome_options is None
        max_workers=2,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
        slow_mo=0.5,  # Slow down the scraper to avoid 'Too many requests 429' errors (in seconds)
        page_load_timeout=40  # Page load timeout (in seconds)
    )

    # Add event listeners
    scraper.on(Events.DATA, on_data)
    scraper.on(Events.END, on_end)

    queries = [
        Query(
            query='Data Analyst',
            options=QueryOptions(
                locations=locations,
                apply_link=True,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page must be navigated. Default to False.
                skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
                page_offset=0,  # How many pages to skip
                limit=limit,
                filters=QueryFilters(
                    relevance=RelevanceFilters.RECENT,
                    time=TimeFilters.MONTH,
                    type=[TypeFilters.FULL_TIME, TypeFilters.INTERNSHIP],
                )
            )
        ),
    ]

    scraper.run(queries)

    return all_data

uri = "mongodb+srv://user:TGHgAjP7quKMl3tC@cluster0.yherqml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
database = client["jobs"]
collection = database["linkedin"]

def upsert_data(data):
    # upsert data
    collection.update_one(
        {"job_id": data["job_id"]},
        {"$set": data},
        upsert=True
    )

# get all data and upsert on mongodb
def get_all_data():
    data = get_data()
    for d in data:
        upsert_data(d)
        print("Data inserted successfully")
    print("Data inserted successfully")
    
get_all_data()