import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time
from pathlib import Path

# ✅ Page Configurations
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="centered")

# [Previous CSS styles remain unchanged]
custom_css = """
[Your existing CSS content]
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ Display Karexpert logo
st.markdown("""
    <div class="logo-container">
        <img src="https://raw.githubusercontent.com/datamagnet-dotcom/medai/main/Karexpert.png" alt="Karexpert Logo">
    </div>
""", unsafe_allow_html=True)

# ✅ MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:1234@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyCQ7t9zx7vxu25gRCT9XLM2LQdNuX2BZoU")
gemini_model = genai.GenerativeModel("gemini-pro")

def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query:
    '{user_query}'
    Consider both full name and first name matches.
    Example:
    'Find details of patient Bobby Jackson' -> {{"Name": {{"$regex": "Bobby.*", "$options": "i"}}}}
    'Who is Bobby?' -> {{"Name": {{"$regex": "Bobby.*", "$options": "i"}}}}
    """
    try:
        response = gemini_model.generate_content(prompt)
        mongo_query = json.loads(response.text.strip())
        return mongo_query
    except Exception as e:
        st.error(f"❌ AI Query Generation Error: {str(e)}")
        return {}

def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)
    
    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip() if isinstance(mongo_query["Name"], str) else mongo_query["Name"]["$regex"].replace(".*", "").strip()
        
        # Create a query that matches either the full name or starts with the given name
        mongo_query = {
            "$or": [
                {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}},  # Exact match
                {"Name": {"$regex": f"^{clean_name}\\s", "$options": "i"}}  # Starts with the given name
            ]
        }

        try:
            start_time = time.time()
            # Find all matching patients
            patients = list(collection.find(mongo_query, {"_id": 0}))
            
            if time.time() - start_time > 5:
                st.error("⏳ Query took too long. Try again later.")
                return None
            
            return patients if patients else None
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
            return None
    return None

# ✅ Streamlit UI
st.markdown('<p class="search-text" style="font-weight: bold; font-size: 22px; text-align: center;">Enter patient name to access medical records</p>', unsafe_allow_html=True)

# Search input with placeholder
user_query = st.text_input("", placeholder="🔍 Search by patient name or ID...", key="search_input")

# Centered search button
st.markdown('<div class="center-container">', unsafe_allow_html=True)
search_button = st.button("Search Records")
st.markdown('</div>', unsafe_allow_html=True)

if search_button:
    if user_query:
        with st.spinner("Searching records..."):
            patients_data = fetch_patient_details(user_query)
        
        if patients_data:
            st.success(f"Found {len(patients_data)} matching patient(s)")

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
            st.warning("No matching patient records found")
    else:
        st.error("Please enter a search term")
