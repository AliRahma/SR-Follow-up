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
from utils import (
    calculate_team_status_summary,
    calculate_srs_created_per_week,
    _get_week_display_str,
    get_df_with_original_column_names
)

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

# Initialize session state
if 'data_loaded' not in st.session_state: st.session_state.data_loaded = False
if 'main_df' not in st.session_state: st.session_state.main_df = None
if 'sr_df' not in st.session_state: st.session_state.sr_df = None
if 'incident_df' not in st.session_state: st.session_state.incident_df = None
if 'filtered_df' not in st.session_state: st.session_state.filtered_df = None # This will store the enriched (normalized) df
if 'last_upload_time' not in st.session_state: st.session_state.last_upload_time = None
if 'selected_users' not in st.session_state: st.session_state.selected_users = []
if 'report_datetime' not in st.session_state: st.session_state.report_datetime = None
if 'column_mappings' not in st.session_state: st.session_state.column_mappings = {}

# Keys for different dataframes within column_mappings
MAIN_DF_KEY = 'main_df'
SR_DF_KEY = 'sr_df'
INCIDENT_DF_KEY = 'incident_df'

@st.cache_data
def load_data(file, file_type_key):
    if file is None:
        return None, None, None
    parsed_datetime_str = None
    df = None
    column_mapping = None # Ensure it's initialized
    try:
        file_name = file.name
        file_extension = os.path.splitext(file_name)[1].lower()
        match = re.search(r'_(\d{8})_(\d{6})\.', file_name)
        if match:
            date_str, time_str = match.group(1), match.group(2)
            try:
                dt_object = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                parsed_datetime_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError: pass
        
        engine = 'xlrd' if file_extension == '.xls' else 'openpyxl'
        try:
            df = pd.read_excel(file, engine=engine)
        except Exception as e:
            if engine == 'xlrd':
                try:
                    file.seek(0)
                    df = pd.read_excel(file, engine='openpyxl')
                except Exception as e_openpyxl:
                    st.error(f"Error loading .xls file '{file.name}' with both xlrd and openpyxl: {e_openpyxl}")
                    return None, parsed_datetime_str, None
            else:
                st.error(f"Error loading file '{file.name}': {e}")
                return None, parsed_datetime_str, None

        if df is not None:
            original_columns = list(df.columns)
            normalized_columns = [str(col).lower().strip().replace(' ', '') for col in original_columns]
            column_mapping = {norm_col: orig_col for norm_col, orig_col in zip(normalized_columns, original_columns)}
            df.columns = normalized_columns
        return df, parsed_datetime_str, column_mapping
            
    except Exception as e:
        st.error(f"Error processing file '{file.name}': {e}")
        return None, parsed_datetime_str, None

def process_main_df(df):
    casestartdate_norm = 'casestartdate'
    lastnotedate_norm = 'lastnotedate'
    currentuserid_norm = 'currentuserid'
    date_columns_normalized = [casestartdate_norm, lastnotedate_norm]

    for col in date_columns_normalized:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
            if df[col].isnull().any():
                 df.loc[df[col].isnull(), col] = pd.to_datetime(df.loc[df[col].isnull(), col], errors='coerce')
    
    if currentuserid_norm in df.columns:
        all_users = sorted(df[currentuserid_norm].dropna().unique().tolist())
        st.session_state.all_users = all_users
    return df

def classify_and_extract(note):
    if not isinstance(note, str): return "Not Triaged", None, None
    note_lower = note.lower()
    match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
    if match:
        ticket_num = int(match.group(2))
        ticket_type = "SR" if 14000 <= ticket_num <= 18000 else "Incident"
        return "Pending SR/Incident", ticket_num, ticket_type
    return "Not Triaged", None, None

def calculate_age(start_date):
    if pd.isna(start_date): return None
    return (datetime.now() - start_date).days

def is_created_today(date_value):
    if pd.isna(date_value): return False
    today = datetime.now().date()
    note_date = date_value.date() if isinstance(date_value, datetime) else date_value
    return note_date == today

