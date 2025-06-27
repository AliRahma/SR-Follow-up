import streamlit as st
import os
import pandas as pd
import numpy as np
import re
import io
import base64
from datetime import datetime, timedelta
import pytz
from streamlit_option_menu import option_menu
import plotly.express as px
from utils import calculate_team_status_summary, calculate_srs_created_per_week, _get_week_display_str # Added _get_week_display_str

# Set page configuration
st.set_page_config(
    page_title="Intellipen SmartQ Test",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
def set_custom_theme():
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stApp {
        color: #1e2a3a;
    }
    .stDataFrame, .stTable {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .badge-pending {
        background-color: #ffecb3;
        color: #b17825;
    }
    .badge-complete {
        background-color: #c8e6c9;
        color: #2e7d32;
    }
    .badge-in-progress {
        background-color: #bbdefb;
        color: #1565c0;
    }
    .badge-cancelled {
        background-color: #ffcdd2;
        color: #c62828;
    }
    .badge-breach {
        background-color: #ff5252;
        color: white;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 0;
    }
    .metric-label {
        font-size: 1em;
        color: #888;
        margin: 0;
    }
    h1, h2, h3 {
        color: #1565c0;
    }
    /* Custom styling for multi-select dataframe */
    div[data-testid="stDataFrame"] table {
        width: 100%;
    }
    div[data-testid="stDataFrame"] th:first-child, 
    div[data-testid="stDataFrame"] td:first-child {
        width: 50px !important;
        min-width: 50px !important;
        max-width: 50px !important;
    }
    .st-ch {
        font-size: 14px;
    }
    .action-button {
        background-color: #1976d2;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;
        cursor: pointer;
        font-size: 14px;
        margin-bottom: 10px;
    }
    .action-button:hover {
        background-color: #1565c0;
    }

    /* Dark Mode Styles */
    @media (prefers-color-scheme: dark) {
        .main {
            background-color: #0e1117; /* Streamlit's default dark background */
            color: #fafafa; /* Light text for dark background */
        }
        .stApp {
            color: #fafafa;
        }
        .stDataFrame, .stTable {
            background-color: #262730; /* Darker background for tables */
            color: #fafafa;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.5);
        }
        .card {
            background-color: #262730; /* Darker card background */
            color: #fafafa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.5);
            margin-bottom: 20px;
        }
        .metric-value {
            color: #fafafa;
        }
        .metric-label {
            color: #aaa; /* Lighter grey for labels */
        }
        h1, h2, h3 {
            color: #5c9dff; /* A lighter blue for headings */
        }
        /* Adjust badge colors for dark mode */
        .badge-pending {
            background-color: #533f00; /* Darker yellow */
            color: #ffecb3;
        }
        .badge-complete {
            background-color: #1b5e20; /* Darker green */
            color: #c8e6c9;
        }
        .badge-in-progress {
            background-color: #0d47a1; /* Darker blue */
            color: #bbdefb;
        }
        .badge-cancelled {
            background-color: #b71c1c; /* Darker red */
            color: #ffcdd2;
        }
        .badge-breach {
            background-color: #d32f2f; /* Slightly different red for breach */
            color: white;
        }
        .action-button {
            background-color: #5c9dff; /* Lighter blue for buttons */
            color: #0e1117; /* Dark text for light buttons */
        }
        .action-button:hover {
            background-color: #4a80cc; /* Darker shade of the button blue for hover */
        }

        /* Ensure selectbox and multiselect dropdowns are styled for dark mode */
        div[data-baseweb="select"] > div, div[data-baseweb="multiselect"] > div {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #555 !important;
        }
        div[data-baseweb="select"] input, div[data-baseweb="multiselect"] input {
            color: #fafafa !important;
        }
        /* Dropdown menu items */
        div[data-baseweb="menu"] li {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        div[data-baseweb="menu"] li:hover {
            background-color: #383943 !important;
        }

        /* Ensure text inputs are styled for dark mode */
        .stTextInput input, .stTextArea textarea, .stDateInput input {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #555 !important;
        }

        /* Style for option menu in dark mode */
        nav[role="tablist"] > a {
            color: #bbb !important; /* Lighter text for non-selected tabs */
        }
        nav[role="tablist"] > a.nav-link-selected {
            background-color: #5c9dff !important; /* Selected tab background */
            color: #0e1117 !important; /* Dark text on selected tab */
        }
        nav[role="tablist"] > a:hover {
            background-color: #383943 !important; /* Hover for non-selected tabs */
            color: #fafafa !important;
        }

        /* Ensure Streamlit buttons are styled */
        .stButton>button {
            background-color: #5c9dff !important;
            color: #0e1117 !important;
            border: 1px solid #5c9dff !important;
        }
        .stButton>button:hover {
            background-color: #4a80cc !important;
            border: 1px solid #4a80cc !important;
            color: #0e1117 !important;
        }
        .stDownloadButton>button {
            background-color: #5c9dff !important;
            color: #0e1117 !important;
            border: 1px solid #5c9dff !important;
        }
        .stDownloadButton>button:hover {
            background-color: #4a80cc !important;
            border: 1px solid #4a80cc !important;
            color: #0e1117 !important;
        }
        /* Sidebar styling */
        .css-1d391kg { /* This class might be Streamlit version specific, targets sidebar */
            background-color: #1a1c22 !important;
        }
        .css-1d391kg .stMarkdown, .css-1d391kg .stSubheader, .css-1d391kg .stTitle {
             color: #fafafa !important;
        }
         /* Adjusting table header in dark mode */
        div[data-testid="stDataFrame"] th {
            background-color: #383943 !important; /* Darker header for tables */
            color: #fafafa !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

set_custom_theme()

# Initialize session state for caching and storing data
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'main_df' not in st.session_state:
    st.session_state.main_df = None
if 'sr_df' not in st.session_state:
    st.session_state.sr_df = None
if 'incident_df' not in st.session_state:
    st.session_state.incident_df = None
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'last_upload_time' not in st.session_state:
    st.session_state.last_upload_time = None
if 'selected_users' not in st.session_state:
    st.session_state.selected_users = []
if 'selected_case_ids' not in st.session_state:
    st.session_state.selected_case_ids = []
if 'incident_overview_df' not in st.session_state:
    st.session_state.incident_overview_df = None
if 'incident_overview_df_original_cols' not in st.session_state: # New state for incident overview original columns
    st.session_state.incident_overview_df_original_cols = None
if 'main_df_original_cols' not in st.session_state: # New state for main_df original columns
    st.session_state.main_df_original_cols = None
if 'sr_df_original_cols' not in st.session_state: # New state for sr_df original columns
    st.session_state.sr_df_original_cols = None
if 'report_datetime' not in st.session_state:
    st.session_state.report_datetime = None

@st.cache_data
def load_data(file):
    if file is None:
        return None, None, None  # Return None for DataFrame, original_cols, and datetime string
    
    parsed_datetime_str = None
    df = None
    original_columns = None

    try:
        file_name = file.name
        # --- TEMPORARY LOGGING START ---
        print(f"--- DEBUG: load_data: file_name is '{file_name}' ---") 
        # --- TEMPORARY LOGGING END ---
        file_extension = os.path.splitext(file_name)[1].lower()

        # Attempt to parse datetime from filename
        match = re.search(r'_(\d{8})_(\d{6})\.', file_name)
        # --- TEMPORARY LOGGING START ---
        print(f"--- DEBUG: load_data: regex match object is {match} ---")
        if match:
            print(f"--- DEBUG: load_data: match.group(1) is '{match.group(1)}', match.group(2) is '{match.group(2)}' ---")
        # --- TEMPORARY LOGGING END ---
        
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            try:
                dt_object = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                parsed_datetime_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                # --- TEMPORARY LOGGING START ---
                print(f"--- DEBUG: load_data: successfully parsed datetime: {parsed_datetime_str} ---")
                # --- TEMPORARY LOGGING END ---
            except ValueError as e:
                # parsed_datetime_str remains None if parsing fails
                # --- TEMPORARY LOGGING START ---
                print(f"--- DEBUG: load_data: ValueError during parsing: {e} ---")
                # --- TEMPORARY LOGGING END ---
                # Optionally, log this error: st.warning(f"Could not parse date/time from filename: {file_name}")
        else:
            # --- TEMPORARY LOGGING START ---
            print(f"--- DEBUG: load_data: No regex match for filename '{file_name}' ---")
            # --- TEMPORARY LOGGING END ---
            # Optionally, log this error: st.warning(f"Could not parse date/time from filename: {file_name}")
        
        # Read the Excel file
        if file_extension == '.xls':
            try:
                df = pd.read_excel(file, engine='xlrd')
            except Exception:
                try:
                    file.seek(0)
                    df = pd.read_excel(file, engine='openpyxl')
                except Exception as e_openpyxl:
                    raise e_openpyxl
        elif file_extension == '.xlsx':
            df = pd.read_excel(file, engine='openpyxl')
        else:
            st.error(f"Unsupported file type: {file_extension}. Please upload .xls or .xlsx files.") # Changed from raise to st.error
            return None, None, parsed_datetime_str # Return None for df and original_cols if unsupported

        if df is not None:
            original_columns = df.columns.tolist()
            df.columns = [col.lower().strip() for col in df.columns]

        return df, original_columns, parsed_datetime_str
            
    except Exception as e:
        st.error(f"Error loading file '{file.name}': {e}")
        return None, None, parsed_datetime_str # Return None for df and original_cols

# Function to process main dataframe
def process_main_df(df): # df here already has normalized columns
    # Ensure date columns are in datetime format using normalized names
    date_columns = ['case start date', 'last note date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
    
    # Extract all unique users using normalized column name
    if 'current user id' in df.columns:
        all_users = sorted(df['current user id'].dropna().unique().tolist())
        st.session_state.all_users = all_users
    
    return df

# Function to classify and extract ticket info
def classify_and_extract(note):
    if not isinstance(note, str):
        return "Not Triaged", None, None
    
    note_lower = note.lower()
    # Enhanced regex pattern to catch more variations
    match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
        
    if match:
        ticket_num = int(match.group(2))
        # SR numbers typically between 14000-18000 (adjust based on your system)
        ticket_type = "SR" if 14000 <= ticket_num <= 18000 else "Incident"
        return "Pending SR/Incident", ticket_num, ticket_type
    
    return "Not Triaged", None, None

# Function to calculate case age in days
def calculate_age(start_date):
    if pd.isna(start_date):
        return None
    return (datetime.now() - start_date).days

# Function to determine if a note was created today
def is_created_today(date_value):
    if pd.isna(date_value):
        return False
    today = datetime.now().date()
    note_date = date_value.date() if isinstance(date_value, datetime) else date_value
    return note_date == today

# Function to create downloadable Excel
def generate_excel_download(data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Results')
        workbook = writer.book
        worksheet = writer.sheets['Results']
        
        # Add formats for better Excel styling
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1976d2',
            'color': 'white',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(data.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Auto-adjust columns' width
        for i, col in enumerate(data.columns):
            max_len = max(data[col].astype(str).apply(len).max(), len(str(col))) + 1
            worksheet.set_column(i, i, max_len)
    
    output.seek(0)
    return output

# Sidebar - File Upload Section
with st.sidebar:
    # Display the logo
    st.image("Smart Q Logo.jpg", width=150)
    st.title("📊 Intellipen SmartQ Test")
    st.markdown("---")

    st.subheader("📁 Data Import")
    uploaded_file = st.file_uploader("Upload Main Excel File (.xlsx)", type=["xlsx"])
    sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type=["xlsx","xls"])
    incident_status_file = st.file_uploader("Upload Incident Report Excel (optional)", type=["xlsx","xls"])
    
    # report_datetime is initialized to None at the start of the session.
    # We process files in order: Main, SR, Incident for setting it IF it's currently None.

    if uploaded_file:
        with st.spinner("Loading main data..."):
            df, original_cols, parsed_dt = load_data(uploaded_file)
            if df is not None:
                st.session_state.main_df = process_main_df(df)
                st.session_state.main_df_original_cols = original_cols # Store original columns
                abu_dhabi_tz = pytz.timezone('Asia/Dubai')
                st.session_state.last_upload_time = datetime.now(abu_dhabi_tz).strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"Main data loaded: {df.shape[0]} records")
                st.session_state.data_loaded = True
                if parsed_dt:
                    st.session_state.report_datetime = parsed_dt
            # If df is None, load_data would have shown an error. parsed_dt might still have a value if filename was parsable but content failed.
            # However, if df is None, we probably shouldn't use its parsed_dt either, as the file is unusable.
            # The current load_data returns (None, parsed_dt) even on file read error.
            # Consider if parsed_dt should only be used if df is not None.
            # For now, strictly following: if parsed_dt is not None from main file, use it.
            # This was already handled by: if parsed_dt: st.session_state.report_datetime = parsed_dt. This is fine.

    if sr_status_file:
        with st.spinner("Loading SR status data..."):
            sr_df, sr_original_cols, parsed_dt_sr = load_data(sr_status_file)
            if sr_df is not None:
                st.session_state.sr_df = sr_df
                st.session_state.sr_df_original_cols = sr_original_cols # Store original columns
                st.success(f"SR status data loaded: {sr_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_sr:
                    st.session_state.report_datetime = parsed_dt_sr
            # else: df is None, error shown by load_data
    
    if incident_status_file:
        with st.spinner("Loading incident report data..."):
            incident_df, incident_original_cols, parsed_dt_incident = load_data(incident_status_file)
            if incident_df is not None:
                st.session_state.incident_df = incident_df
                # We might not need to store incident_original_cols separately for st.session_state.incident_df
                # if it's only used to create incident_overview_df.
                # However, if incident_df itself is ever displayed or its columns selected, we would.
                # For now, let's assume incident_overview_df is the primary one from this file.

                st.success(f"Incident report data loaded: {incident_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_incident:
                    st.session_state.report_datetime = parsed_dt_incident

                # Process for Incident Overview tab (existing logic)
                # The incident_df here already has normalized columns.
                overview_df = incident_df.copy()
                # The rename for "customer" to "creator" should use normalized names.
                # Original column name was 'Customer', normalized is 'customer'.
                # Target new name is 'creator' (already normalized).
                if "customer" in overview_df.columns: # Check using normalized name
                    overview_df.rename(columns={"customer": "creator"}, inplace=True)

                st.session_state.incident_overview_df = overview_df
                # Store the original column names that correspond to the *final* incident_overview_df columns
                # This is tricky because of the rename. If "customer" was renamed to "creator",
                # the original_columns list from load_data (incident_original_cols) needs to be updated.
                # For simplicity, if a rename happened, we should adjust incident_original_cols before storing.
                current_overview_cols = overview_df.columns.tolist()
                overview_original_cols_map = dict(zip(incident_df.columns, incident_original_cols))

                final_overview_original_cols = []
                for col in current_overview_cols:
                    if col == "creator" and "customer" in overview_original_cols_map and "creator" not in overview_original_cols_map:
                        # If 'creator' is the new column and 'customer' was its source
                        final_overview_original_cols.append(overview_original_cols_map.get("customer", "Creator")) # Fallback to "Creator" if somehow not in map
                    elif col in overview_original_cols_map:
                        final_overview_original_cols.append(overview_original_cols_map[col])
                    else:
                        final_overview_original_cols.append(col.replace("_", " ").title()) # Fallback for new cols or if mapping fails

                st.session_state.incident_overview_df_original_cols = final_overview_original_cols

                st.success(f"Incident Overview data loaded: {len(overview_df)} records, {len(overview_df.columns)} columns.")
            else:
                st.session_state.incident_overview_df = None
                st.session_state.incident_overview_df_original_cols = None
    
    # Display last upload time (existing logic)
    if 'last_upload_time' not in st.session_state or st.session_state.last_upload_time is None:
        pass
    if st.session_state.get('last_upload_time'):
        st.info(f"Last data import: {st.session_state.last_upload_time}")
    else:
        st.info("No data imported yet in this session.")
    
    st.markdown("---")
    
    # Filters section (existing logic, depends on st.session_state.data_loaded)
    if st.session_state.data_loaded:
        st.subheader("🔍 Filters")
        df_main = st.session_state.main_df.copy() # Should be safe as data_loaded is True
        # Use normalized column name for Current User Id
        all_users = df_main['current user id'].dropna().unique().tolist() if 'current user id' in df_main.columns else []
        SELECT_ALL_USERS_OPTION = "[Select All Users]"
        default_users_hardcoded = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa','GPSSA_H.Salah','alharith.alfki']
        default_users = [u for u in default_users_hardcoded if u in all_users]

        if 'sidebar_user_widget_selection_controlled' not in st.session_state:
            st.session_state.selected_users = list(default_users)
            if not default_users and all_users:
                st.session_state.selected_users = list(all_users)
                st.session_state.sidebar_user_widget_selection_controlled = [SELECT_ALL_USERS_OPTION]
            elif all_users and set(default_users) == set(all_users):
                st.session_state.sidebar_user_widget_selection_controlled = [SELECT_ALL_USERS_OPTION]
            elif not all_users:
                 st.session_state.selected_users = []
                 st.session_state.sidebar_user_widget_selection_controlled = []
            else:
                st.session_state.sidebar_user_widget_selection_controlled = list(default_users)

        options_for_user_widget = [SELECT_ALL_USERS_OPTION] + all_users
        raw_widget_selection = st.multiselect(
            "Select Users",
            options=options_for_user_widget,
            default=st.session_state.sidebar_user_widget_selection_controlled,
            key="multi_select_sidebar_users"
        )

        prev_widget_display_state = list(st.session_state.sidebar_user_widget_selection_controlled)
        current_select_all_option_selected = SELECT_ALL_USERS_OPTION in raw_widget_selection
        currently_selected_actual_items = [u for u in raw_widget_selection if u != SELECT_ALL_USERS_OPTION]
        user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_USERS_OPTION not in prev_widget_display_state)
        user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_USERS_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

        if user_clicked_select_all:
            st.session_state.selected_users = list(all_users)
            st.session_state.sidebar_user_widget_selection_controlled = [SELECT_ALL_USERS_OPTION]
        elif user_clicked_unselect_all:
            st.session_state.selected_users = []
            st.session_state.sidebar_user_widget_selection_controlled = []
        else:
            if current_select_all_option_selected:
                if len(currently_selected_actual_items) < len(all_users):
                    st.session_state.selected_users = list(currently_selected_actual_items)
                    st.session_state.sidebar_user_widget_selection_controlled = list(currently_selected_actual_items)
                else:
                    st.session_state.selected_users = list(all_users)
                    st.session_state.sidebar_user_widget_selection_controlled = [SELECT_ALL_USERS_OPTION]
            else:
                st.session_state.selected_users = list(currently_selected_actual_items)
                if all_users and set(currently_selected_actual_items) == set(all_users):
                    st.session_state.sidebar_user_widget_selection_controlled = [SELECT_ALL_USERS_OPTION]
                else:
                    st.session_state.sidebar_user_widget_selection_controlled = list(currently_selected_actual_items)
        
        # Use normalized column name for Case Start Date
        if 'case start date' in df_main.columns and not df_main['case start date'].dropna().empty:
            min_date = df_main['case start date'].min().date()
            max_date = df_main['case start date'].max().date()
            if 'sidebar_date_range_value' not in st.session_state:
                st.session_state.sidebar_date_range_value = (min_date, max_date)
            if st.button("Select Full Range", key="btn_select_full_date_range"):
                st.session_state.sidebar_date_range_value = (min_date, max_date)
            current_date_range_from_widget = st.date_input(
                "Date Range",
                value=st.session_state.sidebar_date_range_value,
                min_value=min_date,
                max_value=max_date,
                key="date_input_sidebar"
            )
            if current_date_range_from_widget != st.session_state.sidebar_date_range_value:
                st.session_state.sidebar_date_range_value = current_date_range_from_widget
            date_range = st.session_state.sidebar_date_range_value

# Main content
if not st.session_state.data_loaded:
    st.title("📊 Intellipen SmartQ Test")
    st.markdown("""
    ### Welcome to the Intellipen SmartQ Test!
    
    This application helps you analyze Service Requests and Incidents efficiently.
    
    To get started:
    1. Upload your main Excel file using the sidebar
    2. Optionally upload SR status file for enhanced analysis
    3. Optionally upload Incident report file for incident tracking
    4. Use the application to analyze and export your data
    
    **Enhanced Features:**
    - Advanced filtering and search
    - Detailed SR and Incident Analysis
    - SLA/Incident Breach monitoring
    - Today's new incidents and SRs
    - Unified Status tracking for both SRs and Incidents
    """)
else:
    # Process and filter data
    df_main = st.session_state.main_df.copy()
    
    # Apply user filters
    # Use normalized column name for Current User Id
    if st.session_state.selected_users and 'current user id' in df_main.columns:
        df_filtered = df_main[df_main['current user id'].isin(st.session_state.selected_users)].copy()
    else:
        df_filtered = df_main.copy()
    
    # Apply date filter if date range is selected
    # Use normalized column name for Case Start Date
    if 'case start date' in df_filtered.columns and 'date_range' in locals() and not df_filtered['case start date'].dropna().empty:
        start_date, end_date = date_range
        # Ensure the column is in datetime format before trying to access .dt accessor
        if not pd.api.types.is_datetime64_any_dtype(df_filtered['case start date']):
            df_filtered['case start date'] = pd.to_datetime(df_filtered['case start date'], errors='coerce')

        # Filter out NaT values that might result from coercion errors before date comparison
        df_filtered_no_nat = df_filtered.dropna(subset=['case start date'])
        df_filtered = df_filtered_no_nat[
            (df_filtered_no_nat['case start date'].dt.date >= start_date) &
            (df_filtered_no_nat['case start date'].dt.date <= end_date)
        ]
    
    # Prepare tab interface
    selected = option_menu(
        menu_title=None,
        options=["Analysis", "SLA Breach", "Today's SR/Incidents", "Incident Overview", "SR Overview"],
        icons=["kanban", "exclamation-triangle", "calendar-date", "clipboard-data", "bar-chart-line"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "margin": "0!important"},
            "icon": {"color": "#1565c0", "font-size": "14px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#1976d2", "color": "white"},
        }
    )
    
    # Function to further process and enrich data
    def enrich_data(df): # df comes in with already normalized columns
        df_enriched = df.copy()
        
        # Classify and extract ticket info using normalized column name
        if 'last note' in df_enriched.columns:
            df_enriched[['Triage Status', 'Ticket Number', 'Type']] = pd.DataFrame( # These new columns are fine as is
                df_enriched['last note'].apply(lambda x: pd.Series(classify_and_extract(x)))
            )
        else:
            df_enriched['Triage Status'] = "Error: Last Note missing"
            df_enriched['Ticket Number'] = None
            df_enriched['Type'] = None

        # Calculate case age using normalized column name
        if 'case start date' in df_enriched.columns:
            df_enriched['Age (Days)'] = df_enriched['case start date'].apply(calculate_age) # New column
        else:
            df_enriched['Age (Days)'] = None

        # Determine if note was created today using normalized column name
        if 'last note date' in df_enriched.columns:
            df_enriched['Created Today'] = df_enriched['last note date'].apply(is_created_today) # New column
        else:
            df_enriched['Created Today'] = False
        
        # Initialize Status, Last Update, and Breach Passed columns (these are new, names are fine)
        df_enriched['Status'] = None
        df_enriched['Last Update'] = None
        df_enriched['Breach Passed'] = None # This will store boolean
        
        # Ensure 'Ticket Number' (a new column from classify_and_extract) is numeric before any merges
        if 'Ticket Number' in df_enriched.columns: # This is a new column, not from original upload
            df_enriched['Ticket Number'] = pd.to_numeric(df_enriched['Ticket Number'], errors='coerce')

        # Merge with SR status data if available
        # st.session_state.sr_df has normalized columns from load_data
        if hasattr(st.session_state, 'sr_df') and st.session_state.sr_df is not None:
            sr_df_copy = st.session_state.sr_df.copy()
            
            # Use normalized column names for sr_df_copy
            service_request_col_norm = 'service request'
            status_col_norm = 'status'
            last_mod_col_norm = 'lastmoddatetime'
            breach_passed_col_norm = 'breach passed' # This is the expected normalized name from SR file

            if service_request_col_norm in sr_df_copy.columns:
                sr_df_copy[service_request_col_norm] = sr_df_copy[service_request_col_norm].astype(str).str.extract(r'(\d{4,})')
                sr_df_copy[service_request_col_norm] = pd.to_numeric(sr_df_copy[service_request_col_norm], errors='coerce')
                sr_df_copy.dropna(subset=[service_request_col_norm], inplace=True)

                cols_to_merge_from_sr = [service_request_col_norm]
                sr_rename_for_merge = {}

                if status_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[status_col_norm] = 'SR_Status_temp'
                if last_mod_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[last_mod_col_norm] = 'SR_Last_Update_temp'
                # For 'Breach Passed' from SR file, its normalized name is 'breach passed'
                if breach_passed_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[breach_passed_col_norm] = 'SR_Breach_Value_temp'

                sr_df_copy.rename(columns=sr_rename_for_merge, inplace=True)

                for new_name in sr_rename_for_merge.values():
                    if new_name not in cols_to_merge_from_sr:
                        cols_to_merge_from_sr.append(new_name)

                df_enriched = df_enriched.merge(
                    sr_df_copy[cols_to_merge_from_sr], # These are already the temp names or normalized names
                    how='left',
                    left_on='Ticket Number', # This is a new column in df_enriched
                    right_on=service_request_col_norm if service_request_col_norm not in sr_rename_for_merge else sr_rename_for_merge[service_request_col_norm], # Join on the correct name in sr_df_copy
                    suffixes=('', '_sr_merged')
                )

                # Clean up merged column if it was created (e.g. 'service request_sr_merged')
                merged_sr_col_name = f"{service_request_col_norm}_sr_merged"
                if merged_sr_col_name in df_enriched.columns:
                    df_enriched.drop(columns=[merged_sr_col_name], inplace=True)
                # If the original service_request_col_norm from sr_df_copy was not renamed and got merged, drop it if it's a duplicate.
                # This situation is less likely if it's the join key and handled by suffixes, but as a safe guard.
                elif service_request_col_norm in df_enriched.columns and service_request_col_norm != 'Ticket Number' and df_enriched.columns.tolist().count(service_request_col_norm) > 1 :
                     df_enriched.drop(columns=[service_request_col_norm], errors='ignore', inplace=True)


                sr_mask = df_enriched['Type'] == 'SR' # Type is a new column

                if 'SR_Status_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, 'Status'] = df_enriched.loc[sr_mask, 'SR_Status_temp']
                    df_enriched.drop(columns=['SR_Status_temp'], inplace=True)
                if 'SR_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, 'Last Update'] = df_enriched.loc[sr_mask, 'SR_Last_Update_temp']
                    df_enriched.drop(columns=['SR_Last_Update_temp'], inplace=True)

                if 'SR_Breach_Value_temp' in df_enriched.columns:
                    def map_str_to_bool_sr(value):
                        if pd.isna(value): return None
                        val_lower = str(value).lower()
                        if val_lower in ['yes', 'true', '1', 'passed'] : return True
                        if val_lower in ['no', 'false', '0', 'failed']: return False
                        return None # Default for unmapped strings

                    mapped_values = df_enriched.loc[sr_mask, 'SR_Breach_Value_temp'].apply(map_str_to_bool_sr)
                    df_enriched.loc[sr_mask, 'Breach Passed'] = mapped_values
                    df_enriched.drop(columns=['SR_Breach_Value_temp'], inplace=True)

        # Merge with Incident status data if available
        # st.session_state.incident_df has normalized columns
        if hasattr(st.session_state, 'incident_df') and st.session_state.incident_df is not None:
            incident_df_copy = st.session_state.incident_df.copy()

            # Define normalized versions of potential incident ID column names
            incident_id_col_options_norm = ['incident', 'incident id', 'incidentid', 'id', 'number']
            incident_id_col_norm = None # This will store the actual normalized column name found

            for col_option_norm in incident_id_col_options_norm:
                if col_option_norm in incident_df_copy.columns:
                    incident_id_col_norm = col_option_norm
                    break
            
            if incident_id_col_norm:
                incident_df_copy[incident_id_col_norm] = incident_df_copy[incident_id_col_norm].astype(str).str.extract(r'(\d{4,})')
                incident_df_copy[incident_id_col_norm] = pd.to_numeric(incident_df_copy[incident_id_col_norm], errors='coerce')
                incident_df_copy.dropna(subset=[incident_id_col_norm], inplace=True)
                
                inc_rename_map = {incident_id_col_norm: 'Incident_Number_temp'} # Use the found normalized name
                inc_merge_cols = ['Incident_Number_temp']

                # Normalized column names for incident file
                status_col_inc_norm = 'status'
                breach_passed_col_inc_norm = 'breach passed' # Expected normalized name

                if status_col_inc_norm in incident_df_copy.columns:
                    inc_rename_map[status_col_inc_norm] = 'INC_Status_temp'
                    inc_merge_cols.append('INC_Status_temp')

                # Normalized potential last update columns
                last_update_options_norm = {
                    'last checked at': 'last checked at', # value is original, key is normalized
                    'last checked atc': 'last checked atc',
                    'modified on': 'modified on',
                    'last update': 'last update'
                }
                actual_last_update_col_norm = None
                for norm_name, _ in last_update_options_norm.items():
                    if norm_name in incident_df_copy.columns:
                        actual_last_update_col_norm = norm_name
                        break

                if actual_last_update_col_norm:
                    inc_rename_map[actual_last_update_col_norm] = 'INC_Last_Update_temp'
                    inc_merge_cols.append('INC_Last_Update_temp')

                if breach_passed_col_inc_norm in incident_df_copy.columns:
                    inc_rename_map[breach_passed_col_inc_norm] = 'INC_Breach_Passed_temp'
                    inc_merge_cols.append('INC_Breach_Passed_temp')

                incident_df_copy.rename(columns=inc_rename_map, inplace=True)
                
                df_enriched = df_enriched.merge(
                    incident_df_copy[inc_merge_cols],
                    how='left',
                    left_on='Ticket Number',
                    right_on='Incident_Number_temp',
                    suffixes=('', '_inc_merged')
                )
                if 'Incident_Number_temp_inc_merged' in df_enriched.columns:
                     df_enriched.drop(columns=['Incident_Number_temp_inc_merged'], inplace=True)
                elif 'Incident_Number_temp' in df_enriched.columns :
                     df_enriched.drop(columns=['Incident_Number_temp'], inplace=True, errors='ignore')

                incident_mask = df_enriched['Type'] == 'Incident'
                
                if 'INC_Status_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, 'Status'] = df_enriched.loc[incident_mask, 'INC_Status_temp']
                    df_enriched.drop(columns=['INC_Status_temp'], inplace=True)
                if 'INC_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, 'Last Update'] = df_enriched.loc[incident_mask, 'INC_Last_Update_temp']
                    df_enriched.drop(columns=['INC_Last_Update_temp'], inplace=True)
                
                if 'INC_Breach_Passed_temp' in df_enriched.columns:
                    def map_str_to_bool_inc(value):
                        if pd.isna(value): return None
                        if isinstance(value, bool): return value
                        val_lower = str(value).lower()
                        if val_lower in ['yes', 'true', '1', 'passed', 'breached']: return True
                        if val_lower in ['no', 'false', '0', 'failed', 'not breached']: return False
                        return None

                    mapped_inc_breach_values = df_enriched.loc[incident_mask, 'INC_Breach_Passed_temp'].apply(map_str_to_bool_inc)
                    df_enriched.loc[incident_mask, 'Breach Passed'] = mapped_inc_breach_values
                    df_enriched.drop(columns=['INC_Breach_Passed_temp'], inplace=True)

        if 'Last Update' in df_enriched.columns: # This is a new column, name is fine
            df_enriched['Last Update'] = pd.to_datetime(df_enriched['Last Update'], errors='coerce')

        # 'breach date' is a column that might come from the main sheet, so it needs to be normalized if accessed directly
        # However, the current logic doesn't seem to use a 'breach date' column directly from the input 'df' for df_enriched.
        # 'Breach Passed' is the boolean flag being set.
        # If there IS a 'breach date' column from the original Excel that needs processing here, it should be:
        # if 'breach date' in df_enriched.columns: # Assuming 'breach date' is the normalized name
        #     df_enriched['breach date'] = pd.to_datetime(df_enriched['breach date'], errors='coerce')
        # For now, I'll assume the existing 'Breach Passed' logic is sufficient and there's no separate 'Breach Date' field from input being directly processed here.

        if 'Ticket Number' in df_enriched.columns and 'Type' in df_enriched.columns: # New columns, names are fine
            valid_ticket_mask = df_enriched['Ticket Number'].notna() & df_enriched['Type'].notna()
            if valid_ticket_mask.any():
                 df_enriched.loc[valid_ticket_mask, 'Case Count'] = df_enriched[valid_ticket_mask].groupby(['Ticket Number', 'Type'])['Ticket Number'].transform('size') # New column
        else:
            df_enriched['Case Count'] = pd.NA
            
        return df_enriched
    
    # Enrich data with classifications and metrics
    df_enriched = enrich_data(df_filtered)
    
    # Store the enriched dataframe for use across tabs
    st.session_state.filtered_df = df_enriched
    
    #
    # ANALYSIS TAB (Formerly SR/INCIDENT ANALYSIS)
    #
    if selected == "Analysis":
        st.title("🔍 Analysis")
        
        # Adjusted "Last data update" display
        if st.session_state.get('last_upload_time'):
            # Use a clearer label now that last_upload_time is corrected
            update_time_display = st.session_state.last_upload_time
            st.markdown(f"**Last Data Import Time:** {update_time_display}")
        else:
            st.markdown("**Last Data Import Time:** No data imported yet")

        # New "Report Datetime" label
        if st.session_state.get('report_datetime'):
            report_datetime_display = st.session_state.report_datetime
            st.markdown(f"**Report Datetime (from filename):** {report_datetime_display}")
        else:
            st.markdown("**Report Datetime (from filename):** Not available")
        
        # Filtering options
        col1, col2,col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Triage Status",
                ["All"] + df_enriched["Triage Status"].dropna().unique().tolist()
            )
        
        with col2:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "SR", "Incident"]
            )
        
        with col3:
            # Unified Status filter
            if 'Status' in df_enriched.columns:
                status_options = ["All"] + df_enriched['Status'].dropna().unique().tolist() + ["None"]
                unified_status_filter = st.selectbox("Filter by Status", status_options)
            else:
                unified_status_filter = "All"
        
        # Apply filters
        df_display = df_enriched.copy()
        
        if status_filter != "All":
            df_display = df_display[df_display["Triage Status"] == status_filter]
        
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]
        
        if unified_status_filter != "All":
            if unified_status_filter == "None":
                df_display = df_display[df_display["Status"].isna()]
            else:
                df_display = df_display[df_display["Status"] == unified_status_filter]
        
        # Statistics and summary
        st.subheader("📊 Summary Analysis")
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.markdown("**🔸 Triage Status Count**")
            triage_summary = df_enriched['Triage Status'].value_counts().rename_axis('Triage Status').reset_index(name='Count')
            triage_total = {'Triage Status': 'Total', 'Count': triage_summary['Count'].sum()}
            triage_df = pd.concat([triage_summary, pd.DataFrame([triage_total])], ignore_index=True)
            
            st.dataframe(
                triage_df.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(triage_df)-1 else '' for _ in x],
                    axis=1
                )
            )
        with summary_col2:
            st.markdown("**🔹 SR vs Incident Count**")
            type_summary = df_enriched['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
            type_total = {'Type': 'Total', 'Count': type_summary['Count'].sum()}
            type_df = pd.concat([type_summary, pd.DataFrame([type_total])], ignore_index=True)
            
            st.dataframe(
                type_df.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(type_df)-1 else '' for _ in x],
                    axis=1
                )
            )
        summary_col3, summary_col4 = st.columns(2)
        with summary_col3:
            st.markdown("**🟢 SR Status Summary**")
            if 'Status' in df_enriched.columns and 'Type' in df_enriched.columns and not df_enriched[df_enriched['Type'] == 'SR'].empty:
                # Filter only for SRs
                df_srs = df_enriched[df_enriched['Type'] == 'SR'].copy()
                df_srs_status_valid = df_srs.dropna(subset=['Status'])
                
                if not df_srs_status_valid.empty:
                    # All SR status count
                    status_all_counts = df_srs_status_valid['Status'].value_counts().rename_axis('Status').reset_index(name='All Count')
                    
                    # Unique SR tickets
                    ticket_unique = df_srs_status_valid.dropna(subset=['Ticket Number'])[['Ticket Number', 'Status']].drop_duplicates()
                    ticket_unique_counts = ticket_unique['Status'].value_counts().rename_axis('Status').reset_index(name='Unique Count')
                    
                    # Merge both summaries
                    merged_status = pd.merge(status_all_counts, ticket_unique_counts, on='Status', how='outer').fillna(0)
                    merged_status[['All Count', 'Unique Count']] = merged_status[['All Count', 'Unique Count']].astype(int)
                    
                    # Total row
                    total_row = {
                        'Status': 'Total',
                        'All Count': merged_status['All Count'].sum(),
                        'Unique Count': merged_status['Unique Count'].sum()
                    }
                    
                    status_summary_df = pd.concat([merged_status, pd.DataFrame([total_row])], ignore_index=True)
                    
                    # Display
                    st.dataframe(
                        status_summary_df.style.apply(
                            lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(status_summary_df)-1 else '' for _ in x],
                            axis=1
                        )
                    )
                else:
                    st.info("No SRs with status information available.")
            else:
                st.info("Upload SR Status Excel file to view SR Status Summary.")

        #Incident Status Summary
        with summary_col4: # Or create new columns if layout needs adjustment
            st.markdown("**🟣 Incident Status Summary**")
            if 'Status' in df_enriched.columns and 'Type' in df_enriched.columns and not df_enriched[df_enriched['Type'] == 'Incident'].empty:
                df_incidents = df_enriched[df_enriched['Type'] == 'Incident'].copy()
                df_incidents_status_valid = df_incidents.dropna(subset=['Status'])

                if not df_incidents_status_valid.empty:
                    # All incident status count
                    incident_status_all_counts = df_incidents_status_valid['Status'].value_counts().rename_axis('Status').reset_index(name='Cases Count')
                    
                    # Unique incident tickets
                    incident_ticket_unique = df_incidents_status_valid.dropna(subset=['Ticket Number'])[['Ticket Number', 'Status']].drop_duplicates()
                    incident_ticket_unique_counts = incident_ticket_unique['Status'].value_counts().rename_axis('Status').reset_index(name='Unique Count')
                    
                    # Merge both summaries for incidents
                    merged_incident_status = pd.merge(incident_status_all_counts, incident_ticket_unique_counts, on='Status', how='outer').fillna(0)
                    merged_incident_status[['Cases Count', 'Unique Count']] = merged_incident_status[['Cases Count', 'Unique Count']].astype(int)
                    
                    # Total row for incidents
                    incident_total_row = {
                        'Status': 'Total',
                        'Cases Count': merged_incident_status['Cases Count'].sum(),
                        'Unique Count': merged_incident_status['Unique Count'].sum()
                    }
                    
                    incident_status_summary_df = pd.concat([merged_incident_status, pd.DataFrame([incident_total_row])], ignore_index=True)
                    
                    # Display Incident Status Summary
                    st.dataframe(
                        incident_status_summary_df.style.apply(
                            lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(incident_status_summary_df)-1 else '' for _ in x],
                            axis=1
                        )
                    )
                else:
                    st.info("No incidents with status information available to summarize.")
            elif st.session_state.incident_df is None:
                st.info("Upload Incident Report Excel file to view Incident Status Summary.")
            else:
                st.info("No incident data available to summarize.")
        
        # Detailed Results
        st.subheader("📋 Filtered Results")
        
        # Results count and download button
        results_col1, results_col2 = st.columns([3, 1])
        
        with results_col1:
            st.markdown(f"**Total Filtered Records:** {df_display.shape[0]}")
        
        with results_col2:
            if not df_display.empty:
                excel_data = generate_excel_download(df_display)
                st.download_button(
                    label="📥 Download Results",
                    data=excel_data,
                    file_name=f"sr_incident_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Display data table with customizable columns
        if not df_display.empty:
            all_columns = df_display.columns.tolist() # These are normalized at this point
            SELECT_ALL_COLS_ANALYSIS_OPTION = "[Select All Columns]"

            # Define default columns using NORMALIZED names
            default_selected_cols_initial = ['last note', 'case id', 'current user id', 'case start date', 'Triage Status', 'Type', 'Ticket Number']
            # 'Triage Status', 'Type', 'Ticket Number', 'Status', 'Last Update', 'Breach Passed' are new columns created in enrich_data,
            # so their names are already as defined there (mixed case or specific).
            # The ones from the original Excel (last note, case id, current user id, case start date) must be normalized.

            if 'Status' in df_display.columns: # 'Status' is a new column, direct name is fine
                default_selected_cols_initial.extend(['Status', 'Last Update']) # 'Last Update' is new
            if 'Breach Passed' in df_display.columns: # 'Breach Passed' is new
                default_selected_cols_initial.append('Breach Passed')

            # Ensure default columns are valid and exist in df_display
            default_selected_cols = [col for col in default_selected_cols_initial if col in all_columns]

            if 'analysis_tab_column_widget_selection_controlled' not in st.session_state:
                st.session_state.selected_display_cols = list(default_selected_cols) # Actual columns to display

                if not default_selected_cols and all_columns: # If default_selected_cols is empty and there are columns, select all
                    st.session_state.selected_display_cols = list(all_columns)
                    st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                elif all_columns and set(default_selected_cols) == set(all_columns): # If default_selected_cols happens to be all columns
                    st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                elif not all_columns: # If there are no columns at all
                    st.session_state.selected_display_cols = []
                    st.session_state.analysis_tab_column_widget_selection_controlled = []
                else: # Default columns are a subset
                    st.session_state.analysis_tab_column_widget_selection_controlled = list(default_selected_cols)

            options_for_cols_widget = [SELECT_ALL_COLS_ANALYSIS_OPTION] + all_columns
            raw_cols_widget_selection = st.multiselect(
                "Select columns to display:",
                options=options_for_cols_widget,
                default=st.session_state.analysis_tab_column_widget_selection_controlled,
                key="multi_select_analysis_columns"
            )

            prev_widget_display_state = list(st.session_state.analysis_tab_column_widget_selection_controlled)
            current_select_all_option_selected = SELECT_ALL_COLS_ANALYSIS_OPTION in raw_cols_widget_selection
            currently_selected_actual_items = [c for c in raw_cols_widget_selection if c != SELECT_ALL_COLS_ANALYSIS_OPTION]

            user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_COLS_ANALYSIS_OPTION not in prev_widget_display_state)
            user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_COLS_ANALYSIS_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

            if user_clicked_select_all:
                st.session_state.selected_display_cols = list(all_columns)
                st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
            elif user_clicked_unselect_all:
                st.session_state.selected_display_cols = []
                st.session_state.analysis_tab_column_widget_selection_controlled = []
            else:
                if current_select_all_option_selected:
                    if len(currently_selected_actual_items) < len(all_columns):
                        st.session_state.selected_display_cols = list(currently_selected_actual_items)
                        st.session_state.analysis_tab_column_widget_selection_controlled = list(currently_selected_actual_items)
                    else:
                        st.session_state.selected_display_cols = list(all_columns)
                        st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                else:
                    st.session_state.selected_display_cols = list(currently_selected_actual_items)
                    if all_columns and set(currently_selected_actual_items) == set(all_columns):
                        st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                    else:
                        st.session_state.analysis_tab_column_widget_selection_controlled = list(currently_selected_actual_items)

            columns_to_show = st.session_state.get('selected_display_cols', []) # Default to empty list if not set
            if not columns_to_show and all_columns:
                 columns_to_show = all_columns

            if columns_to_show: # Ensure there are columns to show
                st.dataframe(df_display[columns_to_show], hide_index=True)
            else: # This case should ideally be covered by the logic above, but as a fallback
                st.info("Please select at least one column to display, or all columns will be shown if the selection is empty and columns are available.")

        elif df_display.empty: # This elif should be at the same level as the first if not df_display.empty
            st.info("No data to display based on current filters.")
        # If df_display is not empty but columns_to_show ended up empty (e.g. if all_columns was also empty initially)
        # This case is unlikely if df_display was not empty, but good to be robust.
        else:
            st.info("No columns available to display.")

        # Incidents/SRs Linked Cases Summary
        st.subheader("🔗 Incidents/SRs Linked Cases Summary")
        min_linked_cases = st.number_input("Minimum Linked Cases", min_value=1, value=2, step=1)

        if 'Case Count' in df_display.columns and 'Ticket Number' in df_display.columns:
            linked_cases_df = df_display[
                (df_display['Case Count'] >= min_linked_cases) &
                (df_display['Ticket Number'].notna())
            ]

            if not linked_cases_df.empty:
                linked_summary_df = linked_cases_df[['Ticket Number', 'Type','Status', 'Case Count']].drop_duplicates().sort_values(by='Case Count', ascending=False)
                st.dataframe(linked_summary_df, hide_index=True)
            else:
                st.info(f"No Incidents/SRs found with at least {min_linked_cases} linked cases based on current filters.")
        else:
            st.warning("Required columns ('Case Count', 'Ticket Number') not available for linked cases summary.")

        # Note viewer
        st.subheader("📝 Note Details")
        
        selected_case = st.selectbox(
            "Select a case to view notes:", # df_display has normalized 'case id'
            df_display['case id'].tolist() if 'case id' in df_display.columns else []
        )
        
        if selected_case and 'case id' in df_display.columns:
            case_row = df_display[df_display['case id'] == selected_case].iloc[0]
            
            # Display case details in a table
            # When accessing fields from case_row, use normalized names
            case_details = {
                "Field": ["Case ID", "Owner", "Start Date", "Age", "Ticket Number", "Type"],
                "Value": [
                    case_row.get('case id', 'N/A'), # Use .get for safety
                    case_row.get('current user id', 'N/A'),
                    case_row['case start date'].strftime('%Y-%m-%d') if pd.notna(case_row.get('case start date')) else 'N/A',
                    f"{case_row.get('Age (Days)', 'N/A')} days", # 'Age (Days)' is a new column
                    int(case_row['Ticket Number']) if pd.notna(case_row.get('Ticket Number')) else 'N/A', # 'Ticket Number' is new
                    case_row.get('Type', 'N/A') # 'Type' is new
                ]
            }
            
            # Add Status if available (these are new columns, names are direct)
            if 'Status' in case_row and pd.notna(case_row['Status']):
                case_details["Field"].append("Status")
                case_details["Value"].append(case_row['Status'])
                
                if 'Last Update' in case_row and pd.notna(case_row['Last Update']):
                    case_details["Field"].append("Last Update")
                    case_details["Value"].append(case_row['Last Update']) # Already datetime or NaT
                
                if 'Breach Passed' in case_row: # This is a boolean or None
                    case_details["Field"].append("SLA Breach")
                    breach_value = case_row['Breach Passed']
                    display_breach = "Yes ⚠️" if breach_value is True else ("No" if breach_value is False else "N/A")
                    case_details["Value"].append(display_breach)
            
            # Display as a table
            st.table(pd.DataFrame(case_details))
            
            # Display the full note using normalized name
            st.markdown("### Last Note")
            if 'last note' in case_row and pd.notna(case_row['last note']):
                st.text_area("Note Content", case_row['last note'], height=200)
            else:
                st.info("No notes available for this case")
            
            # Download button for case details (df_display has normalized 'case id')
            excel_data = generate_excel_download(df_display[df_display['case id'] == selected_case])
            st.download_button(
                label="📥 Download Case Details",
                data=excel_data,
                file_name=f"case_{selected_case}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    #
    # SLA BREACH TAB
    #
    elif selected == "SLA Breach":
        st.title("⚠️ SLA Breach Analysis")
        
        # Check if either SR or Incident data is available
        if st.session_state.sr_df is None and st.session_state.incident_df is None:
            st.warning("Please upload SR Status Excel file or Incident Report Excel file to view SLA breach information.")
        else:
            # Filter to get only breach cases
            if 'Breach Passed' in df_enriched.columns:
                breach_df = df_enriched[df_enriched['Breach Passed'] == True].copy()
                
                # Display summary statistics
                st.subheader("📊 SLA Breach Summary")
                
                # Statistics cards
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    breach_count = len(breach_df)
                    st.markdown(f'<p class="metric-value">{breach_count}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Total SLA Breaches</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if 'Status' in breach_df.columns:
                        open_breaches = len(breach_df[breach_df['Status'].isin(['Open', 'In Progress', 'Pending', 'New'])])
                        st.markdown(f'<p class="metric-value">{open_breaches}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Open Breached Cases</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Status Not Available</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if 'Type' in breach_df.columns:
                        sr_breaches = len(breach_df[breach_df['Type'] == 'SR'])
                        st.markdown(f'<p class="metric-value">{sr_breaches}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">SR Breaches</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">SR Breaches</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Breach details by type and status
                if not breach_df.empty:
                    st.subheader("📋 SLA Breach Details")
                    
                    # Filter options for breach analysis
                    breach_col1, breach_col2 = st.columns(2)
                    
                    with breach_col1:
                        breach_type_filter = st.selectbox(
                            "Filter by Type (Breach)",
                            ["All", "SR", "Incident"],
                            key="breach_type"
                        )
                    
                    with breach_col2:
                        if 'Status' in breach_df.columns:
                            breach_status_options = ["All"] + breach_df['Status'].dropna().unique().tolist()
                            breach_status_filter = st.selectbox(
                                "Filter by Status (Breach)",
                                breach_status_options,
                                key="breach_status"
                            )
                        else:
                            breach_status_filter = "All"
                    
                    # Apply breach filters
                    breach_display = breach_df.copy()
                    
                    if breach_type_filter != "All":
                        breach_display = breach_display[breach_display["Type"] == breach_type_filter]
                    
                    if breach_status_filter != "All":
                        breach_display = breach_display[breach_display["Status"] == breach_status_filter]
                    
                    # Display breach results
                    st.markdown(f"**Total Breached Records:** {breach_display.shape[0]}")
                    
                    # Download button for breach data
                    if not breach_display.empty:
                        excel_breach_data = generate_excel_download(breach_display) # df_display has original names for display
                        st.download_button(
                            label="📥 Download Breach Analysis",
                            data=excel_breach_data,
                            file_name=f"sla_breach_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Breach data table: Define with normalized names for selection from df_enriched
                    # Type, Ticket Number, Status, Last Update, Age (Days) are new columns from enrich_data
                    breach_cols_normalized = ['case id', 'current user id', 'case start date',
                                              'Type', 'Ticket Number', 'Status', 'Last Update', 'Age (Days)']
                    # Select only those that exist in breach_display (which has normalized columns at this stage before display mapping)
                    breach_display_cols = [col for col in breach_cols_normalized if col in breach_display.columns]
                    
                    if not breach_display.empty:
                        st.dataframe(breach_display[breach_display_cols], hide_index=True)
                    else:
                        st.info("No breached cases match the selected filters.")
                        
                else:
                    st.info("No SLA breaches found in the current dataset.")
            else:
                st.info("SLA breach information not available. Please ensure your SR/Incident status files contain 'Breach Passed' column.")
    
    #
    # TODAY'S SR/INCIDENTS TAB
    #
    elif selected == "Today's SR/Incidents":
        st.title("📅 Today's New SR/Incidents")
        
        # Get today's cases
        today = datetime.now().date()
        
        # Filter for cases with notes created today
        if 'Created Today' in df_enriched.columns:
            today_cases = df_enriched[df_enriched['Created Today'] == True].copy()
        else:
            # Fallback: filter by Last Note Date
            today_cases = df_enriched[df_enriched['Last Note Date'].dt.date == today].copy() if 'Last Note Date' in df_enriched.columns else pd.DataFrame()
        
        # Further filter for SR/Incident cases only
        today_sr_incidents = today_cases[today_cases['Triage Status'] == 'Pending SR/Incident'].copy()
        
        # Display summary
        st.subheader("📊 Today's Summary")
        
        summary_today_col1, summary_today_col2, summary_today_col3 = st.columns(3)
        
        with summary_today_col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            total_today = len(today_sr_incidents)
            st.markdown(f'<p class="metric-value">{total_today}</p>', unsafe_allow_html=True)
            st.markdown('<p class="metric-label">Total New SR/Incidents</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with summary_today_col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            if 'Type' in today_sr_incidents.columns:
                sr_today = len(today_sr_incidents[today_sr_incidents['Type'] == 'SR'])
                st.markdown(f'<p class="metric-value">{sr_today}</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New SRs Today</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New SRs Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with summary_today_col3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            if 'Type' in today_sr_incidents.columns:
                incident_today = len(today_sr_incidents[today_sr_incidents['Type'] == 'Incident'])
                st.markdown(f'<p class="metric-value">{incident_today}</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New Incidents Today</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New Incidents Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Breakdown by user
        if not today_sr_incidents.empty: # today_sr_incidents has normalized columns from main_df
            st.subheader("👥 Breakdown by User")
            
            # Use normalized column names for groupby and aggregation
            user_breakdown = today_sr_incidents.groupby('current user id').agg({
                'case id': 'count', # Normalized
                'Type': lambda x: (x == 'SR').sum(), # 'Type' is a new column
                'Ticket Number': lambda x: (today_sr_incidents.loc[x.index, 'Type'] == 'Incident').sum() # 'Ticket Number' is new
            }).rename(columns={
                'case id': 'Total', # Original key was 'case id'
                'Type': 'SRs',
                'Ticket Number': 'Incidents'
            })
            
            user_breakdown = user_breakdown.reset_index() # 'current user id' becomes a column
            
            # Add total row, ensure 'current user id' is used for the column name
            total_row = pd.DataFrame({
                'current user id': ['TOTAL'], # Normalized column name
                'Total': [user_breakdown['Total'].sum()],
                'SRs': [user_breakdown['SRs'].sum()],
                'Incidents': [user_breakdown['Incidents'].sum()]
            })
            # Before concat, ensure columns match, especially 'current user id'
            if 'Current User Id' in user_breakdown.columns and 'current user id' not in user_breakdown.columns:
                 user_breakdown.rename(columns={'Current User Id': 'current user id'}, inplace=True)

            user_breakdown_display = pd.concat([user_breakdown, total_row], ignore_index=True)
            
            st.dataframe(
                user_breakdown_display.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(user_breakdown_display)-1 else '' for _ in x],
                    axis=1
                )
            )
            
            # Filter options for today's data
            st.subheader("🔍 Filter Today's Data")
            
            today_col1, today_col2 = st.columns(2)
            
            with today_col1: # Use normalized name for unique list
                today_user_filter = st.selectbox(
                    "Filter by User (Today)",
                    ["All"] + (today_sr_incidents['current user id'].unique().tolist() if 'current user id' in today_sr_incidents else []),
                    key="today_user"
                )
            
            with today_col2:
                today_type_filter = st.selectbox(
                    "Filter by Type (Today)", # 'Type' is new column
                    ["All", "SR", "Incident"],
                    key="today_type"
                )
            
            # Apply today's filters
            today_display = today_sr_incidents.copy()
            
            if today_user_filter != "All" and 'current user id' in today_display.columns:
                today_display = today_display[today_display["current user id"] == today_user_filter]
            
            if today_type_filter != "All" and 'Type' in today_display.columns: # 'Type' is new column
                today_display = today_display[today_display["Type"] == today_type_filter]
            
            # Display today's results
            st.subheader("📋 Today's Details")
            
            results_today_col1, results_today_col2 = st.columns([3, 1])
            
            with results_today_col1:
                st.markdown(f"**Filtered Records:** {today_display.shape[0]}")
            
            with results_today_col2:
                if not today_display.empty:
                    excel_today_data = generate_excel_download(today_display) # Will be mapped to original names later
                    st.download_button(
                        label="📥 Download Today's Data",
                        data=excel_today_data,
                        file_name=f"todays_sr_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Today's data table: define with normalized names for selection
            # Type, Ticket Number, Status, Last Update are new/derived
            today_cols_normalized = ['case id', 'current user id', 'last note date',
                                     'Type', 'Ticket Number']
            if 'Status' in today_display.columns: # Status is new
                today_cols_normalized.extend(['Status', 'Last Update']) # Last Update is new
            
            today_display_cols = [col for col in today_cols_normalized if col in today_display.columns]
            
            if not today_display.empty:
                st.dataframe(today_display[today_display_cols], hide_index=True) # Will be mapped later
            else:
                st.info("No records match the selected filters for today.")
                
        else:
            st.info("No new SR/Incidents found for today.")
            
            # Show all today's cases (not just SR/Incidents)
            # today_cases has normalized columns
            if not today_cases.empty:
                st.subheader("📝 All Today's Cases")
                st.markdown(f"**Total cases with notes today:** {len(today_cases)}")
                
                # Define with normalized names
                all_today_cols_normalized = ['case id', 'current user id', 'last note date', 'Triage Status']
                # 'Triage Status' is a new column
                all_today_display_cols = [col for col in all_today_cols_normalized if col in today_cases.columns]
                
                st.dataframe(today_cases[all_today_display_cols], hide_index=True) # Will be mapped later
                
                # Download button for all today's cases
                excel_all_today_data = generate_excel_download(today_cases)
                st.download_button(
                    label="📥 Download All Today's Cases",
                    data=excel_all_today_data,
                    file_name=f"all_todays_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No cases found with notes created today.")

    elif selected == "Incident Overview":
        st.title("📋 Incident Overview")

        SELECT_ALL_BASE_STRING = "[Select All %s]"

        if 'incident_overview_df' not in st.session_state or st.session_state.incident_overview_df is None or st.session_state.incident_overview_df.empty:
            st.warning(
                "The 'Incident Report Excel' has not been uploaded or is missing the required columns. " # Simplified message
                "Please upload the correct file via the sidebar to view the Incident Overview."
            )
        else:
            overview_df = st.session_state.incident_overview_df.copy() # Work with a copy (already has normalized cols like 'creator', 'team', 'priority', 'status')

            st.subheader("Filter Incidents")
            # Create 4 columns for filters to include Status
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Ensure 'creator' column (normalized) exists before trying to access it
                # The column 'creator' was made during the creation of incident_overview_df
                if 'creator' in overview_df.columns:
                    unique_creators = sorted(overview_df['creator'].dropna().unique())
                else:
                    unique_creators = []

                SELECT_ALL_CREATORS_OPTION = SELECT_ALL_BASE_STRING % "Creators"

                if 'incident_creator_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_creators = list(unique_creators) # Default to all selected for filtering
                    if unique_creators: # If there are actual creators
                        st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                    else: # No creators
                        st.session_state.incident_creator_widget_selection_controlled = []

                options_for_creator_widget = [SELECT_ALL_CREATORS_OPTION] + unique_creators
                raw_creator_widget_selection = st.multiselect(
                    "Filter by Creator",
                    options=options_for_creator_widget,
                    default=st.session_state.incident_creator_widget_selection_controlled,
                    key="multi_select_incident_creator"
                )

                prev_widget_display_state = list(st.session_state.incident_creator_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_CREATORS_OPTION in raw_creator_widget_selection
                currently_selected_actual_items = [c for c in raw_creator_widget_selection if c != SELECT_ALL_CREATORS_OPTION]

                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_CREATORS_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_CREATORS_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

                if user_clicked_select_all:
                    st.session_state.selected_creators = list(unique_creators)
                    st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                elif user_clicked_unselect_all:
                    st.session_state.selected_creators = []
                    st.session_state.incident_creator_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_creators):
                            st.session_state.selected_creators = list(currently_selected_actual_items)
                            st.session_state.incident_creator_widget_selection_controlled = list(currently_selected_actual_items)
                        else:
                            st.session_state.selected_creators = list(unique_creators)
                            st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                    else:
                        st.session_state.selected_creators = list(currently_selected_actual_items)
                        if unique_creators and set(currently_selected_actual_items) == set(unique_creators):
                            st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                        else:
                            st.session_state.incident_creator_widget_selection_controlled = list(currently_selected_actual_items)

            with col2: # overview_df already has normalized 'team' column if it exists
                if 'team' in overview_df.columns:
                    unique_teams = sorted(overview_df['team'].dropna().unique())
                else:
                    unique_teams = []

                SELECT_ALL_TEAMS_OPTION = SELECT_ALL_BASE_STRING % "Teams"

                # Define the desired default teams
                default_teams_to_select = ["GPSSA App Team L1", "GPSSA App Team L3"]

                if 'incident_team_widget_selection_controlled' not in st.session_state:
                    # Filter desired default teams to only those present in unique_teams
                    actual_default_teams = [team for team in default_teams_to_select if team in unique_teams]

                    if actual_default_teams:
                        st.session_state.selected_teams = list(actual_default_teams)
                        # Check if all unique_teams are selected by the new default
                        if unique_teams and set(actual_default_teams) == set(unique_teams):
                            st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                        else:
                            st.session_state.incident_team_widget_selection_controlled = list(actual_default_teams)
                    elif unique_teams: # If desired defaults are not present, but other teams are, select all (original fallback)
                        st.session_state.selected_teams = list(unique_teams)
                        st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                    else: # No teams in data, or desired defaults not present and no other teams
                        st.session_state.selected_teams = []
                        st.session_state.incident_team_widget_selection_controlled = []

                options_for_team_widget = [SELECT_ALL_TEAMS_OPTION] + unique_teams
                # The default for the multiselect widget is now correctly initialized in session state
                raw_team_widget_selection = st.multiselect(
                    "Filter by Team",
                    options=options_for_team_widget,
                    default=st.session_state.incident_team_widget_selection_controlled, # This uses the initialized value
                    key="multi_select_incident_team"
                )

                prev_widget_display_state = list(st.session_state.incident_team_widget_selection_controlled) # Used for "Select All" logic
                current_select_all_option_selected = SELECT_ALL_TEAMS_OPTION in raw_team_widget_selection
                currently_selected_actual_items = [t for t in raw_team_widget_selection if t != SELECT_ALL_TEAMS_OPTION]

                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_TEAMS_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_TEAMS_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

                if user_clicked_select_all:
                    st.session_state.selected_teams = list(unique_teams)
                    st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                elif user_clicked_unselect_all:
                    st.session_state.selected_teams = []
                    st.session_state.incident_team_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_teams):
                            st.session_state.selected_teams = list(currently_selected_actual_items)
                            st.session_state.incident_team_widget_selection_controlled = list(currently_selected_actual_items)
                        else:
                            st.session_state.selected_teams = list(unique_teams)
                            st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                    else:
                        st.session_state.selected_teams = list(currently_selected_actual_items)
                        if unique_teams and set(currently_selected_actual_items) == set(unique_teams):
                            st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                        else:
                            st.session_state.incident_team_widget_selection_controlled = list(currently_selected_actual_items)

            with col3: # overview_df already has normalized 'priority' column if it exists
                if 'priority' in overview_df.columns:
                    unique_priorities = sorted(overview_df['priority'].dropna().unique())
                else:
                    unique_priorities = []

                SELECT_ALL_PRIORITIES_OPTION = SELECT_ALL_BASE_STRING % "Priorities"

                if 'incident_priority_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_priorities = list(unique_priorities) # Default to all selected for filtering
                    if unique_priorities: # If there are actual priorities
                        st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                    else: # No priorities
                        st.session_state.incident_priority_widget_selection_controlled = []

                options_for_priority_widget = [SELECT_ALL_PRIORITIES_OPTION] + unique_priorities
                raw_priority_widget_selection = st.multiselect(
                    "Filter by Priority",
                    options=options_for_priority_widget,
                    default=st.session_state.incident_priority_widget_selection_controlled,
                    key="multi_select_incident_priority"
                )

                prev_widget_display_state = list(st.session_state.incident_priority_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_PRIORITIES_OPTION in raw_priority_widget_selection
                currently_selected_actual_items = [p for p in raw_priority_widget_selection if p != SELECT_ALL_PRIORITIES_OPTION]

                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_PRIORITIES_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_PRIORITIES_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

                if user_clicked_select_all:
                    st.session_state.selected_priorities = list(unique_priorities)
                    st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                elif user_clicked_unselect_all:
                    st.session_state.selected_priorities = []
                    st.session_state.incident_priority_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_priorities):
                            st.session_state.selected_priorities = list(currently_selected_actual_items)
                            st.session_state.incident_priority_widget_selection_controlled = list(currently_selected_actual_items)
                        else:
                            st.session_state.selected_priorities = list(unique_priorities)
                            st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                    else:
                        st.session_state.selected_priorities = list(currently_selected_actual_items)
                        if unique_priorities and set(currently_selected_actual_items) == set(unique_priorities):
                            st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                        else:
                            st.session_state.incident_priority_widget_selection_controlled = list(currently_selected_actual_items)

            with col4: # New column for Status filter; overview_df has 'status' (normalized)
                if 'status' in overview_df.columns:
                    unique_statuses = sorted(overview_df['status'].dropna().unique())
                    # Exclude 'Closed', 'Resolved', 'Cancelled' by default (comparison should be case-insensitive or use normalized values)
                    # The unique_statuses are already normalized (lowercase), so direct comparison is fine.
                    closed_like_statuses = {'closed', 'cancelled'} # Use lowercase for comparison
                    default_selected_statuses = [s for s in unique_statuses if s not in closed_like_statuses]
                else:
                    unique_statuses = []
                    default_selected_statuses = []

                SELECT_ALL_STATUSES_OPTION = SELECT_ALL_BASE_STRING % "Statuses"

                if 'incident_status_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_statuses = list(default_selected_statuses) # Actual statuses for filtering

                    if not default_selected_statuses and unique_statuses: # If default_selected_statuses is empty and there are statuses, select all
                        st.session_state.selected_statuses = list(unique_statuses)
                        st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif unique_statuses and set(default_selected_statuses) == set(unique_statuses): # If default_selected_statuses happens to be all unique_statuses
                        st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif not unique_statuses: # If there are no statuses at all
                        st.session_state.selected_statuses = []
                        st.session_state.incident_status_widget_selection_controlled = []
                    else: # Default statuses are a specific subset
                        st.session_state.incident_status_widget_selection_controlled = list(default_selected_statuses)

                options_for_status_widget = [SELECT_ALL_STATUSES_OPTION] + unique_statuses
                raw_status_widget_selection = st.multiselect(
                    "Filter by Status",
                    options=options_for_status_widget,
                    default=st.session_state.incident_status_widget_selection_controlled,
                    key="multi_select_incident_status"
                )

                prev_widget_display_state = list(st.session_state.incident_status_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_STATUSES_OPTION in raw_status_widget_selection
                currently_selected_actual_items = [s for s in raw_status_widget_selection if s != SELECT_ALL_STATUSES_OPTION]

                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_STATUSES_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_STATUSES_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

                if user_clicked_select_all:
                    st.session_state.selected_statuses = list(unique_statuses)
                    st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                elif user_clicked_unselect_all:
                    st.session_state.selected_statuses = []
                    st.session_state.incident_status_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_statuses):
                            st.session_state.selected_statuses = list(currently_selected_actual_items)
                            st.session_state.incident_status_widget_selection_controlled = list(currently_selected_actual_items)
                        else:
                            st.session_state.selected_statuses = list(unique_statuses)
                            st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    else:
                        st.session_state.selected_statuses = list(currently_selected_actual_items)
                        if unique_statuses and set(currently_selected_actual_items) == set(unique_statuses):
                            st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                        else:
                            st.session_state.incident_status_widget_selection_controlled = list(currently_selected_actual_items)

            # Apply filters
            filtered_overview_df = overview_df # This df has normalized columns like 'creator', 'team', 'priority', 'status'

            if st.session_state.get('selected_creators') and 'creator' in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df['creator'].isin(st.session_state.selected_creators)]
            if st.session_state.get('selected_teams') and 'team' in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df['team'].isin(st.session_state.selected_teams)]
            if st.session_state.get('selected_priorities') and 'priority' in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df['priority'].isin(st.session_state.selected_priorities)]
            if st.session_state.get('selected_statuses') and 'status' in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df['status'].isin(st.session_state.selected_statuses)]

            # Calculate team and status totals
            # calculate_team_status_summary will expect normalized 'team' and 'status' columns
            team_status_summary_df = calculate_team_status_summary(filtered_overview_df)

                    # --- Pie Chart for Closed Incidents ---
            st.markdown("---") # Visual separator before the pie chart
            # Use normalized 'status' column. Compare with normalized 'closed'.
            if 'status' in overview_df.columns:
                closed_count = overview_df[overview_df['status'] == 'closed'].shape[0]
                total_incidents = overview_df.shape[0]
                other_count = total_incidents - closed_count

                if total_incidents > 0: # Avoid division by zero if no incidents
                    chart_data = pd.DataFrame({
                        'Status Category': ['Closed', 'Open/Other'],
                        'Count': [closed_count, other_count]
                    })
                    fig_status_pie = px.pie(chart_data, names='Status Category', values='Count', title='Percentage of Closed Incidents')
                    st.plotly_chart(fig_status_pie, use_container_width=True)
                else:
                    st.info("No incident data available to display the status pie chart.")
            else:
                st.warning("Cannot display Percentage of Closed Incidents: 'Status' column missing from source data.")
        # --- Team Assignment Distribution ---
        st.markdown("---") # Visual separator
        st.subheader("Team Assignment Distribution")
        if not filtered_overview_df.empty: # filtered_overview_df has normalized 'team'
            if 'team' in filtered_overview_df.columns:
                team_distribution_data = filtered_overview_df['team'].value_counts()
                
                if not team_distribution_data.empty:
                    fig_team_dist = px.pie(
                        team_distribution_data,
                        names=team_distribution_data.index,
                        values=team_distribution_data.values,
                        title="Distribution of Incidents by Team"
                    )
                    fig_team_dist.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_team_dist, use_container_width=True)
                else:
                    st.info("No team assignment data to display based on current filters.")
            else:
                st.warning("Cannot display Team Assignment Distribution: 'Team' column not found in the data.")
        else:
            st.info("No data available to display for Team Assignment Distribution based on current filters.")
        # --- Incidents by Team and Status Table ---
        st.markdown("---") # Visual separator
        st.subheader("Incidents by Team and Status")
        # Check if 'team' or 'status' column was missing when team_status_summary_df was created.
        # These are normalized names in filtered_overview_df.
        if 'team' not in filtered_overview_df.columns or 'status' not in filtered_overview_df.columns:
            st.warning("The 'Team' or 'Status' column (normalized) is missing in the uploaded incident data, so the 'Incidents by Team and Status' table cannot be generated.")
        elif not team_status_summary_df.empty:
            st.dataframe(team_status_summary_df, use_container_width=True, hide_index=True) # This df is generated by util function, names are as defined there
        else:
            # This case means columns existed, but the dataframe is empty (e.g., due to filters or no matching data)
            st.info("No incident data to display in the 'Incidents by Team and Status' table based on current filters or data availability.")
         
        # --- New Filtered Incident Details Table ---
        st.markdown("---") # Separator before the new table
        st.subheader("Filtered Incident Details")

        if not filtered_overview_df.empty: # filtered_overview_df has normalized columns
            # Define default columns for the table using NORMALIZED names
            default_table_columns_normalized = ["incident", "creator", "team", "priority", "status"]

            # Filter default columns to only include those present in the DataFrame
            available_default_columns = [col for col in default_table_columns_normalized if col in filtered_overview_df.columns]

            # Add column selector multiselect
            if not filtered_overview_df.empty:
                all_available_columns = filtered_overview_df.columns.tolist() # These are normalized
                SELECT_ALL_COLS_INCIDENT_OPTION = "[Select All Columns]"

                # available_default_columns (normalized) is defined above this block
                if 'incident_tab_column_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_table_columns = list(available_default_columns) # Actual columns for table

                    if not available_default_columns and all_available_columns: # If no defaults specified but columns exist, select all
                        st.session_state.selected_table_columns = list(all_available_columns)
                        st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                    elif all_available_columns and set(available_default_columns) == set(all_available_columns): # If defaults are all columns
                        st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                    elif not all_available_columns: # No columns available at all
                        st.session_state.selected_table_columns = []
                        st.session_state.incident_tab_column_widget_selection_controlled = []
                    else: # Defaults are a specific subset
                        st.session_state.incident_tab_column_widget_selection_controlled = list(available_default_columns)

                options_for_incident_cols_widget = [SELECT_ALL_COLS_INCIDENT_OPTION] + all_available_columns
                raw_incident_cols_widget_selection = st.multiselect(
                    "Select columns for table:",
                    options=options_for_incident_cols_widget,
                    default=st.session_state.incident_tab_column_widget_selection_controlled,
                    key="multi_select_incident_overview_columns"
                )

                prev_widget_display_state = list(st.session_state.incident_tab_column_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_COLS_INCIDENT_OPTION in raw_incident_cols_widget_selection
                currently_selected_actual_items = [c for c in raw_incident_cols_widget_selection if c != SELECT_ALL_COLS_INCIDENT_OPTION]

                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_COLS_INCIDENT_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_COLS_INCIDENT_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)

                if user_clicked_select_all:
                    st.session_state.selected_table_columns = list(all_available_columns)
                    st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                elif user_clicked_unselect_all:
                    st.session_state.selected_table_columns = []
                    st.session_state.incident_tab_column_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(all_available_columns):
                            st.session_state.selected_table_columns = list(currently_selected_actual_items)
                            st.session_state.incident_tab_column_widget_selection_controlled = list(currently_selected_actual_items)
                        else:
                            st.session_state.selected_table_columns = list(all_available_columns)
                            st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                    else:
                        st.session_state.selected_table_columns = list(currently_selected_actual_items)
                        if all_available_columns and set(currently_selected_actual_items) == set(all_available_columns):
                            st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                        else:
                            st.session_state.incident_tab_column_widget_selection_controlled = list(currently_selected_actual_items)

                current_cols_to_display_incident_tab = st.session_state.get('selected_table_columns', [])

                if not current_cols_to_display_incident_tab: # Check based on the processed selection
                    st.info("Please select at least one column to display the table.")
                else:
                    # Check if essential columns (even if not selected) are missing from the original data source for context
                    # Use normalized names for check
                    essential_source_cols_normalized = ["incident", "status"]
                    missing_essential_source_cols = [col for col in essential_source_cols_normalized if col not in filtered_overview_df.columns]
                    if missing_essential_source_cols:
                        st.caption(f"Warning: Source data is missing essential columns for full detail: {', '.join(missing_essential_source_cols)}.")

                    st.write(f"Displaying {len(filtered_overview_df)} records in table with selected columns.")
                    st.dataframe( # This dataframe will be mapped to original names later
                        filtered_overview_df[current_cols_to_display_incident_tab],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                pass

        else:
            st.info("No data to display in the 'Filtered Incident Details' table based on current filters.")
   
        # --- High-Priority Incidents Table (remains, now affected by Status filter too) ---
        st.markdown("---")
        st.subheader("High-Priority Incidents (P1 & P2)")
        if not filtered_overview_df.empty: # filtered_overview_df has normalized columns
            # Define with normalized names. 'Status' is already direct.
            high_priority_table_cols_normalized = ["incident", "creator", "team", "priority"]
            if 'status' in filtered_overview_df.columns: # Check normalized 'status'
                high_priority_table_cols_normalized.append("status")

            # Check if all *intended* (normalized) columns for this table are present
            missing_cols_for_high_priority_table = [col for col in ["incident", "creator", "team", "priority"] if col not in filtered_overview_df.columns]

            if not missing_cols_for_high_priority_table:
                high_priority_values = ["1", "2"] # Priority values are strings
                
                # Use normalized 'priority' for filtering
                high_priority_incidents_df = filtered_overview_df[
                    filtered_overview_df['priority'].astype(str).isin(high_priority_values)
                ]
                
                if not high_priority_incidents_df.empty:
                    st.dataframe( # This dataframe will be mapped to original names later
                        high_priority_incidents_df[[col for col in high_priority_table_cols_normalized if col in high_priority_incidents_df.columns]],
                        use_container_width=True,
                        hide_index=True 
                    )
                else:
                    st.info("No high-priority incidents (P1 or P2) found based on current filters.")
            else:
                st.warning(f"Cannot display High-Priority Incidents table: Missing essential columns: {', '.join(missing_cols_for_high_priority_table)}.")
        else:
            st.info("No data available to display for High-Priority Incidents based on current filters.")

    #
    # SR OVERVIEW TAB
    #
    elif selected == "SR Overview":
        st.title("📊 Service Request (SR) Overview")
        # Import the new function
        from utils import calculate_srs_created_and_closed_per_week


        if 'sr_df' not in st.session_state or st.session_state.sr_df is None or st.session_state.sr_df.empty:
            st.warning(
                "The 'SR Status Excel' has not been uploaded or is empty. "
                "Please upload the SR status file via the sidebar to view the SR Overview."
            )
        else:
            sr_overview_df = st.session_state.sr_df.copy() # sr_overview_df has normalized columns
            st.markdown(f"**Total SRs Loaded:** {len(sr_overview_df)}")

            # Check for required columns for the new chart using NORMALIZED names
            required_cols_for_chart_normalized = ['created on', 'lastmoddatetime', 'status']
            missing_cols = [col for col in required_cols_for_chart_normalized if col not in sr_overview_df.columns]

            if missing_cols:
                # Displaying original-like names in error for user readability
                user_friendly_missing_cols = [st.session_state.sr_df_original_cols[sr_overview_df.columns.get_loc(col)] if col in sr_overview_df.columns and st.session_state.sr_df_original_cols else col for col in missing_cols]
                st.error(f"The SR data must contain the following columns to generate the weekly overview: {', '.join(user_friendly_missing_cols)}.")
            else:
                # Use the new function; it will expect normalized columns
                srs_weekly_combined_df = calculate_srs_created_and_closed_per_week(sr_overview_df)

                if srs_weekly_combined_df.empty:
                    st.info("No valid data found to generate the weekly SRs created/closed chart.")
                else:
                    # Filter data for created SRs
                    created_df = srs_weekly_combined_df[srs_weekly_combined_df['Category'] == 'Created'].copy()
                    # Filter data for closed SRs
                    closed_df = srs_weekly_combined_df[srs_weekly_combined_df['Category'] == 'Closed'].copy()
                    
                    chart_x_axis = 'WeekDisplay'

                    if not created_df.empty:
                        st.subheader("Service Requests Created Per Week")
                        fig_created = px.bar(
                            created_df,
                            x=chart_x_axis,
                            y='Count',
                            title="Service Requests Created Per Week",
                            labels={'Count': 'Number of SRs Created', chart_x_axis: 'Week Period'},
                            color_discrete_sequence=px.colors.qualitative.Plotly, # Optional: for a consistent color
                            text='Count' # Add text to display on bars
                        )
                        fig_created.update_traces(texttemplate='%{text}', textposition='outside') # Show text outside bars
                        fig_created.update_layout(xaxis_title='Week Period', yaxis_title="Number of SRs Created")
                        st.plotly_chart(fig_created, use_container_width=True)
                    else:
                        st.info("No data available for 'SRs Created Per Week' chart.")

                    if not closed_df.empty:
                        st.subheader("Service Requests Closed Per Week")
                        fig_closed = px.bar(
                            closed_df,
                            x=chart_x_axis,
                            y='Count',
                            title="Service Requests Closed Per Week: SR Status (Closed,Completed, Cancelled, Approval rejected, Rejected by ps)",
                            labels={'Count': 'Number of SRs Closed', chart_x_axis: 'Week Period'},
                            color_discrete_sequence=px.colors.qualitative.Plotly, # Optional: pick a different color if desired e.g., px.colors.qualitative.Plotly[1:]
                            text='Count' # Add text to display on bars
                        )
                        fig_closed.update_traces(texttemplate='%{text}', textposition='outside') # Show text outside bars
                        fig_closed.update_layout(xaxis_title='Week Period', yaxis_title="Number of SRs Closed")
                        st.plotly_chart(fig_closed, use_container_width=True)
                    else:
                        st.info("No data available for 'SRs Closed Per Week' chart.")

                st.markdown("---")
                st.subheader("Filterable SR Data")

                # Prepare data for table display and its filters
                table_display_df = sr_overview_df.copy() # This is the raw SR data for the table
                week_map_for_filter = {}
                week_options_for_multiselect = []

                # Populate week filter options from the combined data used for the chart
                if 'srs_weekly_combined_df' in locals() and not srs_weekly_combined_df.empty:
                    if 'WeekDisplay' in srs_weekly_combined_df.columns and 'Year-Week' in srs_weekly_combined_df.columns:
                        unique_week_options_df = srs_weekly_combined_df[['Year-Week', 'WeekDisplay']].drop_duplicates().sort_values(by='Year-Week')
                        week_options_for_multiselect = unique_week_options_df['WeekDisplay'].tolist()
                        for _, row in unique_week_options_df.iterrows():
                            week_map_for_filter[row['WeekDisplay']] = row['Year-Week']
                
                # The table_display_df needs 'created on' (normalized) and 'Year-Week' for filtering logic below
                if 'created on' in table_display_df.columns:
                    table_display_df['created on'] = pd.to_datetime(table_display_df['created on'], errors='coerce')
                    # Keep rows with valid 'created on' for the table, as filtering is based on this
                    table_display_df.dropna(subset=['created on'], inplace=True)
                    if not table_display_df.empty:
                         table_display_df['Year-Week'] = table_display_df['created on'].dt.strftime('%G-W%V') # New column
                else:
                    # If 'created on' is not in table_display_df, week filtering on it won't work.
                    if 'Year-Week' in table_display_df.columns:
                        pass

                col_filter1, col_filter2 = st.columns(2)

                with col_filter1:
                    selected_week_displays = st.multiselect(
                        "Filter by Week Period:",
                        options=week_options_for_multiselect,
                        default=[]
                    )

                with col_filter2:
                    # Use normalized 'created on'
                    min_date_val = table_display_df['created on'].min().date() if not table_display_df.empty and 'created on' in table_display_df.columns and not table_display_df['created on'].dropna().empty else None
                    max_date_val = table_display_df['created on'].max().date() if not table_display_df.empty and 'created on' in table_display_df.columns and not table_display_df['created on'].dropna().empty else None
                    selected_day = st.date_input("Filter by Specific Day (Created On):", value=None, min_value=min_date_val, max_value=max_date_val)

                # Apply filters to table_display_df using normalized 'created on'
                if selected_day and 'created on' in table_display_df.columns:
                    table_display_df = table_display_df[table_display_df['created on'].dt.date == selected_day]
                elif selected_week_displays and 'Year-Week' in table_display_df.columns: # Year-Week is new, direct name
                    selected_year_weeks_short = [week_map_for_filter[wd] for wd in selected_week_displays if wd in week_map_for_filter]
                    if selected_year_weeks_short:
                         table_display_df = table_display_df[table_display_df['Year-Week'].isin(selected_year_weeks_short)]

                # Display total row count using table_display_df
                st.markdown(f"**Total Displayed SRs:** {len(table_display_df)}")

                # Column selector using table_display_df
                if not table_display_df.empty:
                    all_columns = table_display_df.columns.tolist()
                    # Remove 'Year-Week' from selectable columns if it was added for filtering only
                    if 'Year-Week' in all_columns: # Year-Week is new, direct name
                        all_columns.remove('Year-Week')

                    # Use normalized names for default_cols that come from original file
                    default_cols_normalized = ['service request', 'status', 'created on']
                    sanitized_default_cols = [col for col in default_cols_normalized if col in all_columns]

                    if 'filterable_sr_data_cols_multiselect' not in st.session_state:
                        st.session_state.filterable_sr_data_cols_multiselect = sanitized_default_cols

                    selected_columns = st.multiselect(
                        "Select columns to display for Filterable SR Data:",
                        options=all_columns, # Offer all columns from the filtered DF
                        default=st.session_state.filterable_sr_data_cols_multiselect,
                        key="multiselect_filterable_sr_data"
                    )
                    st.session_state.filterable_sr_data_cols_multiselect = selected_columns


                    if selected_columns:
                        st.dataframe(table_display_df[selected_columns], hide_index=True)
                    else:
                        # Show all (minus internal Year-Week) if no columns are selected but data exists
                        st.dataframe(table_display_df[[col for col in all_columns if col != 'Year-Week']] if 'Year-Week' in all_columns else table_display_df, hide_index=True)
                else:
                    st.info("No SR data to display based on current filters for Filterable SR Data.")

                st.markdown("---") # Separator before the new Closed SRs table

                # --- Closed SRs Table ---
                st.subheader("Closed Service Requests")

                # Essential columns for this section, using normalized names
                essential_cols_closed_sr_normalized = ['status', 'lastmoddatetime']
                missing_essential_cols = [col for col in essential_cols_closed_sr_normalized if col not in sr_overview_df.columns]

                if missing_essential_cols:
                    user_friendly_missing_cols = [st.session_state.sr_df_original_cols[sr_overview_df.columns.get_loc(col)] if col in sr_overview_df.columns and st.session_state.sr_df_original_cols else col for col in missing_essential_cols]
                    st.warning(f"The uploaded SR data is missing the following essential column(s) for the Closed SRs table: {', '.join(user_friendly_missing_cols)}. This table cannot be displayed.")
                else:
                    closed_sr_statuses = ["closed", "completed", "cancelled", "approval rejected", "rejected by ps"] # these are already lowercase
                    # Filter SRs that have one of the closed statuses, using normalized 'status'
                    closed_srs_df = sr_overview_df[
                        sr_overview_df['status'].astype(str).str.lower().str.strip().isin(closed_sr_statuses)
                    ].copy()

                    # Convert normalized 'lastmoddatetime' to datetime and generate 'Closure-Year-Week'
                    closed_srs_df['lastmoddatetime'] = pd.to_datetime(closed_srs_df['lastmoddatetime'], errors='coerce', dayfirst=True, infer_datetime_format=True)
                    closed_srs_df.dropna(subset=['lastmoddatetime'], inplace=True)

                    if not closed_srs_df.empty:
                        closed_srs_df['Closure-Year-Week'] = closed_srs_df['lastmoddatetime'].dt.strftime('%G-W%V') # New column
                    else:
                        # Ensure the column exists even if empty, for consistency in later steps
                        closed_srs_df['Closure-Year-Week'] = pd.Series(dtype='str')


                    # Prepare week filter options based on LastModDateTime of closed SRs
                    # This is different from the main week_options_for_multiselect which is based on Created On of all SRs
                    closed_sr_week_map_for_filter = {}
                    closed_sr_week_options_for_multiselect = []
                    if not closed_srs_df.empty and 'Closure-Year-Week' in closed_srs_df.columns:
                        unique_closed_week_options_df = closed_srs_df[['Closure-Year-Week']].copy()
                        unique_closed_week_options_df.dropna(subset=['Closure-Year-Week'], inplace=True)
                        # Apply the _get_week_display_str helper to the 'Closure-Year-Week'
                        # Ensure _get_week_display_str is available or define it if it's moved/not imported
                        # For now, assuming _get_week_display_str is accessible
                        unique_closed_week_options_df['WeekDisplay'] = unique_closed_week_options_df['Closure-Year-Week'].apply(_get_week_display_str)
                        unique_closed_week_options_df = unique_closed_week_options_df[['Closure-Year-Week', 'WeekDisplay']].drop_duplicates().sort_values(by='Closure-Year-Week')

                        closed_sr_week_options_for_multiselect = unique_closed_week_options_df['WeekDisplay'].tolist()
                        for _, row in unique_closed_week_options_df.iterrows():
                            closed_sr_week_map_for_filter[row['WeekDisplay']] = row['Closure-Year-Week']


                    col_filter_closed_sr1, col_filter_closed_sr2 = st.columns(2)

                    with col_filter_closed_sr1:
                        selected_week_displays_closed = st.multiselect(
                            "Filter Closed SRs by Closure Week Period:",
                            options=closed_sr_week_options_for_multiselect,
                            default=[],
                            key="closed_sr_closure_week_filter"
                        )

                    with col_filter_closed_sr2: # Use normalized 'lastmoddatetime'
                        min_date_val_closed = closed_srs_df['lastmoddatetime'].min().date() if not closed_srs_df.empty and not closed_srs_df['lastmoddatetime'].dropna().empty else None
                        max_date_val_closed = closed_srs_df['lastmoddatetime'].max().date() if not closed_srs_df.empty and not closed_srs_df['lastmoddatetime'].dropna().empty else None
                        selected_day_closed = st.date_input(
                            "Filter Closed SRs by Specific Closure Day:",
                            value=None,
                            min_value=min_date_val_closed,
                            max_value=max_date_val_closed,
                            key="closed_sr_closure_day_filter"
                        )

                    # Apply filters to closed_srs_df
                    filtered_closed_srs_df = closed_srs_df.copy()

                    if selected_day_closed and 'lastmoddatetime' in filtered_closed_srs_df.columns:
                        # Ensure LastModDateTime is date part for comparison
                        filtered_closed_srs_df = filtered_closed_srs_df[filtered_closed_srs_df['lastmoddatetime'].dt.date == selected_day_closed]
                    elif selected_week_displays_closed and 'Closure-Year-Week' in filtered_closed_srs_df.columns: # Closure-Year-Week is new
                        if closed_sr_week_map_for_filter: # Ensure map is not empty
                            selected_closure_year_weeks_short = [closed_sr_week_map_for_filter[wd] for wd in selected_week_displays_closed if wd in closed_sr_week_map_for_filter]
                            if selected_closure_year_weeks_short:
                                filtered_closed_srs_df = filtered_closed_srs_df[filtered_closed_srs_df['Closure-Year-Week'].isin(selected_closure_year_weeks_short)]

                    st.markdown(f"**Total Displayed Closed SRs (filtered by closure date):** {len(filtered_closed_srs_df)}")

                    if not filtered_closed_srs_df.empty: # This is line 2108 approx.
                        all_closed_columns = filtered_closed_srs_df.columns.tolist() # Line 2109 - Start of block to indent
                        # Remove internal helper columns from user selection options
                        # 'Closure-Year-Week' is the one specifically created for this table's filtering.
                        # 'Year-Week' might exist if it was in the original sr_overview_df from created_on processing.
                        internal_cols_to_remove = ['Closure-Year-Week', 'Year-Week']
                        for col_to_remove in internal_cols_to_remove: # These are new columns, direct names
                            if col_to_remove in all_closed_columns:
                                all_closed_columns.remove(col_to_remove)

                        # Use normalized names for default_closed_cols from original file
                        default_closed_cols_normalized = ['service request', 'status', 'created on', 'lastmoddatetime', 'resolution']
                        sanitized_default_closed_cols = [col for col in default_closed_cols_normalized if col in all_closed_columns]

                        if 'closed_sr_data_cols_multiselect' not in st.session_state:
                            st.session_state.closed_sr_data_cols_multiselect = sanitized_default_closed_cols

                        selected_closed_columns = st.multiselect(
                            "Select columns to display for Closed SRs:",
                            options=all_closed_columns,
                            default=st.session_state.closed_sr_data_cols_multiselect,
                            key="multiselect_closed_sr_data"
                        )
                        st.session_state.closed_sr_data_cols_multiselect = selected_closed_columns

                        if selected_closed_columns:
                            st.dataframe(filtered_closed_srs_df[selected_closed_columns], hide_index=True)
                        else:
                            # Show all available (minus internal Year-Week) if no columns selected but data exists
                            # Ensure we use the correct list of all_closed_columns (which has helpers removed)
                            st.dataframe(filtered_closed_srs_df[all_closed_columns] if all_closed_columns else filtered_closed_srs_df, hide_index=True)

                        # Download button for Closed SRs
                        # Ensure download uses the correct set of columns (selected or all available for display)
                        cols_for_download = selected_closed_columns if selected_closed_columns else all_closed_columns
                        excel_closed_sr_data = generate_excel_download(filtered_closed_srs_df[cols_for_download] if cols_for_download else filtered_closed_srs_df)
                        st.download_button(
                            label="📥 Download Closed SRs Data",
                            data=excel_closed_sr_data,
                            file_name=f"closed_srs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_closed_srs"
                        )
                    # This else corresponds to 'if not filtered_closed_srs_df.empty:'
                    else:
                        st.info("No Closed SR data to display based on current filters.")


st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.8em;">
    Intellipen SmartQ Test V3.6 | Developed by Ali Babiker | © June 2025
    </div>""",
    unsafe_allow_html=True
)