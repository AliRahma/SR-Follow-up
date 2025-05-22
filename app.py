
# SR Analyzer Pro - Unified SR and Incident Analysis
import streamlit as st
import pandas as pd
import numpy as np
import re
import io
from datetime import datetime, timedelta
import pytz
from streamlit_option_menu import option_menu

# Page config
st.set_page_config(page_title="SR Analyzer Pro", layout="wide")

# Theming
st.markdown("""
<style>
.stApp { background-color: #f5f7fa; color: #1e2a3a; }
</style>
""", unsafe_allow_html=True)

# Session init
for key in ['data_loaded', 'main_df', 'sr_df', 'incident_df', 'filtered_df', 'last_upload_time']:
    if key not in st.session_state:
        st.session_state[key] = None if 'df' in key else False

# Load Excel
@st.cache_data
def load_data(file):
    return pd.read_excel(file)

# Classify Note
def classify_and_extract(note):
    if not isinstance(note, str): return "Not Triaged", None, None
    note = note.lower()
    match = re.search(r'(tkt|sr|inc|ticket|incident)[^\d]*(\d{4,})', note)
    if match:
        num = int(match.group(2))
        return "Pending SR/Incident", num, "SR" if 14000 <= num <= 17000 else "Incident"
    return "Not Triaged", None, None

# Helper functions
def calculate_age(date): return (datetime.now() - date).days if pd.notna(date) else None
def is_created_today(date): return date.date() == datetime.now().date() if pd.notna(date) else False

def generate_excel_download(data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Results')
    output.seek(0)
    return output

# Sidebar upload
with st.sidebar:
    st.title("📊 SR Analyzer Pro")
    main_file = st.file_uploader("Upload Main File", type=["xlsx", "xls"])
    sr_file = st.file_uploader("Upload SR Status File", type=["xlsx", "xls"])
    incident_file = st.file_uploader("Upload Incident Report", type=["xlsx", "xls"])

    if main_file:
        df = load_data(main_file)
        df['Case Start Date'] = pd.to_datetime(df.get('Case Start Date'), errors='coerce')
        df['Last Note Date'] = pd.to_datetime(df.get('Last Note Date'), errors='coerce')
        st.session_state.main_df = df
        st.session_state.data_loaded = True
        st.success(f"Main data loaded: {df.shape[0]} records")
    if sr_file:
        st.session_state.sr_df = load_data(sr_file)
        st.success("SR status loaded")
    if incident_file:
        st.session_state.incident_df = load_data(incident_file)
        st.success("Incident report loaded")

# Enrich
def enrich_data(df):
    df = df.copy()
    df[['Temp Status', 'Ticket Number', 'Type']] = df['Last Note'].apply(lambda x: pd.Series(classify_and_extract(x)))
    df['Ticket Number'] = pd.to_numeric(df['Ticket Number'], errors='coerce')
    df['Age (Days)'] = df['Case Start Date'].apply(calculate_age)
    df['Created Today'] = df['Last Note Date'].apply(is_created_today)

    # SR merge
    if st.session_state.sr_df is not None:
        sr_df = st.session_state.sr_df.copy()
        sr_df['Service Request'] = pd.to_numeric(sr_df['Service Request'].astype(str).str.extract(r'(\d{4,})')[0], errors='coerce')
        sr_df.rename(columns={'Status': 'SR Status', 'LastModDateTime': 'Last Update'}, inplace=True)
        df = df.merge(sr_df[['Service Request', 'SR Status', 'Last Update', 'Breach Passed']], how='left', left_on='Ticket Number', right_on='Service Request')
        df.drop(columns=['Service Request'], inplace=True)

    # Incident merge
    if st.session_state.incident_df is not None:
        inc = st.session_state.incident_df.copy()
        inc['Incident ID'] = pd.to_numeric(inc['Incident ID'], errors='coerce')
        inc.rename(columns={'Status': 'Incident Status', 'Last Updated': 'Incident Last Update'}, inplace=True)
        df = df.merge(inc[['Incident ID', 'Incident Status', 'Incident Last Update', 'Breach Passed']], how='left', left_on='Ticket Number', right_on='Incident ID')

    df['Status'] = df['SR Status'].combine_first(df['Incident Status'])
    df['Last Update'] = df['Last Update'].combine_first(df['Incident Last Update'])
    df.drop(columns=['SR Status', 'Incident Status', 'Incident ID', 'Incident Last Update'], errors='ignore', inplace=True)
    return df

# Main logic
if not st.session_state.data_loaded:
    st.warning("Upload a main file to begin.")
    st.stop()

df_main = st.session_state.main_df.copy()
df_enriched = enrich_data(df_main)
st.session_state.filtered_df = df_enriched

# Tabs
selected = option_menu(None, ["Analysis", "SLA Breach", "Breached Incidents", "Today's SR/Incidents"],
    icons=["bar-chart", "alert-triangle", "activity", "calendar"],
    orientation="horizontal", default_index=0)

# Analysis
if selected == "Analysis":
    st.title("📊 Unified SR & Incident Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Triage Status Count")
        triage = df_enriched['Status'].value_counts().rename_axis('Triage').reset_index(name='Count')
        st.dataframe(triage)
    with col2:
        st.markdown("### Type Count")
        types = df_enriched['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
        st.dataframe(types)

    st.markdown("### 🟢 Incident Status Summary")
    inc_summary = df_enriched[df_enriched['Type'] == 'Incident']['Status'].value_counts().rename_axis('Incident Status').reset_index(name='Count')
    if inc_summary.empty:
        st.info("No incident data available.")
    else:
        st.dataframe(inc_summary)

# SLA Breach
elif selected == "SLA Breach":
    st.title("⚠️ SLA Breach Summary (SRs & Incidents)")
    breached = df_enriched[df_enriched['Breach Passed'] == True]
    st.write(f"Total Breaches: {len(breached)}")
    if not breached.empty:
        st.dataframe(breached[['Case Id', 'Current User Id', 'Status', 'Type', 'Ticket Number', 'Last Update']])

# Breached Incidents
elif selected == "Breached Incidents":
    st.title("🚨 Breached Incidents")
    inc_breach = df_enriched[(df_enriched['Type'] == 'Incident') & (df_enriched['Breach Passed'] == True)]
    st.write(f"Breached Incidents: {len(inc_breach)}")
    if not inc_breach.empty:
        st.dataframe(inc_breach[['Case Id', 'Current User Id', 'Status', 'Ticket Number', 'Last Update']])
        excel = generate_excel_download(inc_breach)
        st.download_button("Download Breached Incidents", data=excel, file_name="breached_incidents.xlsx")

# Today tab
elif selected == "Today's SR/Incidents":
    st.title("📅 Today's SRs/Incidents")
    today = df_enriched[df_enriched['Created Today'] == True]
    st.write(f"Total Today: {len(today)}")
    if not today.empty:
        st.dataframe(today[['Case Id', 'Current User Id', 'Status', 'Type', 'Ticket Number', 'Last Note']])

# Footer
st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.8em;">
    SR Analyzer Pro v2.0 | Developed by Ali Babiker | © 2025
    </div>""",
    unsafe_allow_html=True
)
