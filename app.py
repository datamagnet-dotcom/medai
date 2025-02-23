import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time
from pathlib import Path

# ✅ Page Configurations
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="centered")

# ✅ Apply KareXpert-inspired UI theme
custom_css = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #f4f5f7 !important;
        color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }

    /* Centered logo container */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .logo-container img {
        max-width: 250px;
        height: auto;
    }

    /* Search bar improvements */
    .stTextInput>div>div>input {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 2px solid #005bbb !important;
        padding: 15px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        box-shadow: 0 2px 4px rgba(0, 91, 187, 0.1) !important;
        margin-bottom: 15px;
    }

    /* Search button styling */
    .stButton>button {
        background-color: #005bbb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 15px 30px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        width: 200px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border: none !important;
    }

    .stButton>button:hover {
        background-color: #004a99 !important;
        box-shadow: 0 4px 8px rgba(0, 91, 187, 0.2) !important;
        transform: translateY(-1px);
    }

    /* Patient card styling */
    .patient-card {
        background-color: #ffffff !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        margin-top: 30px !important;
        border-left: 4px solid #005bbb !important;
    }

    .patient-card h3 {
        color: #005bbb !important;
        font-size: 24px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e0e0e0;
    }

    .highlight {
        font-weight: 600;
        color: #005bbb !important;
        min-width: 150px;
        display: inline-block;
    }

    /* Search text styling */
    .search-text {
        color: #333333 !important;
        font-size: 18px !important;
        margin: 20px 0 !important;
        text-align: center;
    }

    /* Center container */
    .center-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ Display KareXpert logo centered
st.markdown("""
    <div class="logo-container">
        <img src="https://github.com/datamagnet-dotcom/medai/blob/main/Karexpert.png" alt="KareXpert Logo">
    </div>
""", unsafe_allow_html=True)
# ✅ MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:<db_password>@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyCQ7t9zx7vxu25gRCT9XLM2LQdNuX2BZoU")
gemini_model = genai.GenerativeModel("gemini-pro")

# ✅ Function to generate MongoDB query
def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query:
    '{user_query}'
    Example:
    'Find details of patient Bobby Jackson' -> {{"Name": "Bobby Jackson"}}
    'Who is Bobby Jackson?' -> {{"Name": "Bobby Jackson"}}
    """
    try:
        response = gemini_model.generate_content(prompt)
        mongo_query = json.loads(response.text.strip())
        return mongo_query
    except Exception as e:
        st.error(f"❌ AI Query Generation Error: {str(e)}")
        return {}

# ✅ Fetch Patient Details
def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)
    
    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}

        try:
            start_time = time.time()
            patient = collection.find_one(mongo_query, {"_id": 0})
            if time.time() - start_time > 5:
                st.error("⏳ Query took too long. Try again later.")
                return None
            return patient if patient else None
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
            return None
    return None

# ✅ Streamlit UI
st.markdown('<p class="search-text">Enter patient name to access medical records</p>', unsafe_allow_html=True)

# Search input
user_query = st.text_input("", placeholder="🔍 Search by patient name or ID...", key="search_input")

# Centered search button
st.markdown('<div class="center-container">', unsafe_allow_html=True)
search_button = st.button("Search Records")
st.markdown('</div>', unsafe_allow_html=True)

if search_button:
    if user_query:
        with st.spinner("Searching records..."):
            patient_data = fetch_patient_details(user_query)
        
        if patient_data:
            st.success("Patient Record Found")
        else:
            st.warning("No matching patient records found")
    else:
        st.error("Please enter a search term")
