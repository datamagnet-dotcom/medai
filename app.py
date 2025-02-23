import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time

# ✅ Set up page configuration
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="centered")

# ✅ Apply a black & white theme
custom_css = """
<style>
    body {
        background-color: #000;
        color: #fff;
    }
    .stTextInput>div>div>input {
        background-color: #333;
        color: #fff;
        border: 1px solid #666;
    }
    .stButton>button {
        background-color: #fff;
        color: #000;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ccc;
        color: #000;
    }
    .stAlert {
        border-radius: 5px;
        padding: 10px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ✅ MongoDB Configuration (Replace with your connection string)
MONGO_URI = "mongodb://sainandan3mn:<db_password>@cluster0-shard-00-00.ik5xa.mongodb.net:27017,cluster0-shard-00-01.ik5xa.mongodb.net:27017,cluster0-shard-00-02.ik5xa.mongodb.net:27017/?ssl=true&replicaSet=atlas-6p2mwc-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["hospital_db"]
collection = db["patients"]

# ✅ Configure Gemini AI (Replace with your API Key)
genai.configure(api_key="AIzaSyDzds9brrJzltcJePvaF1kMyv6hXB_P9Lw")
gemini_model = genai.GenerativeModel("gemini-pro")

# ✅ Convert Natural Language to MongoDB Query
def generate_mongo_query(user_query):
    """Converts a natural language query into a MongoDB JSON query using Gemini AI."""
    
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

# ✅ Fetch Patient Details from MongoDB
def fetch_patient_details(user_query):
    """Fetches patient details from MongoDB using an LLM-generated query with a timeout."""
    
    mongo_query = generate_mongo_query(user_query)

    if mongo_query and "Name" in mongo_query:
        clean_name = mongo_query["Name"].strip()
        mongo_query = {"Name": {"$regex": f"^{clean_name}$", "$options": "i"}}  # Case-insensitive match

        try:
            start_time = time.time()
            patient = collection.find_one(mongo_query, {"_id": 0})
            
            # Timeout check (Prevent long-running queries)
            if time.time() - start_time > 5:  # 5 seconds max
                st.error("⏳ Query took too long. Try again later.")
                return None
            
            return patient if patient else None
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
            return None

    return None

# ✅ Streamlit UI
st.title("🏥 Hospital Patient Search")
st.write("Enter a patient's name or related query to fetch details.")

# User input field
user_query = st.text_input("🔎 Enter your query", "")

if st.button("Search", help="Click to search patient details"):
    if user_query:
        with st.spinner("🔄 Searching..."):
            patient_data = fetch_patient_details(user_query)
        
        if patient_data:
            st.success("✅ Patient Found!")
            st.json(patient_data)  # Display details in JSON format
        else:
            st.warning("⚠️ No matching patient found.")
    else:
        st.error("❌ Please enter a query.")
