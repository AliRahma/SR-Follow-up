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
from utils import calculate_team_status_summary, calculate_srs_created_per_week, _get_week_display_str, normalize_column_name # Added normalize_column_name

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
if 'report_datetime' not in st.session_state:
    st.session_state.report_datetime = None

@st.cache_data
def load_data(file):
    if file is None:
        return None, None  # Return None for both DataFrame and datetime string
    
    parsed_datetime_str = None
    df = None

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
            return None, parsed_datetime_str # Return None for df if unsupported, but retain parsed_datetime_str if filename was parsable

        if df is not None:
            df.columns = [normalize_column_name(col) for col in df.columns]

        return df, parsed_datetime_str
            
    except Exception as e:
        st.error(f"Error loading file '{file.name}': {e}")
        return None, parsed_datetime_str # Return None for df, but parsed_datetime_str might have a value if filename parsing happened before exception

# Function to process main dataframe
def process_main_df(df):
    # Ensure date columns are in datetime format
    # Columns are already normalized by load_data
    case_start_date_col = normalize_column_name('Case Start Date')
    last_note_date_col = normalize_column_name('Last Note Date')
    current_user_id_col = normalize_column_name('Current User Id')

    date_columns = [case_start_date_col, last_note_date_col]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
    
    # Extract all unique users
    if current_user_id_col in df.columns:
        all_users = sorted(df[current_user_id_col].dropna().unique().tolist())
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
            df, parsed_dt = load_data(uploaded_file)
            if df is not None:
                st.session_state.main_df = process_main_df(df)
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
            sr_df, parsed_dt_sr = load_data(sr_status_file)
            if sr_df is not None:
                st.session_state.sr_df = sr_df
                st.success(f"SR status data loaded: {sr_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_sr:
                    st.session_state.report_datetime = parsed_dt_sr
            # else: df is None, error shown by load_data
    
    if incident_status_file:
        with st.spinner("Loading incident report data..."):
            incident_df, parsed_dt_incident = load_data(incident_status_file)
            if incident_df is not None:
                st.session_state.incident_df = incident_df
                st.success(f"Incident report data loaded: {incident_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_incident:
                    st.session_state.report_datetime = parsed_dt_incident

                # Process for Incident Overview tab
                overview_df = incident_df.copy() # incident_df has normalized cols
                customer_col_norm = normalize_column_name('Customer')
                creator_col_norm = normalize_column_name('Creator')
                if customer_col_norm in overview_df.columns:
                    overview_df.rename(columns={customer_col_norm: creator_col_norm}, inplace=True)
                st.session_state.incident_overview_df = overview_df
                st.success(f"Incident Overview data loaded: {len(overview_df)} records, {len(overview_df.columns)} columns.")
            else:
                st.session_state.incident_overview_df = None
    
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
        current_user_id_col = normalize_column_name('Current User Id')
        case_start_date_col = normalize_column_name('Case Start Date')

        all_users = df_main[current_user_id_col].dropna().unique().tolist() if current_user_id_col in df_main.columns else []
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
        
        if case_start_date_col in df_main.columns:
            min_date = df_main[case_start_date_col].min().date()
            max_date = df_main[case_start_date_col].max().date()
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
    current_user_id_col = normalize_column_name('Current User Id') # ensure it's defined in this scope
    case_start_date_col = normalize_column_name('Case Start Date') # ensure it's defined in this scope

    if st.session_state.selected_users and current_user_id_col in df_main.columns:
        df_filtered = df_main[df_main[current_user_id_col].isin(st.session_state.selected_users)].copy()
    else:
        df_filtered = df_main.copy()
    
    # Apply date filter if date range is selected
    if case_start_date_col in df_filtered.columns and 'date_range' in locals():
        start_date, end_date = date_range
        df_filtered = df_filtered[
            (df_filtered[case_start_date_col].dt.date >= start_date) &
            (df_filtered[case_start_date_col].dt.date <= end_date)
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
    def enrich_data(df):
        df_enriched = df.copy()

        # Define normalized column names (many will be used throughout this function)
        last_note_col = normalize_column_name('Last Note')
        triage_status_col = 'triage_status' # Derived, so can be defined directly
        ticket_number_col = normalize_column_name('Ticket Number') # This will be derived, but good to normalize the name
        type_col = 'type' # Derived
        case_start_date_col = normalize_column_name('Case Start Date')
        age_days_col = 'age_days' # Derived
        last_note_date_col = normalize_column_name('Last Note Date')
        created_today_col = 'created_today' # Derived
        status_col = normalize_column_name('Status') # Will be populated from SR/Incident files
        last_update_col = normalize_column_name('Last Update') # Will be populated
        breach_passed_col = normalize_column_name('Breach Passed') # Will be populated
        
        # Classify and extract ticket info
        if last_note_col in df_enriched.columns:
            # Ensure derived column names are also consistently named
            df_enriched[[triage_status_col, ticket_number_col, type_col]] = pd.DataFrame(
                df_enriched[last_note_col].apply(lambda x: pd.Series(classify_and_extract(x)))
            )
        else:
            df_enriched[triage_status_col] = "Error: Last Note missing"
            df_enriched[ticket_number_col] = None
            df_enriched[type_col] = None

        # Calculate case age
        if case_start_date_col in df_enriched.columns:
            df_enriched[age_days_col] = df_enriched[case_start_date_col].apply(calculate_age)
        else:
            df_enriched[age_days_col] = None

        # Determine if note was created today
        if last_note_date_col in df_enriched.columns:
            df_enriched[created_today_col] = df_enriched[last_note_date_col].apply(is_created_today)
        else:
            df_enriched[created_today_col] = False
        
        # Initialize Status, Last Update, and Breach Passed columns
        df_enriched[status_col] = None
        df_enriched[last_update_col] = None
        df_enriched[breach_passed_col] = None
        
        # Ensure 'Ticket Number' is numeric before any merges
        if ticket_number_col in df_enriched.columns: # Use normalized name
            df_enriched[ticket_number_col] = pd.to_numeric(df_enriched[ticket_number_col], errors='coerce')

        # Merge with SR status data if available
        # sr_df columns are already normalized at load time
        if hasattr(st.session_state, 'sr_df') and st.session_state.sr_df is not None:
            sr_df_copy = st.session_state.sr_df.copy()
            
            # sr_df_copy already has normalized column names
            sr_ticket_col_norm = normalize_column_name('Service Request')
            sr_status_col_norm = normalize_column_name('Status')
            sr_last_mod_col_norm = normalize_column_name('LastModDateTime')
            sr_breach_col_norm = normalize_column_name('Breach Passed')

            if sr_ticket_col_norm in sr_df_copy.columns:
                # The extraction of digits is fine.
                sr_df_copy[sr_ticket_col_norm] = sr_df_copy[sr_ticket_col_norm].astype(str).str.extract(r'(\d{4,})')
                sr_df_copy[sr_ticket_col_norm] = pd.to_numeric(sr_df_copy[sr_ticket_col_norm], errors='coerce')
                sr_df_copy.dropna(subset=[sr_ticket_col_norm], inplace=True)

                cols_to_merge_from_sr = [sr_ticket_col_norm] # Start with the join key
                sr_rename_for_merge = {}

                # If these normalized columns exist in sr_df_copy, prepare to rename them to avoid clashes during merge
                if sr_status_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[sr_status_col_norm] = 'sr_status_temp'
                if sr_last_mod_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[sr_last_mod_col_norm] = 'sr_last_update_temp'
                if sr_breach_col_norm in sr_df_copy.columns:
                    sr_rename_for_merge[sr_breach_col_norm] = 'sr_breach_value_temp'

                sr_df_copy.rename(columns=sr_rename_for_merge, inplace=True)

                # Add the new temporary names to the list of columns to merge
                for temp_name in sr_rename_for_merge.values():
                    if temp_name not in cols_to_merge_from_sr:
                        cols_to_merge_from_sr.append(temp_name)

                # Perform the merge
                df_enriched = df_enriched.merge(
                    sr_df_copy[cols_to_merge_from_sr], # Use only the necessary (renamed) columns
                    how='left',
                    left_on=ticket_number_col, # from df_enriched (already normalized or defined as such)
                    right_on=sr_ticket_col_norm, # from sr_df_copy (normalized key)
                    suffixes=('', '_sr_merged') # Suffix for any unexpected conflicts, though we renamed
                )

                # Clean up the merged key if it was duplicated with a suffix
                if f"{sr_ticket_col_norm}_sr_merged" in df_enriched.columns:
                     df_enriched.drop(columns=[f"{sr_ticket_col_norm}_sr_merged"], inplace=True)
                # If the original sr_ticket_col_norm from sr_df_copy is still there AND it's not ticket_number_col, drop it.
                if sr_ticket_col_norm in df_enriched.columns and sr_ticket_col_norm != ticket_number_col:
                    df_enriched.drop(columns=[sr_ticket_col_norm], inplace=True, errors='ignore')


                # Populate df_enriched columns from the temporary merged columns
                sr_mask = df_enriched[type_col] == 'SR' # type_col is already defined and normalized

                if 'sr_status_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, status_col] = df_enriched.loc[sr_mask, 'sr_status_temp'] # status_col is normalized target
                    df_enriched.drop(columns=['sr_status_temp'], inplace=True)
                if 'sr_last_update_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, last_update_col] = df_enriched.loc[sr_mask, 'sr_last_update_temp'] # last_update_col is normalized target
                    df_enriched.drop(columns=['sr_last_update_temp'], inplace=True)

                if 'sr_breach_value_temp' in df_enriched.columns:
                    def map_str_to_bool_sr(value): # This helper function is fine
                        if pd.isna(value): return None
                        val_lower = str(value).lower()
                        if val_lower in ['yes', 'true', '1', 'passed'] : return True
                        if val_lower in ['no', 'false', '0', 'failed']: return False
                        return None

                    mapped_values = df_enriched.loc[sr_mask, 'sr_breach_value_temp'].apply(map_str_to_bool_sr)
                    df_enriched.loc[sr_mask, breach_passed_col] = mapped_values # breach_passed_col is normalized target
                    df_enriched.drop(columns=['sr_breach_value_temp'], inplace=True)

        # Merge with Incident status data if available
        # incident_df columns are already normalized at load time
        if hasattr(st.session_state, 'incident_df') and st.session_state.incident_df is not None:
            incident_df_copy = st.session_state.incident_df.copy()

            # Define normalized versions of potential incident ID column names
            incident_id_col_options_norm = [normalize_column_name(name) for name in ['Incident', 'Incident ID', 'IncidentID', 'ID', 'Number']]
            actual_incident_id_col_norm = None
            for col_option_norm in incident_id_col_options_norm:
                if col_option_norm in incident_df_copy.columns:
                    actual_incident_id_col_norm = col_option_norm
                    break
            
            if actual_incident_id_col_norm:
                incident_df_copy[actual_incident_id_col_norm] = incident_df_copy[actual_incident_id_col_norm].astype(str).str.extract(r'(\d{4,})')
                incident_df_copy[actual_incident_id_col_norm] = pd.to_numeric(incident_df_copy[actual_incident_id_col_norm], errors='coerce')
                incident_df_copy.dropna(subset=[actual_incident_id_col_norm], inplace=True)
                
                inc_rename_map = {}
                # inc_merge_cols will be built with actual_incident_id_col_norm and the temp names
                inc_merge_cols = [actual_incident_id_col_norm]

                # Normalized column names from incident_df that we want to merge
                inc_status_col_norm = normalize_column_name('Status')
                inc_last_update_options_norm = [normalize_column_name(name) for name in ['Last Checked at', 'Last Checked atc', 'Modified On', 'Last Update']]
                actual_inc_last_update_col_norm = None
                for lu_option_norm in inc_last_update_options_norm:
                    if lu_option_norm in incident_df_copy.columns:
                        actual_inc_last_update_col_norm = lu_option_norm
                        break
                inc_breach_col_norm = normalize_column_name('Breach Passed')

                if inc_status_col_norm in incident_df_copy.columns:
                    inc_rename_map[inc_status_col_norm] = 'inc_status_temp'
                if actual_inc_last_update_col_norm:
                    inc_rename_map[actual_inc_last_update_col_norm] = 'inc_last_update_temp'
                if inc_breach_col_norm in incident_df_copy.columns:
                    inc_rename_map[inc_breach_col_norm] = 'inc_breach_passed_temp'

                incident_df_copy.rename(columns=inc_rename_map, inplace=True)
                
                # Add the new temporary names to the list of columns to merge
                for temp_name in inc_rename_map.values():
                    if temp_name not in inc_merge_cols: # Should always be true as temp_names are new
                        inc_merge_cols.append(temp_name)

                # Ensure all columns in inc_merge_cols actually exist in incident_df_copy after renaming
                inc_merge_cols = [col for col in inc_merge_cols if col in incident_df_copy.columns]

                df_enriched = df_enriched.merge(
                    incident_df_copy[inc_merge_cols],
                    how='left',
                    left_on=ticket_number_col,
                    right_on=actual_incident_id_col_norm,
                    suffixes=('', '_inc_merged')
                )

                if f"{actual_incident_id_col_norm}_inc_merged" in df_enriched.columns:
                     df_enriched.drop(columns=[f"{actual_incident_id_col_norm}_inc_merged"], inplace=True)
                if actual_incident_id_col_norm in df_enriched.columns and actual_incident_id_col_norm != ticket_number_col:
                     df_enriched.drop(columns=[actual_incident_id_col_norm], inplace=True, errors='ignore')

                incident_mask = df_enriched[type_col] == 'Incident'
                
                if 'inc_status_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, status_col] = df_enriched.loc[incident_mask, 'inc_status_temp']
                    df_enriched.drop(columns=['inc_status_temp'], inplace=True)
                if 'inc_last_update_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, last_update_col] = df_enriched.loc[incident_mask, 'inc_last_update_temp']
                    df_enriched.drop(columns=['inc_last_update_temp'], inplace=True)
                
                if 'inc_breach_passed_temp' in df_enriched.columns:
                    def map_str_to_bool_inc(value):
                        if pd.isna(value): return None
                        if isinstance(value, bool): return value
                        val_lower = str(value).lower()
                        if val_lower in ['yes', 'true', '1', 'passed', 'breached']: return True
                        if val_lower in ['no', 'false', '0', 'failed', 'not breached']: return False
                        return None

                    mapped_inc_breach_values = df_enriched.loc[incident_mask, 'inc_breach_passed_temp'].apply(map_str_to_bool_inc)
                    df_enriched.loc[incident_mask, breach_passed_col] = mapped_inc_breach_values
                    df_enriched.drop(columns=['inc_breach_passed_temp'], inplace=True)

        # Use normalized column names defined at the start of enrich_data
        if last_update_col in df_enriched.columns:
            df_enriched[last_update_col] = pd.to_datetime(df_enriched[last_update_col], errors='coerce')

        breach_date_col_norm = normalize_column_name('Breach Date')
        if breach_date_col_norm in df_enriched.columns: # Check for normalized 'Breach Date'
            df_enriched[breach_date_col_norm] = pd.to_datetime(df_enriched[breach_date_col_norm], errors='coerce')

        case_count_col = 'case_count' # This is a derived column, name it consistently
        if ticket_number_col in df_enriched.columns and type_col in df_enriched.columns:
            valid_ticket_mask = df_enriched[ticket_number_col].notna() & df_enriched[type_col].notna()
            if valid_ticket_mask.any():
                 df_enriched.loc[valid_ticket_mask, case_count_col] = df_enriched[valid_ticket_mask].groupby([ticket_number_col, type_col])[ticket_number_col].transform('size')
        else:
            df_enriched[case_count_col] = pd.NA
            
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
        
        # Normalized column names from enrich_data context
        # triage_status_col = 'triage_status' (defined in enrich_data)
        # type_col = 'type' (defined in enrich_data)
        # status_col = normalize_column_name('Status') (defined in enrich_data)

        with col1:
            # Use the already defined triage_status_col for consistency
            status_filter = st.selectbox(
                "Filter by Triage Status",
                ["All"] + df_enriched[triage_status_col].dropna().unique().tolist() if triage_status_col in df_enriched.columns else ["All"]
            )
        
        with col2:
            # Use the already defined type_col
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "SR", "Incident"] # Type is derived, these values are fixed
            )
        
        with col3:
            # Unified Status filter using status_col
            if status_col in df_enriched.columns:
                status_options = ["All"] + df_enriched[status_col].dropna().unique().tolist() + ["None"]
                unified_status_filter = st.selectbox("Filter by Status", status_options)
            else:
                unified_status_filter = "All"
        
        # Apply filters
        df_display = df_enriched.copy()
        
        if status_filter != "All" and triage_status_col in df_display.columns:
            df_display = df_display[df_display[triage_status_col] == status_filter]
        
        if type_filter != "All" and type_col in df_display.columns:
            df_display = df_display[df_display[type_col] == type_filter]
        
        if unified_status_filter != "All" and status_col in df_display.columns:
            if unified_status_filter == "None":
                df_display = df_display[df_display[status_col].isna()]
            else:
                df_display = df_display[df_display[status_col] == unified_status_filter]
        
        # Statistics and summary
        st.subheader("📊 Summary Analysis")
        
        summary_col1, summary_col2 = st.columns(2)
        
        # triage_status_col, type_col, status_col, ticket_number_col are from enrich_data context

        with summary_col1:
            st.markdown("**🔸 Triage Status Count**")
            if triage_status_col in df_enriched.columns:
                triage_summary = df_enriched[triage_status_col].value_counts().rename_axis(triage_status_col).reset_index(name='Count')
                triage_total = {triage_status_col: 'Total', 'Count': triage_summary['Count'].sum()}
                triage_df = pd.concat([triage_summary, pd.DataFrame([triage_total])], ignore_index=True)
                st.dataframe(
                    triage_df.style.apply(
                        lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(triage_df)-1 else '' for _ in x],
                        axis=1
                    )
                )
            else:
                st.info("Triage Status column not found.")
        with summary_col2:
            st.markdown("**🔹 SR vs Incident Count**")
            if type_col in df_enriched.columns:
                type_summary = df_enriched[type_col].value_counts().rename_axis(type_col).reset_index(name='Count')
                type_total = {type_col: 'Total', 'Count': type_summary['Count'].sum()}
                type_df = pd.concat([type_summary, pd.DataFrame([type_total])], ignore_index=True)
                st.dataframe(
                    type_df.style.apply(
                        lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(type_df)-1 else '' for _ in x],
                        axis=1
                    )
                )
            else:
                st.info("Type column not found.")

        summary_col3, summary_col4 = st.columns(2)
        with summary_col3:
            st.markdown("**🟢 SR Status Summary**")
            if status_col in df_enriched.columns and type_col in df_enriched.columns and ticket_number_col in df_enriched.columns:
                df_srs_all_types = df_enriched[df_enriched[type_col] == 'SR'] # Filter by type 'SR'
                if not df_srs_all_types.empty:
                    df_srs_status_valid = df_srs_all_types.dropna(subset=[status_col])
                    
                    if not df_srs_status_valid.empty:
                        status_all_counts = df_srs_status_valid[status_col].value_counts().rename_axis(status_col).reset_index(name='All Count')

                        ticket_unique = df_srs_status_valid.dropna(subset=[ticket_number_col])[[ticket_number_col, status_col]].drop_duplicates()
                        ticket_unique_counts = ticket_unique[status_col].value_counts().rename_axis(status_col).reset_index(name='Unique Count')

                        merged_status = pd.merge(status_all_counts, ticket_unique_counts, on=status_col, how='outer').fillna(0)
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
        # status_col, type_col, ticket_number_col are from enrich_data context
        with summary_col4:
            st.markdown("**🟣 Incident Status Summary**")
            if status_col in df_enriched.columns and type_col in df_enriched.columns and ticket_number_col in df_enriched.columns:
                df_incidents_all_types = df_enriched[df_enriched[type_col] == 'Incident'] # Filter by type 'Incident'
                if not df_incidents_all_types.empty:
                    df_incidents_status_valid = df_incidents_all_types.dropna(subset=[status_col])

                    if not df_incidents_status_valid.empty:
                        incident_status_all_counts = df_incidents_status_valid[status_col].value_counts().rename_axis(status_col).reset_index(name='Cases Count')

                        incident_ticket_unique = df_incidents_status_valid.dropna(subset=[ticket_number_col])[[ticket_number_col, status_col]].drop_duplicates()
                        incident_ticket_unique_counts = incident_ticket_unique[status_col].value_counts().rename_axis(status_col).reset_index(name='Unique Count')

                        merged_incident_status = pd.merge(incident_status_all_counts, incident_ticket_unique_counts, on=status_col, how='outer').fillna(0)
                        merged_incident_status[['Cases Count', 'Unique Count']] = merged_incident_status[['Cases Count', 'Unique Count']].astype(int)

                        incident_total_row = {
                            status_col: 'Total', # Use normalized status_col here
                            'Cases Count': merged_incident_status['Cases Count'].sum(),
                            'Unique Count': merged_incident_status['Unique Count'].sum()
                        }

                        incident_status_summary_df = pd.concat([merged_incident_status, pd.DataFrame([incident_total_row])], ignore_index=True)

                        st.dataframe(
                            incident_status_summary_df.style.apply(
                                lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(incident_status_summary_df)-1 else '' for _ in x],
                                axis=1
                            )
                        )
                    else:
                        st.info("No incidents with status information available to summarize.")
                else: # No incidents of type 'Incident'
                    st.info("No incident data of type 'Incident' available to summarize.")
            elif st.session_state.incident_df is None: # Check if incident_df was loaded at all
                st.info("Upload Incident Report Excel file to view Incident Status Summary.")
            else: # Columns missing or other issues
                st.info("Required columns for Incident Status Summary are missing or no incident data available.")
        
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
            all_columns = df_display.columns.tolist()
            SELECT_ALL_COLS_ANALYSIS_OPTION = "[Select All Columns]"

            # Define default columns using normalized names
            # Many of these are already defined variables in the enrich_data or current tab's scope
            # For clarity, re-normalize or use existing normalized variables:
            # last_note_col, case_id_col (assuming 'Case Id' is a col), current_user_id_col, case_start_date_col,
            # triage_status_col, type_col, ticket_number_col, status_col, last_update_col, breach_passed_col

            default_selected_cols_initial_raw = ['Last Note', 'Case Id', 'Current User Id', 'Case Start Date', 'Triage Status', 'Type', 'Ticket Number']
            default_selected_cols_initial_normalized = [normalize_column_name(col) for col in default_selected_cols_initial_raw]

            # Add conditional columns (already normalized if they exist, as they come from df_display.columns)
            if status_col in df_display.columns: # status_col is normalized
                default_selected_cols_initial_normalized.extend([status_col, last_update_col]) # last_update_col is normalized
            if breach_passed_col in df_display.columns: # breach_passed_col is normalized
                default_selected_cols_initial_normalized.append(breach_passed_col)

            # Ensure default columns are valid and exist in df_display (all_columns are from df_display, so normalized)
            default_selected_cols = [col for col in default_selected_cols_initial_normalized if col in all_columns]

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

        # Using normalized column names from enrich_data context:
        # case_count_col = 'case_count'
        # ticket_number_col (normalized 'Ticket Number')
        # type_col = 'type'
        # status_col (normalized 'Status')

        if case_count_col in df_display.columns and ticket_number_col in df_display.columns:
            linked_cases_df = df_display[
                (df_display[case_count_col] >= min_linked_cases) &
                (df_display[ticket_number_col].notna())
            ]

            if not linked_cases_df.empty:
                # Ensure columns for display in linked_summary_df are selected using normalized names
                cols_for_linked_summary = [ticket_number_col, type_col]
                if status_col in linked_cases_df.columns: # status_col is already normalized
                    cols_for_linked_summary.append(status_col)
                cols_for_linked_summary.append(case_count_col)

                linked_summary_df = linked_cases_df[cols_for_linked_summary].drop_duplicates().sort_values(by=case_count_col, ascending=False)
                st.dataframe(linked_summary_df, hide_index=True)
            else:
                st.info(f"No Incidents/SRs found with at least {min_linked_cases} linked cases based on current filters.")
        else:
            st.warning(f"Required columns ('{case_count_col}', '{ticket_number_col}') not available for linked cases summary.")

        # Note viewer
        st.subheader("📝 Note Details")
        
        case_id_col_norm = normalize_column_name('Case Id') # Assuming 'Case Id' is the name from input
        current_user_id_col_norm = normalize_column_name('Current User Id')
        case_start_date_col_norm = normalize_column_name('Case Start Date')
        age_days_col_norm = age_days_col # from enrich_data context ('age_days')
        # ticket_number_col, type_col, status_col, last_update_col, breach_passed_col, last_note_col from enrich_data context

        selected_case_id_options = df_display[case_id_col_norm].tolist() if case_id_col_norm in df_display.columns else []
        
        if not selected_case_id_options:
            st.info("No cases available to select for note viewing.")
        else:
            selected_case = st.selectbox(
                "Select a case to view notes:",
                selected_case_id_options
            )
            
            if selected_case and case_id_col_norm in df_display.columns:
                case_row = df_display[df_display[case_id_col_norm] == selected_case].iloc[0]
                
                details_data = []
                if case_id_col_norm in case_row: details_data.append(("Case ID", case_row[case_id_col_norm]))
                if current_user_id_col_norm in case_row: details_data.append(("Owner", case_row[current_user_id_col_norm]))
                if case_start_date_col_norm in case_row and pd.notna(case_row[case_start_date_col_norm]):
                    details_data.append(("Start Date", case_row[case_start_date_col_norm].strftime('%Y-%m-%d')))
                if age_days_col_norm in case_row: details_data.append(("Age", f"{case_row[age_days_col_norm]} days"))
                if ticket_number_col in case_row:
                    details_data.append(("Ticket Number", int(case_row[ticket_number_col]) if pd.notna(case_row[ticket_number_col]) else 'N/A'))
                if type_col in case_row:
                    details_data.append(("Type", case_row[type_col] if pd.notna(case_row[type_col]) else 'N/A'))

                if status_col in case_row and pd.notna(case_row[status_col]):
                    details_data.append(("Status", case_row[status_col]))
                    if last_update_col in case_row and pd.notna(case_row[last_update_col]):
                        details_data.append(("Last Update", case_row[last_update_col]))
                if breach_passed_col in case_row: # breach_passed_col is already normalized
                    details_data.append(("SLA Breach", "Yes ⚠️" if case_row[breach_passed_col] == True else "No"))
                
                case_details_df = pd.DataFrame(details_data, columns=["Field", "Value"])
                st.table(case_details_df)

                st.markdown("### Last Note")
                if last_note_col in case_row and pd.notna(case_row[last_note_col]):
                    st.text_area("Note Content", case_row[last_note_col], height=200)
                else:
                    st.info("No notes available for this case")

                excel_data = generate_excel_download(df_display[df_display[case_id_col_norm] == selected_case])
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
        if st.session_state.sr_df is None and st.session_state.incident_df is None: # This check is about data loading, not column names
            st.warning("Please upload SR Status Excel file or Incident Report Excel file to view SLA breach information.")
        else:
            # Use normalized column names from enrich_data context
            # breach_passed_col, status_col, type_col
            # For display: case_id_col_norm, current_user_id_col_norm, case_start_date_col_norm, ticket_number_col, last_update_col, age_days_col_norm

            if breach_passed_col in df_enriched.columns:
                breach_df = df_enriched[df_enriched[breach_passed_col] == True].copy()
                
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
                    if status_col in breach_df.columns: # status_col is normalized
                        open_breaches = len(breach_df[breach_df[status_col].isin(['Open', 'In Progress', 'Pending', 'New'])])
                        st.markdown(f'<p class="metric-value">{open_breaches}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Open Breached Cases</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Status Not Available</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    if type_col in breach_df.columns: # type_col is normalized ('type')
                        sr_breaches = len(breach_df[breach_df[type_col] == 'SR'])
                        st.markdown(f'<p class="metric-value">{sr_breaches}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">SR Breaches</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">SR Breaches</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Breach details by type and status
                if not breach_df.empty:
                    st.subheader("📋 SLA Breach Details")
                    
                    breach_col1, breach_col2 = st.columns(2)
                    
                    with breach_col1:
                        breach_type_filter = st.selectbox(
                            "Filter by Type (Breach)",
                            ["All", "SR", "Incident"], # Values for type_col
                            key="breach_type"
                        )
                    
                    with breach_col2:
                        if status_col in breach_df.columns: # status_col is normalized
                            breach_status_options = ["All"] + breach_df[status_col].dropna().unique().tolist()
                            breach_status_filter = st.selectbox(
                                "Filter by Status (Breach)",
                                breach_status_options,
                                key="breach_status"
                            )
                        else:
                            breach_status_filter = "All"
                    
                    breach_display = breach_df.copy()
                    
                    if breach_type_filter != "All" and type_col in breach_display.columns:
                        breach_display = breach_display[breach_display[type_col] == breach_type_filter]
                    
                    if breach_status_filter != "All" and status_col in breach_display.columns:
                        breach_display = breach_display[breach_display[status_col] == breach_status_filter]
                    
                    st.markdown(f"**Total Breached Records:** {breach_display.shape[0]}")
                    
                    if not breach_display.empty:
                        excel_breach_data = generate_excel_download(breach_display)
                        st.download_button(
                            label="📥 Download Breach Analysis",
                            data=excel_breach_data,
                            file_name=f"sla_breach_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Define normalized column names for display
                    case_id_col_norm = normalize_column_name('Case Id')
                    current_user_id_col_norm = normalize_column_name('Current User Id')
                    case_start_date_col_norm = normalize_column_name('Case Start Date')
                    # ticket_number_col, status_col, last_update_col, age_days_col_norm (age_days) are from enrich_data/tab scope

                    breach_cols_raw = ['Case Id', 'Current User Id', 'Case Start Date', 'Type', 'Ticket Number', 'Status', 'Last Update', 'Age (Days)']
                    # Map to normalized versions, using variables already defined in enrich_data or this tab's scope where possible
                    breach_display_cols_normalized = [
                        case_id_col_norm, current_user_id_col_norm, case_start_date_col_norm,
                        type_col, ticket_number_col, status_col, last_update_col, age_days_col # age_days_col was 'age_days'
                    ]
                    # Filter to only include columns that actually exist in breach_display
                    breach_display_cols = [col for col in breach_display_cols_normalized if col in breach_display.columns]
                    
                    if not breach_display.empty and breach_display_cols:
                        st.dataframe(breach_display[breach_display_cols], hide_index=True)
                    elif not breach_display.empty: # Columns list ended up empty but df not
                        st.dataframe(breach_display, hide_index=True) # Show all if specific list is empty
                    else:
                        st.info("No breached cases match the selected filters.")
                        
                else:
                    st.info("No SLA breaches found in the current dataset.")
            else: # breach_passed_col not in df_enriched.columns
                st.info(f"SLA breach information not available. Please ensure your SR/Incident status files contain '{normalize_column_name('Breach Passed')}' column.")
    
    #
    # TODAY'S SR/INCIDENTS TAB
    #
    elif selected == "Today's SR/Incidents":
        st.title("📅 Today's New SR/Incidents")
        
        # Get today's cases
        today = datetime.now().date()

        # Use normalized column names from enrich_data context:
        # created_today_col = 'created_today'
        # last_note_date_col (normalized 'Last Note Date')
        # triage_status_col = 'triage_status'
        # type_col = 'type'
        # current_user_id_col_norm (normalized 'Current User Id')
        # case_id_col_norm (normalized 'Case Id')
        # ticket_number_col (normalized 'Ticket Number')
        # status_col (normalized 'Status')
        # last_update_col (normalized 'Last Update')
        
        if created_today_col in df_enriched.columns:
            today_cases = df_enriched[df_enriched[created_today_col] == True].copy()
        elif last_note_date_col in df_enriched.columns: # Fallback
            today_cases = df_enriched[df_enriched[last_note_date_col].dt.date == today].copy()
        else:
            today_cases = pd.DataFrame() # Ensure it's a DataFrame
        
        # Further filter for SR/Incident cases only
        if triage_status_col in today_cases.columns:
            today_sr_incidents = today_cases[today_cases[triage_status_col] == 'Pending SR/Incident'].copy()
        else:
            today_sr_incidents = pd.DataFrame()
        
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
            if type_col in today_sr_incidents.columns: # type_col is normalized
                sr_today = len(today_sr_incidents[today_sr_incidents[type_col] == 'SR'])
                st.markdown(f'<p class="metric-value">{sr_today}</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New SRs Today</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New SRs Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with summary_today_col3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            if type_col in today_sr_incidents.columns: # type_col is normalized
                incident_today = len(today_sr_incidents[today_sr_incidents[type_col] == 'Incident'])
                st.markdown(f'<p class="metric-value">{incident_today}</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New Incidents Today</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">New Incidents Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Breakdown by user
        if not today_sr_incidents.empty:
            st.subheader("👥 Breakdown by User")
            
            # Normalized column names
            current_user_id_col_norm = normalize_column_name('Current User Id')
            case_id_col_norm = normalize_column_name('Case Id')
            # type_col and ticket_number_col are already in scope and normalized

            if current_user_id_col_norm in today_sr_incidents.columns and \
               case_id_col_norm in today_sr_incidents.columns and \
               type_col in today_sr_incidents.columns and \
               ticket_number_col in today_sr_incidents.columns:

                user_breakdown = today_sr_incidents.groupby(current_user_id_col_norm).agg(
                    Total=(case_id_col_norm, 'count'),
                    SRs=(type_col, lambda x: (x == 'SR').sum()),
                    Incidents=(type_col, lambda x: (x == 'Incident').sum()) # Simpler way to count incidents
                ).reset_index()

                # Add total row
                total_row = pd.DataFrame({
                    current_user_id_col_norm: ['TOTAL'],
                    'Total': [user_breakdown['Total'].sum()],
                    'SRs': [user_breakdown['SRs'].sum()],
                    'Incidents': [user_breakdown['Incidents'].sum()]
                })
                user_breakdown_display = pd.concat([user_breakdown, total_row], ignore_index=True)
            else:
                user_breakdown_display = pd.DataFrame() # Empty if required columns are missing
            
            st.dataframe(
                user_breakdown_display.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(user_breakdown_display)-1 else '' for _ in x],
                    axis=1
                )
            )
            
            # Filter options for today's data
            st.subheader("🔍 Filter Today's Data")
            
            today_col1, today_col2 = st.columns(2)
            
            # current_user_id_col_norm, type_col are defined/normalized earlier or in enrich_data
            with today_col1:
                user_options_today = []
                if current_user_id_col_norm in today_sr_incidents.columns:
                    user_options_today = today_sr_incidents[current_user_id_col_norm].unique().tolist()
                today_user_filter = st.selectbox(
                    "Filter by User (Today)",
                    ["All"] + user_options_today,
                    key="today_user"
                )
            
            with today_col2:
                today_type_filter = st.selectbox(
                    "Filter by Type (Today)",
                    ["All", "SR", "Incident"], # Values for type_col
                    key="today_type"
                )
            
            today_display = today_sr_incidents.copy()
            
            if today_user_filter != "All" and current_user_id_col_norm in today_display.columns:
                today_display = today_display[today_display[current_user_id_col_norm] == today_user_filter]
            
            if today_type_filter != "All" and type_col in today_display.columns:
                today_display = today_display[today_display[type_col] == today_type_filter]
            
            st.subheader("📋 Today's Details")
            results_today_col1, results_today_col2 = st.columns([3, 1])
            
            with results_today_col1:
                st.markdown(f"**Filtered Records:** {today_display.shape[0]}")
            
            with results_today_col2:
                if not today_display.empty:
                    excel_today_data = generate_excel_download(today_display)
                    st.download_button(
                        label="📥 Download Today's Data",
                        data=excel_today_data,
                        file_name=f"todays_sr_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Define display columns using normalized names
            # case_id_col_norm, current_user_id_col_norm, last_note_date_col, type_col, ticket_number_col, status_col, last_update_col
            today_cols_raw = ['Case Id', 'Current User Id', 'Last Note Date', 'Type', 'Ticket Number']
            today_cols_normalized = [
                case_id_col_norm, current_user_id_col_norm, last_note_date_col,
                type_col, ticket_number_col
            ]
            if status_col in today_display.columns: # status_col is normalized
                today_cols_normalized.extend([status_col, last_update_col]) # last_update_col is normalized
            
            today_display_cols = [col for col in today_cols_normalized if col in today_display.columns]
            
            if not today_display.empty and today_display_cols:
                st.dataframe(today_display[today_display_cols], hide_index=True)
            elif not today_display.empty:
                 st.dataframe(today_display, hide_index=True) # Show all if column list is empty
            else:
                st.info("No records match the selected filters for today.")
                
        else: # if not today_sr_incidents.empty:
            st.info("No new SR/Incidents found for today.")
            
            if not today_cases.empty:
                st.subheader("📝 All Today's Cases")
                st.markdown(f"**Total cases with notes today:** {len(today_cases)}")
                
                # Define display columns for all today's cases using normalized names
                all_today_cols_raw = ['Case Id', 'Current User Id', 'Last Note Date', 'Triage Status']
                all_today_cols_normalized = [
                    normalize_column_name('Case Id'), # case_id_col_norm
                    normalize_column_name('Current User Id'), # current_user_id_col_norm
                    last_note_date_col, # from enrich_data
                    triage_status_col # from enrich_data
                ]
                all_today_display_cols = [col for col in all_today_cols_normalized if col in today_cases.columns]
                
                if all_today_display_cols:
                    st.dataframe(today_cases[all_today_display_cols], hide_index=True)
                else:
                    st.dataframe(today_cases, hide_index=True) # Show all if specific list empty
                
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

        # Define normalized column names relevant for this tab
        # Note: incident_overview_df is created from incident_df, whose columns are already normalized at load time.
        # So, when incident_overview_df is copied, its columns are already normalized.

        customer_col_norm = normalize_column_name('Customer') # Original name in file
        creator_col_norm = normalize_column_name('Creator')   # Target name after rename
        incident_col_norm = normalize_column_name('Incident')
        team_col_norm = normalize_column_name('Team')
        priority_col_norm = normalize_column_name('Priority')
        status_col_norm = normalize_column_name('Status') # This is the generic status, same as status_col in enrich_data

        # Warning message check - uses raw names as that's what user expects in file
        missing_cols_for_warning_check = []
        # We need to check if the *normalized* versions of these raw names are present in the loaded incident_df
        # This check happens before the overview_df is even populated in some cases.
        # For simplicity in the warning, we'll list the raw names. The actual check for df operations uses normalized.
        raw_expected_cols = ['Customer', 'Incident', 'Team', 'Priority', 'Status']
        # This warning logic might need to be re-evaluated if st.session_state.incident_df itself is None.

        if 'incident_overview_df' not in st.session_state or st.session_state.incident_overview_df is None or st.session_state.incident_overview_df.empty:
            # Check if incident_df exists and if it has the required *normalized* columns
            required_norm_cols_in_source = [normalize_column_name(c) for c in raw_expected_cols]
            cols_actually_missing_in_source_for_warning = []
            if st.session_state.get('incident_df') is not None:
                for req_col in required_norm_cols_in_source:
                    if req_col not in st.session_state.incident_df.columns:
                        # Find the raw name that corresponds to this missing normalized col for the warning
                        original_raw_name = "Unknown"
                        for r_idx, r_norm in enumerate(required_norm_cols_in_source):
                            if r_norm == req_col:
                                original_raw_name = raw_expected_cols[r_idx]
                                break
                        cols_actually_missing_in_source_for_warning.append(original_raw_name)

            warning_msg = "The 'Incident Report Excel' has not been uploaded"
            if st.session_state.get('incident_df') is not None and st.session_state.incident_overview_df is not None and st.session_state.incident_overview_df.empty :
                 warning_msg = "The 'Incident Report Excel' resulted in an empty overview DataFrame (possibly after initial processing)."
            elif cols_actually_missing_in_source_for_warning:
                 warning_msg = f"The 'Incident Report Excel' is missing the required columns: {', '.join(cols_actually_missing_in_source_for_warning)}."
            warning_msg += " Please upload the correct file via the sidebar to view the Incident Overview."
            st.warning(warning_msg)
        else:
            overview_df = st.session_state.incident_overview_df.copy() # This df should have normalized cols

            # The rename from "Customer" to "Creator" happened during the initial load of incident_overview_df.
            # It should have been: if customer_col_norm in overview_df.columns: overview_df.rename(columns={customer_col_norm: creator_col_norm}, inplace=True)
            # This logic is in the file upload section. We need to adjust it there.
            # For now, assume overview_df *has* creator_col_norm if the rename was successful.

            st.subheader("Filter Incidents")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Filter by Creator (creator_col_norm)
                unique_creators = []
                if creator_col_norm in overview_df.columns: # creator_col_norm is normalized
                    unique_creators = sorted(overview_df[creator_col_norm].dropna().unique())

                SELECT_ALL_CREATORS_OPTION = SELECT_ALL_BASE_STRING % "Creators"

                if 'incident_creator_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_creators = list(unique_creators)
                    if unique_creators:
                        st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                    else:
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

            with col2:
                # Filter by Team (team_col_norm)
                unique_teams = []
                if team_col_norm in overview_df.columns: # team_col_norm is normalized
                    unique_teams = sorted(overview_df[team_col_norm].dropna().unique())

                SELECT_ALL_TEAMS_OPTION = SELECT_ALL_BASE_STRING % "Teams"
                # Default teams are raw strings, their normalized versions will be checked against normalized unique_teams
                default_teams_to_select_raw = ["GPSSA App Team L1", "GPSSA App Team L3"]
                default_teams_to_select_norm = [normalize_column_name(t) for t in default_teams_to_select_raw]

                if 'incident_team_widget_selection_controlled' not in st.session_state:
                    # unique_teams are already normalized if team_col_norm was found
                    actual_default_teams = [team_norm for team_norm in default_teams_to_select_norm if team_norm in unique_teams]

                    if actual_default_teams:
                        st.session_state.selected_teams = list(actual_default_teams)
                        if unique_teams and set(actual_default_teams) == set(unique_teams):
                            st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                        else:
                            st.session_state.incident_team_widget_selection_controlled = list(actual_default_teams)
                    elif unique_teams:
                        st.session_state.selected_teams = list(unique_teams)
                        st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                    else:
                        st.session_state.selected_teams = []
                        st.session_state.incident_team_widget_selection_controlled = []

                options_for_team_widget = [SELECT_ALL_TEAMS_OPTION] + unique_teams
                raw_team_widget_selection = st.multiselect(
                    "Filter by Team",
                    options=options_for_team_widget,
                    default=st.session_state.incident_team_widget_selection_controlled,
                    key="multi_select_incident_team"
                )

                prev_widget_display_state = list(st.session_state.incident_team_widget_selection_controlled)
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

            with col3:
                # Filter by Priority (priority_col_norm)
                unique_priorities = []
                if priority_col_norm in overview_df.columns: # priority_col_norm is normalized
                    unique_priorities = sorted(overview_df[priority_col_norm].dropna().unique())

                SELECT_ALL_PRIORITIES_OPTION = SELECT_ALL_BASE_STRING % "Priorities"

                if 'incident_priority_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_priorities = list(unique_priorities)
                    if unique_priorities:
                        st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                    else:
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

            with col4:
                # Filter by Status (status_col_norm)
                unique_statuses = []
                if status_col_norm in overview_df.columns: # status_col_norm is normalized
                    unique_statuses = sorted(overview_df[status_col_norm].dropna().unique())

                # Exclude 'Closed', 'Resolved', 'Cancelled' by default - these are raw strings
                closed_like_statuses_raw = {'Closed', 'Cancelled'}
                # We need to compare against unique_statuses which are actual values from the (normalized) column
                # Assuming status values themselves are not needing normalization if they are like 'Closed', 'Open' etc.
                default_selected_statuses = [s for s in unique_statuses if s not in closed_like_statuses_raw]

                SELECT_ALL_STATUSES_OPTION = SELECT_ALL_BASE_STRING % "Statuses"

                if 'incident_status_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_statuses = list(default_selected_statuses)

                    if not default_selected_statuses and unique_statuses:
                        st.session_state.selected_statuses = list(unique_statuses)
                        st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif unique_statuses and set(default_selected_statuses) == set(unique_statuses):
                        st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif not unique_statuses:
                        st.session_state.selected_statuses = []
                        st.session_state.incident_status_widget_selection_controlled = []
                    else:
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

            # Apply filters (using normalized column names)
            filtered_overview_df = overview_df.copy() # Start with a fresh copy

            if st.session_state.get('selected_creators') and creator_col_norm in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df[creator_col_norm].isin(st.session_state.selected_creators)]
            if st.session_state.get('selected_teams') and team_col_norm in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df[team_col_norm].isin(st.session_state.selected_teams)]
            if st.session_state.get('selected_priorities') and priority_col_norm in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df[priority_col_norm].isin(st.session_state.selected_priorities)]
            if st.session_state.get('selected_statuses') and status_col_norm in filtered_overview_df.columns:
                filtered_overview_df = filtered_overview_df[filtered_overview_df[status_col_norm].isin(st.session_state.selected_statuses)]

            # Calculate team and status totals
            team_status_summary_df = calculate_team_status_summary(filtered_overview_df) # This function will need to use normalized names too

            # --- Pie Chart for Closed Incidents ---
            st.markdown("---")
            if status_col_norm in overview_df.columns:
                closed_count = overview_df[overview_df[status_col_norm] == 'Closed'].shape[0] # Use status_col_norm here
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
            else: # status_col_norm not in overview_df.columns
                st.warning(f"Cannot display Percentage of Closed Incidents: '{status_col_norm}' column missing from source data.")

        # --- Team Assignment Distribution ---
        st.markdown("---")
        st.subheader("Team Assignment Distribution")
        if not filtered_overview_df.empty:
            if team_col_norm in filtered_overview_df.columns: # team_col_norm is normalized
                team_distribution_data = filtered_overview_df[team_col_norm].value_counts()
                
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
                st.warning(f"Cannot display Team Assignment Distribution: '{team_col_norm}' column not found in the data.")
        else:
            st.info("No data available to display for Team Assignment Distribution based on current filters.")

        # --- Incidents by Team and Status Table ---
        st.markdown("---")
        st.subheader("Incidents by Team and Status")
        if team_col_norm not in filtered_overview_df.columns or status_col_norm not in filtered_overview_df.columns:
            st.warning(f"The '{team_col_norm}' or '{status_col_norm}' column is missing in the uploaded incident data, so the 'Incidents by Team and Status' table cannot be generated.")
        elif not team_status_summary_df.empty: # team_status_summary_df is from calculate_team_status_summary which should use normalized names
            st.dataframe(team_status_summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("No incident data to display in the 'Incidents by Team and Status' table based on current filters or data availability.")
         
        # --- New Filtered Incident Details Table ---
        st.markdown("---")
        st.subheader("Filtered Incident Details")

        if not filtered_overview_df.empty:
            # Define default columns using normalized names
            default_table_cols_raw = ["Incident", "Creator", "Team", "Priority", "Status"]
            default_table_columns_normalized = [
                incident_col_norm, creator_col_norm, team_col_norm, priority_col_norm, status_col_norm
            ]
            available_default_columns = [col for col in default_table_columns_normalized if col in filtered_overview_df.columns]

            if not filtered_overview_df.empty: # This check is redundant given outer if, but kept for structure
                all_available_columns = filtered_overview_df.columns.tolist()
                SELECT_ALL_COLS_INCIDENT_OPTION = "[Select All Columns]"

                if 'incident_tab_column_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_table_columns = list(available_default_columns)
                    if not available_default_columns and all_available_columns:
                        st.session_state.selected_table_columns = list(all_available_columns)
                        st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                    elif all_available_columns and set(available_default_columns) == set(all_available_columns):
                        st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_INCIDENT_OPTION]
                    elif not all_available_columns:
                        st.session_state.selected_table_columns = []
                        st.session_state.incident_tab_column_widget_selection_controlled = []
                    else:
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

                if not current_cols_to_display_incident_tab:
                    st.info("Please select at least one column to display the table.")
                else:
                    essential_source_cols_norm = [incident_col_norm, status_col_norm]
                    missing_essential_source_cols = [col for col in essential_source_cols_norm if col not in filtered_overview_df.columns]
                    if missing_essential_source_cols:
                        # Map back to raw names for user warning
                        raw_missing_names = []
                        for missing_norm in missing_essential_source_cols:
                            if missing_norm == incident_col_norm: raw_missing_names.append("Incident")
                            elif missing_norm == status_col_norm: raw_missing_names.append("Status")
                            else: raw_missing_names.append(missing_norm) # fallback
                        st.caption(f"Warning: Source data is missing essential columns for full detail: {', '.join(raw_missing_names)}.")

                    st.write(f"Displaying {len(filtered_overview_df)} records in table with selected columns.")
                    st.dataframe(
                        filtered_overview_df[current_cols_to_display_incident_tab],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                pass
        else:
            st.info("No data to display in the 'Filtered Incident Details' table based on current filters.")
   
        # --- High-Priority Incidents Table ---
        st.markdown("---")
        st.subheader("High-Priority Incidents (P1 & P2)")
        if not filtered_overview_df.empty:
            high_priority_table_cols_normalized = [incident_col_norm, creator_col_norm, team_col_norm, priority_col_norm]
            if status_col_norm in filtered_overview_df.columns:
                high_priority_table_cols_normalized.append(status_col_norm)

            # Check if all *intended normalized* columns for this table are present
            missing_cols_for_high_priority_table_norm = [
                col for col in [incident_col_norm, creator_col_norm, team_col_norm, priority_col_norm]
                if col not in filtered_overview_df.columns
            ]

            if not missing_cols_for_high_priority_table_norm:
                high_priority_values = ["1", "2"] # These are data values, not column names
                
                # Ensure priority_col_norm is used for filtering
                high_priority_incidents_df = filtered_overview_df[
                    filtered_overview_df[priority_col_norm].astype(str).isin(high_priority_values)
                ]
                
                if not high_priority_incidents_df.empty:
                    # Display only available columns from the normalized list
                    display_cols_for_hp_table = [col for col in high_priority_table_cols_normalized if col in high_priority_incidents_df.columns]
                    if display_cols_for_hp_table:
                        st.dataframe(
                            high_priority_incidents_df[display_cols_for_hp_table],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No columns selected or available for High-Priority Incidents table.")
                else:
                    st.info("No high-priority incidents (P1 or P2) found based on current filters.")
            else:
                # Map back to raw names for user warning
                raw_missing_hp_names = []
                for missing_hp_norm in missing_cols_for_high_priority_table_norm:
                    if missing_hp_norm == incident_col_norm: raw_missing_hp_names.append("Incident")
                    elif missing_hp_norm == creator_col_norm: raw_missing_hp_names.append("Creator")
                    elif missing_hp_norm == team_col_norm: raw_missing_hp_names.append("Team")
                    elif missing_hp_norm == priority_col_norm: raw_missing_hp_names.append("Priority")
                    else: raw_missing_hp_names.append(missing_hp_norm)
                st.warning(f"Cannot display High-Priority Incidents table: Missing essential columns: {', '.join(raw_missing_hp_names)}.")
        else:
            st.info("No data available to display for High-Priority Incidents based on current filters.")

    #
    # SR OVERVIEW TAB
    #
    elif selected == "SR Overview":
        st.title("📊 Service Request (SR) Overview")
        from utils import calculate_srs_created_and_closed_per_week # Import is fine

        # Define normalized column names relevant for this tab
        # sr_df columns are already normalized at load time.
        created_on_col_norm = normalize_column_name('Created On')
        last_mod_dt_col_norm = normalize_column_name('LastModDateTime')
        status_col_norm = normalize_column_name('Status') # Consistent with other status_col definitions
        service_request_col_norm = normalize_column_name('Service Request')
        resolution_col_norm = normalize_column_name('Resolution')


        if 'sr_df' not in st.session_state or st.session_state.sr_df is None or st.session_state.sr_df.empty:
            st.warning(
                "The 'SR Status Excel' has not been uploaded or is empty. "
                "Please upload the SR status file via the sidebar to view the SR Overview."
            )
        else:
            sr_overview_df = st.session_state.sr_df.copy() # This df has normalized column names
            st.markdown(f"**Total SRs Loaded:** {len(sr_overview_df)}")

            # Check for required *normalized* columns for the new chart
            required_cols_for_chart_norm = [created_on_col_norm, last_mod_dt_col_norm, status_col_norm]

            # For the error message, map back to raw names
            raw_names_for_error = ['Created On', 'LastModDateTime', 'Status']
            missing_cols_for_error_display = []
            for i, norm_col in enumerate(required_cols_for_chart_norm):
                if norm_col not in sr_overview_df.columns:
                    missing_cols_for_error_display.append(raw_names_for_error[i])

            if missing_cols_for_error_display:
                st.error(f"The SR data must contain the following columns to generate the weekly overview: {', '.join(missing_cols_for_error_display)}.")
            else:
                # calculate_srs_created_and_closed_per_week will receive df with normalized names
                # and is expected to use normalized names internally (needs update in utils.py)
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
                    # These column names ('WeekDisplay', 'Year-Week') are from the output of calculate_srs_created_and_closed_per_week
                    if 'WeekDisplay' in srs_weekly_combined_df.columns and 'Year-Week' in srs_weekly_combined_df.columns:
                        unique_week_options_df = srs_weekly_combined_df[['Year-Week', 'WeekDisplay']].drop_duplicates().sort_values(by='Year-Week')
                        week_options_for_multiselect = unique_week_options_df['WeekDisplay'].tolist()
                        for _, row in unique_week_options_df.iterrows():
                            week_map_for_filter[row['WeekDisplay']] = row['Year-Week']
                
                # Use normalized created_on_col_norm
                year_week_derived_col = 'year_week_derived' # Temporary derived column for filtering
                if created_on_col_norm in table_display_df.columns:
                    table_display_df[created_on_col_norm] = pd.to_datetime(table_display_df[created_on_col_norm], errors='coerce')
                    table_display_df.dropna(subset=[created_on_col_norm], inplace=True)
                    if not table_display_df.empty:
                         table_display_df[year_week_derived_col] = table_display_df[created_on_col_norm].dt.strftime('%G-W%V')
                else:
                    if year_week_derived_col in table_display_df.columns:
                        pass

                col_filter1, col_filter2 = st.columns(2)

                with col_filter1:
                    selected_week_displays = st.multiselect(
                        "Filter by Week Period:",
                        options=week_options_for_multiselect,
                        default=[]
                    )

                with col_filter2:
                    min_date_val = None
                    max_date_val = None
                    if created_on_col_norm in table_display_df.columns and not table_display_df[created_on_col_norm].dropna().empty:
                        min_date_val = table_display_df[created_on_col_norm].min().date()
                        max_date_val = table_display_df[created_on_col_norm].max().date()
                    selected_day = st.date_input(f"Filter by Specific Day ({created_on_col_norm}):", value=None, min_value=min_date_val, max_value=max_date_val)

                if selected_day and created_on_col_norm in table_display_df.columns:
                    table_display_df = table_display_df[table_display_df[created_on_col_norm].dt.date == selected_day]
                elif selected_week_displays and year_week_derived_col in table_display_df.columns:
                    selected_year_weeks_short = [week_map_for_filter[wd] for wd in selected_week_displays if wd in week_map_for_filter]
                    if selected_year_weeks_short:
                         table_display_df = table_display_df[table_display_df[year_week_derived_col].isin(selected_year_weeks_short)]

                st.markdown(f"**Total Displayed SRs:** {len(table_display_df)}")

                if not table_display_df.empty:
                    all_columns_for_display = table_display_df.columns.tolist()
                    if year_week_derived_col in all_columns_for_display:
                        all_columns_for_display.remove(year_week_derived_col)

                    # Default columns for this table, using normalized names
                    default_cols_raw = ['Service Request', 'Status', 'Created On']
                    default_cols_normalized = [service_request_col_norm, status_col_norm, created_on_col_norm]
                    sanitized_default_cols = [col for col in default_cols_normalized if col in all_columns_for_display]

                    if 'filterable_sr_data_cols_multiselect' not in st.session_state:
                        st.session_state.filterable_sr_data_cols_multiselect = sanitized_default_cols

                    selected_columns = st.multiselect(
                        "Select columns to display for Filterable SR Data:",
                        options=all_columns_for_display,
                        default=st.session_state.filterable_sr_data_cols_multiselect,
                        key="multiselect_filterable_sr_data"
                    )
                    st.session_state.filterable_sr_data_cols_multiselect = selected_columns

                    if selected_columns:
                        st.dataframe(table_display_df[selected_columns], hide_index=True)
                    else:
                        st.dataframe(table_display_df[all_columns_for_display], hide_index=True)
                else:
                    st.info("No SR data to display based on current filters for Filterable SR Data.")

                st.markdown("---")
                st.subheader("Closed Service Requests")

                # Essential columns for this section (normalized)
                essential_cols_closed_sr_norm = [status_col_norm, last_mod_dt_col_norm]
                raw_names_essential_closed = ['Status', 'LastModDateTime'] # For error message
                missing_essential_closed_display = []

                for i, norm_col in enumerate(essential_cols_closed_sr_norm):
                    if norm_col not in sr_overview_df.columns: # Check original sr_overview_df
                        missing_essential_closed_display.append(raw_names_essential_closed[i])

                if missing_essential_closed_display:
                    st.warning(f"The uploaded SR data is missing the following essential column(s) for the Closed SRs table: {', '.join(missing_essential_closed_display)}. This table cannot be displayed.")
                else:
                    closed_sr_statuses_text = ["closed", "completed", "cancelled", "approval rejected", "rejected by ps"]
                    closed_srs_df = sr_overview_df[
                        sr_overview_df[status_col_norm].astype(str).str.lower().str.strip().isin(closed_sr_statuses_text)
                    ].copy()

                    closure_year_week_derived_col = 'closure_year_week_derived'
                    closed_srs_df[last_mod_dt_col_norm] = pd.to_datetime(closed_srs_df[last_mod_dt_col_norm], errors='coerce', dayfirst=True, infer_datetime_format=True)
                    closed_srs_df.dropna(subset=[last_mod_dt_col_norm], inplace=True)

                    if not closed_srs_df.empty:
                        closed_srs_df[closure_year_week_derived_col] = closed_srs_df[last_mod_dt_col_norm].dt.strftime('%G-W%V')
                    else:
                        closed_srs_df[closure_year_week_derived_col] = pd.Series(dtype='str')

                    closed_sr_week_map_for_filter = {}
                    closed_sr_week_options_for_multiselect = []
                    if not closed_srs_df.empty and closure_year_week_derived_col in closed_srs_df.columns:
                        unique_closed_week_options_df = closed_srs_df[[closure_year_week_derived_col]].copy()
                        unique_closed_week_options_df.dropna(subset=[closure_year_week_derived_col], inplace=True)
                        unique_closed_week_options_df['WeekDisplay'] = unique_closed_week_options_df[closure_year_week_derived_col].apply(_get_week_display_str)
                        unique_closed_week_options_df = unique_closed_week_options_df[[closure_year_week_derived_col, 'WeekDisplay']].drop_duplicates().sort_values(by=closure_year_week_derived_col)

                        closed_sr_week_options_for_multiselect = unique_closed_week_options_df['WeekDisplay'].tolist()
                        for _, row in unique_closed_week_options_df.iterrows():
                            closed_sr_week_map_for_filter[row['WeekDisplay']] = row[closure_year_week_derived_col]

                    col_filter_closed_sr1, col_filter_closed_sr2 = st.columns(2)

                    with col_filter_closed_sr1:
                        selected_week_displays_closed = st.multiselect(
                            "Filter Closed SRs by Closure Week Period:",
                            options=closed_sr_week_options_for_multiselect,
                            default=[],
                            key="closed_sr_closure_week_filter"
                        )

                    with col_filter_closed_sr2:
                        min_date_val_closed = None
                        max_date_val_closed = None
                        if last_mod_dt_col_norm in closed_srs_df.columns and not closed_srs_df[last_mod_dt_col_norm].dropna().empty:
                             min_date_val_closed = closed_srs_df[last_mod_dt_col_norm].min().date()
                             max_date_val_closed = closed_srs_df[last_mod_dt_col_norm].max().date()
                        selected_day_closed = st.date_input(
                            f"Filter Closed SRs by Specific Closure Day ({last_mod_dt_col_norm}):",
                            value=None, min_value=min_date_val_closed, max_value=max_date_val_closed,
                            key="closed_sr_closure_day_filter"
                        )

                    filtered_closed_srs_df = closed_srs_df.copy()

                    if selected_day_closed and last_mod_dt_col_norm in filtered_closed_srs_df.columns:
                        filtered_closed_srs_df = filtered_closed_srs_df[filtered_closed_srs_df[last_mod_dt_col_norm].dt.date == selected_day_closed]
                    elif selected_week_displays_closed and closure_year_week_derived_col in filtered_closed_srs_df.columns and closed_sr_week_map_for_filter:
                        selected_closure_year_weeks_short = [closed_sr_week_map_for_filter[wd] for wd in selected_week_displays_closed if wd in closed_sr_week_map_for_filter]
                        if selected_closure_year_weeks_short:
                            filtered_closed_srs_df = filtered_closed_srs_df[filtered_closed_srs_df[closure_year_week_derived_col].isin(selected_closure_year_weeks_short)]

                    st.markdown(f"**Total Displayed Closed SRs (filtered by closure date):** {len(filtered_closed_srs_df)}")

                    if not filtered_closed_srs_df.empty:
                        all_closed_columns_display = filtered_closed_srs_df.columns.tolist()
                        internal_cols_to_remove = [closure_year_week_derived_col, year_week_derived_col] # Remove both potential temp cols
                        for col_to_remove in internal_cols_to_remove:
                            if col_to_remove in all_closed_columns_display:
                                all_closed_columns_display.remove(col_to_remove)

                        # Default columns for this table using normalized names
                        default_closed_cols_raw = ['Service Request', 'Status', 'Created On', 'LastModDateTime', 'Resolution']
                        default_closed_cols_normalized = [
                            service_request_col_norm, status_col_norm, created_on_col_norm,
                            last_mod_dt_col_norm, resolution_col_norm
                        ]
                        sanitized_default_closed_cols = [col for col in default_closed_cols_normalized if col in all_closed_columns_display]

                        if 'closed_sr_data_cols_multiselect' not in st.session_state:
                            st.session_state.closed_sr_data_cols_multiselect = sanitized_default_closed_cols

                        selected_closed_columns = st.multiselect(
                            "Select columns to display for Closed SRs:",
                            options=all_closed_columns_display,
                            default=st.session_state.closed_sr_data_cols_multiselect,
                            key="multiselect_closed_sr_data"
                        )
                        st.session_state.closed_sr_data_cols_multiselect = selected_closed_columns

                        if selected_closed_columns:
                            st.dataframe(filtered_closed_srs_df[selected_closed_columns], hide_index=True)
                        else:
                            st.dataframe(filtered_closed_srs_df[all_closed_columns_display] if all_closed_columns_display else filtered_closed_srs_df, hide_index=True)

                        cols_for_download = selected_closed_columns if selected_closed_columns else all_closed_columns_display
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
