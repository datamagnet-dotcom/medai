import streamlit as st
import pymongo
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# ✅ Step 1: Load Environment Variables (Security Fix)
load_dotenv()
MONGO_URI = os.getenv("mongodb://sainandan3mn:1234@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0")
GOOGLE_API_KEY = os.getenv("AIzaSyDzds9brrJzltcJePvaF1kMyv6hXB_P9Lw")

# ✅ Step 2: Connect to MongoDB Atlas
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Step 3: Configure Gemini AI Securely
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-pro")

# ✅ Step 4: Function to Convert Natural Language to MongoDB Query
def generate_mongo_query(user_query):
    """Convert natural language query into MongoDB JSON query using Gemini AI."""
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query:

    '{user_query}'

    Example:
    'Find details of patient Bobby Jackson' -> {{"Name": "Bobby Jackson"}}
    """

    response = gemini_model.generate_content(prompt)

    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        return {}

# ✅ Step 5: Function to Fetch Patient Details
def fetch_patient_details(user_query):
    """Fetch patient details from MongoDB using an AI-generated query."""
    mongo_query = generate_mongo_query(user_query)

    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}

        patient = collection.find_one(mongo_query, {"_id": 0})  # Exclude MongoDB ID

        if patient:
            return f"""
            🔹 **Patient Details:**
            - **Name:** {patient.get('Name', 'N/A')}
            - **Age:** {patient.get('Age', 'N/A')}
            - **Gender:** {patient.get('Gender', 'N/A')}
            - **Blood Type:** {patient.get('Blood Type', 'N/A')}
            - **Medical Condition:** {patient.get('Medical Condition', 'N/A')}
            - **Doctor:** {patient.get('Doctor', 'N/A')}
            - **Room Number:** {patient.get('Room Number', 'N/A')}
            """
        else:
            return "❌ No matching patient found."

    return "⚠️ Invalid query."

# ✅ Step 6: Streamlit UI for Patient Search
st.title("🏥 AI-Powered Patient Search")
st.write("Search patient details using natural language!")

user_query = st.text_input("🔍 Enter your query (e.g., 'Who is Bobby Jackson?')")

if st.button("Search"):
    if user_query:
        result = fetch_patient_details(user_query)
        st.markdown(result)
    else:
        st.warning("⚠️ Please enter a search query.")
