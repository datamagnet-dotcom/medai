import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time

# ✅ Page Configurations
st.set_page_config(page_title="MediScope - Smart Patient Search", page_icon="🏥", layout="wide")

# ✅ Apply a professional light theme with blue accents
custom_css = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }
    .stTextInput>div>div>input {
        background-color: #f5f5f5 !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        padding: 10px;
        border-radius: 5px;
    }
    .stButton>button {
        background-color: #007bff !important;
        color: #ffffff !important;
        border-radius: 5px;
        padding: 12px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #0056b3 !important;
    }
    .stAlert {
        border-radius: 5px;
        padding: 12px;
    }
    .patient-card {
        background-color: #f8f9fa !important;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 0px 12px rgba(0, 123, 255, 0.5) !important;
        font-size: 16px;
        line-height: 1.6;
        margin-top: 20px;
    }
    .patient-card h3 {
        color: #007bff !important;
        font-size: 24px;
        margin-bottom: 12px;
    }
    .highlight {
        font-weight: bold;
        color: #000000 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:1234@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyCQ7t9zx7vxu25gRCT9XLM2LQdNuX2BZoU")
gemini_model = genai.GenerativeModel("gemini-pro")

# ✅ Convert Natural Language to MongoDB Query
def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query:
    '{user_query}'
    """
    try:
        response = gemini_model.generate_content(prompt)
        mongo_query = json.loads(response.text.strip())
        return mongo_query
    except:
        return {}

# ✅ Fetch Patient Details
def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)
    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}
        try:
            patient = collection.find_one(mongo_query, {"_id": 0})
            return patient if patient else None
        except:
            return None
    return None

# ✅ Streamlit UI
st.title("🏥 MediScope - Smart Patient Lookup")
st.write("Effortlessly search for patient records using natural language.")
user_query = st.text_input("🔎 Enter a patient's name or query", "")

if st.button("Search"):
    if user_query:
        with st.spinner("🔄 Searching..."):
            patient_data = fetch_patient_details(user_query)
        if patient_data:
            st.success("✅ Patient Record Found!")
            st.markdown(
                f"""
                <div class="patient-card">
                    <h3>👤 {patient_data.get('Name', 'N/A')}</h3>
                    <p><span class="highlight">🆔 Age:</span> {patient_data.get('Age', 'N/A')}</p>
                    <p><span class="highlight">⚧ Gender:</span> {patient_data.get('Gender', 'N/A')}</p>
                    <p><span class="highlight">🩸 Blood Type:</span> {patient_data.get('Blood Type', 'N/A')}</p>
                    <p><span class="highlight">🏥 Hospital:</span> {patient_data.get('Hospital', 'N/A')}</p>
                    <p><span class="highlight">🩺 Doctor:</span> {patient_data.get('Doctor', 'N/A')}</p>
                    <p><span class="highlight">📝 Medical Condition:</span> {patient_data.get('Medical Condition', 'N/A')}</p>
                    <p><span class="highlight">📅 Admission Date:</span> {patient_data.get('Date of Admission', 'N/A')}</p>
                    <p><span class="highlight">💊 Medication:</span> {patient_data.get('Medication', 'N/A')}</p>
                    <p><span class="highlight">🏡 Room Number:</span> {patient_data.get('Room Number', 'N/A')}</p>
                    <p><span class="highlight">💰 Billing Amount:</span> {patient_data.get('Billing Amount', 'N/A')}</p>
                    <p><span class="highlight">📝 Test Results:</span> {patient_data.get('Test Results', 'N/A')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ No matching patient record found.")
    else:
        st.error("❌ Please enter a valid query.")
