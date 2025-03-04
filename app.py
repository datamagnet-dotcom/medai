import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time
from pathlib import Path

# ✅ Page Configurations
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="centered")

# ✅ Apply professional theme with improved visibility
custom_css = """
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }

    /* Logo container */
    .logo-container {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .logo-container img {
        max-width: 300px;
        height: auto;
    }

    /* Search bar improvements */
    .stTextInput>div>div>input {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 2px solid #2d62ed !important;
        padding: 15px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        box-shadow: 0 2px 4px rgba(45, 98, 237, 0.1) !important;
        margin-bottom: 15px;
    }

    /* Search button styling */
    .stButton>button {
        background-color: #007bff !important;
        color: #ffffff !important;
        border-radius: 20px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        transition: 0.3s;
        box-shadow: 0px 4px 6px rgba(0, 123, 255, 0.3);
    }

    .stButton>button:hover {
        background-color: #0056b3 !important;
        box-shadow: 0px 6px 10px rgba(0, 123, 255, 0.5);
    }

    /* Patient card styling */
    .patient-card {
        background-color: #ffffff !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        margin-top: 30px !important;
        border-left: 4px solid #2d62ed !important;
    }

    .patient-card h3 {
        color: #2d62ed !important;
        font-size: 24px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .highlight {
        font-weight: 600;
        color: #2d62ed !important;
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

    /* Error and warning message styling */
    .stAlert {
        background-color: #ffffff !important;
        color: #333333 !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
    
    div[data-baseweb="notification"] {
        background-color: #ffffff !important;
        color: #333333 !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ Display Karexpert logo
st.markdown("""
    <div class="logo-container">
        <img src="https://raw.githubusercontent.com/datamagnet-dotcom/bootcamp2024sai/main/Karexpert.png" alt="Karexpert Logo"> 
    </div>
""", unsafe_allow_html=True)

# ✅ MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:5855@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyB5bTQbnFOnpaGOweZ7AP0hxJHh7hrHfJ0")
gemini_model = genai.GenerativeModel("gemini-pro")

def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query.
    Consider all relevant fields and use appropriate query operators.
    For text fields, use case-insensitive regex matches for partial searches.

    Examples:
    - 'Find patients named John' → {{"Name": {{"$regex": "John", "$options": "i"}}}}
    - 'Patients with blood type O+' → {{"Blood Type": "O+"}}
    - 'Show patients aged 30' → {{"Age": 30}}
    - 'Patients under Dr. Smith' → {{"Doctor": {{"$regex": "Dr. Smith", "$options": "i"}}}}
    - 'Diabetic patients' → {{"Medical Condition": {{"$regex": "diabetes", "$options": "i"}}}}
    - 'Admitted on 2023-05-15' → {{"Date of Admission": "2023-05-15"}}
    - 'Billing over $5000' → {{"Billing Amount": {{"$gt": 5000}}}}
    - 'Room 205 patients' → {{"Room Number": "205"}}

    Now convert: '{user_query}'
    """
    try:
        response = gemini_model.generate_content(prompt)
        return json.loads(response.text.strip().replace("'", '"'))
    except json.JSONDecodeError:
        st.error("❌ Failed to parse AI-generated query")
        return {}
    except Exception as e:
        st.error(f"❌ AI Query Generation Error: {str(e)}")
        return {}

def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)

    if mongo_query:
        try:
            start_time = time.time()
            patients = list(collection.find(mongo_query, {"_id": 0}).limit(50))

            if time.time() - start_time > 5:
                st.error("⏳ Query took too long. Try again later.")
                return None

            return patients if patients else None
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
            return None
    return None

# ✅ Streamlit UI
st.markdown('<p class="search-text" style="font-weight: bold; font-size: 22px; text-align: center;">Enter patient details to access medical records</p>', unsafe_allow_html=True)

user_query = st.text_input("", placeholder="🔍 Search by patient name, condition, doctor, or other criteria...", key="search_input")

st.markdown('<div class="center-container">', unsafe_allow_html=True)
search_button = st.button("Search Records")
st.markdown('</div>', unsafe_allow_html=True)

if search_button:
    if user_query:
        with st.spinner("Analyzing query and searching records..."):
            patients = fetch_patient_details(user_query)

        if patients:
            st.success(f"Found {len(patients)} matching records")
            for patient in patients:
                st.markdown(
                    f"""
                    <div class="patient-card">
                        <h3>{patient.get('Name', 'Unknown Patient')}</h3>
                        <p><span class="highlight">Age:</span> {patient.get('Age', 'N/A')}</p>
                        <p><span class="highlight">Gender:</span> {patient.get('Gender', 'N/A')}</p>
                        <p><span class="highlight">Blood Type:</span> {patient.get('Blood Type', 'N/A')}</p>
                        <p><span class="highlight">Hospital:</span> {patient.get('Hospital', 'N/A')}</p>
                        <p><span class="highlight">Doctor:</span> {patient.get('Doctor', 'N/A')}</p>
                        <p><span class="highlight">Medical Condition:</span> {patient.get('Medical Condition', 'N/A')}</p>
                        <p><span class="highlight">Admission Date:</span> {patient.get('Date of Admission', 'N/A')}</p>
                        <p><span class="highlight">Room Number:</span> {patient.get('Room Number', 'N/A')}</p>
                        <p><span class="highlight">Billing Amount:</span> ${patient.get('Billing Amount', 'N/A'):,}</p>
                        <p><span class="highlight">Test Results:</span> {patient.get('Test Results', 'N/A')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("No matching patient records found")
    else:
        st.error("Please enter a search term")
