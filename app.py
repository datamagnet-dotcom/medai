import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time
from pathlib import Path

[Previous imports and configurations remain exactly the same...]

def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query that searches across all fields:
    '{user_query}'
    Example:
    'Find details of patient Bobby Jackson' -> {{"$or": [
        {{"Name": {{"$regex": "Bobby Jackson", "$options": "i"}}}},
        {{"Doctor": {{"$regex": "Bobby Jackson", "$options": "i"}}}},
        {{"Medical Condition": {{"$regex": "Bobby Jackson", "$options": "i"}}}},
        {{"Blood Type": {{"$regex": "Bobby Jackson", "$options": "i"}}}},
        {{"Hospital": {{"$regex": "Bobby Jackson", "$options": "i"}}}}
    ]}}
    """
    try:
        response = gemini_model.generate_content(prompt)
        return {"$or": [
            {"Name": {"$regex": user_query, "$options": "i"}},
            {"Doctor": {"$regex": user_query, "$options": "i"}},
            {"Medical Condition": {"$regex": user_query, "$options": "i"}},
            {"Blood Type": {"$regex": user_query, "$options": "i"}},
            {"Hospital": {"$regex": user_query, "$options": "i"}},
            {"Room Number": {"$regex": user_query, "$options": "i"}},
            {"Test Results": {"$regex": user_query, "$options": "i"}}
        ]}
    except Exception as e:
        st.error(f"❌ AI Query Generation Error: {str(e)}")
        return {}

def fetch_patient_details(user_query):
    search_query = generate_mongo_query(user_query)
    
    try:
        start_time = time.time()
        # Changed to find() to get multiple results
        patients = list(collection.find(search_query, {"_id": 0}))
        
        if time.time() - start_time > 5:
            st.error("⏳ Query took too long. Try again later.")
            return None
        
        return patients if patients else None
    except Exception as e:
        st.error(f"❌ Database Error: {str(e)}")
        return None

# ✅ Streamlit UI
[Previous UI code remains exactly the same until the search button handling...]

if search_button:
    if user_query:
        with st.spinner("Searching records..."):
            patients_data = fetch_patient_details(user_query)
        
        if patients_data:
            st.success(f"Found {len(patients_data)} matching record(s)")

            # Display each patient's information
            for patient_data in patients_data:
                st.markdown(
                    f"""
                    <div class="patient-card">
                        <h3>Patient Information</h3>
                        <p><span class="highlight">Name:</span> {patient_data.get('Name', 'N/A')}</p>
                        <p><span class="highlight">Age:</span> {patient_data.get('Age', 'N/A')}</p>
                        <p><span class="highlight">Gender:</span> {patient_data.get('Gender', 'N/A')}</p>
                        <p><span class="highlight">Blood Type:</span> {patient_data.get('Blood Type', 'N/A')}</p>
                        <p><span class="highlight">Hospital:</span> {patient_data.get('Hospital', 'N/A')}</p>
                        <p><span class="highlight">Doctor:</span> {patient_data.get('Doctor', 'N/A')}</p>
                        <p><span class="highlight">Medical Condition:</span> {patient_data.get('Medical Condition', 'N/A')}</p>
                        <p><span class="highlight">Admission Date:</span> {patient_data.get('Date of Admission', 'N/A')}</p>
                        <p><span class="highlight">Room Number:</span> {patient_data.get('Room Number', 'N/A')}</p>
                        <p><span class="highlight">Billing Amount:</span> {patient_data.get('Billing Amount', 'N/A')}</p>
                        <p><span class="highlight">Test Results:</span> {patient_data.get('Test Results', 'N/A')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("No matching records found")
    else:
        st.error("Please enter a search term")
