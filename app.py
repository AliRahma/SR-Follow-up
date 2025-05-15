import streamlit as st
import pandas as pd
import numpy as np
import re
import io
from datetime import datetime
from streamlit_option_menu import option_menu

# Import utility functions
from utils import (
    classify_and_extract,
    calculate_age,
    is_created_today,
    generate_excel_download,
    generate_csv_download,
    time_since_breach,
    time_to_resolve_after_breach
)

# --- Page Configuration ---
st.set_page_config(
    page_title="SR Analyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
def set_custom_theme():
    st.markdown("""
    <style>
    /* General */
    .main { background-color: #f0f2f6; }
    .stApp { color: #31333F; }
    h1, h2, h3, h4, h5, h6 { color: #0072C6; } /* Main accent color */

    /* DataFrames and Tables */
    .stDataFrame, .stTable {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #E0E0E0;
    }
    div[data-testid="stDataFrame"] table { width: 100%; }
    div[data-testid="stDataFrame"] th:first-child,
    div[data-testid="stDataFrame"] td:first-child {
        width: 40px !important; min-width: 40px !important; max-width: 40px !important;
    }

    /* Cards for Metrics */
    .card {
        background-color: white;
        border-radius: 8px;
        padding: 15px; /* Slightly reduced padding */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #0072C6;
    }
    .metric-value { font-size: 2em; font-weight: bold; margin: 0; color: #1E2A3A; }
    .metric-label { font-size: 0.9em; color: #5E6C84; margin: 0; }

    /* Buttons */
    .stButton>button { /* General buttons, not data processing */
        background-color: #0072C6;
        color: white;
        border-radius: 5px;
        padding: 8px 15px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover { background-color: #005A9E; }
    .stDownloadButton>button {
        background-color: #28a745;
    }
    .stDownloadButton>button:hover { background-color: #218838; }
    
    /* Badges */
    .status-badge { padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: 600; display: inline-block;}
    .badge-pending-sr-incident { background-color: #FFF3CD; color: #856404; } /* Specific for "Pending SR/Incident" */
    .badge-not-triaged { background-color: #E2E3E5; color: #4F545C; }
    .badge-regex-error { background-color: #f5c6cb; color: #721c24; } /* For regex errors */
    .badge-breach-yes { background-color: #F8D7DA; color: #721C24; border: 1px solid #F5C6CB; }
    .badge-breach-no { background-color: #D4EDDA; color: #155724; }


    /* Option Menu */
    .option-menu-horizontal .nav-link {
        font-size: 15px !important;
        padding: 10px 15px !important;
    }
    .option-menu-horizontal .nav-link-selected {
        background-color: #0072C6 !important;
        color: white !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

set_custom_theme()

# --- Session State Initialization ---
def initialize_session_state():
    defaults = {
        'data_loaded': False, 'main_df_raw': None, 'sr_df_raw': None,
        'processed_df': None, 'last_upload_time': None,
        'all_users': [], 'selected_sbar_users': [], # Initialize as empty list
        'sbar_date_range': (None, None),
        # Configurable values
        'config_ticket_regex': r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})',
        'config_sr_min_range': 14000, 'config_sr_max_range': 17000,
        # File tracking
        'last_processed_main_file_id': None, 
        'last_processed_sr_file_id': None,
        # SR Analysis Tab filters
        'sr_analysis_status_filter': "All", 'sr_analysis_type_filter': "All",
        'sr_analysis_sr_status_filter': "All", 'sr_analysis_search_note': "",
        'sr_analysis_selected_cols': None,
        'sr_analysis_current_case_idx': 0,
        # SLA Breach Tab filters
        'sla_breach_status_filter': "All", 'sla_breach_user_filter': "All",
        'sla_breach_selected_cols': None,
        # Today's SR/Incidents Tab filters
        'today_type_filter': "All", 'today_user_filter': "All",
        'today_selected_cols': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# --- Essential Column Definitions ---
ESSENTIAL_MAIN_COLS = ['Case Id', 'Current User Id', 'Case Start Date', 'Last Note', 'Last Note Date']
ESSENTIAL_SR_COLS = ['Service Request', 'Status', 'LastModDateTime']
OPTIONAL_MAIN_COLS = ['Resolution Date']
OPTIONAL_SR_COLS = ['Breach Passed', 'Breach Date']

# --- Data Loading and Processing Functions ---
@st.cache_data(ttl=3600)
def load_data(file, sheet_name=0):
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except Exception as e:
        # st.error(f"Error loading Excel file: {e}") # Avoid st calls in cached func if possible
        print(f"Error loading Excel file: {e}") # Log to console
        return None

def validate_df(df, required_cols, df_name="DataFrame"):
    if df is None: return False
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"{df_name} is missing required columns: {', '.join(missing_cols)}.")
        return False
    return True

def process_and_enrich_data(main_df_raw, sr_df_raw):
    if not validate_df(main_df_raw, ESSENTIAL_MAIN_COLS, "Main Data"):
        return None
    
    main_df = main_df_raw.copy()

    date_cols_main = ['Case Start Date', 'Last Note Date']
    if 'Resolution Date' in main_df.columns and 'Resolution Date' in OPTIONAL_MAIN_COLS:
        date_cols_main.append('Resolution Date')

    for col in date_cols_main:
        if col in main_df.columns:
            main_df[col] = pd.to_datetime(main_df[col], errors='coerce')

    main_df[['Triage Status', 'Ticket Number', 'Type']] = main_df.apply(
        lambda row: pd.Series(classify_and_extract(
            row['Last Note'],
            st.session_state.config_ticket_regex,
            st.session_state.config_sr_min_range,
            st.session_state.config_sr_max_range
        )), axis=1
    )
    main_df['Ticket Number'] = pd.to_numeric(main_df['Ticket Number'], errors='coerce')
    main_df['Age (Days)'] = main_df['Case Start Date'].apply(calculate_age)
    main_df['Created Today Flag'] = main_df['Last Note Date'].apply(is_created_today)

    if sr_df_raw is not None:
        if not validate_df(sr_df_raw, ESSENTIAL_SR_COLS, "SR Status Data"):
            st.warning("SR Status data is invalid. Proceeding without SR-specific enrichments.")
        else:
            sr_df = sr_df_raw.copy()
            sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d+)', expand=False)
            sr_df['Service Request'] = pd.to_numeric(sr_df['Service Request'], errors='coerce')
            sr_df = sr_df.dropna(subset=['Service Request'])
            sr_df = sr_df.drop_duplicates(subset=['Service Request'], keep='last')

            rename_map_sr = {'Status': 'SR Status', 'LastModDateTime': 'SR Last Update'}
            if 'Breach Passed' in OPTIONAL_SR_COLS and 'Breach Passed' in sr_df.columns:
                rename_map_sr['Breach Passed'] = 'SR Breach Passed'
            if 'Breach Date' in OPTIONAL_SR_COLS and 'Breach Date' in sr_df.columns:
                rename_map_sr['Breach Date'] = 'SR Breach Date'
            
            sr_df = sr_df.rename(columns=rename_map_sr)
            
            if 'SR Breach Date' in sr_df.columns:
                 sr_df['SR Breach Date'] = pd.to_datetime(sr_df['SR Breach Date'], errors='coerce')

            merge_cols = ['Service Request', 'SR Status', 'SR Last Update']
            if 'SR Breach Passed' in sr_df.columns: merge_cols.append('SR Breach Passed')
            if 'SR Breach Date' in sr_df.columns: merge_cols.append('SR Breach Date')
            
            main_df = main_df.merge(
                sr_df[merge_cols],
                how='left', left_on='Ticket Number', right_on='Service Request'
            ).drop(columns=['Service Request'], errors='ignore')
            
            if 'SR Breach Date' in main_df.columns:
                 main_df['Time Since Breach'] = main_df.apply(lambda row: time_since_breach(row['SR Breach Date'], row.get('Resolution Date')), axis=1)
                 if 'Resolution Date' in main_df.columns:
                     main_df['Time to Resolve After Breach'] = main_df.apply(lambda row: time_to_resolve_after_breach(row['SR Breach Date'], row['Resolution Date']), axis=1)

    expected_sr_cols_final = ['SR Status', 'SR Last Update', 'SR Breach Passed', 'SR Breach Date', 'Time Since Breach', 'Time to Resolve After Breach']
    for col in expected_sr_cols_final:
        if col not in main_df.columns:
            if 'Date' in col or 'Update' in col: main_df[col] = pd.NaT
            elif 'Passed' in col : main_df[col] = np.nan
            else: main_df[col] = np.nan
            
    if 'Resolution Date' in main_df.columns and 'Case Start Date' in main_df.columns:
        main_df['Resolution Time (Days)'] = (main_df['Resolution Date'] - main_df['Case Start Date']).dt.days
    else:
        main_df['Resolution Time (Days)'] = np.nan

    return main_df

# --- Sidebar ---
with st.sidebar:
    st.title("📊 SR Analyzer Pro")
    st.markdown("---")

    st.subheader("⚙️ Configuration")
    st.session_state.config_ticket_regex = st.text_input("Ticket Regex Pattern", value=st.session_state.config_ticket_regex, key="cfg_regex")
    c1_cfg, c2_cfg = st.columns(2)
    st.session_state.config_sr_min_range = c1_cfg.number_input("SR Min Number", value=st.session_state.config_sr_min_range, step=1, key="cfg_sr_min")
    st.session_state.config_sr_max_range = c2_cfg.number_input("SR Max Number", value=st.session_state.config_sr_max_range, step=1, key="cfg_sr_max")

    st.subheader("📁 Data Import")
    uploaded_main_file = st.file_uploader("Upload Main Excel File", type=["xlsx", "xls"], key="main_file_uploader_widget")
    uploaded_sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type=["xlsx", "xls"], key="sr_file_uploader_widget")

    # --- Automatic Data Processing Logic ---
    current_main_file_id = uploaded_main_file.file_id if uploaded_main_file else None
    current_sr_file_id = uploaded_sr_status_file.file_id if uploaded_sr_status_file else None
    
    config_changed = (
        st.session_state.config_ticket_regex != st.session_state.get('_old_config_ticket_regex', None) or
        st.session_state.config_sr_min_range != st.session_state.get('_old_config_sr_min_range', None) or
        st.session_state.config_sr_max_range != st.session_state.get('_old_config_sr_max_range', None)
    )

    should_process_data = False
    if uploaded_main_file: # Main file must be present
        if current_main_file_id != st.session_state.last_processed_main_file_id:
            should_process_data = True # New main file
        elif current_sr_file_id != st.session_state.last_processed_sr_file_id:
            should_process_data = True # SR file changed (added, removed, or replaced)
        elif config_changed and st.session_state.data_loaded: # Config changed and data was already loaded
            should_process_data = True
        elif not st.session_state.data_loaded: # Data not loaded yet, but files are present
             should_process_data = True


    if should_process_data and uploaded_main_file:
        with st.spinner("Loading and processing data..."):
            main_df_raw_loaded = load_data(uploaded_main_file) # Load fresh
            sr_df_raw_loaded = load_data(uploaded_sr_status_file) if uploaded_sr_status_file else None

            if main_df_raw_loaded is not None:
                processed_df_result = process_and_enrich_data(main_df_raw_loaded, sr_df_raw_loaded)
                if processed_df_result is not None:
                    st.session_state.main_df_raw = main_df_raw_loaded
                    st.session_state.sr_df_raw = sr_df_raw_loaded
                    st.session_state.processed_df = processed_df_result
                    st.session_state.data_loaded = True
                    st.session_state.last_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if 'Current User Id' in processed_df_result.columns:
                        st.session_state.all_users = sorted(processed_df_result['Current User Id'].dropna().unique().tolist())
                    else:
                        st.session_state.all_users = []
                    
                    # Set default users only if they haven't been manually changed OR if all_users list changed
                    # This preserves user's multiselect choices across simple re-processing unless data changes user list
                    default_users_list = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
                    actual_default_users = [u for u in default_users_list if u in st.session_state.all_users]
                    
                    # If selected_sbar_users is empty (initial state) or if its contents are no longer valid against all_users
                    if not st.session_state.selected_sbar_users or \
                       not all(user in st.session_state.all_users for user in st.session_state.selected_sbar_users):
                        st.session_state.selected_sbar_users = actual_default_users
                    
                    st.session_state.last_processed_main_file_id = current_main_file_id
                    st.session_state.last_processed_sr_file_id = current_sr_file_id
                    # Store current config to detect changes next time
                    st.session_state._old_config_ticket_regex = st.session_state.config_ticket_regex
                    st.session_state._old_config_sr_min_range = st.session_state.config_sr_min_range
                    st.session_state._old_config_sr_max_range = st.session_state.config_sr_max_range

                    st.success(f"Data processed automatically: {len(processed_df_result)} records.")
                    # Implicit rerun will happen due to state changes by Streamlit itself
                else:
                    st.error("Failed to process data. Check columns and format.")
                    st.session_state.data_loaded = False # Ensure data_loaded is false on failure
            else:
                st.error("Main data file could not be loaded.")
                st.session_state.data_loaded = False
    elif config_changed and not uploaded_main_file and st.session_state.data_loaded:
        st.warning("Config changed. Please re-upload the main file to apply changes.")
        st.session_state.data_loaded = False # Invalidate old data

    # --- Display status and global filters ---
    if st.session_state.data_loaded:
        st.info(f"Last update: {st.session_state.last_upload_time}")
        st.markdown("---")
        st.subheader("GLOBAL FILTERS")

        # Use the already set (or defaulted) selected_sbar_users
        st.session_state.selected_sbar_users = st.multiselect(
            "Filter by Users (Global)",
            options=st.session_state.all_users,
            default=st.session_state.selected_sbar_users, # This will now use the correctly initialized list
            key="global_user_multiselect_key"
        )

        if 'Case Start Date' in st.session_state.processed_df.columns:
            min_d_filter = st.session_state.processed_df['Case Start Date'].min()
            max_d_filter = st.session_state.processed_df['Case Start Date'].max()
            if pd.NaT not in [min_d_filter, max_d_filter] and min_d_filter <= max_d_filter:
                current_date_range_filter = st.session_state.sbar_date_range
                # Ensure current_date_range_filter is tuple of date objects
                if not (isinstance(current_date_range_filter, tuple) and len(current_date_range_filter) == 2 and 
                        isinstance(current_date_range_filter[0], type(datetime.now().date())) and
                        isinstance(current_date_range_filter[1], type(datetime.now().date()))):
                     current_date_range_filter = (min_d_filter.date(), max_d_filter.date())
                else: # Clamp existing range if it's outside new min/max
                    current_date_range_filter = (
                        max(current_date_range_filter[0], min_d_filter.date()),
                        min(current_date_range_filter[1], max_d_filter.date())
                    )


                st.session_state.sbar_date_range = st.date_input(
                    "Filter by Case Start Date (Global)",
                    value=current_date_range_filter,
                    min_value=min_d_filter.date(), max_value=max_d_filter.date(),
                    key="global_date_range_picker_key"
                )
    elif uploaded_main_file and not st.session_state.data_loaded:
        # This case can happen if processing failed or is in progress
        st.warning("Processing data or waiting for full data load...")
    else: # No files uploaded yet, or config changed and needs re-upload
        st.warning("Upload data to enable filters and analysis.")


# --- Main Content ---
if not st.session_state.data_loaded:
    st.title("📊 SR Analyzer Pro")
    st.markdown("### Welcome! Please upload your data via the sidebar to begin analysis.")
    st.markdown("Data will be processed automatically once files are uploaded.")
else: # Data is loaded and processed
    df_globally_filtered = st.session_state.processed_df.copy()
    if st.session_state.selected_sbar_users: # Filter by users if any selected
        df_globally_filtered = df_globally_filtered[df_globally_filtered['Current User Id'].isin(st.session_state.selected_sbar_users)]

    # Apply date range filter
    if 'Case Start Date' in df_globally_filtered.columns and \
       st.session_state.sbar_date_range and \
       st.session_state.sbar_date_range[0] is not None and \
       st.session_state.sbar_date_range[1] is not None:
        start_dt_sbar_filter, end_dt_sbar_filter = st.session_state.sbar_date_range
        # Ensure the column is datetime before using .dt accessor
        df_globally_filtered['Case Start Date'] = pd.to_datetime(df_globally_filtered['Case Start Date'], errors='coerce')
        df_globally_filtered = df_globally_filtered[
            (df_globally_filtered['Case Start Date'].dt.date >= start_dt_sbar_filter) &
            (df_globally_filtered['Case Start Date'].dt.date <= end_dt_sbar_filter)
        ]

    selected_tab = option_menu(
        menu_title=None,
        options=["SR Analysis", "SLA Breach", "Today's Activity"],
        icons=["kanban", "exclamation-triangle", "calendar-event"],
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
            "container": {"padding": "5px !important", "background-color": "#f0f2f6", "margin-bottom": "15px"},
            "icon": {"color": "#0072C6", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "center", "margin": "0px 5px",
                         "padding": "10px 15px", "border-radius": "5px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#0072C6", "color": "white", "font-weight": "bold"},
        }
    )

    # ========================== SR ANALYSIS TAB ==========================
    if selected_tab == "SR Analysis":
        st.header("🔍 SR Analysis")
        df_tab_filtered_sr = df_globally_filtered.copy()

        st.markdown("##### Filters for this view:")
        f_cols_sr = st.columns(4)
        
        # Triage Status Filter
        triage_options_sr = ["All"] + df_tab_filtered_sr["Triage Status"].dropna().unique().tolist()
        current_triage_filter_sr = st.session_state.sr_analysis_status_filter if st.session_state.sr_analysis_status_filter in triage_options_sr else "All"
        st.session_state.sr_analysis_status_filter = f_cols_sr[0].selectbox("Triage Status", triage_options_sr, index=triage_options_sr.index(current_triage_filter_sr), key='sr_an_ts_sel_key')
        
        # Type Filter
        type_options_sr = ["All", "SR", "Incident"] + [t for t in df_tab_filtered_sr["Type"].dropna().unique() if t not in ["SR", "Incident"]]
        current_type_filter_sr = st.session_state.sr_analysis_type_filter if st.session_state.sr_analysis_type_filter in type_options_sr else "All"
        st.session_state.sr_analysis_type_filter = f_cols_sr[1].selectbox("Type (SR/Incident)", type_options_sr, index=type_options_sr.index(current_type_filter_sr), key='sr_an_ty_sel_key')
        
        # SR Status Filter
        sr_stat_opts_sr = ["All"] + df_tab_filtered_sr['SR Status'].dropna().unique().tolist() + ["N/A (No SR Data)"]
        current_sr_stat_filter_sr = st.session_state.sr_analysis_sr_status_filter if st.session_state.sr_analysis_sr_status_filter in sr_stat_opts_sr else "All"
        st.session_state.sr_analysis_sr_status_filter = f_cols_sr[2].selectbox("SR Status (from SR file)", sr_stat_opts_sr, index=sr_stat_opts_sr.index(current_sr_stat_filter_sr), key='sr_an_srs_sel_key')
        
        st.session_state.sr_analysis_search_note = f_cols_sr[3].text_input("Search in Last Note", st.session_state.sr_analysis_search_note, key='sr_an_search_inp_key')

        if st.session_state.sr_analysis_status_filter != "All": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["Triage Status"] == st.session_state.sr_analysis_status_filter]
        if st.session_state.sr_analysis_type_filter != "All": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["Type"] == st.session_state.sr_analysis_type_filter]
        if st.session_state.sr_analysis_sr_status_filter != "All":
            if st.session_state.sr_analysis_sr_status_filter == "N/A (No SR Data)": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["SR Status"].isna()]
            else: df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["SR Status"] == st.session_state.sr_analysis_sr_status_filter]
        if st.session_state.sr_analysis_search_note: df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr['Last Note'].astype(str).str.contains(st.session_state.sr_analysis_search_note, case=False, na=False)]

        st.markdown("---")
        st.subheader("📊 Summary Tables")
        summary_cols_sr_display = st.columns(3)
        with summary_cols_sr_display[0]:
            st.markdown("**Triage Status Count**")
            if not df_globally_filtered.empty and 'Triage Status' in df_globally_filtered:
                triage_summary_display = df_globally_filtered['Triage Status'].value_counts().reset_index()
                triage_summary_display.columns = ['Triage Status', 'Count']
                st.dataframe(triage_summary_display.set_index('Triage Status'), use_container_width=True)
            else: st.caption("No data for Triage Status summary.")
        with summary_cols_sr_display[1]:
            st.markdown("**Type (SR/Incident) Count**")
            if not df_globally_filtered.empty and 'Type' in df_globally_filtered:
                type_summary_display = df_globally_filtered['Type'].value_counts().reset_index()
                type_summary_display.columns = ['Type', 'Count']
                st.dataframe(type_summary_display.set_index('Type'), use_container_width=True)
            else: st.caption("No data for Type summary.")
        with summary_cols_sr_display[2]:
            st.markdown("**SR Status Count (from SR file)**")
            if 'SR Status' in df_globally_filtered.columns and not df_globally_filtered['SR Status'].dropna().empty:
                sr_status_summary_display = df_globally_filtered['SR Status'].value_counts().reset_index()
                sr_status_summary_display.columns = ['SR Status', 'Count']
                st.dataframe(sr_status_summary_display.set_index('SR Status'), use_container_width=True)
            else: st.caption("SR Status data not available or empty.")

        st.markdown("---")
        st.subheader("📋 Filtered Results Details")
        all_cols_sr_display = df_tab_filtered_sr.columns.tolist()
        def_cols_sr_display = ['Case Id', 'Current User Id', 'Case Start Date', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status', 'SR Last Update', 'Age (Days)']
        if st.session_state.sr_analysis_selected_cols is None or not all(c in all_cols_sr_display for c in st.session_state.sr_analysis_selected_cols): # Initialize or reset if cols changed
            st.session_state.sr_analysis_selected_cols = [col for col in def_cols_sr_display if col in all_cols_sr_display]

        with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
            st.session_state.sr_analysis_selected_cols = st.multiselect("Select columns:", all_cols_sr_display, default=st.session_state.sr_analysis_selected_cols, key="sr_an_col_sel_key")
            if not df_tab_filtered_sr.empty and st.session_state.sr_analysis_selected_cols:
                ex_c1_sr, ex_c2_sr = st.columns(2)
                excel_data_sr_dl = generate_excel_download(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols], "SR_Analysis")
                ex_c1_sr.download_button("📥 Excel", excel_data_sr_dl, f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel_sr")
                csv_data_sr_dl = generate_csv_download(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols])
                ex_c2_sr.download_button("📝 CSV", csv_data_sr_dl, f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", key="dl_csv_sr")
            elif df_tab_filtered_sr.empty: st.warning("No data to export.")
        
        st.info(f"Showing {len(df_tab_filtered_sr)} records.")
        if not df_tab_filtered_sr.empty and st.session_state.sr_analysis_selected_cols:
            st.dataframe(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols], height=400, use_container_width=True)
        elif df_tab_filtered_sr.empty: st.warning("No data matches filters.")
        else: st.warning("Select columns to display or data is empty.")

        st.markdown("---")
        st.subheader("📝 Case Details & Note Viewer")
        if not df_tab_filtered_sr.empty:
            ids_sr_display = df_tab_filtered_sr['Case Id'].tolist()
            if ids_sr_display:
                nav_c1_sr, nav_c2_sr, nav_c3_sr = st.columns([1,5,1])
                if nav_c1_sr.button("⬅️ Prev", key="sr_prev_case_key") and st.session_state.sr_analysis_current_case_idx > 0: st.session_state.sr_analysis_current_case_idx -= 1
                if nav_c3_sr.button("Next ➡️", key="sr_next_case_key") and st.session_state.sr_analysis_current_case_idx < len(ids_sr_display) - 1: st.session_state.sr_analysis_current_case_idx += 1
                
                # Ensure index is valid after button presses or if list shrinks
                st.session_state.sr_analysis_current_case_idx = min(max(0, st.session_state.sr_analysis_current_case_idx), len(ids_sr_display)-1 if ids_sr_display else 0)

                sel_id_sr_display = nav_c2_sr.selectbox("Select Case ID:", ids_sr_display, index=st.session_state.sr_analysis_current_case_idx, key="sr_an_case_sel_key")
                # Update index if selectbox changes it directly
                if sel_id_sr_display != ids_sr_display[st.session_state.sr_analysis_current_case_idx]: st.session_state.sr_analysis_current_case_idx = ids_sr_display.index(sel_id_sr_display)

                case_row_sr_display = df_tab_filtered_sr[df_tab_filtered_sr['Case Id'] == sel_id_sr_display].iloc[0]
                det_c1_sr, det_c2_sr = st.columns(2)
                triage_stat_html_class_sr = str(case_row_sr_display.get('Triage Status','unknown')).lower().replace(' ','-').replace('/','-') # Sanitize for CSS class
                with det_c1_sr:
                    st.markdown(f"**Case ID:** {case_row_sr_display['Case Id']}")
                    st.markdown(f"**Owner:** {case_row_sr_display.get('Current User Id', 'N/A')}")
                    st.markdown(f"**Start Date:** {case_row_sr_display.get('Case Start Date', pd.NaT).strftime('%Y-%m-%d %H:%M') if pd.notna(case_row_sr_display.get('Case Start Date')) else 'N/A'}")
                    st.markdown(f"**Triage Status:** <span class='status-badge badge-{triage_stat_html_class_sr}'>{case_row_sr_display.get('Triage Status','N/A')}</span>", unsafe_allow_html=True)
                with det_c2_sr:
                    st.markdown(f"**Ticket Number:** {int(case_row_sr_display['Ticket Number']) if pd.notna(case_row_sr_display['Ticket Number']) else 'N/A'}")
                    st.markdown(f"**Type:** {case_row_sr_display.get('Type', 'N/A')}")
                    st.markdown(f"**SR Status:** {case_row_sr_display.get('SR Status', 'N/A')}")
                    if 'SR Breach Passed' in case_row_sr_display and pd.notna(case_row_sr_display['SR Breach Passed']):
                        breach_txt_sr = "Yes ⚠️" if case_row_sr_display['SR Breach Passed'] else "No"
                        breach_class_sr = "badge-breach-yes" if case_row_sr_display['SR Breach Passed'] else "badge-breach-no"
                        st.markdown(f"**SLA Breach:** <span class='status-badge {breach_class_sr}'>{breach_txt_sr}</span>", unsafe_allow_html=True)
                
                st.markdown("##### Last Note:")
                note_sr_display = str(case_row_sr_display.get('Last Note', 'No note available.'))
                if st.session_state.sr_analysis_search_note: note_sr_display = re.sub(f"({re.escape(st.session_state.sr_analysis_search_note)})", r"<mark>\1</mark>", note_sr_display, flags=re.IGNORECASE)
                st.markdown(f"<div style='background-color:#f9f9f9; border:1px solid #eee; padding:10px; border-radius:5px; max-height:200px; overflow-y:auto;'>{note_sr_display}</div>", unsafe_allow_html=True)
            else: st.info("No cases to display in detail view for current filters.")
        else: st.info("No data for case details. Adjust filters or upload data.")

    # ========================== SLA BREACH TAB ==========================
    elif selected_tab == "SLA Breach":
        st.header("⚠️ SLA Breach Analysis")
        if 'SR Breach Passed' not in df_globally_filtered.columns or df_globally_filtered['SR Breach Passed'].isna().all():
            st.warning("SLA Breach data ('SR Breach Passed' column) not found or empty. Ensure SR Status file has this information.")
        else:
            breach_df_all_tab = df_globally_filtered[df_globally_filtered['SR Breach Passed'] == True].copy() # Filter for breached cases
            
            st.markdown("##### Breach Summary Metrics")
            met_c1_b, met_c2_b, met_c3_b = st.columns(3)
            met_c1_b.markdown(f"""<div class="card"><p class="metric-label">Total Breached Cases (in selection)</p><p class="metric-value">{len(breach_df_all_tab)}</p></div>""", unsafe_allow_html=True)
            open_stats_b = ['Open', 'In Progress', 'Pending', 'Assigned'] # Customize as needed
            open_b_count = len(breach_df_all_tab[breach_df_all_tab['SR Status'].isin(open_stats_b)]) if 'SR Status' in breach_df_all_tab else 'N/A'
            met_c2_b.markdown(f"""<div class="card"><p class="metric-label">Open Breached Cases</p><p class="metric-value">{open_b_count}</p></div>""", unsafe_allow_html=True)
            users_aff_b = breach_df_all_tab['Current User Id'].nunique() if 'Current User Id' in breach_df_all_tab else 'N/A'
            met_c3_b.markdown(f"""<div class="card"><p class="metric-label">Users with Breaches</p><p class="metric-value">{users_aff_b}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            bf_c1_b, bf_c2_b = st.columns(2)
            
            s_opts_b_tab = ["All"] + (breach_df_all_tab['SR Status'].dropna().unique().tolist() if 'SR Status' in breach_df_all_tab and not breach_df_all_tab.empty else [])
            current_s_filter_b = st.session_state.sla_breach_status_filter if st.session_state.sla_breach_status_filter in s_opts_b_tab else "All"
            st.session_state.sla_breach_status_filter = bf_c1_b.selectbox("Filter by SR Status", s_opts_b_tab, index=s_opts_b_tab.index(current_s_filter_b), key='sla_b_stat_sel_key')
            
            u_opts_b_tab = ["All"] + (breach_df_all_tab['Current User Id'].dropna().unique().tolist() if 'Current User Id' in breach_df_all_tab and not breach_df_all_tab.empty else [])
            current_u_filter_b = st.session_state.sla_breach_user_filter if st.session_state.sla_breach_user_filter in u_opts_b_tab else "All"
            st.session_state.sla_breach_user_filter = bf_c2_b.selectbox("Filter by User", u_opts_b_tab, index=u_opts_b_tab.index(current_u_filter_b), key='sla_b_user_sel_key')

            df_tab_filtered_breach_display = breach_df_all_tab.copy()
            if st.session_state.sla_breach_status_filter != "All" and 'SR Status' in df_tab_filtered_breach_display: df_tab_filtered_breach_display = df_tab_filtered_breach_display[df_tab_filtered_breach_display['SR Status'] == st.session_state.sla_breach_status_filter]
            if st.session_state.sla_breach_user_filter != "All" and 'Current User Id' in df_tab_filtered_breach_display: df_tab_filtered_breach_display = df_tab_filtered_breach_display[df_tab_filtered_breach_display['Current User Id'] == st.session_state.sla_breach_user_filter]

            st.markdown("---")
            st.subheader("📋 Breached Cases Details")
            def_cols_b_display = ['Case Id', 'Current User Id', 'Ticket Number', 'Type', 'SR Status', 'SR Breach Date', 'Age (Days)', 'Time Since Breach', 'Time to Resolve After Breach']
            all_cols_b_display = df_tab_filtered_breach_display.columns.tolist()
            if st.session_state.sla_breach_selected_cols is None or not all(c in all_cols_b_display for c in st.session_state.sla_breach_selected_cols):
                st.session_state.sla_breach_selected_cols = [col for col in def_cols_b_display if col in all_cols_b_display]
            
            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                st.session_state.sla_breach_selected_cols = st.multiselect("Select columns:", all_cols_b_display, default=st.session_state.sla_breach_selected_cols, key="sla_b_col_sel_key")
                if not df_tab_filtered_breach_display.empty and st.session_state.sla_breach_selected_cols:
                    bex_c1_dl, bex_c2_dl = st.columns(2)
                    excel_data_b_dl = generate_excel_download(df_tab_filtered_breach_display[st.session_state.sla_breach_selected_cols], "SLA_Breaches")
                    bex_c1_dl.download_button("📥 Excel", excel_data_b_dl, f"sla_breaches_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel_b")
                    csv_data_b_dl = generate_csv_download(df_tab_filtered_breach_display[st.session_state.sla_breach_selected_cols])
                    bex_c2_dl.download_button("📝 CSV", csv_data_b_dl, f"sla_breaches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", key="dl_csv_b")
                elif df_tab_filtered_breach_display.empty: st.warning("No breached cases to export.")

            st.info(f"Showing {len(df_tab_filtered_breach_display)} breached records based on current filters.")
            if not df_tab_filtered_breach_display.empty and st.session_state.sla_breach_selected_cols:
                st.dataframe(df_tab_filtered_breach_display[st.session_state.sla_breach_selected_cols], height=300, use_container_width=True)
            elif df_tab_filtered_breach_display.empty: st.warning("No breached cases match current filters.")
            else: st.warning("Select columns to display or data is empty.")

            if not df_tab_filtered_breach_display.empty:
                st.markdown("---")
                st.subheader("📊 Breach Analysis by Group (Tables)")
                gb_c1_disp, gb_c2_disp = st.columns(2)
                with gb_c1_disp:
                    if 'Current User Id' in df_tab_filtered_breach_display:
                        st.markdown("**Breaches by User (Top 10)**")
                        breach_by_user_tb_disp = df_tab_filtered_breach_display.groupby('Current User Id').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        st.dataframe(breach_by_user_tb_disp.set_index('Current User Id').head(10), use_container_width=True)
                with gb_c2_disp:
                    if 'Type' in df_tab_filtered_breach_display:
                        st.markdown("**Breaches by Type**")
                        breach_by_type_tb_disp = df_tab_filtered_breach_display.groupby('Type').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        st.dataframe(breach_by_type_tb_disp.set_index('Type'), use_container_width=True)

    # ========================== TODAY'S ACTIVITY TAB ==========================
    elif selected_tab == "Today's Activity":
        st.header("📅 Today's Activity (Based on Last Note Date)")
        if 'Created Today Flag' not in df_globally_filtered.columns:
            st.warning("'Created Today Flag' column not found. This feature requires 'Last Note Date'.")
        else:
            today_df_all_tab = df_globally_filtered[df_globally_filtered['Created Today Flag'] == True].copy()

            st.markdown("##### Today's Activity Summary")
            tm_c1_td, tm_c2_td, tm_c3_td = st.columns(3)
            tm_c1_td.markdown(f"""<div class="card"><p class="metric-label">Total Activities Today (in selection)</p><p class="metric-value">{len(today_df_all_tab)}</p></div>""", unsafe_allow_html=True)
            sr_td_c_val = len(today_df_all_tab[today_df_all_tab['Type'] == 'SR']) if 'Type' in today_df_all_tab else 'N/A'
            tm_c2_td.markdown(f"""<div class="card"><p class="metric-label">SRs Today</p><p class="metric-value">{sr_td_c_val}</p></div>""", unsafe_allow_html=True)
            inc_td_c_val = len(today_df_all_tab[today_df_all_tab['Type'] == 'Incident']) if 'Type' in today_df_all_tab else 'N/A'
            tm_c3_td.markdown(f"""<div class="card"><p class="metric-label">Incidents Today</p><p class="metric-value">{inc_td_c_val}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            tdf_c1_td, tdf_c2_td = st.columns(2)
            
            t_opts_td_tab = ["All", "SR", "Incident"] + ([t for t in today_df_all_tab["Type"].dropna().unique() if t not in ["SR", "Incident"]] if 'Type' in today_df_all_tab and not today_df_all_tab.empty else [])
            current_t_filter_td = st.session_state.today_type_filter if st.session_state.today_type_filter in t_opts_td_tab else "All"
            st.session_state.today_type_filter = tdf_c1_td.selectbox("Filter by Type", t_opts_td_tab, index=t_opts_td_tab.index(current_t_filter_td), key='td_type_sel_key')
            
            u_opts_td_tab = ["All"] + (today_df_all_tab['Current User Id'].dropna().unique().tolist() if 'Current User Id' in today_df_all_tab and not today_df_all_tab.empty else [])
            current_u_filter_td = st.session_state.today_user_filter if st.session_state.today_user_filter in u_opts_td_tab else "All"
            st.session_state.today_user_filter = tdf_c2_td.selectbox("Filter by User", u_opts_td_tab, index=u_opts_td_tab.index(current_u_filter_td), key='td_user_sel_key')

            df_tab_filtered_today_display = today_df_all_tab.copy()
            if st.session_state.today_type_filter != "All" and 'Type' in df_tab_filtered_today_display: df_tab_filtered_today_display = df_tab_filtered_today_display[df_tab_filtered_today_display['Type'] == st.session_state.today_type_filter]
            if st.session_state.today_user_filter != "All" and 'Current User Id' in df_tab_filtered_today_display: df_tab_filtered_today_display = df_tab_filtered_today_display[df_tab_filtered_today_display['Current User Id'] == st.session_state.today_user_filter]

            st.markdown("---")
            st.subheader("📋 Today's Activity Details")
            def_cols_td_display = ['Case Id', 'Current User Id', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status']
            all_cols_td_display = df_tab_filtered_today_display.columns.tolist()
            if st.session_state.today_selected_cols is None or not all(c in all_cols_td_display for c in st.session_state.today_selected_cols):
                st.session_state.today_selected_cols = [col for col in def_cols_td_display if col in all_cols_td_display]

            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                st.session_state.today_selected_cols = st.multiselect("Select columns:", all_cols_td_display, default=st.session_state.today_selected_cols, key="td_col_sel_key")
                if not df_tab_filtered_today_display.empty and st.session_state.today_selected_cols:
                    tex_c1_dl, tex_c2_dl = st.columns(2)
                    excel_data_td_dl = generate_excel_download(df_tab_filtered_today_display[st.session_state.today_selected_cols], "Today_Activity")
                    tex_c1_dl.download_button("📥 Excel", excel_data_td_dl, f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel_td")
                    csv_data_td_dl = generate_csv_download(df_tab_filtered_today_display[st.session_state.today_selected_cols])
                    tex_c2_dl.download_button("📝 CSV", csv_data_td_dl, f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", key="dl_csv_td")
                elif df_tab_filtered_today_display.empty: st.warning("No data for today to export.")
            
            st.info(f"Showing {len(df_tab_filtered_today_display)} activities from today based on current filters.")
            if not df_tab_filtered_today_display.empty and st.session_state.today_selected_cols:
                st.dataframe(df_tab_filtered_today_display[st.session_state.today_selected_cols], height=300, use_container_width=True)
            elif df_tab_filtered_today_display.empty: st.warning("No activities found for today with current filters.")
            else: st.warning("Select columns to display or data is empty.")

# --- Footer ---
st.markdown("---")
st.markdown(f"""<div style="text-align:center; color:#888; font-size:0.9em;">
📊 SR Analyzer Pro | © {datetime.now().year}
</div>""", unsafe_allow_html=True)