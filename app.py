import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time

# ✅ Page Configurations
st.set_page_config(page_title="Med AI - Patient Search", page_icon="🏥", layout="centered")

# ✅ Apply KareXpert-inspired professional theme
custom_css = """
<style>
    body {
        background-color: #121212;
        color: #ffffff;
        font-family: 'Arial', sans-serif;
    }
    .stTextInput>div>div>input {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #555;
        padding: 8px;
        border-radius: 5px;
    }
    .stButton>button {
        background-color: #00aaff;
        color: #ffffff;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0088cc;
        color: #ffffff;
    }
    .card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 0px 10px rgba(255, 255, 255, 0.2);
        font-size: 16px;
        line-height: 1.6;
        margin-top: 15px;
    }
    .card h3 {
        color: #00d1ff;
        font-size: 22px;
        margin-bottom: 10px;
    }
    .highlight {
        font-weight: bold;
        color: #ffffff;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ MongoDB Configuration
MONGO_URI = "mongodb://sainandan3mn:1234@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyDzds9brrJzltcJePvaF1kMyv6hXB_P9Lw")
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
st.title("🏥 Med AI - Patient Lookup")
st.write("Search for patient details using AI-powered lookup.")
user_query = st.text_input("🔎 Enter a patient's name or query", "")

if st.button("Search"):
    if user_query:
        with st.spinner("🔄 Searching..."):
            patient_data = fetch_patient_details(user_query)
        if patient_data:
            st.success("✅ Patient Record Found!")
            st.markdown(
                f"""
                <div class="card">
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