def generate_excel_download_customized(df_to_download, df_type_key_for_mapping):
    df_for_excel = get_df_with_original_column_names(df_to_download, df_type_key_for_mapping)
    if df_for_excel is None or df_for_excel.empty: # Handle empty df
        df_for_excel = pd.DataFrame() # Create empty if None, or use as is if empty

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_for_excel.to_excel(writer, index=False, sheet_name='Results')
        workbook = writer.book
        worksheet = writer.sheets['Results']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#1976d2', 'color': 'white', 'border': 1})
        if not df_for_excel.empty: # Only format if there's data
            for col_num, value in enumerate(df_for_excel.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ensure column exists before trying to calculate max_len
                if value in df_for_excel:
                    max_len = max(df_for_excel[value].astype(str).apply(len).max(skipna=True), len(str(value))) + 1
                    worksheet.set_column(col_num, col_num, max_len)
                else: # Fallback for safety, though should not happen if value is from df_for_excel.columns
                    worksheet.set_column(col_num, col_num, len(str(value)) + 2)

    output.seek(0)
    return output

# Sidebar
with st.sidebar:
    st.image("Smart Q Logo.jpg", width=150)
    st.title("📊 Intellipen SmartQ Test")
    st.markdown("---")
    st.subheader("📁 Data Import")
    uploaded_file = st.file_uploader("Upload Main Excel File (.xlsx)", type=["xlsx"])
    sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type=["xlsx","xls"])
    incident_status_file = st.file_uploader("Upload Incident Report Excel (optional)", type=["xlsx","xls"])

    if uploaded_file:
        df, parsed_dt, mapping = load_data(uploaded_file, MAIN_DF_KEY)
        if df is not None:
            st.session_state.main_df = process_main_df(df)
            if mapping: st.session_state.column_mappings[MAIN_DF_KEY] = mapping
            st.session_state.last_upload_time = datetime.now(pytz.timezone('Asia/Dubai')).strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Main data loaded: {df.shape[0]} records")
            st.session_state.data_loaded = True
            if parsed_dt: st.session_state.report_datetime = parsed_dt

    if sr_status_file:
        sr_df, parsed_dt_sr, sr_mapping = load_data(sr_status_file, SR_DF_KEY)
        if sr_df is not None:
            st.session_state.sr_df = sr_df
            if sr_mapping: st.session_state.column_mappings[SR_DF_KEY] = sr_mapping
            st.success(f"SR status data loaded: {sr_df.shape[0]} records")
            if st.session_state.report_datetime is None and parsed_dt_sr: st.session_state.report_datetime = parsed_dt_sr
    
    if incident_status_file:
        incident_df, parsed_dt_incident, incident_mapping = load_data(incident_status_file, INCIDENT_DF_KEY)
        if incident_df is not None:
            st.session_state.incident_df = incident_df
            if incident_mapping: st.session_state.column_mappings[INCIDENT_DF_KEY] = incident_mapping
            st.success(f"Incident report data loaded: {incident_df.shape[0]} records")
            if st.session_state.report_datetime is None and parsed_dt_incident: st.session_state.report_datetime = parsed_dt_incident

            overview_df = incident_df.copy() # Has normalized names
            if 'customer' in overview_df.columns:
                overview_df.rename(columns={'customer': 'creator'}, inplace=True)
            st.session_state.incident_overview_df = overview_df

    if st.session_state.get('last_upload_time'): st.info(f"Last data import: {st.session_state.last_upload_time}")
    else: st.info("No data imported yet.")
    st.markdown("---")

    if st.session_state.data_loaded and st.session_state.main_df is not None:
        st.subheader("🔍 Filters")
        df_main_for_filters = st.session_state.main_df
        currentuserid_norm = 'currentuserid'
        casestartdate_norm = 'casestartdate'

        if currentuserid_norm in df_main_for_filters.columns:
            all_users = sorted(df_main_for_filters[currentuserid_norm].dropna().unique().tolist())
        else: all_users = []

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
        raw_widget_selection = st.multiselect("Select Users", options=options_for_user_widget, default=st.session_state.sidebar_user_widget_selection_controlled, key="multi_select_sidebar_users")

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

        if casestartdate_norm in df_main_for_filters.columns and pd.api.types.is_datetime64_any_dtype(df_main_for_filters[casestartdate_norm]) and not df_main_for_filters[casestartdate_norm].dropna().empty:
            min_date = df_main_for_filters[casestartdate_norm].min().date()
            max_date = df_main_for_filters[casestartdate_norm].max().date()
            if 'sidebar_date_range_value' not in st.session_state: st.session_state.sidebar_date_range_value = (min_date, max_date)
            if st.button("Select Full Range", key="btn_select_full_date_range"): st.session_state.sidebar_date_range_value = (min_date, max_date)
            current_date_range_from_widget = st.date_input("Date Range", value=st.session_state.sidebar_date_range_value, min_value=min_date, max_value=max_date, key="date_input_sidebar")
            if current_date_range_from_widget != st.session_state.sidebar_date_range_value: st.session_state.sidebar_date_range_value = current_date_range_from_widget
            date_range = st.session_state.sidebar_date_range_value
        else: date_range = (None, None)

