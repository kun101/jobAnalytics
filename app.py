import streamlit as st
import pandas as pd

from transformers import pipeline

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

pipe = pipeline("token-classification", model="GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription")


def get_data(locations=["India"], job_title="Data Analyst", limit=5):
    import logging
    from linkedin_jobs_scraper import LinkedinScraper
    from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
    from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
    from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters, \
        OnSiteOrRemoteFilters, SalaryBaseFilters

    # Change root logger level (default is WARN)
    logging.basicConfig(level=logging.INFO)

    all_data = []


    # Fired once for each successfully processed job
    def on_data(data: EventData):
        all_data.append(data)


    # Fired once for each page (25 jobs)
    # def on_metrics(metrics: EventMetrics):
    #     print('[ON_METRICS]', str(metrics))


    def on_end():
        print('[ON_END]')

    path = ChromeService(ChromeDriverManager().install()).path

    scraper = LinkedinScraper(
        chrome_executable_path=path,  # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
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

def skills_from_description(all_data):
    # print(all_data)
    all_jobs = []
    for data in all_data:
        description = word_tokenize(data.description)
        s = " ".join(description)
        
        result = pipe(data.description)
        
        skills = ""
        for i in result:
            skills+=i["word"]+","
        
        skills = skills.replace(',##','')
        skills = skills.replace('machine,learning','machine learning')
        skills = skills.replace('data,analytics','data analytics')
        skills = skills.replace('deep,learning','deep learning')
        skills = skills.split(",")
        
        # print(skills)
        
        all_jobs.append({
            "title": data.title,
            "company": data.company,
            "company_link": data.company_link,
            "date": data.date,
            "link": data.link,
            "insights": data.insights,
            "skills": skills
        })
    return all_jobs

st.title("Job Analytics")
locations = st.text_input("Enter locations separated by comma", "India")
job_title = st.text_input("Enter job title", "Data Analyst")
limit = st.slider("Enter number of jobs to scrape", 1, 100, 5)

if st.button("Scrape"):
    all_data = get_data(locations=locations.split(","), job_title=job_title, limit=limit)
    st.write("Scraping done")
    st.write("Data")
    df = pd.DataFrame(all_data)
    st.write(df)
    
    all_jobs = skills_from_description(all_data)
    # print(all_jobs)
    st.write("Insights")
    df = pd.DataFrame(all_jobs)
    st.write(df)
    
    # make a chart for each company and their skills
    for company in df["company"].unique():
        st.write(f"Skills for {company}")
        skills = df[df["company"]==company]["skills"].sum()
        skills = pd.Series(skills).value_counts()
        # sort the skills
        skills = skills.sort_values(ascending=False)
        st.bar_chart(skills)