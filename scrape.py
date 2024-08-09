import pymongo
from pymongo import MongoClient
import os

from transformers import pipeline

import altair as alt

import time

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

LI_AT_COOKIE = os.environ['LI_AT_COOKIE'] if 'LI_AT_COOKIE' in os.environ else None

pipe = pipeline("token-classification", model="GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription", token="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")

if LI_AT_COOKIE is None:
    print("LI_AT_COOKIE is not set")
    exit()

def get_data(locations=["India"], job_title="Data Analyst", limit=50):
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
        result = pipe(data.description)
        
        skills = ""
        for i in result:
            skills+=i["word"]+","
            
        print(skills)
        
        skills = skills.replace(',##','')
        skills = skills.replace('machine,learning','machine learning')
        skills = skills.replace('deep,learning','deep learning')
        skills = skills.replace('data,','data ')
        skills = skills.split(",")
        # remove blank elements
        skills = list(filter(None, skills))
        
        new_skills = skills + data.skills
        
        all_data.append({
            "job_id": data.job_id,
            "title": data.title,
            "company": data.company,
            "place": data.place,
            "date": data.date,
            "description": data.description,
            "link": data.link,
            "skills": new_skills,
        })
        print("[ON_DATA]", data.title, data.company, data.date, data.link, data.place, data.skills)


    # Fired once for each page (25 jobs)
    # def on_metrics(metrics: EventMetrics):
    #     print('[ON_METRICS]', str(metrics))


    def on_end():
        print('[ON_END]')

    scraper = LinkedinScraper(
        headless=True,  # Overrides headless mode only if chrome_options is None
        max_workers=1,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
        slow_mo=2,  # Slow down the scraper to avoid 'Too many requests 429' errors (in seconds)
        page_load_timeout=40  # Page load timeout (in seconds)
    )

    # Add event listeners
    scraper.on(Events.DATA, on_data)
    scraper.on(Events.END, on_end)

    queries = [
        Query(
            query=job_title,
            options=QueryOptions(
                locations=locations,
                apply_link=False,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page must be navigated. Default to False.
                skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
                page_offset=0,  # How many pages to skip
                limit=limit,
                filters=QueryFilters(
                    relevance=RelevanceFilters.RECENT,
                    time=TimeFilters.MONTH,
                    type=[TypeFilters.FULL_TIME, TypeFilters.INTERNSHIP],
                    on_site_or_remote=[OnSiteOrRemoteFilters.ON_SITE],
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
    data = get_data(job_title="Data Analyst", limit=100)
    for d in data:
        upsert_data(d)
        print("Data inserted successfully")
    print("Data inserted successfully")
    
get_all_data()