# Main content
if not st.session_state.data_loaded or st.session_state.main_df is None:
    st.title("📊 Intellipen SmartQ Test")
    st.markdown("Welcome! Please upload your main Excel file using the sidebar to begin analysis.")
else:
    df_main = st.session_state.main_df
    df_filtered = df_main.copy()
    currentuserid_norm = 'currentuserid'
    casestartdate_norm = 'casestartdate'

    if currentuserid_norm in df_filtered.columns and st.session_state.selected_users:
        df_filtered = df_filtered[df_filtered[currentuserid_norm].isin(st.session_state.selected_users)]
    
    if casestartdate_norm in df_filtered.columns and 'date_range' in locals() and date_range[0] is not None and date_range[1] is not None:
        if pd.api.types.is_datetime64_any_dtype(df_filtered[casestartdate_norm]):
            start_date, end_date = date_range
            df_filtered = df_filtered[(df_filtered[casestartdate_norm].dt.date >= start_date) & (df_filtered[casestartdate_norm].dt.date <= end_date)]

    selected_tab = option_menu(menu_title=None, options=["Analysis", "SLA Breach", "Today's SR/Incidents", "Incident Overview", "SR Overview"], icons=["kanban", "exclamation-triangle", "calendar-date", "clipboard-data", "bar-chart-line"], menu_icon="cast", default_index=0, orientation="horizontal", styles={"container": {"padding": "0!important", "margin": "0!important"}, "icon": {"color": "#1565c0", "font-size": "14px"}, "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"}, "nav-link-selected": {"background-color": "#1976d2", "color": "white"}})
    
    col_lastnote = 'lastnote'
    col_casestartdate = 'casestartdate'
    col_lastnotedate = 'lastnotedate'
    col_ticketnumber = 'ticketnumber'
    col_type = 'type'
    col_triagestatus = 'triagestatus'
    col_agedays = 'age(days)'
    col_createdtoday = 'createdtoday'
    col_status = 'status'
    col_lastupdate = 'lastupdate'
    col_breachpassed = 'breachpassed'
    col_casecount = 'casecount'
    col_caseid = 'caseid'
    col_currentuserid = 'currentuserid'
    
    sr_col_servicerequest = 'servicerequest'
    sr_col_status = 'status' # Note: This is the same as col_status, context is key
    sr_col_lastmoddatetime = 'lastmoddatetime'
    sr_col_breachpassed = 'breachpassed' # Same as col_breachpassed
    sr_col_createdon = 'createdon'
    sr_col_resolution = 'resolution'

    inc_col_id_options = ['incident', 'incidentid', 'id', 'number']
    inc_col_status = 'status' # Same as col_status
    inc_col_lastupdate_options = ['lastcheckedat', 'lastcheckedatc', 'modifiedon', 'lastupdate']
    inc_col_breachpassed = 'breachpassed' # Same as col_breachpassed
    inc_col_customer_normalized = 'customer'
    inc_col_creator_normalized = 'creator'
    inc_col_team = 'team'
    inc_col_priority = 'priority'

    def enrich_data(df_input):
        df_enriched = df_input.copy()
        if col_lastnote in df_enriched.columns:
            df_enriched[[col_triagestatus, col_ticketnumber, col_type]] = pd.DataFrame(df_enriched[col_lastnote].apply(lambda x: pd.Series(classify_and_extract(x))).values)
        else:
            df_enriched[[col_triagestatus, col_ticketnumber, col_type]] = ["Error: Last Note missing", None, None]

        if col_casestartdate in df_enriched.columns: df_enriched[col_agedays] = df_enriched[col_casestartdate].apply(calculate_age)
        else: df_enriched[col_agedays] = None

        if col_lastnotedate in df_enriched.columns: df_enriched[col_createdtoday] = df_enriched[col_lastnotedate].apply(is_created_today)
        else: df_enriched[col_createdtoday] = False
        
        df_enriched[[col_status, col_lastupdate, col_breachpassed]] = [None, None, None]
        if col_ticketnumber in df_enriched.columns: df_enriched[col_ticketnumber] = pd.to_numeric(df_enriched[col_ticketnumber], errors='coerce')

        if st.session_state.sr_df is not None:
            sr_df_copy = st.session_state.sr_df.copy()
            if sr_col_servicerequest in sr_df_copy.columns:
                sr_df_copy[sr_col_servicerequest] = sr_df_copy[sr_col_servicerequest].astype(str).str.extract(r'(\d{4,})')[0].pipe(pd.to_numeric, errors='coerce')
                sr_df_copy.dropna(subset=[sr_col_servicerequest], inplace=True)

                sr_rename_map = {}
                if sr_col_status in sr_df_copy.columns: sr_rename_map[sr_col_status] = 'SR_Status_temp'
                if sr_col_lastmoddatetime in sr_df_copy.columns: sr_rename_map[sr_col_lastmoddatetime] = 'SR_Last_Update_temp'
                if sr_col_breachpassed in sr_df_copy.columns: sr_rename_map[sr_col_breachpassed] = 'SR_Breach_Value_temp'

                cols_to_merge_sr = [sr_col_servicerequest] + list(sr_rename_map.keys())
                cols_to_merge_sr = [c for c in cols_to_merge_sr if c in sr_df_copy.columns] # ensure all exist before rename

                sr_df_copy.rename(columns=sr_rename_map, inplace=True)

                # Ensure only columns that exist after rename (original or new temp names) are used
                final_sr_merge_cols = [sr_col_servicerequest] + [v for k,v in sr_rename_map.items() if k in cols_to_merge_sr]
                final_sr_merge_cols = [c for c in final_sr_merge_cols if c in sr_df_copy.columns]

                if final_sr_merge_cols:
                    df_enriched = pd.merge(df_enriched, sr_df_copy[final_sr_merge_cols], how='left', left_on=col_ticketnumber, right_on=sr_col_servicerequest, suffixes=('', '_sr'))
                    if sr_col_servicerequest in df_enriched and sr_col_servicerequest != col_ticketnumber : df_enriched.drop(columns=[sr_col_servicerequest], inplace=True, errors='ignore')

                sr_mask = df_enriched[col_type] == 'SR'
                if 'SR_Status_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, col_status] = df_enriched['SR_Status_temp']
                    df_enriched.drop(columns=['SR_Status_temp'], inplace=True)
                if 'SR_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, col_lastupdate] = df_enriched['SR_Last_Update_temp']
                    df_enriched.drop(columns=['SR_Last_Update_temp'], inplace=True)
                if 'SR_Breach_Value_temp' in df_enriched.columns:
                    df_enriched.loc[sr_mask, col_breachpassed] = df_enriched['SR_Breach_Value_temp'].apply(lambda x: True if str(x).lower() in ['yes', 'true', '1', 'passed'] else (False if str(x).lower() in ['no', 'false', '0', 'failed'] else None))
                    df_enriched.drop(columns=['SR_Breach_Value_temp'], inplace=True)

        if st.session_state.incident_df is not None:
            incident_df_copy = st.session_state.incident_df.copy()
            actual_inc_id_col = next((col for col in inc_col_id_options if col in incident_df_copy.columns), None)
            if actual_inc_id_col:
                incident_df_copy[actual_inc_id_col] = incident_df_copy[actual_inc_id_col].astype(str).str.extract(r'(\d{4,})')[0].pipe(pd.to_numeric, errors='coerce')
                incident_df_copy.dropna(subset=[actual_inc_id_col], inplace=True)

                inc_rename_map = {actual_inc_id_col: 'INC_ID_temp'}
                if inc_col_status in incident_df_copy.columns: inc_rename_map[inc_col_status] = 'INC_Status_temp'
                actual_inc_lastupdate_col = next((col for col in inc_col_lastupdate_options if col in incident_df_copy.columns), None)
                if actual_inc_lastupdate_col: inc_rename_map[actual_inc_lastupdate_col] = 'INC_Last_Update_temp'
                if inc_col_breachpassed in incident_df_copy.columns: inc_rename_map[inc_col_breachpassed] = 'INC_Breach_Passed_temp'
                
                cols_to_merge_inc_orig = [actual_inc_id_col] + [k for k in [inc_col_status, actual_inc_lastupdate_col, inc_col_breachpassed] if k is not None and k in incident_df_copy.columns]
                incident_df_copy.rename(columns=inc_rename_map, inplace=True)
                
                final_inc_merge_cols = [inc_rename_map.get(c,c) for c in cols_to_merge_inc_orig] # use new temp names
                final_inc_merge_cols = [c for c in final_inc_merge_cols if c in incident_df_copy.columns]

                if final_inc_merge_cols:
                    df_enriched = pd.merge(df_enriched, incident_df_copy[final_inc_merge_cols], how='left', left_on=col_ticketnumber, right_on='INC_ID_temp', suffixes=('', '_inc'))
                    if 'INC_ID_temp' in df_enriched.columns: df_enriched.drop(columns=['INC_ID_temp'], inplace=True)

                inc_mask = df_enriched[col_type] == 'Incident'
                if 'INC_Status_temp' in df_enriched.columns:
                    df_enriched.loc[inc_mask, col_status] = df_enriched['INC_Status_temp']
                    df_enriched.drop(columns=['INC_Status_temp'], inplace=True)
                if 'INC_Last_Update_temp' in df_enriched.columns:
                    df_enriched.loc[inc_mask, col_lastupdate] = df_enriched['INC_Last_Update_temp']
                    df_enriched.drop(columns=['INC_Last_Update_temp'], inplace=True)
                if 'INC_Breach_Passed_temp' in df_enriched.columns:
                    df_enriched.loc[inc_mask, col_breachpassed] = df_enriched['INC_Breach_Passed_temp'].apply(lambda x: True if str(x).lower() in ['yes', 'true', '1', 'passed', 'breached'] else (False if str(x).lower() in ['no', 'false', '0', 'failed', 'not breached'] else None))
                    df_enriched.drop(columns=['INC_Breach_Passed_temp'], inplace=True)

        if col_lastupdate in df_enriched.columns: df_enriched[col_lastupdate] = pd.to_datetime(df_enriched[col_lastupdate], errors='coerce')
        if 'breachdate' in df_enriched.columns: df_enriched['breachdate'] = pd.to_datetime(df_enriched['breachdate'], errors='coerce')

        if col_ticketnumber in df_enriched.columns and col_type in df_enriched.columns:
            valid_mask = df_enriched[col_ticketnumber].notna() & df_enriched[col_type].notna()
            if valid_mask.any():
                 df_enriched.loc[valid_mask, col_casecount] = df_enriched[valid_mask].groupby([col_ticketnumber, col_type])[col_ticketnumber].transform('size')
        else: df_enriched[col_casecount] = pd.NA
        return df_enriched

    df_enriched = enrich_data(df_filtered)
    st.session_state.filtered_df = df_enriched.copy()

    # Tab: Analysis
    if selected_tab == "Analysis":
        st.title("🔍 Analysis")
        if st.session_state.get('last_upload_time'): st.markdown(f"**Last Data Import Time:** {st.session_state.last_upload_time}")
        else: st.markdown("**Last Data Import Time:** No data imported yet")
        if st.session_state.get('report_datetime'): st.markdown(f"**Report Datetime (from filename):** {st.session_state.report_datetime}")
        else: st.markdown("**Report Datetime (from filename):** Not available")
        
        col1, col2,col3 = st.columns(3)
        with col1: status_filter = st.selectbox("Filter by Triage Status",["All"] + df_enriched[col_triagestatus].dropna().unique().tolist())
        with col2: type_filter = st.selectbox("Filter by Type", ["All", "SR", "Incident"])
        with col3:
            if col_status in df_enriched.columns: unified_status_filter = st.selectbox("Filter by Status", ["All"] + df_enriched[col_status].dropna().unique().tolist() + ["None"])
            else: unified_status_filter = "All"
        
        df_display = df_enriched.copy()
        if status_filter != "All": df_display = df_display[df_display[col_triagestatus] == status_filter]
        if type_filter != "All": df_display = df_display[df_display[col_type] == type_filter]
        if unified_status_filter != "All":
            if unified_status_filter == "None": df_display = df_display[df_display[col_status].isna()]
            else: df_display = df_display[df_display[col_status] == unified_status_filter]
        
        st.subheader("📊 Summary Analysis")
        summary_col1, summary_col2 = st.columns(2)
        with summary_col1:
            st.markdown("**🔸 Triage Status Count**")
            triage_summary = df_enriched[col_triagestatus].value_counts().rename_axis(col_triagestatus).reset_index(name='Count')
            triage_total = {col_triagestatus: 'Total', 'Count': triage_summary['Count'].sum()}
            triage_df_display = get_df_with_original_column_names(pd.concat([triage_summary, pd.DataFrame([triage_total])], ignore_index=True), MAIN_DF_KEY) # Assuming triagestatus is from main_df context
            st.dataframe(triage_df_display.style.apply(lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(triage_df_display)-1 else '' for _ in x], axis=1))
        with summary_col2:
            st.markdown("**🔹 SR vs Incident Count**")
            type_summary = df_enriched[col_type].value_counts().rename_axis(col_type).reset_index(name='Count')
            type_total = {col_type: 'Total', 'Count': type_summary['Count'].sum()}
            type_df_display = get_df_with_original_column_names(pd.concat([type_summary, pd.DataFrame([type_total])], ignore_index=True), MAIN_DF_KEY) # Assuming type is from main_df context
            st.dataframe(type_df_display.style.apply(lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(type_df_display)-1 else '' for _ in x], axis=1))

        # ... (SR and Incident Status Summaries - ensure to use get_df_with_original_column_names for display if they show column names)
        
        st.subheader("📋 Filtered Results")
        results_col1, results_col2 = st.columns([3, 1])
        with results_col1: st.markdown(f"**Total Filtered Records:** {len(df_display)}")
        with results_col2:
            if not df_display.empty:
                excel_data_analysis = generate_excel_download_customized(df_display, MAIN_DF_KEY)
                st.download_button(label="📥 Download Results", data=excel_data_analysis, file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_analysis")
        
        if not df_display.empty:
            df_display_original_cols = get_df_with_original_column_names(df_display, MAIN_DF_KEY)
            all_original_columns = df_display_original_cols.columns.tolist()
            
            default_norm_cols_analysis = [col_lastnote, col_caseid, col_currentuserid, col_casestartdate, col_triagestatus, col_type, col_ticketnumber]
            if col_status in df_display.columns: default_norm_cols_analysis.extend([col_status, col_lastupdate])
            if col_breachpassed in df_display.columns: default_norm_cols_analysis.append(col_breachpassed)
            
            default_selected_original_cols = []
            main_mapping = st.session_state.column_mappings.get(MAIN_DF_KEY, {})
            for norm_col in default_norm_cols_analysis:
                original_name = main_mapping.get(norm_col, norm_col)
                if original_name in all_original_columns: default_selected_original_cols.append(original_name)

            selected_original_cols = st.multiselect("Select columns to display:", options=all_original_columns, default=default_selected_original_cols, key="multi_select_analysis_columns_orig")
            
            if selected_original_cols: st.dataframe(df_display_original_cols[selected_original_cols], hide_index=True)
            else: st.dataframe(df_display_original_cols, hide_index=True)
        # ... (Rest of Analysis tab, like Note Details, ensuring similar handling)

    # Tab: Incident Overview (Corrected Plot Layout)
    elif selected_tab == "Incident Overview":
        st.title("📋 Incident Overview")
        if st.session_state.incident_overview_df is not None and not st.session_state.incident_overview_df.empty:
            overview_df_norm = st.session_state.incident_overview_df # This is already normalized, has 'creator'

            plot_col1, plot_col2 = st.columns(2)
            with plot_col1:
                if col_status in overview_df_norm.columns:
                    closed_count = overview_df_norm[overview_df_norm[col_status].astype(str).str.lower() == 'closed'].shape[0]
                    total_incidents = len(overview_df_norm)
                    if total_incidents > 0:
                        chart_data_status = pd.DataFrame({'Status Category': ['Closed', 'Open/Other'], 'Count': [closed_count, total_incidents - closed_count]})
                        fig_status_pie = px.pie(chart_data_status, names='Status Category', values='Count', title='Percentage of Closed Incidents', hole=0.3)
                        fig_status_pie.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_status_pie, use_container_width=True)
                else: st.warning(f"'{col_status}' column missing for status pie chart.")
            with plot_col2:
                if inc_col_team in overview_df_norm.columns:
                    team_dist_data = overview_df_norm[inc_col_team].value_counts()
                    if not team_dist_data.empty:
                        fig_team_dist = px.pie(team_dist_data, names=team_dist_data.index, values=team_dist_data.values, title="Incidents by Team", hole=0.3)
                        fig_team_dist.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_team_dist, use_container_width=True)
                else: st.warning(f"'{inc_col_team}' column missing for team distribution chart.")

            st.markdown("---")
            overview_df_display_original_cols = get_df_with_original_column_names(overview_df_norm, INCIDENT_DF_KEY)
            # ... (Add column selector for this table similar to Analysis tab if desired) ...
            st.dataframe(overview_df_display_original_cols, use_container_width=True, hide_index=True)
        else: st.warning("Incident data not loaded or empty.")

    # Tab: SR Overview (Corrected Multiselects)
    elif selected_tab == "SR Overview":
        st.title("📊 Service Request (SR) Overview")
        if st.session_state.sr_df is not None and not st.session_state.sr_df.empty:
            sr_overview_df_norm = st.session_state.sr_df # Already normalized
            # ... (Chart generation logic remains the same, using sr_overview_df_norm) ...

            st.markdown("---")
            st.subheader("Filterable SR Data")
            table_display_df_norm = sr_overview_df_norm.copy() # Filter this for display
            # ... (Filtering logic for table_display_df_norm) ...

            if not table_display_df_norm.empty:
                table_display_df_orig = get_df_with_original_column_names(table_display_df_norm, SR_DF_KEY)
                all_orig_cols_filterable = table_display_df_orig.columns.tolist()
                
                default_norm_cols_filterable = [sr_col_servicerequest, sr_col_status, sr_col_createdon]
                default_orig_cols_filterable = [st.session_state.column_mappings.get(SR_DF_KEY,{}).get(nc,nc) for nc in default_norm_cols_filterable if st.session_state.column_mappings.get(SR_DF_KEY,{}).get(nc,nc) in all_orig_cols_filterable]

                selected_orig_cols_filterable = st.multiselect("Select columns for Filterable SR Data:", options=all_orig_cols_filterable, default=default_orig_cols_filterable, key="ms_sr_filterable_orig")
                display_filterable = table_display_df_orig[selected_orig_cols_filterable] if selected_orig_cols_filterable else table_display_df_orig
                st.dataframe(display_filterable, hide_index=True)
                # ... (Download button for display_filterable) ...
            else: st.info("No SR data for Filterable SR Data table.")

            st.markdown("---")
            st.subheader("Closed Service Requests")
            # ... (Filtering logic for filtered_closed_srs_df_norm) ...
            filtered_closed_srs_df_norm = sr_overview_df_norm # Placeholder, apply actual filtering

            if not filtered_closed_srs_df_norm.empty:
                filtered_closed_srs_df_orig = get_df_with_original_column_names(filtered_closed_srs_df_norm, SR_DF_KEY)
                all_orig_cols_closed = filtered_closed_srs_df_orig.columns.tolist()

                default_norm_cols_closed = [sr_col_servicerequest, sr_col_status, sr_col_createdon, sr_col_lastmoddatetime, sr_col_resolution]
                default_orig_cols_closed = [st.session_state.column_mappings.get(SR_DF_KEY,{}).get(nc,nc) for nc in default_norm_cols_closed if st.session_state.column_mappings.get(SR_DF_KEY,{}).get(nc,nc) in all_orig_cols_closed]

                selected_orig_cols_closed = st.multiselect("Select columns for Closed SRs:", options=all_orig_cols_closed, default=default_orig_cols_closed, key="ms_sr_closed_orig")
                display_closed = filtered_closed_srs_df_orig[selected_orig_cols_closed] if selected_orig_cols_closed else filtered_closed_srs_df_orig
                st.dataframe(display_closed, hide_index=True)
                # ... (Download button for display_closed) ...
            else: st.info("No SR data for Closed SRs table.")
        else: st.warning("SR data not loaded or empty.")

st.markdown("---")
st.markdown("<div style='text-align:center; color:#888; font-size:0.8em;'>Intellipen SmartQ Test V3.6 | Developed by Ali Babiker | © June 2025</div>", unsafe_allow_html=True)
