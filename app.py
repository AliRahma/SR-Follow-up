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
if 'report_datetime' not in st.session_state:
    st.session_state.report_datetime = None
if 'column_name_mapping' not in st.session_state: # Ensure it's initialized early
    st.session_state.column_name_mapping = {}

# Helper function to get DataFrame with original column names for display
def get_display_df(df_to_display: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a copy of the DataFrame with columns renamed to original names for display,
    using st.session_state.column_name_mapping.
    If mapping is not available or df is None, returns a copy of the original df.
    """
    if df_to_display is None:
        return None

    df_copy = df_to_display.copy()

    # Check if the mapping is available and not empty
    if hasattr(st.session_state, 'column_name_mapping') and st.session_state.column_name_mapping:
        # The stored mapping is {normalized: original}
        # We want to rename df_copy's columns (which are normalized) to their original versions.
        # So, we need a rename_map of {current_col_name (normalized): new_col_name (original)}
        # This is exactly what st.session_state.column_name_mapping provides.

        # Only rename columns that are present in the DataFrame AND in the mapping
        rename_map = {
            norm_col: orig_col
            for norm_col, orig_col in st.session_state.column_name_mapping.items()
            if norm_col in df_copy.columns
        }
        if rename_map:
            df_copy.rename(columns=rename_map, inplace=True)
    return df_copy

@st.cache_data
def load_data(file):
    if file is None:
        return None, None, None  # Return None for df, datetime, and mapping
    
    parsed_datetime_str = None
    df = None
    column_name_mapping = None

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
                    st.error(f"Error reading .xls file '{file.name}' with both xlrd and openpyxl: {e_openpyxl}")
                    return None, parsed_datetime_str, None
        elif file_extension == '.xlsx':
            df = pd.read_excel(file, engine='openpyxl')
        else:
            st.error(f"Unsupported file type: {file_extension}. Please upload .xls or .xlsx files.")
            return None, parsed_datetime_str, None

        if df is not None:
            original_columns = list(df.columns)
            normalized_columns = [str(col).lower().strip() for col in original_columns]

            # It's important that the mapping stores {normalized_name: original_name}
            # if we are renaming the DataFrame to use normalized names internally.
            # Or, if we want to lookup original names from normalized ones:
            # {normalized_name: original_name for original_name, normalized_name in zip(original_columns, normalized_columns)}
            # Let's store {normalized_name: original_name} for easier revert for display
            column_name_mapping = {norm_col: orig_col for norm_col, orig_col in zip(normalized_columns, original_columns)}

            # Create a reverse mapping to check for duplicate normalized names, which could be problematic.
            # If multiple original columns normalize to the same name, this needs careful handling.
            # For now, we'll assume distinct normalized names or take the first original name in case of conflict.
            df.columns = normalized_columns

            # Store the mapping in session state - this should be done *outside* load_data,
            # specifically when processing the main_df. load_data should return the mapping.
            # st.session_state.column_name_mapping = column_name_mapping # Moved out

        return df, parsed_datetime_str, column_name_mapping
            
    except Exception as e:
        st.error(f"Error loading file '{file.name}': {e}")
        return None, parsed_datetime_str, None # Return None for df and mapping, but parsed_datetime_str might have a value

# Function to process main dataframe
def process_main_df(df):
    # df.columns are already normalized by load_data
    # Ensure date columns are in datetime format using their normalized names
    # Assuming common normalizations; actual normalized names depend on input Excel
    
    # It's safer to iterate through expected original names, normalize them, and then check in df.columns
    expected_date_cols_original_case = ['Case Start Date', 'Last Note Date']
    for original_col_name in expected_date_cols_original_case:
        normalized_col_name = original_col_name.lower().strip()
        if normalized_col_name in df.columns:
            df[normalized_col_name] = pd.to_datetime(df[normalized_col_name], format="%d/%m/%Y", errors='coerce')

    # Extract all unique users - using normalized name
    normalized_user_id_col = 'current user id' # Assuming 'Current User Id' -> 'current user id'
    if normalized_user_id_col in df.columns:
        all_users = sorted(df[normalized_user_id_col].dropna().unique().tolist())
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
    if 'column_name_mapping' not in st.session_state: # Initialize if not present
        st.session_state.column_name_mapping = {}

    if uploaded_file:
        with st.spinner("Loading main data..."):
            # load_data now returns df, parsed_dt, column_mapping
            df, parsed_dt, col_map = load_data(uploaded_file)
            if df is not None:
                st.session_state.main_df = process_main_df(df)
                st.session_state.column_name_mapping = col_map # Store the mapping for the main file
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
            # SR file uses its own columns, no mapping needed here from main file's logic
            sr_df, parsed_dt_sr, _ = load_data(sr_status_file) # Ignore column_mapping for SR file
            if sr_df is not None:
                st.session_state.sr_df = sr_df
                st.success(f"SR status data loaded: {sr_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_sr:
                    st.session_state.report_datetime = parsed_dt_sr
            # else: df is None, error shown by load_data
    
    if incident_status_file:
        with st.spinner("Loading incident report data..."):
            # Incident file uses its own columns
            incident_df, parsed_dt_incident, _ = load_data(incident_status_file) # Ignore column_mapping
            if incident_df is not None:
                st.session_state.incident_df = incident_df
                st.success(f"Incident report data loaded: {incident_df.shape[0]} records")
                if st.session_state.report_datetime is None and parsed_dt_incident:
                    st.session_state.report_datetime = parsed_dt_incident

                # Process for Incident Overview tab (existing logic)
                # This part needs to be careful if incident_df columns were also normalized by load_data
                # For now, assuming incident_df from load_data has its columns as they are (original or normalized by load_data)
                # If load_data normalized them, then "Customer" might be "customer".
                # The requirement was for the "uploaded file" (main file), so auxiliary files might not need this.
                # Let's assume auxiliary files' columns are not subject to this specific mapping display logic for now.
                # If they ARE normalized by load_data, the rename below needs to use the normalized name.
                overview_df = incident_df.copy()
                # If incident_df columns are now normalized (e.g. 'customer'), this check needs to be 'customer'
                # And the rename should be to "Creator" (which is a new, fixed name, not from mapping)
                # Let's assume 'Customer' is the original name and if load_data normalized it, it would be 'customer'
                normalized_customer_col = 'customer' # Example if it gets normalized
                original_customer_col = 'Customer' # The original name we might expect

                # Check if the normalized version exists (if load_data normalizes all files)
                # or if the original version exists (if load_data only normalizes main file's df.columns)
                # Given load_data was changed to normalize columns for *any* df it processes,
                # we should check for the normalized 'customer'.
                if normalized_customer_col in overview_df.columns:
                    overview_df.rename(columns={normalized_customer_col: "Creator"}, inplace=True)
                elif original_customer_col in overview_df.columns: # Fallback if not normalized
                     overview_df.rename(columns={original_customer_col: "Creator"}, inplace=True)

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
        all_users = df_main['Current User Id'].dropna().unique().tolist()
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
        
        if 'Case Start Date' in df_main.columns:
            min_date = df_main['Case Start Date'].min().date()
            max_date = df_main['Case Start Date'].max().date()
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
    if st.session_state.selected_users:
        df_filtered = df_main[df_main['Current User Id'].isin(st.session_state.selected_users)].copy()
    else:
        df_filtered = df_main.copy()
    
    # Apply date filter if date range is selected
    if 'Case Start Date' in df_filtered.columns and 'date_range' in locals():
        start_date, end_date = date_range
        df_filtered = df_filtered[
            (df_filtered['Case Start Date'].dt.date >= start_date) & 
            (df_filtered['Case Start Date'].dt.date <= end_date)
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
        
        # Normalized column names (assuming common pattern, verify with actual Excel files)
        norm_last_note_col = 'last note'
        norm_case_start_date_col = 'case start date'
        norm_last_note_date_col = 'last note date'
        norm_ticket_number_col = 'ticket number' # This column is created by classify_and_extract
        norm_type_col = 'type' # This column is created by classify_and_extract
        norm_breach_date_col = 'breach date' # If this column exists in the input

        # Classify and extract ticket info
        if norm_last_note_col in df_enriched.columns:
            # classify_and_extract returns 'Triage Status', 'Ticket Number', 'Type'
            # These new columns should also be considered "normalized" in their naming convention (e.g. lowercase)
            # For consistency, ensure classify_and_extract returns names that don't need re-normalization,
            # or adjust here. Assuming classify_and_extract's output names are fine as is.
            # Let's ensure the new columns are lowercase and spaced if needed.
            # However, the current classify_and_extract creates 'Triage Status', 'Ticket Number', 'Type'.
            # We will use these as is, and they are not part of the original Excel mapping.
            new_cols_from_classify = ['Triage Status', 'Ticket Number', 'Type']
            df_enriched[new_cols_from_classify] = pd.DataFrame(
                df_enriched[norm_last_note_col].apply(lambda x: pd.Series(classify_and_extract(x)))
            )
        else:
            df_enriched['Triage Status'] = "Error: Last Note missing"
            df_enriched['Ticket Number'] = None
            df_enriched['Type'] = None

        # Calculate case age
        if norm_case_start_date_col in df_enriched.columns:
            df_enriched['Age (Days)'] = df_enriched[norm_case_start_date_col].apply(calculate_age)
        else:
            df_enriched['Age (Days)'] = None

        # Determine if note was created today
        if norm_last_note_date_col in df_enriched.columns:
            df_enriched['Created Today'] = df_enriched[norm_last_note_date_col].apply(is_created_today)
        else:
            df_enriched['Created Today'] = False
        
        # Initialize Status, Last Update, and Breach Passed columns
        # These are new columns, not from original Excel, so their names are fixed.
        df_enriched['Status'] = None
        df_enriched['Last Update'] = None
        df_enriched['Breach Passed'] = None # This is a boolean based on SR/Incident file
        
        # Ensure 'Ticket Number' (newly created column) is numeric before any merges
        # This 'Ticket Number' is the one derived from 'Last Note', not necessarily from an Excel column.
        if 'Ticket Number' in df_enriched.columns: # This is the column created by classify_and_extract
            df_enriched['Ticket Number'] = pd.to_numeric(df_enriched['Ticket Number'], errors='coerce')

        # Merge with SR status data if available
        # sr_df columns are also normalized by load_data if it went through it.
        # We need to assume normalized names for sr_df as well.
        if hasattr(st.session_state, 'sr_df') and st.session_state.sr_df is not None:
            sr_df_copy = st.session_state.sr_df.copy() # sr_df_copy has normalized column names
            
            norm_sr_service_request_col = 'service request' # Normalized name in sr_df
            norm_sr_status_col = 'status'
            norm_sr_last_mod_col = 'lastmoddatetime'
            norm_sr_breach_passed_col = 'breach passed'


            if norm_sr_service_request_col in sr_df_copy.columns:
                sr_df_copy[norm_sr_service_request_col] = sr_df_copy[norm_sr_service_request_col].astype(str).str.extract(r'(\d{4,})')
                sr_df_copy[norm_sr_service_request_col] = pd.to_numeric(sr_df_copy[norm_sr_service_request_col], errors='coerce')
                sr_df_copy.dropna(subset=[norm_sr_service_request_col], inplace=True)

                cols_to_merge_from_sr = [norm_sr_service_request_col]
                sr_rename_for_merge = {}

                if norm_sr_status_col in sr_df_copy.columns:
                    sr_rename_for_merge[norm_sr_status_col] = 'SR_Status_temp'
                if norm_sr_last_mod_col in sr_df_copy.columns:
                    sr_rename_for_merge[norm_sr_last_mod_col] = 'SR_Last_Update_temp'
                if norm_sr_breach_passed_col in sr_df_copy.columns: # Check for normalized 'breach passed'
                    sr_rename_for_merge[norm_sr_breach_passed_col] = 'SR_Breach_Value_temp'

                sr_df_copy.rename(columns=sr_rename_for_merge, inplace=True)

                for new_name in sr_rename_for_merge.values():
                    if new_name not in cols_to_merge_from_sr and new_name in sr_df_copy.columns: # Ensure renamed col exists
                        cols_to_merge_from_sr.append(new_name)

                # df_enriched['Ticket Number'] is the target for merge (from classify_and_extract)
                # sr_df_copy[norm_sr_service_request_col] is the source for merge
                df_enriched = df_enriched.merge(
                    sr_df_copy[cols_to_merge_from_sr],
                    how='left',
                    left_on='Ticket Number', # This 'Ticket Number' is from classify_and_extract
                    right_on=norm_sr_service_request_col, # Use the normalized name from sr_df_copy
                    suffixes=('', '_sr_merged')
                )

                # Clean up merge artifacts
                if f"{norm_sr_service_request_col}_sr_merged" in df_enriched.columns:
                    df_enriched.drop(columns=[f"{norm_sr_service_request_col}_sr_merged"], inplace=True)
                # If original norm_sr_service_request_col still exists due to no suffix, and it's not the Ticket Number col
                elif norm_sr_service_request_col in df_enriched.columns and norm_sr_service_request_col != 'Ticket Number':
                     df_enriched.drop(columns=[norm_sr_service_request_col], errors='ignore', inplace=True)


                sr_mask = df_enriched['Type'] == 'SR' # 'Type' is from classify_and_extract

                if 'SR_Status_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, 'Status'] = df_enriched.loc[sr_mask, 'SR_Status_temp'] # 'Status' is a new fixed name col
                    df_enriched.drop(columns=['SR_Status_temp'], inplace=True)
                if 'SR_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, 'Last Update'] = df_enriched.loc[sr_mask, 'SR_Last_Update_temp'] # 'Last Update' is new
                    df_enriched.drop(columns=['SR_Last_Update_temp'], inplace=True)

                if 'SR_Breach_Value_temp' in df_enriched.columns:
                    def map_str_to_bool_sr(value):
                        if pd.isna(value): return None
                        val_lower = str(value).lower()
                        if val_lower in ['yes', 'true', '1', 'passed'] : return True
                        if val_lower in ['no', 'false', '0', 'failed']: return False
                        return None

                    mapped_values = df_enriched.loc[sr_mask, 'SR_Breach_Value_temp'].apply(map_str_to_bool_sr)
                    df_enriched.loc[sr_mask, 'Breach Passed'] = mapped_values # 'Breach Passed' is new
                    df_enriched.drop(columns=['SR_Breach_Value_temp'], inplace=True)

        # Merge with Incident status data if available
        # incident_df columns are also normalized by load_data.
        if hasattr(st.session_state, 'incident_df') and st.session_state.incident_df is not None:
            incident_df_copy = st.session_state.incident_df.copy() # Has normalized columns

            # Try to find the normalized version of incident ID column
            incident_id_col_options_original = ['Incident', 'Incident ID', 'IncidentID', 'ID', 'Number']
            incident_id_col_normalized_found = None
            for col_option in incident_id_col_options_original:
                norm_opt = col_option.lower().strip()
                if norm_opt in incident_df_copy.columns:
                    incident_id_col_normalized_found = norm_opt
                    break
            
            if incident_id_col_normalized_found:
                incident_df_copy[incident_id_col_normalized_found] = incident_df_copy[incident_id_col_normalized_found].astype(str).str.extract(r'(\d{4,})')
                incident_df_copy[incident_id_col_normalized_found] = pd.to_numeric(incident_df_copy[incident_id_col_normalized_found], errors='coerce')
                incident_df_copy.dropna(subset=[incident_id_col_normalized_found], inplace=True)
                
                inc_rename_map = {incident_id_col_normalized_found: 'Incident_Number_temp'}
                inc_merge_cols = ['Incident_Number_temp']

                norm_inc_status_col = 'status' # Normalized name for status in incident_df
                if norm_inc_status_col in incident_df_copy.columns:
                    inc_rename_map[norm_inc_status_col] = 'INC_Status_temp'
                    inc_merge_cols.append('INC_Status_temp')

                # Normalized names for last update columns in incident_df
                last_update_col_options_original = ['Last Checked at', 'Last Checked atc', 'Modified On', 'Last Update']
                last_update_col_normalized_found = None
                for col_option in last_update_col_options_original:
                    norm_opt = col_option.lower().strip()
                    if norm_opt in incident_df_copy.columns:
                        last_update_col_normalized_found = norm_opt
                        break
                if last_update_col_normalized_found:
                    inc_rename_map[last_update_col_normalized_found] = 'INC_Last_Update_temp'
                    inc_merge_cols.append('INC_Last_Update_temp')

                norm_inc_breach_passed_col = 'breach passed' # Normalized name for breach in incident_df
                if norm_inc_breach_passed_col in incident_df_copy.columns:
                    inc_rename_map[norm_inc_breach_passed_col] = 'INC_Breach_Passed_temp'
                    inc_merge_cols.append('INC_Breach_Passed_temp')

                incident_df_copy.rename(columns=inc_rename_map, inplace=True)
                
                # Ensure all columns in inc_merge_cols actually exist in incident_df_copy after rename
                inc_merge_cols = [col for col in inc_merge_cols if col in incident_df_copy.columns]

                df_enriched = df_enriched.merge(
                    incident_df_copy[inc_merge_cols],
                    how='left',
                    left_on='Ticket Number', # From classify_and_extract
                    right_on='Incident_Number_temp', # Temp column from incident_df_copy
                    suffixes=('', '_inc_merged')
                )

                if 'Incident_Number_temp_inc_merged' in df_enriched.columns:
                     df_enriched.drop(columns=['Incident_Number_temp_inc_merged'], inplace=True)
                elif 'Incident_Number_temp' in df_enriched.columns :
                     df_enriched.drop(columns=['Incident_Number_temp'], inplace=True, errors='ignore')

                incident_mask = df_enriched['Type'] == 'Incident' # 'Type' from classify_and_extract
                
                if 'INC_Status_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, 'Status'] = df_enriched.loc[incident_mask, 'INC_Status_temp'] # 'Status' is new
                    df_enriched.drop(columns=['INC_Status_temp'], inplace=True)
                if 'INC_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[incident_mask, 'Last Update'] = df_enriched.loc[incident_mask, 'INC_Last_Update_temp'] # 'Last Update' is new
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
                    df_enriched.loc[incident_mask, 'Breach Passed'] = mapped_inc_breach_values # 'Breach Passed' is new
                    df_enriched.drop(columns=['INC_Breach_Passed_temp'], inplace=True)

        # 'Last Update' is a new column, convert to datetime
        if 'Last Update' in df_enriched.columns:
            df_enriched['Last Update'] = pd.to_datetime(df_enriched['Last Update'], errors='coerce')

        # If 'breach date' (normalized) exists in the original df_enriched (from main excel)
        if norm_breach_date_col in df_enriched.columns:
            df_enriched[norm_breach_date_col] = pd.to_datetime(df_enriched[norm_breach_date_col], errors='coerce')

        # 'Ticket Number' and 'Type' are from classify_and_extract
        if 'Ticket Number' in df_enriched.columns and 'Type' in df_enriched.columns:
            valid_ticket_mask = df_enriched['Ticket Number'].notna() & df_enriched['Type'].notna()
            if valid_ticket_mask.any():
                 df_enriched.loc[valid_ticket_mask, 'Case Count'] = df_enriched[valid_ticket_mask].groupby(['Ticket Number', 'Type'])['Ticket Number'].transform('size')
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
        
        # Filtering options - df_enriched has normalized columns
        col1, col2,col3 = st.columns(3)
        
        with col1:
            # 'Triage Status' is a column created by enrich_data, not from original Excel.
            # So its name is fixed and does not need mapping for display of filter options.
            status_filter = st.selectbox(
                "Filter by Triage Status",
                ["All"] + df_enriched["Triage Status"].dropna().unique().tolist()
            )
        
        with col2:
            # 'Type' is also from enrich_data.
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "SR", "Incident"]
            )
        
        with col3:
            # 'Status' is also from enrich_data.
            if 'Status' in df_enriched.columns:
                status_options = ["All"] + df_enriched['Status'].dropna().unique().tolist() + ["None"]
                unified_status_filter = st.selectbox("Filter by Status", status_options)
            else:
                unified_status_filter = "All"
        
        # Apply filters to df_enriched (which has normalized columns)
        df_display_internal = df_enriched.copy() # Internal representation for filtering
        
        if status_filter != "All":
            df_display_internal = df_display_internal[df_display_internal["Triage Status"] == status_filter]
        
        if type_filter != "All":
            df_display_internal = df_display_internal[df_display_internal["Type"] == type_filter]
        
        if unified_status_filter != "All":
            if unified_status_filter == "None":
                df_display_internal = df_display_internal[df_display_internal["Status"].isna()]
            else:
                df_display_internal = df_display_internal[df_display_internal["Status"] == unified_status_filter]
        
        # Statistics and summary
        st.subheader("📊 Summary Analysis")
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.markdown("**🔸 Triage Status Count**")
            # 'Triage Status' is from enrich_data, fixed name.
            triage_summary = df_enriched['Triage Status'].value_counts().rename_axis('Triage Status').reset_index(name='Count')
            triage_total = {'Triage Status': 'Total', 'Count': triage_summary['Count'].sum()}
            triage_df_for_display = pd.concat([triage_summary, pd.DataFrame([triage_total])], ignore_index=True)
            # This df is simple, no mapping needed as columns are 'Triage Status', 'Count'
            st.dataframe(
                triage_df_for_display.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(triage_df_for_display)-1 else '' for _ in x],
                    axis=1
                )
            )
        with summary_col2:
            st.markdown("**🔹 SR vs Incident Count**")
            # 'Type' is from enrich_data, fixed name.
            type_summary = df_enriched['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
            type_total = {'Type': 'Total', 'Count': type_summary['Count'].sum()}
            type_df_for_display = pd.concat([type_summary, pd.DataFrame([type_total])], ignore_index=True)
            # Simple df, no mapping needed.
            st.dataframe(
                type_df_for_display.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(type_df_for_display)-1 else '' for _ in x],
                    axis=1
                )
            )

        summary_col3, summary_col4 = st.columns(2)
        with summary_col3:
            st.markdown("**🟢 SR Status Summary**")
            # 'Status', 'Type', 'Ticket Number' are from enrich_data or SR file processing; not main Excel mapping.
            if 'Status' in df_enriched.columns and 'Type' in df_enriched.columns and not df_enriched[df_enriched['Type'] == 'SR'].empty:
                df_srs = df_enriched[df_enriched['Type'] == 'SR'].copy()
                df_srs_status_valid = df_srs.dropna(subset=['Status'])
                if not df_srs_status_valid.empty:
                    status_all_counts = df_srs_status_valid['Status'].value_counts().rename_axis('Status').reset_index(name='All Count')
                    ticket_unique = df_srs_status_valid.dropna(subset=['Ticket Number'])[['Ticket Number', 'Status']].drop_duplicates()
                    ticket_unique_counts = ticket_unique['Status'].value_counts().rename_axis('Status').reset_index(name='Unique Count')
                    merged_status = pd.merge(status_all_counts, ticket_unique_counts, on='Status', how='outer').fillna(0)
                    merged_status[['All Count', 'Unique Count']] = merged_status[['All Count', 'Unique Count']].astype(int)
                    total_row = {'Status': 'Total', 'All Count': merged_status['All Count'].sum(), 'Unique Count': merged_status['Unique Count'].sum()}
                    status_summary_df_for_display = pd.concat([merged_status, pd.DataFrame([total_row])], ignore_index=True)
                    st.dataframe(
                        status_summary_df_for_display.style.apply(
                            lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(status_summary_df_for_display)-1 else '' for _ in x],
                            axis=1
                        )
                    )
                else: st.info("No SRs with status information available.")
            else: st.info("Upload SR Status Excel file to view SR Status Summary.")

        with summary_col4:
            st.markdown("**🟣 Incident Status Summary**")
            if 'Status' in df_enriched.columns and 'Type' in df_enriched.columns and not df_enriched[df_enriched['Type'] == 'Incident'].empty:
                df_incidents = df_enriched[df_enriched['Type'] == 'Incident'].copy()
                df_incidents_status_valid = df_incidents.dropna(subset=['Status'])
                if not df_incidents_status_valid.empty:
                    incident_status_all_counts = df_incidents_status_valid['Status'].value_counts().rename_axis('Status').reset_index(name='Cases Count')
                    incident_ticket_unique = df_incidents_status_valid.dropna(subset=['Ticket Number'])[['Ticket Number', 'Status']].drop_duplicates()
                    incident_ticket_unique_counts = incident_ticket_unique['Status'].value_counts().rename_axis('Status').reset_index(name='Unique Count')
                    merged_incident_status = pd.merge(incident_status_all_counts, incident_ticket_unique_counts, on='Status', how='outer').fillna(0)
                    merged_incident_status[['Cases Count', 'Unique Count']] = merged_incident_status[['Cases Count', 'Unique Count']].astype(int)
                    incident_total_row = {'Status': 'Total', 'Cases Count': merged_incident_status['Cases Count'].sum(), 'Unique Count': merged_incident_status['Unique Count'].sum()}
                    incident_status_summary_df_for_display = pd.concat([merged_incident_status, pd.DataFrame([incident_total_row])], ignore_index=True)
                    st.dataframe(
                        incident_status_summary_df_for_display.style.apply(
                            lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(incident_status_summary_df_for_display)-1 else '' for _ in x],
                            axis=1
                        )
                    )
                else: st.info("No incidents with status information available to summarize.")
            elif st.session_state.incident_df is None: st.info("Upload Incident Report Excel file to view Incident Status Summary.")
            else: st.info("No incident data available to summarize.")
        
        st.subheader("📋 Filtered Results")
        results_col1, results_col2 = st.columns([3, 1])
        with results_col1:
            st.markdown(f"**Total Filtered Records:** {df_display_internal.shape[0]}")
        
        with results_col2:
            if not df_display_internal.empty:
                excel_data = generate_excel_download(
                    df_display_internal,
                    column_mapping=st.session_state.get('column_name_mapping')
                )
                st.download_button(
                    label="📥 Download Results",
                    data=excel_data,
                    file_name=f"sr_incident_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        if not df_display_internal.empty:
            df_for_multiselect_options = get_display_df(df_display_internal) # Get original names for options
            all_original_columns = df_for_multiselect_options.columns.tolist()
            SELECT_ALL_COLS_ANALYSIS_OPTION = "[Select All Columns]"

            # Default columns should be original names for display in widget
            # Mapping: {norm_col: orig_col}
            # Reverse mapping: {orig_col: norm_col}
            reverse_map = {v: k for k, v in st.session_state.column_name_mapping.items()}

            default_selected_normalized_cols = ['last note', 'case id', 'current user id', 'case start date', 'Triage Status', 'Type', 'Ticket Number']
            if 'Status' in df_display_internal.columns: default_selected_normalized_cols.extend(['Status', 'Last Update'])
            if 'Breach Passed' in df_display_internal.columns: default_selected_normalized_cols.append('Breach Passed')

            # Convert default normalized names to original names for the widget's default
            default_selected_original_cols = []
            for norm_col in default_selected_normalized_cols:
                if norm_col in st.session_state.column_name_mapping: # Mapped from Excel
                    default_selected_original_cols.append(st.session_state.column_name_mapping[norm_col])
                elif norm_col in all_original_columns: # Fixed name, already original-like
                    default_selected_original_cols.append(norm_col)

            # Ensure default_selected_original_cols only contains valid columns from all_original_columns
            default_selected_original_cols = [col for col in default_selected_original_cols if col in all_original_columns]

            if 'analysis_tab_column_widget_selection_controlled' not in st.session_state:
                st.session_state.selected_display_cols_orig_names = list(default_selected_original_cols)
                if not default_selected_original_cols and all_original_columns:
                    st.session_state.selected_display_cols_orig_names = list(all_original_columns)
                    st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                elif all_original_columns and set(default_selected_original_cols) == set(all_original_columns):
                    st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
                elif not all_original_columns:
                    st.session_state.selected_display_cols_orig_names = []
                    st.session_state.analysis_tab_column_widget_selection_controlled = []
                else:
                    st.session_state.analysis_tab_column_widget_selection_controlled = list(default_selected_original_cols)

            options_for_cols_widget = [SELECT_ALL_COLS_ANALYSIS_OPTION] + all_original_columns
            raw_cols_widget_selection_original_names = st.multiselect( # This returns selected original names
                "Select columns to display:",
                options=options_for_cols_widget,
                default=st.session_state.analysis_tab_column_widget_selection_controlled,
                key="multi_select_analysis_columns"
            )

            # Logic for "Select All" options (operates on original names from widget)
            prev_widget_display_state_orig = list(st.session_state.analysis_tab_column_widget_selection_controlled)
            current_select_all_opt_selected_orig = SELECT_ALL_COLS_ANALYSIS_OPTION in raw_cols_widget_selection_original_names
            currently_selected_actual_items_orig = [c for c in raw_cols_widget_selection_original_names if c != SELECT_ALL_COLS_ANALYSIS_OPTION]

            user_clicked_select_all_orig = current_select_all_opt_selected_orig and (SELECT_ALL_COLS_ANALYSIS_OPTION not in prev_widget_display_state_orig)
            user_clicked_unselect_all_orig = (not current_select_all_opt_selected_orig) and (SELECT_ALL_COLS_ANALYSIS_OPTION in prev_widget_display_state_orig and len(prev_widget_display_state_orig) == 1)

            if user_clicked_select_all_orig:
                st.session_state.selected_display_cols_orig_names = list(all_original_columns)
                st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION]
            elif user_clicked_unselect_all_orig:
                st.session_state.selected_display_cols_orig_names = []
                st.session_state.analysis_tab_column_widget_selection_controlled = []
            else: # Regular selection changes
                if current_select_all_opt_selected_orig: # Select All is checked
                    if len(currently_selected_actual_items_orig) < len(all_original_columns): # But not all items are actually selected
                        st.session_state.selected_display_cols_orig_names = list(currently_selected_actual_items_orig)
                        st.session_state.analysis_tab_column_widget_selection_controlled = list(currently_selected_actual_items_orig) # Uncheck "Select All"
                    else: # All items are selected
                        st.session_state.selected_display_cols_orig_names = list(all_original_columns)
                        st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION] # Keep "Select All"
                else: # Select All is not checked
                    st.session_state.selected_display_cols_orig_names = list(currently_selected_actual_items_orig)
                    if all_original_columns and set(currently_selected_actual_items_orig) == set(all_original_columns):
                        st.session_state.analysis_tab_column_widget_selection_controlled = [SELECT_ALL_COLS_ANALYSIS_OPTION] # Auto-check "Select All"
                    else:
                        st.session_state.analysis_tab_column_widget_selection_controlled = list(currently_selected_actual_items_orig)

            # Convert selected original names back to normalized names for slicing df_display_internal
            selected_normalized_cols_for_slicing = []
            for orig_col_name in st.session_state.selected_display_cols_orig_names:
                if orig_col_name in reverse_map: # Mapped from Excel
                    selected_normalized_cols_for_slicing.append(reverse_map[orig_col_name])
                elif orig_col_name in df_display_internal.columns: # Fixed name, already normalized-like
                     selected_normalized_cols_for_slicing.append(orig_col_name)

            if not selected_normalized_cols_for_slicing and all_original_columns: # If selection is empty, show all
                 selected_normalized_cols_for_slicing = df_display_internal.columns.tolist()


            if selected_normalized_cols_for_slicing:
                df_to_show_in_st_dataframe = get_display_df(df_display_internal[selected_normalized_cols_for_slicing])
                st.dataframe(df_to_show_in_st_dataframe, hide_index=True)
            else:
                st.info("Please select at least one column to display, or all columns will be shown if columns are available.")

        elif df_display_internal.empty:
            st.info("No data to display based on current filters.")
        else:
            st.info("No columns available to display.")

        st.subheader("🔗 Incidents/SRs Linked Cases Summary")
        min_linked_cases = st.number_input("Minimum Linked Cases", min_value=1, value=2, step=1)
        # 'Case Count', 'Ticket Number', 'Type', 'Status' are from enrich_data or processing, not direct Excel mapping for display.
        if 'Case Count' in df_display_internal.columns and 'Ticket Number' in df_display_internal.columns:
            linked_cases_df_internal = df_display_internal[
                (df_display_internal['Case Count'] >= min_linked_cases) &
                (df_display_internal['Ticket Number'].notna())
            ]
            if not linked_cases_df_internal.empty:
                linked_summary_df_internal = linked_cases_df_internal[['Ticket Number', 'Type','Status', 'Case Count']].drop_duplicates().sort_values(by='Case Count', ascending=False)
                # These columns are fixed, no get_display_df needed unless they clash with main excel names.
                st.dataframe(linked_summary_df_internal, hide_index=True)
            else:
                st.info(f"No Incidents/SRs found with at least {min_linked_cases} linked cases based on current filters.")
        else:
            st.warning("Required columns ('Case Count', 'Ticket Number') not available for linked cases summary.")

        st.subheader("📝 Note Details")
        # df_display_internal has 'case id' (normalized). We need original 'Case Id' for selectbox options if it's different.
        # However, Case ID is usually clean. Let's assume 'case id' is fine for selectbox value.
        # The displayed label of 'case id' in the table later will be handled by get_display_df.
        norm_case_id_col = 'case id'
        case_id_options = []
        if norm_case_id_col in df_display_internal.columns:
            case_id_options = df_display_internal[norm_case_id_col].tolist()

        selected_case_norm_id = st.selectbox( # This will show the normalized case id if not mapped
            "Select a case to view notes:",
            case_id_options
        )
        
        if selected_case_norm_id:
            # case_row_internal has normalized column names
            case_row_internal = df_display_internal[df_display_internal[norm_case_id_col] == selected_case_norm_id].iloc[0]
            
            # Prepare data for st.table, using original names for "Field"
            # And values from case_row_internal (which uses normalized keys)
            # The mapping st.session_state.column_name_mapping is {normalized: original}
            
            details_list = []
            details_list.append({"Field": st.session_state.column_name_mapping.get(norm_case_id_col, norm_case_id_col), "Value": case_row_internal[norm_case_id_col]})

            norm_user_id_col = 'current user id'
            details_list.append({"Field": st.session_state.column_name_mapping.get(norm_user_id_col, norm_user_id_col), "Value": case_row_internal[norm_user_id_col]})

            norm_case_start_date_col = 'case start date'
            details_list.append({"Field": st.session_state.column_name_mapping.get(norm_case_start_date_col, norm_case_start_date_col), "Value": case_row_internal[norm_case_start_date_col].strftime('%Y-%m-%d') if pd.notna(case_row_internal[norm_case_start_date_col]) else 'N/A'})

            details_list.append({"Field": "Age (Days)", "Value": f"{case_row_internal['Age (Days)']} days" if pd.notna(case_row_internal['Age (Days)']) else 'N/A'}) # Fixed name
            details_list.append({"Field": "Ticket Number", "Value": int(case_row_internal['Ticket Number']) if not pd.isna(case_row_internal['Ticket Number']) else 'N/A'}) # Fixed name
            details_list.append({"Field": "Type", "Value": case_row_internal['Type'] if not pd.isna(case_row_internal['Type']) else 'N/A'}) # Fixed name
            
            if 'Status' in case_row_internal and not pd.isna(case_row_internal['Status']): # Fixed name
                details_list.append({"Field": "Status", "Value": case_row_internal['Status']})
                if 'Last Update' in case_row_internal and not pd.isna(case_row_internal['Last Update']): # Fixed name
                    details_list.append({"Field": "Last Update", "Value": case_row_internal['Last Update']})
                if 'Breach Passed' in case_row_internal: # Fixed name
                    details_list.append({"Field": "SLA Breach", "Value": "Yes ⚠️" if case_row_internal['Breach Passed'] == True else "No"})

            st.table(pd.DataFrame(details_list))
            
            st.markdown("### Last Note")
            norm_last_note_col = 'last note'
            if norm_last_note_col in case_row_internal and not pd.isna(case_row_internal[norm_last_note_col]):
                st.text_area("Note Content", case_row_internal[norm_last_note_col], height=200)
            else:
                st.info("No notes available for this case")
            
            excel_data_case = generate_excel_download(
                df_display_internal[df_display_internal[norm_case_id_col] == selected_case_norm_id],
                column_mapping=st.session_state.get('column_name_mapping')
            )
            st.download_button(
                label="📥 Download Case Details",
                data=excel_data_case,
                file_name=f"case_{selected_case_norm_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
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
                        excel_breach_data = generate_excel_download(
                            breach_display,
                            column_mapping=st.session_state.get('column_name_mapping')
                            )
                        st.download_button(
                            label="📥 Download Breach Analysis",
                            data=excel_breach_data,
                            file_name=f"sla_breach_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Breach data table
                    breach_cols = ['Case Id', 'Current User Id', 'Case Start Date', 'Type', 'Ticket Number', 'Status', 'Last Update', 'Age (Days)']
                    breach_display_cols = [col for col in breach_cols if col in breach_display.columns]
                    
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
        if not today_sr_incidents.empty:
            st.subheader("👥 Breakdown by User")
            
            user_breakdown = today_sr_incidents.groupby('Current User Id').agg({
                'Case Id': 'count',
                'Type': lambda x: (x == 'SR').sum(),
                'Ticket Number': lambda x: (today_sr_incidents.loc[x.index, 'Type'] == 'Incident').sum()
            }).rename(columns={
                'Case Id': 'Total',
                'Type': 'SRs',
                'Ticket Number': 'Incidents'
            })
            
            user_breakdown = user_breakdown.reset_index()
            
            # Add total row
            total_row = pd.DataFrame({
                'Current User Id': ['TOTAL'],
                'Total': [user_breakdown['Total'].sum()],
                'SRs': [user_breakdown['SRs'].sum()],
                'Incidents': [user_breakdown['Incidents'].sum()]
            })
            
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
            
            with today_col1:
                today_user_filter = st.selectbox(
                    "Filter by User (Today)",
                    ["All"] + today_sr_incidents['Current User Id'].unique().tolist(),
                    key="today_user"
                )
            
            with today_col2:
                today_type_filter = st.selectbox(
                    "Filter by Type (Today)",
                    ["All", "SR", "Incident"],
                    key="today_type"
                )
            
            # Apply today's filters
            today_display = today_sr_incidents.copy()
            
            if today_user_filter != "All":
                today_display = today_display[today_display["Current User Id"] == today_user_filter]
            
            if today_type_filter != "All":
                today_display = today_display[today_display["Type"] == today_type_filter]
            
            # Display today's results
            st.subheader("📋 Today's Details")
            
            results_today_col1, results_today_col2 = st.columns([3, 1])
            
            with results_today_col1:
                st.markdown(f"**Filtered Records:** {today_display.shape[0]}")
            
            with results_today_col2:
                if not today_display.empty:
                    excel_today_data = generate_excel_download(
                        today_display,
                        column_mapping=st.session_state.get('column_name_mapping')
                        )
                    st.download_button(
                        label="📥 Download Today's Data",
                        data=excel_today_data,
                        file_name=f"todays_sr_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Today's data table
            today_cols = ['Case Id', 'Current User Id', 'Last Note Date', 'Type', 'Ticket Number']
            if 'Status' in today_display.columns:
                today_cols.extend(['Status', 'Last Update'])
            
            today_display_cols = [col for col in today_cols if col in today_display.columns]
            
            if not today_display.empty:
                st.dataframe(today_display[today_display_cols], hide_index=True)
            else:
                st.info("No records match the selected filters for today.")
                
        else:
            st.info("No new SR/Incidents found for today.")
            
            # Show all today's cases (not just SR/Incidents)
            if not today_cases.empty:
                st.subheader("📝 All Today's Cases")
                st.markdown(f"**Total cases with notes today:** {len(today_cases)}")
                
                all_today_cols = ['Case Id', 'Current User Id', 'Last Note Date', 'Triage Status']
                all_today_display_cols = [col for col in all_today_cols if col in today_cases.columns]
                
                st.dataframe(today_cases[all_today_display_cols], hide_index=True)
                
                # Download button for all today's cases
                excel_all_today_data = generate_excel_download(
                    today_cases,
                    column_mapping=st.session_state.get('column_name_mapping')
                    )
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
        # This tab uses st.session_state.incident_overview_df
        # This df is created from incident_status_file.
        # load_data normalizes its columns. The renaming of 'Customer' to 'Creator'
        # already considers this (checks for 'customer' then 'Customer').
        # Other columns like 'Team', 'Priority', 'Status', 'Incident' are used.
        # For display in tables here, we should use their current names as they are
        # not derived from the main excel file's mapping.
        # The user's request was about the "uploaded file" (main file) names.
        # So, no get_display_df calls are strictly needed here unless these column names
        # also need to revert to some original form from the incident_status_file itself,
        # which would require a separate mapping for that file.
        # Assuming for now this tab's display is fine with the (potentially normalized by load_data)
        # column names from the incident_status_file.

        SELECT_ALL_BASE_STRING = "[Select All %s]"

        if 'incident_overview_df' not in st.session_state or st.session_state.incident_overview_df is None or st.session_state.incident_overview_df.empty:
            st.warning(
                "The 'Incident Report Excel' has not been uploaded or is missing the required columns "
                "(e.g., 'Creator' (or 'Customer'), 'Incident', 'Team', 'Priority', 'Status'). "
                "Please upload the correct file via the sidebar to view the Incident Overview."
            )
        else:
            overview_df_internal = st.session_state.incident_overview_df.copy() # Has normalized or fixed names

            st.subheader("Filter Incidents")
            col1, col2, col3, col4 = st.columns(4)

            # For these filters, we use the column names as they are in overview_df_internal.
            # E.g., 'Creator' (if renamed from 'customer'), 'Team', 'Priority', 'Status'.
            # These are not subject to the main file's original name mapping.
            with col1:
                if 'Creator' in overview_df_internal.columns: # Fixed name 'Creator'
                    unique_creators = sorted(overview_df_internal['Creator'].dropna().unique())
                else: unique_creators = []
                SELECT_ALL_CREATORS_OPTION = SELECT_ALL_BASE_STRING % "Creators"
                if 'incident_creator_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_creators = list(unique_creators)
                    st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION] if unique_creators else []
                options_for_creator_widget = [SELECT_ALL_CREATORS_OPTION] + unique_creators
                raw_creator_widget_selection = st.multiselect("Filter by Creator", options=options_for_creator_widget, default=st.session_state.incident_creator_widget_selection_controlled, key="multi_select_incident_creator")
                # ... (rest of multiselect logic for creators - unchanged as it operates on 'Creator' name)
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
                        if len(currently_selected_actual_items) < len(unique_creators): st.session_state.selected_creators = list(currently_selected_actual_items); st.session_state.incident_creator_widget_selection_controlled = list(currently_selected_actual_items)
                        else: st.session_state.selected_creators = list(unique_creators); st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                    else:
                        st.session_state.selected_creators = list(currently_selected_actual_items)
                        if unique_creators and set(currently_selected_actual_items) == set(unique_creators): st.session_state.incident_creator_widget_selection_controlled = [SELECT_ALL_CREATORS_OPTION]
                        else: st.session_state.incident_creator_widget_selection_controlled = list(currently_selected_actual_items)

            with col2: # Filter by 'Team'
                norm_team_col_inc = 'team' # Assuming normalized name
                if norm_team_col_inc in overview_df_internal.columns:
                    unique_teams = sorted(overview_df_internal[norm_team_col_inc].dropna().unique())
                else: unique_teams = []
                SELECT_ALL_TEAMS_OPTION = SELECT_ALL_BASE_STRING % "Teams"
                default_teams_to_select = ["GPSSA App Team L1", "GPSSA App Team L3"] # These are values, not column names
                if 'incident_team_widget_selection_controlled' not in st.session_state:
                    actual_default_teams = [team for team in default_teams_to_select if team in unique_teams]
                    if actual_default_teams: st.session_state.selected_teams = list(actual_default_teams); st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION] if unique_teams and set(actual_default_teams) == set(unique_teams) else list(actual_default_teams)
                    elif unique_teams: st.session_state.selected_teams = list(unique_teams); st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                    else: st.session_state.selected_teams = []; st.session_state.incident_team_widget_selection_controlled = []
                options_for_team_widget = [SELECT_ALL_TEAMS_OPTION] + unique_teams
                raw_team_widget_selection = st.multiselect("Filter by Team", options=options_for_team_widget, default=st.session_state.incident_team_widget_selection_controlled, key="multi_select_incident_team")
                # ... (rest of multiselect logic for teams - unchanged)
                prev_widget_display_state = list(st.session_state.incident_team_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_TEAMS_OPTION in raw_team_widget_selection
                currently_selected_actual_items = [t for t in raw_team_widget_selection if t != SELECT_ALL_TEAMS_OPTION]
                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_TEAMS_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_TEAMS_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)
                if user_clicked_select_all: st.session_state.selected_teams = list(unique_teams); st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                elif user_clicked_unselect_all: st.session_state.selected_teams = []; st.session_state.incident_team_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_teams): st.session_state.selected_teams = list(currently_selected_actual_items); st.session_state.incident_team_widget_selection_controlled = list(currently_selected_actual_items)
                        else: st.session_state.selected_teams = list(unique_teams); st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                    else:
                        st.session_state.selected_teams = list(currently_selected_actual_items)
                        if unique_teams and set(currently_selected_actual_items) == set(unique_teams): st.session_state.incident_team_widget_selection_controlled = [SELECT_ALL_TEAMS_OPTION]
                        else: st.session_state.incident_team_widget_selection_controlled = list(currently_selected_actual_items)


            with col3: # Filter by 'Priority'
                norm_priority_col_inc = 'priority' # Assuming normalized name
                if norm_priority_col_inc in overview_df_internal.columns:
                    unique_priorities = sorted(overview_df_internal[norm_priority_col_inc].dropna().unique())
                else: unique_priorities = []
                SELECT_ALL_PRIORITIES_OPTION = SELECT_ALL_BASE_STRING % "Priorities"
                if 'incident_priority_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_priorities = list(unique_priorities)
                    st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION] if unique_priorities else []
                options_for_priority_widget = [SELECT_ALL_PRIORITIES_OPTION] + unique_priorities
                raw_priority_widget_selection = st.multiselect("Filter by Priority", options=options_for_priority_widget, default=st.session_state.incident_priority_widget_selection_controlled, key="multi_select_incident_priority")
                # ... (rest of multiselect logic for priorities - unchanged)
                prev_widget_display_state = list(st.session_state.incident_priority_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_PRIORITIES_OPTION in raw_priority_widget_selection
                currently_selected_actual_items = [p for p in raw_priority_widget_selection if p != SELECT_ALL_PRIORITIES_OPTION]
                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_PRIORITIES_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_PRIORITIES_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)
                if user_clicked_select_all: st.session_state.selected_priorities = list(unique_priorities); st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                elif user_clicked_unselect_all: st.session_state.selected_priorities = []; st.session_state.incident_priority_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_priorities): st.session_state.selected_priorities = list(currently_selected_actual_items); st.session_state.incident_priority_widget_selection_controlled = list(currently_selected_actual_items)
                        else: st.session_state.selected_priorities = list(unique_priorities); st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                    else:
                        st.session_state.selected_priorities = list(currently_selected_actual_items)
                        if unique_priorities and set(currently_selected_actual_items) == set(unique_priorities): st.session_state.incident_priority_widget_selection_controlled = [SELECT_ALL_PRIORITIES_OPTION]
                        else: st.session_state.incident_priority_widget_selection_controlled = list(currently_selected_actual_items)

            with col4: # Filter by 'Status'
                norm_status_col_inc = 'status' # Assuming normalized name
                if norm_status_col_inc in overview_df_internal.columns:
                    unique_statuses = sorted(overview_df_internal[norm_status_col_inc].dropna().unique())
                    closed_like_statuses = {'Closed', 'Cancelled'} # Values, not column names
                    default_selected_statuses = [s for s in unique_statuses if s not in closed_like_statuses]
                else: unique_statuses = []; default_selected_statuses = []
                SELECT_ALL_STATUSES_OPTION = SELECT_ALL_BASE_STRING % "Statuses"
                if 'incident_status_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_statuses = list(default_selected_statuses)
                    if not default_selected_statuses and unique_statuses: st.session_state.selected_statuses = list(unique_statuses); st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif unique_statuses and set(default_selected_statuses) == set(unique_statuses): st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    elif not unique_statuses: st.session_state.selected_statuses = []; st.session_state.incident_status_widget_selection_controlled = []
                    else: st.session_state.incident_status_widget_selection_controlled = list(default_selected_statuses)
                options_for_status_widget = [SELECT_ALL_STATUSES_OPTION] + unique_statuses
                raw_status_widget_selection = st.multiselect("Filter by Status", options=options_for_status_widget, default=st.session_state.incident_status_widget_selection_controlled, key="multi_select_incident_status")
                # ... (rest of multiselect logic for status - unchanged)
                prev_widget_display_state = list(st.session_state.incident_status_widget_selection_controlled)
                current_select_all_option_selected = SELECT_ALL_STATUSES_OPTION in raw_status_widget_selection
                currently_selected_actual_items = [s for s in raw_status_widget_selection if s != SELECT_ALL_STATUSES_OPTION]
                user_clicked_select_all = current_select_all_option_selected and (SELECT_ALL_STATUSES_OPTION not in prev_widget_display_state)
                user_clicked_unselect_all = (not current_select_all_option_selected) and (SELECT_ALL_STATUSES_OPTION in prev_widget_display_state and len(prev_widget_display_state) == 1)
                if user_clicked_select_all: st.session_state.selected_statuses = list(unique_statuses); st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                elif user_clicked_unselect_all: st.session_state.selected_statuses = []; st.session_state.incident_status_widget_selection_controlled = []
                else:
                    if current_select_all_option_selected:
                        if len(currently_selected_actual_items) < len(unique_statuses): st.session_state.selected_statuses = list(currently_selected_actual_items); st.session_state.incident_status_widget_selection_controlled = list(currently_selected_actual_items)
                        else: st.session_state.selected_statuses = list(unique_statuses); st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                    else:
                        st.session_state.selected_statuses = list(currently_selected_actual_items)
                        if unique_statuses and set(currently_selected_actual_items) == set(unique_statuses): st.session_state.incident_status_widget_selection_controlled = [SELECT_ALL_STATUSES_OPTION]
                        else: st.session_state.incident_status_widget_selection_controlled = list(currently_selected_actual_items)

            # Apply filters to overview_df_internal
            filtered_overview_df_internal = overview_df_internal
            if st.session_state.get('selected_creators') and 'Creator' in filtered_overview_df_internal.columns:
                filtered_overview_df_internal = filtered_overview_df_internal[filtered_overview_df_internal['Creator'].isin(st.session_state.selected_creators)]
            if st.session_state.get('selected_teams') and norm_team_col_inc in filtered_overview_df_internal.columns:
                filtered_overview_df_internal = filtered_overview_df_internal[filtered_overview_df_internal[norm_team_col_inc].isin(st.session_state.selected_teams)]
            if st.session_state.get('selected_priorities') and norm_priority_col_inc in filtered_overview_df_internal.columns:
                filtered_overview_df_internal = filtered_overview_df_internal[filtered_overview_df_internal[norm_priority_col_inc].isin(st.session_state.selected_priorities)]
            if st.session_state.get('selected_statuses') and norm_status_col_inc in filtered_overview_df_internal.columns:
                filtered_overview_df_internal = filtered_overview_df_internal[filtered_overview_df_internal[norm_status_col_inc].isin(st.session_state.selected_statuses)]

            team_status_summary_df = calculate_team_status_summary(filtered_overview_df_internal) # Uses existing col names in df

            st.markdown("---")
            if norm_status_col_inc in overview_df_internal.columns:
                closed_count = overview_df_internal[overview_df_internal[norm_status_col_inc] == 'Closed'].shape[0]
                total_incidents = overview_df_internal.shape[0]
                if total_incidents > 0:
                    chart_data = pd.DataFrame({'Status Category': ['Closed', 'Open/Other'], 'Count': [closed_count, total_incidents - closed_count]})
                    fig_status_pie = px.pie(chart_data, names='Status Category', values='Count', title='Percentage of Closed Incidents')
                    st.plotly_chart(fig_status_pie, use_container_width=True)
                else: st.info("No incident data for status pie chart.")
            else: st.warning(f"'{norm_status_col_inc}' column missing for status pie chart.")

            st.markdown("---")
            st.subheader("Team Assignment Distribution")
            if not filtered_overview_df_internal.empty:
                if norm_team_col_inc in filtered_overview_df_internal.columns:
                    team_distribution_data = filtered_overview_df_internal[norm_team_col_inc].value_counts()
                    if not team_distribution_data.empty:
                        fig_team_dist = px.pie(team_distribution_data, names=team_distribution_data.index, values=team_distribution_data.values, title="Distribution of Incidents by Team")
                        fig_team_dist.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_team_dist, use_container_width=True)
                    else: st.info("No team assignment data to display.")
                else: st.warning(f"'{norm_team_col_inc}' column not found for Team Distribution.")
            else: st.info("No data for Team Assignment Distribution.")

            st.markdown("---")
            st.subheader("Incidents by Team and Status")
            # Columns for team_status_summary_df are fixed by calculate_team_status_summary, so no get_display_df needed.
            if norm_team_col_inc not in filtered_overview_df_internal.columns or norm_status_col_inc not in filtered_overview_df_internal.columns:
                st.warning(f"'{norm_team_col_inc}' or '{norm_status_col_inc}' column missing for 'Incidents by Team and Status' table.")
            elif not team_status_summary_df.empty:
                st.dataframe(team_status_summary_df, use_container_width=True, hide_index=True)
            else: st.info("No data for 'Incidents by Team and Status' table.")
         
            st.markdown("---")
            st.subheader("Filtered Incident Details")
            if not filtered_overview_df_internal.empty:
                # Column names here are from incident file (e.g. 'Incident', 'Creator', 'Team', 'Priority', 'Status')
                # These are already normalized by load_data or fixed (like 'Creator').
                # The multiselect options should be these names directly.
                all_incident_cols = filtered_overview_df_internal.columns.tolist()
                SELECT_ALL_INC_COLS_OPTION = "[Select All Columns]"

                default_incident_table_cols = ['incident', 'Creator', 'team', 'priority', 'status'] # Use normalized/fixed names
                # Ensure defaults are valid
                valid_default_incident_cols = [col for col in default_incident_table_cols if col in all_incident_cols]

                if 'incident_tab_column_widget_selection_controlled' not in st.session_state:
                    st.session_state.selected_incident_table_cols = list(valid_default_incident_cols)
                    if not valid_default_incident_cols and all_incident_cols: st.session_state.selected_incident_table_cols = list(all_incident_cols); st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_INC_COLS_OPTION]
                    elif all_incident_cols and set(valid_default_incident_cols) == set(all_incident_cols): st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_INC_COLS_OPTION]
                    elif not all_incident_cols: st.session_state.selected_incident_table_cols = []; st.session_state.incident_tab_column_widget_selection_controlled = []
                    else: st.session_state.incident_tab_column_widget_selection_controlled = list(valid_default_incident_cols)

                options_for_inc_cols_widget = [SELECT_ALL_INC_COLS_OPTION] + all_incident_cols
                raw_inc_cols_selection = st.multiselect("Select columns for table:", options=options_for_inc_cols_widget, default=st.session_state.incident_tab_column_widget_selection_controlled, key="multi_select_incident_overview_columns")

                # ... (multiselect logic for incident columns - operates on all_incident_cols)
                prev_inc_widget_state = list(st.session_state.incident_tab_column_widget_selection_controlled)
                curr_inc_select_all = SELECT_ALL_INC_COLS_OPTION in raw_inc_cols_selection
                curr_inc_actual_items = [c for c in raw_inc_cols_selection if c != SELECT_ALL_INC_COLS_OPTION]
                user_clicked_inc_select_all = curr_inc_select_all and (SELECT_ALL_INC_COLS_OPTION not in prev_inc_widget_state)
                user_clicked_inc_unselect_all = (not curr_inc_select_all) and (SELECT_ALL_INC_COLS_OPTION in prev_inc_widget_state and len(prev_inc_widget_state) == 1)

                if user_clicked_inc_select_all: st.session_state.selected_incident_table_cols = list(all_incident_cols); st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_INC_COLS_OPTION]
                elif user_clicked_inc_unselect_all: st.session_state.selected_incident_table_cols = []; st.session_state.incident_tab_column_widget_selection_controlled = []
                else:
                    if curr_inc_select_all:
                        if len(curr_inc_actual_items) < len(all_incident_cols): st.session_state.selected_incident_table_cols = list(curr_inc_actual_items); st.session_state.incident_tab_column_widget_selection_controlled = list(curr_inc_actual_items)
                        else: st.session_state.selected_incident_table_cols = list(all_incident_cols); st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_INC_COLS_OPTION]
                    else:
                        st.session_state.selected_incident_table_cols = list(curr_inc_actual_items)
                        if all_incident_cols and set(curr_inc_actual_items) == set(all_incident_cols): st.session_state.incident_tab_column_widget_selection_controlled = [SELECT_ALL_INC_COLS_OPTION]
                        else: st.session_state.incident_tab_column_widget_selection_controlled = list(curr_inc_actual_items)

                current_cols_to_display_inc_tab = st.session_state.get('selected_incident_table_cols', [])
                if not current_cols_to_display_inc_tab: st.info("Please select at least one column for the table.")
                else:
                    st.write(f"Displaying {len(filtered_overview_df_internal)} records with selected columns.")
                    # No get_display_df here as these are incident file columns, not main excel.
                    st.dataframe(filtered_overview_df_internal[current_cols_to_display_inc_tab], use_container_width=True, hide_index=True)
            else: st.info("No data for 'Filtered Incident Details' table.")
   
            st.markdown("---")
            st.subheader("High-Priority Incidents (P1 & P2)")
            if not filtered_overview_df_internal.empty:
                # Columns here are from incident file, e.g. 'incident', 'Creator', 'team', 'priority', 'status'
                high_priority_table_cols_inc = ['incident', 'Creator', 'team', 'priority']
                if norm_status_col_inc in filtered_overview_df_internal.columns: high_priority_table_cols_inc.append(norm_status_col_inc)
                
                missing_cols_hp_inc = [col for col in ['incident', 'Creator', 'team', 'priority'] if col not in filtered_overview_df_internal.columns]
                if not missing_cols_hp_inc:
                    high_priority_values = ["1", "2"] # Values
                    # Ensure 'priority' column is correct type for comparison if it's not string
                    hp_inc_df = filtered_overview_df_internal[filtered_overview_df_internal[norm_priority_col_inc].astype(str).isin(high_priority_values)]
                    if not hp_inc_df.empty:
                        # No get_display_df
                        st.dataframe(hp_inc_df[[col for col in high_priority_table_cols_inc if col in hp_inc_df.columns]], use_container_width=True, hide_index=True)
                    else: st.info("No P1 or P2 incidents based on current filters.")
                else: st.warning(f"Missing columns for High-Priority Incidents: {', '.join(missing_cols_hp_inc)}.")
            else: st.info("No data for High-Priority Incidents.")

    #
    # SR OVERVIEW TAB
    #
    elif selected == "SR Overview":
        st.title("📊 Service Request (SR) Overview")
        from utils import calculate_srs_created_and_closed_per_week # Keep import local if only used here

        # This tab uses st.session_state.sr_df.
        # load_data normalizes its columns. Column names like 'Created On', 'LastModDateTime', 'Status',
        # 'Service Request' will be in their normalized forms (e.g., 'created on').
        # Charts and tables here should use these normalized names internally.
        # For display in tables (st.dataframe) or column selectors, if these columns
        # were part of the *main* excel file, get_display_df would handle them.
        # However, sr_df is from a *separate* SR Status Excel.
        # The user's request was for "names of the columns in the tables should be the same as in uploaded excel sheet."
        # This implies that if sr_df has columns like "Service Request", it should be displayed as such,
        # not as "service request". This would require a *separate* column mapping for sr_df,
        # or adapting get_display_df to take a mapping as an argument if we stored one for sr_df.
        # For now, assuming column names in sr_df are relatively standard and their normalized versions are acceptable for display,
        # or that this specific part of the request is focused on the main data table.
        # If original names from sr_status_file are needed, load_data would need to return mapping for it too,
        # and that mapping stored and used. This is outside current scope of change.
        # So, tables in this tab will show columns as they are in sr_df (i.e., normalized by load_data).

        if 'sr_df' not in st.session_state or st.session_state.sr_df is None or st.session_state.sr_df.empty:
            st.warning("The 'SR Status Excel' has not been uploaded or is empty. Please upload to view SR Overview.")
        else:
            sr_overview_df_internal = st.session_state.sr_df.copy() # Has normalized column names
            st.markdown(f"**Total SRs Loaded:** {len(sr_overview_df_internal)}")

            # Define normalized column names expected by calculate_srs_created_and_closed_per_week
            norm_created_on_col_sr = 'created on'
            norm_last_mod_col_sr = 'lastmoddatetime'
            norm_status_col_sr = 'status'

            required_cols_for_chart_normalized = [norm_created_on_col_sr, norm_last_mod_col_sr, norm_status_col_sr]
            missing_cols_sr = [col for col in required_cols_for_chart_normalized if col not in sr_overview_df_internal.columns]

            if missing_cols_sr:
                # Try to find original versions of missing columns to give a more helpful error
                missing_cols_display = []
                temp_sr_mapping = {v:k for k,v in st.session_state.get('sr_column_mapping', {}).items()} # if we had sr specific mapping
                for norm_col in missing_cols_sr:
                    missing_cols_display.append(temp_sr_mapping.get(norm_col, norm_col)) # Show original if poss, else normalized
                st.error(f"SR data must contain columns like: {', '.join(missing_cols_display)} for weekly overview.")
            else:
                srs_weekly_combined_df = calculate_srs_created_and_closed_per_week(sr_overview_df_internal) # Expects normalized names

                if srs_weekly_combined_df.empty:
                    st.info("No valid data for weekly SRs created/closed chart.")
                else:
                    created_df = srs_weekly_combined_df[srs_weekly_combined_df['Category'] == 'Created'].copy()
                    closed_df = srs_weekly_combined_df[srs_weekly_combined_df['Category'] == 'Closed'].copy()
                    chart_x_axis = 'WeekDisplay' # This is a fixed column from the util function

                    if not created_df.empty:
                        st.subheader("Service Requests Created Per Week")
                        fig_created = px.bar(created_df, x=chart_x_axis, y='Count', title="Service Requests Created Per Week", labels={'Count': 'Number of SRs Created', chart_x_axis: 'Week Period'}, color_discrete_sequence=px.colors.qualitative.Plotly, text='Count')
                        fig_created.update_traces(texttemplate='%{text}', textposition='outside')
                        fig_created.update_layout(xaxis_title='Week Period', yaxis_title="Number of SRs Created")
                        st.plotly_chart(fig_created, use_container_width=True)
                    else: st.info("No data for 'SRs Created Per Week' chart.")

                    if not closed_df.empty:
                        st.subheader("Service Requests Closed Per Week")
                        fig_closed = px.bar(closed_df, x=chart_x_axis, y='Count', title="Service Requests Closed Per Week: Status (Closed,Completed, Cancelled, Approval rejected, Rejected by ps)", labels={'Count': 'Number of SRs Closed', chart_x_axis: 'Week Period'}, color_discrete_sequence=px.colors.qualitative.Plotly, text='Count')
                        fig_closed.update_traces(texttemplate='%{text}', textposition='outside')
                        fig_closed.update_layout(xaxis_title='Week Period', yaxis_title="Number of SRs Closed")
                        st.plotly_chart(fig_closed, use_container_width=True)
                    else: st.info("No data for 'SRs Closed Per Week' chart.")

                st.markdown("---")
                st.subheader("Filterable SR Data")
                table_display_df_sr_internal = sr_overview_df_internal.copy()
                week_map_for_filter_sr = {}
                week_options_for_multiselect_sr = []

                if 'srs_weekly_combined_df' in locals() and not srs_weekly_combined_df.empty:
                    if 'WeekDisplay' in srs_weekly_combined_df.columns and 'Year-Week' in srs_weekly_combined_df.columns:
                        unique_week_options_df_sr = srs_weekly_combined_df[['Year-Week', 'WeekDisplay']].drop_duplicates().sort_values(by='Year-Week')
                        week_options_for_multiselect_sr = unique_week_options_df_sr['WeekDisplay'].tolist()
                        for _, row in unique_week_options_df_sr.iterrows(): week_map_for_filter_sr[row['WeekDisplay']] = row['Year-Week']
                
                if norm_created_on_col_sr in table_display_df_sr_internal.columns:
                    table_display_df_sr_internal[norm_created_on_col_sr] = pd.to_datetime(table_display_df_sr_internal[norm_created_on_col_sr], errors='coerce')
                    table_display_df_sr_internal.dropna(subset=[norm_created_on_col_sr], inplace=True)
                    if not table_display_df_sr_internal.empty:
                         table_display_df_sr_internal['Year-Week'] = table_display_df_sr_internal[norm_created_on_col_sr].dt.strftime('%G-W%V')

                col_filter1_sr, col_filter2_sr = st.columns(2)
                with col_filter1_sr:
                    selected_week_displays_sr = st.multiselect("Filter by Week Period:", options=week_options_for_multiselect_sr, default=[])
                with col_filter2_sr:
                    min_date_val_sr = table_display_df_sr_internal[norm_created_on_col_sr].min().date() if not table_display_df_sr_internal.empty and norm_created_on_col_sr in table_display_df_sr_internal.columns and not table_display_df_sr_internal[norm_created_on_col_sr].dropna().empty else None
                    max_date_val_sr = table_display_df_sr_internal[norm_created_on_col_sr].max().date() if not table_display_df_sr_internal.empty and norm_created_on_col_sr in table_display_df_sr_internal.columns and not table_display_df_sr_internal[norm_created_on_col_sr].dropna().empty else None
                    selected_day_sr = st.date_input(f"Filter by Specific Day ({norm_created_on_col_sr}):", value=None, min_value=min_date_val_sr, max_value=max_date_val_sr)

                if selected_day_sr and norm_created_on_col_sr in table_display_df_sr_internal.columns:
                    table_display_df_sr_internal = table_display_df_sr_internal[table_display_df_sr_internal[norm_created_on_col_sr].dt.date == selected_day_sr]
                elif selected_week_displays_sr and 'Year-Week' in table_display_df_sr_internal.columns:
                    selected_year_weeks_short_sr = [week_map_for_filter_sr[wd] for wd in selected_week_displays_sr if wd in week_map_for_filter_sr]
                    if selected_year_weeks_short_sr: table_display_df_sr_internal = table_display_df_sr_internal[table_display_df_sr_internal['Year-Week'].isin(selected_year_weeks_short_sr)]

                st.markdown(f"**Total Displayed SRs:** {len(table_display_df_sr_internal)}")

                if not table_display_df_sr_internal.empty:
                    all_sr_cols_internal = table_display_df_sr_internal.columns.tolist()
                    if 'Year-Week' in all_sr_cols_internal: all_sr_cols_internal.remove('Year-Week') # Internal use only

                    # Default columns for SR table (use normalized names from SR file)
                    default_sr_cols_norm = ['service request', norm_status_col_sr, norm_created_on_col_sr]
                    sanitized_default_sr_cols = [col for col in default_sr_cols_norm if col in all_sr_cols_internal]

                    if 'filterable_sr_data_cols_multiselect' not in st.session_state:
                        st.session_state.filterable_sr_data_cols_multiselect = sanitized_default_sr_cols

                    # Options for multiselect are the normalized names from sr_df
                    selected_sr_columns_norm = st.multiselect("Select columns for Filterable SR Data:", options=all_sr_cols_internal, default=st.session_state.filterable_sr_data_cols_multiselect, key="multiselect_filterable_sr_data")
                    st.session_state.filterable_sr_data_cols_multiselect = selected_sr_columns_norm

                    if selected_sr_columns_norm:
                        st.dataframe(table_display_df_sr_internal[selected_sr_columns_norm], hide_index=True)
                    else: # Show all available if nothing selected
                        st.dataframe(table_display_df_sr_internal[all_sr_cols_internal], hide_index=True)
                else: st.info("No SR data for Filterable SR Data table based on filters.")

                st.markdown("---")
                st.subheader("Closed Service Requests")
                essential_cols_closed_sr_norm = [norm_status_col_sr, norm_last_mod_col_sr]
                missing_essential_cols_sr_closed = [col for col in essential_cols_closed_sr_norm if col not in sr_overview_df_internal.columns]

                if missing_essential_cols_sr_closed:
                    st.warning(f"SR data missing columns: {', '.join(missing_essential_cols_sr_closed)} for Closed SRs table.")
                else:
                    closed_sr_statuses_vals = ["closed", "completed", "cancelled", "approval rejected", "rejected by ps"]
                    closed_srs_df_internal = sr_overview_df_internal[sr_overview_df_internal[norm_status_col_sr].astype(str).str.lower().str.strip().isin(closed_sr_statuses_vals)].copy()
                    closed_srs_df_internal[norm_last_mod_col_sr] = pd.to_datetime(closed_srs_df_internal[norm_last_mod_col_sr], errors='coerce', dayfirst=True, infer_datetime_format=True)
                    closed_srs_df_internal.dropna(subset=[norm_last_mod_col_sr], inplace=True)

                    if not closed_srs_df_internal.empty:
                        closed_srs_df_internal['Closure-Year-Week'] = closed_srs_df_internal[norm_last_mod_col_sr].dt.strftime('%G-W%V')
                    else: closed_srs_df_internal['Closure-Year-Week'] = pd.Series(dtype='str')

                    closed_sr_week_map_filter = {}
                    closed_sr_week_options_multiselect = []
                    if not closed_srs_df_internal.empty and 'Closure-Year-Week' in closed_srs_df_internal.columns:
                        unique_closed_week_options_df_sr = closed_srs_df_internal[['Closure-Year-Week']].copy()
                        unique_closed_week_options_df_sr.dropna(subset=['Closure-Year-Week'], inplace=True)
                        unique_closed_week_options_df_sr['WeekDisplay'] = unique_closed_week_options_df_sr['Closure-Year-Week'].apply(_get_week_display_str)
                        unique_closed_week_options_df_sr = unique_closed_week_options_df_sr[['Closure-Year-Week', 'WeekDisplay']].drop_duplicates().sort_values(by='Closure-Year-Week')
                        closed_sr_week_options_multiselect = unique_closed_week_options_df_sr['WeekDisplay'].tolist()
                        for _, row in unique_closed_week_options_df_sr.iterrows(): closed_sr_week_map_filter[row['WeekDisplay']] = row['Closure-Year-Week']

                    col_filter_closed_sr1, col_filter_closed_sr2 = st.columns(2)
                    with col_filter_closed_sr1:
                        selected_week_displays_closed_sr = st.multiselect("Filter Closed SRs by Closure Week Period:",options=closed_sr_week_options_multiselect,default=[],key="closed_sr_closure_week_filter")
                    with col_filter_closed_sr2:
                        min_d_closed_sr = closed_srs_df_internal[norm_last_mod_col_sr].min().date() if not closed_srs_df_internal.empty and not closed_srs_df_internal[norm_last_mod_col_sr].dropna().empty else None
                        max_d_closed_sr = closed_srs_df_internal[norm_last_mod_col_sr].max().date() if not closed_srs_df_internal.empty and not closed_srs_df_internal[norm_last_mod_col_sr].dropna().empty else None
                        selected_day_closed_sr = st.date_input("Filter Closed SRs by Specific Closure Day:",value=None,min_value=min_d_closed_sr,max_value=max_d_closed_sr,key="closed_sr_closure_day_filter")

                    filtered_closed_srs_df_internal = closed_srs_df_internal.copy()
                    if selected_day_closed_sr and norm_last_mod_col_sr in filtered_closed_srs_df_internal.columns:
                        filtered_closed_srs_df_internal = filtered_closed_srs_df_internal[filtered_closed_srs_df_internal[norm_last_mod_col_sr].dt.date == selected_day_closed_sr]
                    elif selected_week_displays_closed_sr and 'Closure-Year-Week' in filtered_closed_srs_df_internal.columns and closed_sr_week_map_filter:
                        selected_closure_year_weeks_short_sr = [closed_sr_week_map_filter[wd] for wd in selected_week_displays_closed_sr if wd in closed_sr_week_map_filter]
                        if selected_closure_year_weeks_short_sr: filtered_closed_srs_df_internal = filtered_closed_srs_df_internal[filtered_closed_srs_df_internal['Closure-Year-Week'].isin(selected_closure_year_weeks_short_sr)]

                    st.markdown(f"**Total Displayed Closed SRs (filtered by closure date):** {len(filtered_closed_srs_df_internal)}")

                    if not filtered_closed_srs_df_internal.empty:
                        all_closed_sr_cols_internal = filtered_closed_srs_df_internal.columns.tolist()
                        internal_cols_to_remove_sr = ['Closure-Year-Week', 'Year-Week'] # Year-Week might be from created_on processing
                        for col_rem in internal_cols_to_remove_sr:
                            if col_rem in all_closed_sr_cols_internal: all_closed_sr_cols_internal.remove(col_rem)

                        # Default columns for closed SR table (normalized names from SR file)
                        default_closed_sr_cols_norm = ['service request', norm_status_col_sr, norm_created_on_col_sr, norm_last_mod_col_sr, 'resolution'] # 'resolution' might be 'Resolution'
                        # Check actual normalized name for resolution if it exists
                        norm_resolution_col_sr = 'resolution' # or 'Resolution'.lower().strip()
                        if 'Resolution' in sr_overview_df_internal.columns: norm_resolution_col_sr = 'resolution'
                        elif 'resolution' not in sr_overview_df_internal.columns: norm_resolution_col_sr = None # Not available

                        if norm_resolution_col_sr: default_closed_sr_cols_norm = ['service request', norm_status_col_sr, norm_created_on_col_sr, norm_last_mod_col_sr, norm_resolution_col_sr]
                        else: default_closed_sr_cols_norm = ['service request', norm_status_col_sr, norm_created_on_col_sr, norm_last_mod_col_sr]

                        sanitized_default_closed_sr_cols = [col for col in default_closed_sr_cols_norm if col in all_closed_sr_cols_internal]

                        if 'closed_sr_data_cols_multiselect' not in st.session_state:
                            st.session_state.closed_sr_data_cols_multiselect = sanitized_default_closed_sr_cols

                        selected_closed_sr_columns_norm = st.multiselect("Select columns for Closed SRs:", options=all_closed_sr_cols_internal, default=st.session_state.closed_sr_data_cols_multiselect, key="multiselect_closed_sr_data")
                        st.session_state.closed_sr_data_cols_multiselect = selected_closed_sr_columns_norm

                        if selected_closed_sr_columns_norm:
                            st.dataframe(filtered_closed_srs_df_internal[selected_closed_sr_columns_norm], hide_index=True)
                        else: # Show all available
                            st.dataframe(filtered_closed_srs_df_internal[all_closed_sr_cols_internal], hide_index=True)

                        cols_for_download_closed_sr = selected_closed_sr_columns_norm if selected_closed_sr_columns_norm else all_closed_sr_cols_internal
                        # Passing main column_mapping here. It will only apply if sr_df columns happen to match.
                        excel_closed_sr_data = generate_excel_download(
                            filtered_closed_srs_df_internal[cols_for_download_closed_sr] if cols_for_download_closed_sr else filtered_closed_srs_df_internal,
                            column_mapping=st.session_state.get('column_name_mapping')
                            )
                        st.download_button(label="📥 Download Closed SRs Data", data=excel_closed_sr_data, file_name=f"closed_srs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_closed_srs")
                    else: st.info("No Closed SR data to display based on filters.")


st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.8em;">
    Intellipen SmartQ Test V3.6 | Developed by Ali Babiker | © June 2025
    </div>""",
    unsafe_allow_html=True
)
