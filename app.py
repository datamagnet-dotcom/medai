import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time

# Page Configurations
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="wide")

# Karexpert-inspired theme
custom_css = """
<style>
    /* Main theme colors and fonts */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #f5f7ff !important;
        color: #333333 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Header styling */
    h1 {
        color: #2d62ed !important;
        font-weight: 700 !important;
        padding: 20px 0 !important;
    }

    /* Search input styling */
    .stTextInput>div>div>input {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 2px solid #2d62ed !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 16px !important;
        box-shadow: 0 2px 4px rgba(45, 98, 237, 0.1) !important;
    }

    /* Button styling */
    .stButton>button {
        background-color: #2d62ed !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .stButton>button:hover {
        background-color: #1e45b8 !important;
        box-shadow: 0 4px 8px rgba(45, 98, 237, 0.2) !important;
    }

    /* Patient card styling */
    .patient-card {
        background-color: #ffffff !important;
        padding: 24px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(45, 98, 237, 0.1) !important;
        margin: 20px 0 !important;
        border-left: 4px solid #2d62ed !important;
    }

    .patient-card h3 {
        color: #2d62ed !important;
        font-size: 24px !important;
        font-weight: 700 !important;
        margin-bottom: 16px !important;
    }

    /* Info rows styling */
    .info-row {
        display: flex !important;
        padding: 12px 0 !important;
        border-bottom: 1px solid #e6e9f5 !important;
    }

    .info-label {
        font-weight: 600 !important;
        color: #2d62ed !important;
        width: 180px !important;
    }

    .info-value {
        color: #333333 !important;
        flex: 1 !important;
    }

    /* Status indicators */
    .status-badge {
        display: inline-block !important;
        padding: 6px 12px !important;
        border-radius: 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    .status-active {
        background-color: #e6f4ea !important;
        color: #137333 !important;
    }

    /* Alerts styling */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
        padding: 16px !important;
    }

    /* Loading spinner */
    .stSpinner {
        border-color: #2d62ed !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:1234@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# Configure Gemini AI
genai.configure(api_key="AIzaSyCQ7t9zx7vxu25gRCT9XLM2LQdNuX2BZoU")
gemini_model = genai.GenerativeModel("gemini-pro")

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
        st.error(f"🚫 Query Generation Error: {str(e)}")
        return {}

def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)
    
    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}

        try:
            start_time = time.time()
            patient = collection.find_one(mongo_query, {"_id": 0})
            
            if time.time() - start_time > 5:
                st.error("⏳ Request timeout. Please try again.")
                return None
            
            return patient if patient else None
        except Exception as e:
            st.error(f"🚫 Database Error: {str(e)}")
            return None
    return None

# UI Layout
st.markdown("<h1>🏥 Patient Information Portal</h1>", unsafe_allow_html=True)

# Search section with improved layout
col1, col2 = st.columns([3, 1])
with col1:
    user_query = st.text_input("", placeholder="Enter patient name or search query...")
with col2:
    search_button = st.button("🔍 Search")

# Quick filters
st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    if st.button("📅 Recent Patients", key="recent"):
        st.session_state.filter = "recent"
with filter_col2:
    if st.button("⚡ Critical Cases", key="critical"):
        st.session_state.filter = "critical"
with filter_col3:
    if st.button("📋 Pending Reports", key="pending"):
        st.session_state.filter = "pending"
with filter_col4:
    if st.button("🆕 New Admissions", key="new"):
        st.session_state.filter = "new"
st.markdown("</div>", unsafe_allow_html=True)

if search_button and user_query:
    with st.spinner("🔄 Searching patient records..."):
        patient_data = fetch_patient_details(user_query)
    
    if patient_data:
        st.markdown(
            f"""
            <div class="patient-card">
                <h3>👤 Patient Details</h3>
                <div class="info-row">
                    <div class="info-label">Name</div>
                    <div class="info-value">{patient_data.get('Name', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Age</div>
                    <div class="info-value">{patient_data.get('Age', 'N/A')} years</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Gender</div>
                    <div class="info-value">{patient_data.get('Gender', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Blood Type</div>
                    <div class="info-value">{patient_data.get('Blood Type', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Hospital</div>
                    <div class="info-value">{patient_data.get('Hospital', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Doctor</div>
                    <div class="info-value">{patient_data.get('Doctor', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Medical Condition</div>
                    <div class="info-value">{patient_data.get('Medical Condition', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Admission Date</div>
                    <div class="info-value">{patient_data.get('Date of Admission', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Room Number</div>
                    <div class="info-value">{patient_data.get('Room Number', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Billing Amount</div>
                    <div class="info-value">{patient_data.get('Billing Amount', 'N/A')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Test Results</div>
                    <div class="info-value">{patient_data.get('Test Results', 'N/A')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ No matching patient records found.")
