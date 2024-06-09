import streamlit as st
import pandas as pd

import os

from transformers import pipeline

import altair as alt

import time

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

import pymongo
from pymongo import MongoClient


pipe = pipeline("token-classification", model="GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription", token=os.environ['ACCESS_TOKEN'])

# get uri from .env file
uri = os.environ['MONGO_URL']
client = MongoClient(uri)
database = client["jobs"]
collection = database["linkedin"]


def get_data(locations=["India"], job_title="Data Analyst", limit=10):
    # filter data and return all columns except _id
    all_data = list(collection.find({}).limit(limit))
    
    # remove _id from all_data
    for data in all_data:
        data.pop("_id")
    
    return all_data

def skills_from_description(all_data):
    # print(all_data)
    all_jobs = []
    progress_text = "Analyzing Jobs. Please Wait."
    my_bar = st.progress(0, text=progress_text)
    for data in all_data:
        description = word_tokenize(data["description"])
        s = " ".join(description)
        
        result = pipe(data["description"])
        
        skills = ""
        for i in result:
            skills+=i["word"]+","
        
        skills = skills.replace(',##','')
        skills = skills.replace('machine,learning','machine learning')
        skills = skills.replace('deep,learning','deep learning')
        skills = skills.split(",")
        # remove blank elements
        skills = list(filter(None, skills))
        
        all_jobs.append({
            "title": data["title"],
            "company": data["company"],
            "date": data["date"],
            "link": data["link"],
            "skills": skills
        })
        
        my_bar.progress((all_data.index(data)+1)/len(all_data), text=progress_text)
        
        if all_data.index(data)+1 == len(all_data):
            my_bar.progress(100, text="Analysis Complete!")
            time.sleep(1)
            my_bar.empty()        
        
    return all_jobs

st.title("Job Analytics")
locations = st.text_input("Enter locations separated by comma", "India")
job_title = st.text_input("Enter job title", "Data Analyst")

if st.button("Get Insights"):
    
    # fetching data spinner
    with st.spinner("Fetching latest data..."):
        all_data = get_data(locations=locations.split(","), job_title=job_title)
        st.success('Data Fetched Successfully!', icon="✅")
    
    all_jobs = skills_from_description(all_data)
    
    st.header(f'Job Insights for {job_title}')
    
    df = pd.DataFrame(all_jobs)
    with st.expander("Show Full Data"):
        st.write(df)
        
    # print top occuring skills
    st.subheader('Most Frequently Occuring Skills')
    st.write("Top skills extracted from job descriptions, and presented as a bar chart.")
    skills = df["skills"].sum()
    skills = pd.Series(skills).value_counts()
    skills = skills.sort_values(ascending=False)
        
        # make altair chart
    chart = alt.Chart(skills.reset_index()).mark_bar().encode(
        x=alt.X('index', sort=None, title="Skills"),
        y=alt.Y('count', title="Count"),
    )
    st.altair_chart(chart, use_container_width=True)
        
    # make a chart for each company and their skills
    for company in df["company"].unique():
        st.write(f"Skills for {company}")
        skills = df[df["company"]==company]["skills"].sum()
        skills = pd.Series(skills).value_counts()
        # sort the skills
        skills = skills.sort_values(ascending=False)
        st.bar_chart(skills)