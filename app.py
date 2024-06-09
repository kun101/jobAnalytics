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


pipe = pipeline("token-classification", model="GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription", token=st.secrets["ACCESS_TOKEN"])

# get uri from .env file
uri = st.secrets["MONGO_URL"]
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
        
    so_df = pd.read_csv('employed.csv')
    so_df.fillna("", inplace=True)
    
    # filter so_df on country if country contains any value in locations
    so_df = so_df[so_df["Country"].str.contains("India")]
    
    # get only those rows where Employment contains the substring "Employed"
    so_df = so_df[so_df["Employment"].str.contains("Employed")]
    
    so_df = so_df[so_df["DevType"].str.contains("data")]
    
    so_df["skills"] = so_df["LanguageHaveWorkedWith"] + ";" + so_df["DatabaseHaveWorkedWith"] + ";" + so_df["WebframeHaveWorkedWith"] + ";" + so_df["MiscTechHaveWorkedWith"] + ";" + so_df["ToolsTechHaveWorkedWith"]
    so_df["skills"] = so_df["skills"].str.split(";")
    
    # rename DevType to title
    so_df.rename(columns={"DevType":"title"}, inplace=True)
    
    # rename Country to country
    so_df.rename(columns={"Country":"country"}, inplace=True)
    
    # keep only title, country and skills columns
    so_df = so_df[["title", "country", "skills"]]
    
    # add blank company, date and link columns
    so_df["company"] = "Stack Overflow Survey Data"
    so_df["date"] = ""
    so_df["link"] = ""
    
    # append so_df to df
    df = pd.concat([df, so_df])
        
    # print top occuring skills
    st.subheader('Most Frequently Occuring Skills')
    st.write("Top skills extracted from job descriptions, and presented as a bar chart.")
    skills = df["skills"].sum()
    skills = pd.Series(skills).value_counts()
    skills = skills.sort_values(ascending=False)
    
    # remove blank skills
    skills = skills.drop("")
        
        # make altair chart
    chart = alt.Chart(skills.reset_index()).mark_bar().encode(
        x=alt.X('index', sort=None, title="Skills"),
        y=alt.Y('count', title="Count"),
    )
    st.altair_chart(chart, use_container_width=True)
    
    # show skills as dataframe
    st.dataframe(skills.reset_index().rename(columns={"index":"Skill", 0:"Count"}), use_container_width=True)
        
    # make a chart for each company and their skills
    for company in df["company"].unique():
        st.write(f"Skills for {company}")
        skills = df[df["company"]==company]["skills"].sum()
        skills = pd.Series(skills).value_counts()
        # sort the skills
        skills = skills.sort_values(ascending=False)
        st.bar_chart(skills)