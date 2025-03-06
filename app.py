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

# Original collection (for backward compatibility)
original_collection = db["patients"]

# ✅ Configure Gemini AI
genai.configure(api_key="AIzaSyAFnVZdH90z8H6hXtsMT3-ITuOtc_HySQw")
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Add debug mode toggle in sidebar
debug_mode = st.sidebar.checkbox("Debug Mode", False)

# Toggle for using original or multi-collection mode
use_original_collection = st.sidebar.checkbox("Use Original Collection", True, 
                                             help="Toggle this to switch between original single collection and new multi-collection mode")

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

def generate_mongo_query(user_query):
    prompt = f"""
    Convert the following natural language query into a MongoDB JSON query.
    Consider all relevant fields and use appropriate query operators.
    For text fields, use case-insensitive regex matches for partial searches.
    
    IMPORTANT: Return ONLY the valid JSON query with no additional text, explanation, or code formatting.
    
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
            return {"$or": [
                {"Name": {"$regex": user_query, "$options": "i"}},
                {"Medical Condition": {"$regex": user_query, "$options": "i"}},
                {"Doctor": {"$regex": user_query, "$options": "i"}}
            ]}
            
    except Exception as e:
        if debug_mode:
            st.error(f"AI Query Generation Error: {str(e)}")
        # Fallback query
        return {"$or": [
            {"Name": {"$regex": user_query, "$options": "i"}},
            {"Medical Condition": {"$regex": user_query, "$options": "i"}},
            {"Doctor": {"$regex": user_query, "$options": "i"}}
        ]}

def fetch_from_original_collection(user_query):
    mongo_query = generate_mongo_query(user_query)

    if debug_mode:
        st.subheader("MongoDB Query (Original Collection)")
        st.code(json.dumps(mongo_query, indent=4), language="json")

    if mongo_query:
        try:
            start_time = time.time()
            # Add unique patient filtering by adding a distinct pipeline stage
            pipeline = [
                {"$match": mongo_query},
                {"$group": {
                    "_id": "$Name",  # Group by name to eliminate duplicates
                    "doc": {"$first": "$$ROOT"}  # Keep the first document for each name
                }},
                {"$replaceRoot": {"newRoot": "$doc"}},  # Replace the root with the original document
                {"$project": {"_id": 0}}  # Remove the _id field
            ]
            
            patients = list(original_collection.aggregate(pipeline, allowDiskUse=True))
            
            if debug_mode:
                st.write(f"Total records found (original collection): {len(patients)}")
            
            if time.time() - start_time > 5:
                st.error("⏳ Query took too long. Try again later.")
                return None

            return patients if patients else None
        except Exception as e:
            st.error(f"❌ Database Error (Original Collection): {str(e)}")
            if debug_mode:
                st.exception(e)
            return None
    return None

def fetch_from_multi_collections(user_query):
    multi_collection_query = generate_multi_collection_query(user_query)

    if debug_mode:
        st.subheader("MongoDB Multi-Collection Query")
        st.code(json.dumps(multi_collection_query, indent=4), language="json")

    try:
        start_time = time.time()
        matching_patients = []
        
        # Check if collections have data (only in debug mode)
        if debug_mode:
            st.write(f"Patients collection count: {patients_collection.count_documents({})}")
            st.write(f"Medical records collection count: {medical_records_collection.count_documents({})}")
            st.write(f"Appointments collection count: {appointments_collection.count_documents({})}")
            st.write(f"Billing collection count: {billing_collection.count_documents({})}")
            
        # First, search directly in patients collection
        patient_query = multi_collection_query.get("patients", {})
        if patient_query:
            matching_patients_direct = list(patients_collection.find(patient_query))
            if matching_patients_direct:
                matching_patients.extend(matching_patients_direct)
                if debug_mode:
                    st.write(f"Found {len(matching_patients_direct)} patients directly from patients collection")

        # Search in medical_records collection
        med_record_query = multi_collection_query.get("medical_records", {})
        if med_record_query and not matching_patients:
            matching_med_records = list(medical_records_collection.find(med_record_query))
            if matching_med_records:
                if debug_mode:
                    st.write(f"Found {len(matching_med_records)} matching medical records")
                # Extract patient IDs
                patient_ids = []
                for record in matching_med_records:
                    try:
                        patient_id = record.get("patient_id")
                        if patient_id:
                            patient_ids.append(patient_id)
                    except:
                        pass
                
                if patient_ids:
                    # Find patients with these IDs
                    patients_from_med_records = list(patients_collection.find({"_id": {"$in": patient_ids}}))
                    matching_patients.extend(patients_from_med_records)
                    if debug_mode:
                        st.write(f"Found {len(patients_from_med_records)} patients from medical records")

        # Search in appointments collection
        appointment_query = multi_collection_query.get("appointments", {})
        if appointment_query and not matching_patients:
            matching_appointments = list(appointments_collection.find(appointment_query))
            if matching_appointments:
                if debug_mode:
                    st.write(f"Found {len(matching_appointments)} matching appointments")
                # Extract patient IDs
                patient_ids = []
                for appt in matching_appointments:
                    try:
                        patient_id = appt.get("patient_id")
                        if patient_id:
                            patient_ids.append(patient_id)
                    except:
                        pass
                
                if patient_ids:
                    # Find patients with these IDs
                    patients_from_appointments = list(patients_collection.find({"_id": {"$in": patient_ids}}))
                    matching_patients.extend(patients_from_appointments)
                    if debug_mode:
                        st.write(f"Found {len(patients_from_appointments)} patients from appointments")

        # Search in billing collection
        billing_query = multi_collection_query.get("billing", {})
        if billing_query and not matching_patients:
            matching_billings = list(billing_collection.find(billing_query))
            if matching_billings:
                if debug_mode:
                    st.write(f"Found {len(matching_billings)} matching billing records")
                # Extract patient IDs
                patient_ids = []
                for bill in matching_billings:
                    try:
                        patient_id = bill.get("patient_id")
                        if patient_id:
                            patient_ids.append(patient_id)
                    except:
                        pass
                
                if patient_ids:
                    # Find patients with these IDs
                    patients_from_billing = list(patients_collection.find({"_id": {"$in": patient_ids}}))
                    matching_patients.extend(patients_from_billing)
                    if debug_mode:
                        st.write(f"Found {len(patients_from_billing)} patients from billing")

        # If still no patients found, try a broader search
        if not matching_patients:
            if debug_mode:
                st.write("No matches found in specific fields, trying text search across all collections")
            
            # Last resort text search in patients collection
            text_query = {"name": {"$regex": user_query, "$options": "i"}}
            matching_patients = list(patients_collection.find(text_query))
            
            if debug_mode:
                st.write(f"Found {len(matching_patients)} patients with text search")
                
        # If we have matching patients, enrich them with data from other collections
        enriched_patients = []
        
        for patient in matching_patients:
            patient_id = patient.get("_id")
            
            # Get medical record
            medical_record = None
            try:
                medical_record = medical_records_collection.find_one({"patient_id": patient_id})
            except Exception as e:
                if debug_mode:
                    st.write(f"Error fetching medical record: {str(e)}")
            
            # Get appointment
            appointment = None
            try:
                appointment = appointments_collection.find_one({"patient_id": patient_id})
            except Exception as e:
                if debug_mode:
                    st.write(f"Error fetching appointment: {str(e)}")
            
            # Get billing
            billing = None
            try:
                billing = billing_collection.find_one({"patient_id": patient_id})
            except Exception as e:
                if debug_mode:
                    st.write(f"Error fetching billing: {str(e)}")
            
            # Create enriched patient record
            enriched_patient = {
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
            
            enriched_patients.append(enriched_patient)
            
        if debug_mode:
            st.write(f"Final enriched patients count: {len(enriched_patients)}")
            
        if time.time() - start_time > 8:
            st.error("⏳ Query took too long. Try again later.")
            return None
            
        return enriched_patients if enriched_patients else None
    
    except Exception as e:
        st.error(f"❌ Database Error (Multi-Collection): {str(e)}")
        if debug_mode:
            st.exception(e)
        return None

def fetch_patient_details(user_query):
    if use_original_collection:
        return fetch_from_original_collection(user_query)
    else:
        return fetch_from_multi_collections(user_query)

# Add collection validation check
if debug_mode:
    if st.sidebar.button("Validate Collections"):
        collections = db.list_collection_names()
        st.sidebar.write("Available collections:")
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            st.sidebar.write(f"- {collection_name}: {count} documents")
            
        # Show a sample document from each collection
        try:
            st.sidebar.write("Sample from patients collection:")
            st.sidebar.json(patients_collection.find_one())
        except:
            st.sidebar.write("No sample found in patients collection")
            
        try:
            st.sidebar.write("Sample from medical_records collection:")
            st.sidebar.json(medical_records_collection.find_one())
        except:
            st.sidebar.write("No sample found in medical_records collection")
            
        try:
            st.sidebar.write("Sample from appointments collection:")
            st.sidebar.json(appointments_collection.find_one())
        except:
            st.sidebar.write("No sample found in appointments collection")
            
        try:
            st.sidebar.write("Sample from billing collection:")
            st.sidebar.json(billing_collection.find_one())
        except:
            st.sidebar.write("No sample found in billing collection")

# ✅ Streamlit UI
st.markdown('<p class="search-text" style="font-weight: bold; font-size: 22px; text-align: center;">Enter patient details to access medical records</p>', unsafe_allow_html=True)

# Show which mode is active
if use_original_collection:
    st.info("Using original collection mode. Toggle the checkbox in the sidebar to use multi-collection mode.")
else:
    st.info("Using multi-collection mode. Toggle the checkbox in the sidebar to use original collection mode.")

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
