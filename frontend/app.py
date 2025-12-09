import streamlit as st
import pandas as pd
import time
import requests
# --- 1. Page Configuration (Must be first) ---
st.set_page_config(
    page_title="ProviderValidator AI",
    page_icon="🏥",
    layout="wide"
)

# --- 2. Session State Management ---
# This keeps data alive when buttons are clicked
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'data_log' not in st.session_state:
    # Dummy data for the "Prioritized Queue" to show the UI working immediately
    st.session_state.data_log = pd.DataFrame([
        {"ID": "P-002", "Name": "Dr. Sarah Lee", "NPI": "9876543210", "Score": 95, "Status": "Verified"},
        {"ID": "P-003", "Name": "Dr. Mike Ross", "NPI": "1122334455", "Score": 40, "Status": "Critical Mismatch"},
    ])

# --- 3. Sidebar: Input & Controls ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=50) # Placeholder Icon
    st.title("Validation HQ")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Provider Application (PDF/Image)", type=['png', 'jpg', 'pdf'])
    
    if uploaded_file is not None:
        st.success("File Uploaded Successfully")
        if st.button("Run AI Validation Pipeline", type="primary"):
    
            with st.status("🚀 communicating with Backend API...", expanded=True) as status:
                
                # Prepare the file to send over the network
                files = {"file": uploaded_file.getvalue()}
                
                try:
                    # CALL THE API (The "Production Way")
                    response = requests.post("http://localhost:8000/validate_document", files={"file": uploaded_file})
                    
                    if response.status_code == 200:
                        validation_report = response.json()
                        st.session_state.current_result = validation_report
                        st.session_state.processed = True
                        status.update(label="✅ API Response Received!", state="complete")
                    else:
                        st.error(f"API Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"Connection Error: Is the backend running? {e}")

# --- 4. Main Dashboard Area ---
st.title("🏥 Provider Data Validation Dashboard")

# Top Level Metrics (The "Business Value" View)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Providers Processed", "142", "+12 today")
col2.metric("Avg. Confidence Score", "88%", "+5%")
col3.metric("Critical Flags", "3", "Requires Attention")
col4.metric("AHT Savings", "94%", "vs Manual")

st.markdown("---")

# --- 5. The "Wow" Factor: Side-by-Side Comparison ---
if st.session_state.processed and 'current_result' in st.session_state:
    st.subheader("剥 Real-Time Validation Result")
    
    # Get the real data from the backend report
    res = st.session_state.current_result
    extracted = res['extracted']
    official = res['official']
    score = res['validation_result']['score']
    
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        st.info("**Extracted from PDF (VLM)**")
        st.text_input("Name (PDF)", extracted.get("provider_name", "N/A"), disabled=True)
        st.text_input("NPI (PDF)", extracted.get("npi_number", "N/A"), disabled=True)
        st.text_input("Phone (PDF)", extracted.get("phone_number", "N/A"), disabled=True)

    with c2:
        st.success("**Validated NPI Data (Official)**")
        st.text_input("Name (Official)", official.get("official_name", "Not Found"), disabled=True)
        st.text_input("NPI (Official)", extracted.get("npi_number", "N/A"), disabled=True)
        st.text_input("Phone (Official)", official.get("official_phone", "N/A"), disabled=True)

    with c3:
        st.warning("**QA Analysis**")
        st.metric(label="Confidence Score", value=f"{score}%", delta=f"{score-100}%")
        
        if score < 100:
            st.error("MISMATCH DETECTED")
            st.write(f"**Issues:** {', '.join(res['validation_result']['mismatches'])}")
        else:
            st.success("VERIFIED MATCH")

    # Add to Queue Logic
    # Check if this NPI is already in our list to avoid duplicates
    existing_npis = st.session_state.data_log["NPI"].astype(str).values
    current_npi = str(extracted.get("npi_number"))
    
    if current_npi not in existing_npis:
        new_row = {
            "ID": f"P-00{len(st.session_state.data_log) + 2}", 
            "Name": extracted.get("provider_name"), 
            "NPI": current_npi, 
            "Score": score, 
            "Status": "Critical Mismatch" if score < 70 else "Verified"
        }
        st.session_state.data_log = pd.concat([pd.DataFrame([new_row]), st.session_state.data_log], ignore_index=True)

st.markdown("---")

# --- 6. The "Prioritized Queue" (DataFrame) ---
st.subheader("📋 Prioritized Review Queue (Lowest Confidence First)")

# Sort data so lowest score is on top
sorted_df = st.session_state.data_log.sort_values(by="Score", ascending=True)

# Use data_editor so it looks interactive
st.data_editor(
    sorted_df,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Confidence Score",
            help="AI calculated confidence",
            format="%d%%",
            min_value=0,
            max_value=100,
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Verified", "Phone Mismatch", "Critical Mismatch"],
            required=True,
        )
    },
    hide_index=True,
    use_container_width=True
)

# --- 7. Action Area: Email Generator ---
st.subheader("📧 Action Center")
col_a, col_b = st.columns([1, 3])

with col_a:
    target_provider = st.selectbox("Select Provider to Contact", sorted_df["Name"].unique())
    if st.button("Generate Correction Email"):
        st.session_state.show_email = True

with col_b:
    if 'show_email' in st.session_state and st.session_state.show_email:
        st.text_area(
            "Generated Email Draft",
            f"Subject: Important - Data Discrepancy for {target_provider}\n\n"
            f"Dear {target_provider},\n\n"
            "Our automated validation system has detected a discrepancy in your contact information "
            "between your submitted application and the NPI Registry.\n\n"
            "Please confirm your current practice phone number immediately.\n\n"
            "Sincerely,\nProvider Network Team",
            height=200
        )
        st.button("Send Email 🚀")