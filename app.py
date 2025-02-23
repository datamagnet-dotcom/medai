import streamlit as st
import pymongo
import google.generativeai as genai
import json

# ✅ Configure Streamlit Page
st.set_page_config(page_title="Med AI", page_icon="🏥", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: white;
    }
    .stApp {
        background-color: #121212;
    }
    .stTextInput, .stTextArea, .stButton>button {
        color: black !important;
    }
    .css-1cpxqw2, .css-1d391kg, .css-1v0mbdj {
        background-color: white !important;
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ✅ Connect to MongoDB Atlas
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
    Example:
    'Find details of patient Bobby Jackson' -> {{"Name": "Bobby Jackson"}}
    """
    response = gemini_model.generate_content(prompt)
    try:
        mongo_query = json.loads(response.text.strip())
        return mongo_query
    except json.JSONDecodeError:
        return {}

# ✅ Fetch Patient Details from MongoDB
def fetch_patient_details(user_query):
    mongo_query = generate_mongo_query(user_query)
    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}
        patient = collection.find_one(mongo_query, {"_id": 0})
        if patient:
            return patient
    return None

# ✅ Streamlit UI
st.title("🏥 Med AI - Patient Query System")
st.subheader("Search for patient details with ease.")
user_query = st.text_input("Enter your query:", placeholder="E.g., Find details of patient John Doe")
if st.button("Search"):
    with st.spinner("Fetching details..."):
        result = fetch_patient_details(user_query)
        if result:
            st.success("Patient record found:")
            st.json(result)
        else:
            st.error("No patient record found.")
