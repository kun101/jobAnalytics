import streamlit as st
import pandas as pd

from transformers import pipeline

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

import pymongo
from pymongo import MongoClient

pipe = pipeline("token-classification", model="GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription")
# path = ChromeService(ChromeDriverManager().install()).path

# get all data from mongodb
uri = "mongodb+srv://user:TGHgAjP7quKMl3tC@cluster0.yherqml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri,ssl.CERT_NONE)
database = client["jobs"]
collection = database["linkedin"]


def get_data(locations=["India"], job_title="Data Analyst", limit=50):
    # filter data
    all_data = list(collection.find({}).limit(limit))
    
    # print(all_data)

    return all_data

def skills_from_description(all_data):
    # print(all_data)
    all_jobs = []
    for data in all_data:
        print(data)
        description = word_tokenize(data["description"])
        s = " ".join(description)
        
        result = pipe(data["description"])
        
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
            "title": data["title"],
            "company": data["company"],
            "date": data["date"],
            "link": data["link"],
            "skills": skills
        })
    return all_jobs

st.title("Job Analytics")
locations = st.text_input("Enter locations separated by comma", "India")
job_title = st.text_input("Enter job title", "Data Analyst")

if st.button("Scrape"):
    all_data = get_data(locations=locations.split(","), job_title=job_title)
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