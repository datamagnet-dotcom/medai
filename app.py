import streamlit as st
import pymongo
import google.generativeai as genai
import json
import time
import re
from pathlib import Path
from bson import ObjectId

# ✅ Page Configurations
st.set_page_config(page_title="Hospital Patient Search", page_icon="🏥", layout="centered", initial_sidebar_state="collapsed")

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

# Multiple collections
patients_collection = db["patients"]
medical_records_collection = db["medical_records"]
appointments_collection = db["appointments"]
billing_collection = db["billing"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyAFnVZdH90z8H6hXtsMT3-ITuOtc_HySQw")
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Add debug mode toggle in sidebar
debug_mode = st.sidebar.checkbox("Debug Mode", False)

def generate_multi_collection_query(user_query):
    prompt = f"""
    Convert the following natural language query into MongoDB queries for a database with multiple collections.
    The database has the following collections and fields:
    
    1. patients: {{"_id": ObjectId, "name": String, "age": Number, "gender": String, "blood_type": String}}
    
    2. medical_records: {{"_id": ObjectId, "patient_id": ObjectId, "medical_condition": String, "medication": String, "test_results": String}}
    
    3. appointments: {{"_id": ObjectId, "patient_id": ObjectId, "doctor": String, "hospital": String, "room_number": Number, "admission_type": String, "date_of_admission": String, "discharge_date": String}}
    
    4. billing: {{"_id": ObjectId, "patient_id": ObjectId, "insurance_provider": String, "billing_amount": Number}}
    
    Return a JSON object with query parameters for each relevant collection. For text fields, use case-insensitive regex matches.
    ONLY return valid JSON with no additional text, explanation, or code formatting.
    
    Format:
    {{
      "patients": {{ MongoDB query for patients collection }},
      "medical_records": {{ MongoDB query for medical_records collection }},
      "appointments": {{ MongoDB query for appointments collection }},
      "billing": {{ MongoDB query for billing collection }}
    }}
    
    For fields that aren't mentioned in the query, omit them from the returned JSON.
    
    Examples:
    - 'Find patients named John' → {{"patients": {{"name": {{"$regex": "John", "$options": "i"}}}}}}
    - 'Patients with blood type O+' → {{"patients": {{"blood_type": "O+"}}}}
    - 'Show patients aged 30' → {{"patients": {{"age": 30}}}}
    - 'Patients under Dr. Smith' → {{"appointments": {{"doctor": {{"$regex": "Smith", "$options": "i"}}}}}}
    - 'Diabetic patients' → {{"medical_records": {{"medical_condition": {{"$regex": "diabetes", "$options": "i"}}}}}}
    - 'Admitted on 2023-05-15' → {{"appointments": {{"date_of_admission": "2023-05-15"}}}}
    - 'Billing over $5000' → {{"billing": {{"billing_amount": {{"$gt": 5000}}}}}}
    - 'Room 205 patients' → {{"appointments": {{"room_number": 205}}}}
    
    Now convert: '{user_query}'
    """
    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        if debug_mode:
            st.subheader("AI Response (Debug Mode)")
            st.code(response_text)
        
        # Clean up the response to ensure it's valid JSON
        # Remove potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        # Replace single quotes with double quotes for JSON validity
        response_text = response_text.replace("'", '"')
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            if debug_mode:
                st.error("JSON Decode Error - Attempting fallback parsing")
            
            # Fallback: Try to extract anything that looks like JSON
            json_pattern = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_pattern:
                try:
                    extracted_json = json_pattern.group()
                    if debug_mode:
                        st.code(extracted_json, language="json")
                    return json.loads(extracted_json)
                except:
                    if debug_mode:
                        st.error("Fallback extraction failed")
            
            # Last resort: Create a basic query from the user input
            if debug_mode:
                st.warning("Using default search pattern")
            return {
                "patients": {"name": {"$regex": user_query, "$options": "i"}},
                "medical_records": {"medical_condition": {"$regex": user_query, "$options": "i"}},
                "appointments": {"doctor": {"$regex": user_query, "$options": "i"}},
                "billing": {}
            }
            
    except Exception as e:
        if debug_mode:
            st.error(f"AI Query Generation Error: {str(e)}")
        # Fallback query
        return {
            "patients": {"name": {"$regex": user_query, "$options": "i"}},
            "medical_records": {"medical_condition": {"$regex": user_query, "$options": "i"}},
            "appointments": {"doctor": {"$regex": user_query, "$options": "i"}},
            "billing": {}
        }

def fetch_patient_details(user_query):
    multi_collection_query = generate_multi_collection_query(user_query)

    if debug_mode:
        st.subheader("MongoDB Query")
        st.code(json.dumps(multi_collection_query, indent=4), language="json")

    try:
        start_time = time.time()
        
        # First, find matching patients from the patients collection
        patient_query = multi_collection_query.get("patients", {})
        matching_patients = list(patients_collection.find(patient_query, {"_id": 1, "name": 1, "age": 1, "gender": 1, "blood_type": 1}))
        
        # If no patients found directly, try to find patients through other collections
        if not matching_patients:
            # Try medical records
            med_query = multi_collection_query.get("medical_records", {})
            if med_query:
                matching_med_records = list(medical_records_collection.find(med_query, {"patient_id": 1}))
                patient_ids = [record["patient_id"] for record in matching_med_records]
                if patient_ids:
                    matching_patients = list(patients_collection.find({"_id": {"$in": patient_ids}}))
            
            # Try appointments
            if not matching_patients:
                app_query = multi_collection_query.get("appointments", {})
                if app_query:
                    matching_appointments = list(appointments_collection.find(app_query, {"patient_id": 1}))
                    patient_ids = [appt["patient_id"] for appt in matching_appointments]
                    if patient_ids:
                        matching_patients = list(patients_collection.find({"_id": {"$in": patient_ids}}))
            
            # Try billing
            if not matching_patients:
                bill_query = multi_collection_query.get("billing", {})
                if bill_query:
                    matching_bills = list(billing_collection.find(bill_query, {"patient_id": 1}))
                    patient_ids = [bill["patient_id"] for bill in matching_bills]
                    if patient_ids:
                        matching_patients = list(patients_collection.find({"_id": {"$in": patient_ids}}))
        
        # Now enrich the patient data with information from other collections
        enriched_patients = []
        for patient in matching_patients:
            patient_id = patient["_id"]
            
            # Get medical records
            medical_record = medical_records_collection.find_one({"patient_id": patient_id})
            
            # Get appointment info
            appointment = appointments_collection.find_one({"patient_id": patient_id})
            
            # Get billing info
            billing = billing_collection.find_one({"patient_id": patient_id})
            
            # Create comprehensive patient record
            complete_patient = {
                "Name": patient.get("name", "Unknown"),
                "Age": patient.get("age", "N/A"),
                "Gender": patient.get("gender", "N/A"),
                "Blood Type": patient.get("blood_type", "N/A"),
                "Medical Condition": medical_record.get("medical_condition", "N/A") if medical_record else "N/A",
                "Medication": medical_record.get("medication", "N/A") if medical_record else "N/A",
                "Test Results": medical_record.get("test_results", "N/A") if medical_record else "N/A",
                "Doctor": appointment.get("doctor", "N/A") if appointment else "N/A",
                "Hospital": appointment.get("hospital", "N/A") if appointment else "N/A",
                "Room Number": appointment.get("room_number", "N/A") if appointment else "N/A",
                "Admission Type": appointment.get("admission_type", "N/A") if appointment else "N/A",
                "Date of Admission": appointment.get("date_of_admission", "N/A") if appointment else "N/A",
                "Discharge Date": appointment.get("discharge_date", "N/A") if appointment else "N/A",
                "Insurance Provider": billing.get("insurance_provider", "N/A") if billing else "N/A",
                "Billing Amount": billing.get("billing_amount", "N/A") if billing else "N/A"
            }
            
            enriched_patients.append(complete_patient)
        
        if debug_mode:
            st.write(f"Total patient records found: {len(enriched_patients)}")
        
        if time.time() - start_time > 5:
            st.error("⏳ Query took too long. Try again later.")
            return None

        return enriched_patients if enriched_patients else None
    except Exception as e:
        st.error(f"❌ Database Error: {str(e)}")
        if debug_mode:
            st.exception(e)
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
                        <p><span class="highlight">Medication:</span> {patient.get('Medication', 'N/A')}</p>
                        <p><span class="highlight">Admission Type:</span> {patient.get('Admission Type', 'N/A')}</p>
                        <p><span class="highlight">Admission Date:</span> {patient.get('Date of Admission', 'N/A')}</p>
                        <p><span class="highlight">Discharge Date:</span> {patient.get('Discharge Date', 'N/A')}</p>
                        <p><span class="highlight">Room Number:</span> {patient.get('Room Number', 'N/A')}</p>
                        <p><span class="highlight">Insurance Provider:</span> {patient.get('Insurance Provider', 'N/A')}</p>
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
