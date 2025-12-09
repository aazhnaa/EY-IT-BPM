import streamlit as st
import pandas as pd
import time

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
            with st.spinner("Extracting data via VLM..."):
                time.sleep(1) # Fake delay for demo feel
            with st.spinner("Querying NPI Registry..."):
                time.sleep(1)
            st.session_state.processed = True
            st.rerun()

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
if st.session_state.processed:
    st.subheader("🔍 Real-Time Validation Result")
    
    # Create 3 columns for the "Before vs After" effect
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        st.info("**Extracted from PDF (VLM)**")
        # TODO: Replace these hardcoded strings with data from utils.enrichment_agent()
        st.text_input("Name (PDF)", "Dr. John Smith", disabled=True)
        st.text_input("NPI (PDF)", "1234567890", disabled=True)
        st.text_input("Phone (PDF)", "888-555-1234", disabled=True) # The "Wrong" number

    with c2:
        st.success("**Validated NPI Data (Official)**")
        # TODO: Replace with data from utils.validation_agent()
        st.text_input("Name (Official)", "Dr. John Smith", disabled=True)
        st.text_input("NPI (Official)", "1234567890", disabled=True)
        st.text_input("Phone (Official)", "888-555-9999", disabled=True) # The "Right" number

    with c3:
        st.warning("**QA Analysis**")
        # TODO: Replace with data from utils.qa_agent()
        st.metric(label="Confidence Score", value="60%", delta="-40%")
        st.error("MISMATCH DETECTED")
        st.write("**Discrepancy:** Phone number does not match NPI Registry.")

    # Add this result to the queue (Simulated)
    if st.session_state.processed and len(st.session_state.data_log) == 2:
        new_row = {"ID": "P-001", "Name": "Dr. John Smith", "NPI": "1234567890", "Score": 60, "Status": "Phone Mismatch"}
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