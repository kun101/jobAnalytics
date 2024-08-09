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