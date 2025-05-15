import streamlit as st
import pandas as pd
import numpy as np
import re
import io
# import base64 # Not explicitly used in the final version, can be removed
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import plotly.express as px

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
    page_title="SR Analyzer Pro Elite",
    page_icon="🚀",
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
    h1, h2, h3 { color: #0072C6; } /* Main accent color */

    /* DataFrames and Tables */
    .stDataFrame, .stTable {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #E0E0E0;
    }
    div[data-testid="stDataFrame"] table { width: 100%; }
    div[data-testid="stDataFrame"] th:first-child,
    div[data-testid="stDataFrame"] td:first-child { /* For selection checkbox column */
        width: 40px !important; min-width: 40px !important; max-width: 40px !important;
    }

    /* Cards for Metrics */
    .card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #0072C6; /* Accent border */
    }
    .metric-value { font-size: 2.2em; font-weight: bold; margin: 0; color: #1E2A3A; }
    .metric-label { font-size: 0.95em; color: #5E6C84; margin: 0; }

    /* Buttons */
    .stButton>button {
        background-color: #0072C6;
        color: white;
        border-radius: 5px;
        padding: 8px 15px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover { background-color: #005A9E; }
    .stDownloadButton>button {
        background-color: #28a745; /* Green for download */
    }
    .stDownloadButton>button:hover { background-color: #218838; }

    /* Badges (simplified for brevity, can be expanded) */
    .status-badge { padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: 600; }
    .badge-pending { background-color: #FFF3CD; color: #856404; }
    .badge-complete { background-color: #D4EDDA; color: #155724; }
    .badge-in-progress { background-color: #D1ECF1; color: #0C5460; }
    .badge-breach { background-color: #F8D7DA; color: #721C24; border: 1px solid #F5C6CB; }
    .badge-not-triaged { background-color: #E2E3E5; color: #4F545C; }

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
        'data_loaded': False, 'main_df': None, 'sr_df': None,
        'processed_df': None, 'last_upload_time': None,
        'all_users': [], 'selected_sbar_users': [], 'sbar_date_range': (None, None),
        # Configurable values
        'config_ticket_regex': r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})',
        'config_sr_min_range': 14000, 'config_sr_max_range': 17000,
        # SR Analysis Tab filters
        'sr_analysis_status_filter': "All", 'sr_analysis_type_filter': "All",
        'sr_analysis_sr_status_filter': "All", 'sr_analysis_search_note': "",
        'sr_analysis_selected_cols': None, # Will be populated later
        'sr_analysis_current_case_idx': 0,
        # SLA Breach Tab filters
        'sla_breach_status_filter': "All", 'sla_breach_user_filter': "All",
        'sla_breach_current_case_idx': 0,
        # Today's SR/Incidents Tab filters
        'today_type_filter': "All", 'today_user_filter': "All",
        'today_current_case_idx': 0,
        # User Performance Tab filters
        'user_perf_selected_users': [],
        # Trend Analysis Tab filters
        'trend_time_group': 'D' # Daily by default
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# --- Essential Column Definitions (Adapt to your Excel files) ---
# These should match your actual column names
ESSENTIAL_MAIN_COLS = ['Case Id', 'Current User Id', 'Case Start Date', 'Last Note', 'Last Note Date']
ESSENTIAL_SR_COLS = ['Service Request', 'Status', 'LastModDateTime'] # 'Breach Passed' is optional but good
OPTIONAL_MAIN_COLS = ['Resolution Date'] # For performance metrics
OPTIONAL_SR_COLS = ['Breach Passed', 'Breach Date'] # For SLA analysis

# --- Data Loading and Processing Functions ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def load_data(file, sheet_name=0):
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

def validate_df(df, required_cols, df_name="DataFrame"):
    if df is None:
        return False
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"{df_name} is missing required columns: {', '.join(missing_cols)}. Please check the uploaded file.")
        return False
    return True

def process_and_enrich_data(main_df_raw, sr_df_raw):
    if not validate_df(main_df_raw, ESSENTIAL_MAIN_COLS, "Main Data"):
        return None
    
    main_df = main_df_raw.copy()

    # Date Conversions for Main DF
    date_cols_main = ['Case Start Date', 'Last Note Date']
    if 'Resolution Date' in main_df.columns: # Optional
        date_cols_main.append('Resolution Date')

    for col in date_cols_main:
        if col in main_df.columns:
            main_df[col] = pd.to_datetime(main_df[col], errors='coerce') # Coerce for robustness

    # Classify and Extract Ticket Info
    main_df[['Triage Status', 'Ticket Number', 'Type']] = main_df.apply(
        lambda row: pd.Series(classify_and_extract(
            row['Last Note'],
            st.session_state.config_ticket_regex,
            st.session_state.config_sr_min_range,
            st.session_state.config_sr_max_range
        )), axis=1
    )
    main_df['Ticket Number'] = pd.to_numeric(main_df['Ticket Number'], errors='coerce')

    # Calculate Age and Created Today
    main_df['Age (Days)'] = main_df['Case Start Date'].apply(calculate_age)
    main_df['Created Today Flag'] = main_df['Last Note Date'].apply(is_created_today)

    # Merge with SR Status Data (if available)
    if sr_df_raw is not None:
        if not validate_df(sr_df_raw, ESSENTIAL_SR_COLS, "SR Status Data"):
            st.warning("SR Status data is invalid. Proceeding without it.")
            # Add empty SR-related columns to main_df to prevent KeyErrors later
            for col in ['SR Status', 'SR Last Update', 'SR Breach Passed', 'SR Breach Date']:
                if col not in main_df.columns: main_df[col] = np.nan
        else:
            sr_df = sr_df_raw.copy()
            sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d+)', expand=False)
            sr_df['Service Request'] = pd.to_numeric(sr_df['Service Request'], errors='coerce')
            sr_df = sr_df.dropna(subset=['Service Request'])
            sr_df = sr_df.drop_duplicates(subset=['Service Request'], keep='last') # Keep most recent SR status

            sr_df = sr_df.rename(columns={
                'Status': 'SR Status',
                'LastModDateTime': 'SR Last Update'
            })
            # Ensure Breach Passed and Breach Date exist, if not, create them as NaN
            if 'Breach Passed' not in sr_df.columns and 'SR Breach Passed' not in sr_df.columns:
                 sr_df['SR Breach Passed'] = np.nan # Or False by default
            elif 'Breach Passed' in sr_df.columns and 'SR Breach Passed' not in sr_df.columns:
                sr_df = sr_df.rename(columns={'Breach Passed': 'SR Breach Passed'})

            if 'Breach Date' not in sr_df.columns and 'SR Breach Date' not in sr_df.columns:
                sr_df['SR Breach Date'] = pd.NaT
            elif 'Breach Date' in sr_df.columns and 'SR Breach Date' not in sr_df.columns:
                sr_df = sr_df.rename(columns={'Breach Date': 'SR Breach Date'})
                sr_df['SR Breach Date'] = pd.to_datetime(sr_df['SR Breach Date'], errors='coerce')

            merge_cols = ['Service Request', 'SR Status', 'SR Last Update']
            if 'SR Breach Passed' in sr_df.columns: merge_cols.append('SR Breach Passed')
            if 'SR Breach Date' in sr_df.columns: merge_cols.append('SR Breach Date')
            
            main_df = main_df.merge(
                sr_df[merge_cols],
                how='left',
                left_on='Ticket Number',
                right_on='Service Request'
            ).drop(columns=['Service Request'], errors='ignore')
            
            # Calculate time since breach / time to resolve after breach
            if 'SR Breach Date' in main_df.columns:
                 main_df['Time Since Breach'] = main_df.apply(lambda row: time_since_breach(row['SR Breach Date'], row.get('Resolution Date')), axis=1)
                 if 'Resolution Date' in main_df.columns:
                     main_df['Time to Resolve After Breach'] = main_df.apply(lambda row: time_to_resolve_after_breach(row['SR Breach Date'], row['Resolution Date']), axis=1)


    # Ensure all expected columns exist, even if SR file wasn't loaded or valid
    expected_sr_cols = ['SR Status', 'SR Last Update', 'SR Breach Passed', 'SR Breach Date', 'Time Since Breach', 'Time to Resolve After Breach']
    for col in expected_sr_cols:
        if col not in main_df.columns:
            if 'Date' in col or 'Update' in col: main_df[col] = pd.NaT
            elif 'Passed' in col : main_df[col] = np.nan # or False
            else: main_df[col] = np.nan


    # Calculate Resolution Time if 'Resolution Date' is available
    if 'Resolution Date' in main_df.columns and 'Case Start Date' in main_df.columns:
        main_df['Resolution Time (Days)'] = (main_df['Resolution Date'] - main_df['Case Start Date']).dt.days
    else:
        main_df['Resolution Time (Days)'] = np.nan


    return main_df

# --- Sidebar ---
with st.sidebar:
    st.title("🚀 SR Analyzer Pro Elite")
    st.markdown("---")

    st.subheader("⚙️ Configuration")
    st.session_state.config_ticket_regex = st.text_input(
        "Ticket Regex Pattern",
        value=st.session_state.config_ticket_regex,
        help="Regex to find ticket numbers. Group 2 should be the number. e.g., `(SR|INC)-?(\d{5,})`"
    )
    col_sr1, col_sr2 = st.columns(2)
    st.session_state.config_sr_min_range = col_sr1.number_input("SR Min Number", value=st.session_state.config_sr_min_range, step=1)
    st.session_state.config_sr_max_range = col_sr2.number_input("SR Max Number", value=st.session_state.config_sr_max_range, step=1)


    st.subheader("📁 Data Import")
    uploaded_main_file = st.file_uploader("Upload Main Excel File (.xlsx, .xls)", type=["xlsx", "xls"], key="main_uploader")
    uploaded_sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type=["xlsx", "xls"], key="sr_uploader")

    if uploaded_main_file:
        if st.button("🔄 Process Uploaded Data", use_container_width=True):
            with st.spinner("Loading and processing data..."):
                main_df_raw = load_data(uploaded_main_file)
                sr_df_raw = load_data(uploaded_sr_status_file) if uploaded_sr_status_file else None

                if main_df_raw is not None:
                    processed_df = process_and_enrich_data(main_df_raw, sr_df_raw)
                    if processed_df is not None:
                        st.session_state.main_df = main_df_raw # Store raw for re-processing if config changes
                        st.session_state.sr_df = sr_df_raw     # Store raw
                        st.session_state.processed_df = processed_df
                        st.session_state.data_loaded = True
                        st.session_state.last_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        if 'Current User Id' in processed_df.columns:
                            st.session_state.all_users = sorted(processed_df['Current User Id'].dropna().unique().tolist())
                        else:
                            st.session_state.all_users = []
                        st.success(f"Data processed: {len(processed_df)} records.")
                        st.experimental_rerun() # Rerun to update UI with loaded data
                    else:
                        st.error("Failed to process data. Check column names and data format.")
                else:
                    st.error("Failed to load main data file.")
    
    if st.session_state.data_loaded:
        st.info(f"Last data update: {st.session_state.last_upload_time}")

        st.markdown("---")
        st.subheader("GLOBAL FILTERS")
        # User filter
        default_users_sbar = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa'] # Example
        sbar_users_to_select = [u for u in default_users_sbar if u in st.session_state.all_users]
        
        st.session_state.selected_sbar_users = st.multiselect(
            "Filter by Users (Global)",
            options=st.session_state.all_users,
            default=st.session_state.get('selected_sbar_users', sbar_users_to_select) # Persist selection
        )

        # Date range filter
        if 'Case Start Date' in st.session_state.processed_df.columns:
            min_date_sbar = st.session_state.processed_df['Case Start Date'].min()
            max_date_sbar = st.session_state.processed_df['Case Start Date'].max()
            if pd.NaT not in [min_date_sbar, max_date_sbar] and min_date_sbar <= max_date_sbar : # Check for valid date range
                # Persist date range selection
                current_sbar_date_range = st.session_state.get('sbar_date_range', (min_date_sbar.date(), max_date_sbar.date()))
                if current_sbar_date_range[0] is None or current_sbar_date_range[1] is None :
                    current_sbar_date_range = (min_date_sbar.date(), max_date_sbar.date())


                st.session_state.sbar_date_range = st.date_input(
                    "Filter by Case Start Date (Global)",
                    value=current_sbar_date_range,
                    min_value=min_date_sbar.date(),
                    max_value=max_date_sbar.date(),
                    key="sbar_date_filter"
                )
            else:
                st.warning("Case Start Date column has invalid data for date range filter.")
    else:
        st.warning("Upload and process data to enable filters.")


# --- Main Content ---
if not st.session_state.data_loaded:
    st.title("🚀 SR Analyzer Pro Elite")
    st.markdown("""
    ### Welcome! Analyze your Service Requests and Incidents with ease.
    1.  **Configure** ticket identification parameters in the sidebar (optional).
    2.  **Upload** your main Excel file.
    3.  **Optionally upload** an SR status file for richer analysis.
    4.  Click **"Process Uploaded Data"**.
    5.  Navigate through the tabs to explore your data.
    """)
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg", width=300) # Placeholder image
else:
    # Apply global filters from sidebar
    df_globally_filtered = st.session_state.processed_df.copy()
    if st.session_state.selected_sbar_users:
        df_globally_filtered = df_globally_filtered[df_globally_filtered['Current User Id'].isin(st.session_state.selected_sbar_users)]

    if 'Case Start Date' in df_globally_filtered.columns and \
       st.session_state.sbar_date_range and \
       st.session_state.sbar_date_range[0] is not None and \
       st.session_state.sbar_date_range[1] is not None:
        start_date_sbar, end_date_sbar = st.session_state.sbar_date_range
        # Ensure Series is datetime before .dt accessor
        df_globally_filtered['Case Start Date'] = pd.to_datetime(df_globally_filtered['Case Start Date'], errors='coerce')
        df_globally_filtered = df_globally_filtered[
            (df_globally_filtered['Case Start Date'].dt.date >= start_date_sbar) &
            (df_globally_filtered['Case Start Date'].dt.date <= end_date_sbar)
        ]

    # --- Tab Interface ---
    selected_tab = option_menu(
        menu_title=None,
        options=["SR Analysis", "SLA Breach", "Today's Activity", "User Performance", "Trend Analysis"],
        icons=["kanban", "exclamation-triangle", "calendar-event", "people-fill", "graph-up"],
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
            "container": {"padding": "5px !important", "background-color": "#f0f2f6", "margin-bottom": "15px"},
            "icon": {"color": "#0072C6", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "center", "margin": "0px 5px",
                         "padding": "10px 15px", "border-radius": "5px", "--hover-color": "#e0e0e0"},
            "nav-link-selected": {"background-color": "#0072C6", "color": "white", "font-weight": "bold"},
        }
    )

    # ==============================================================================
    # SR ANALYSIS TAB
    # ==============================================================================
    if selected_tab == "SR Analysis":
        st.header("🔍 SR Analysis")
        df_tab_filtered = df_globally_filtered.copy()

        # --- Filters for this tab ---
        st.markdown("##### Filters for this view:")
        filter_cols = st.columns(4)
        with filter_cols[0]:
            st.session_state.sr_analysis_status_filter = st.selectbox(
                "Triage Status", ["All"] + df_tab_filtered["Triage Status"].dropna().unique().tolist(),
                key='sr_triage_filter', index=0 if st.session_state.sr_analysis_status_filter == "All" else (["All"] + df_tab_filtered["Triage Status"].dropna().unique().tolist()).index(st.session_state.sr_analysis_status_filter)
            )
        with filter_cols[1]:
            st.session_state.sr_analysis_type_filter = st.selectbox(
                "Type (SR/Incident)", ["All", "SR", "Incident"] + [t for t in df_tab_filtered["Type"].dropna().unique() if t not in ["SR", "Incident"]], # Include other types if any
                key='sr_type_filter', index=0 if st.session_state.sr_analysis_type_filter == "All" else (["All", "SR", "Incident"] + [t for t in df_tab_filtered["Type"].dropna().unique() if t not in ["SR", "Incident"]]).index(st.session_state.sr_analysis_type_filter)
            )
        with filter_cols[2]:
            sr_status_options = ["All"] + df_tab_filtered['SR Status'].dropna().unique().tolist() + ["N/A (No SR Data)"]
            st.session_state.sr_analysis_sr_status_filter = st.selectbox(
                "SR Status (from SR file)", sr_status_options, key='sr_status_file_filter',
                index=0 if st.session_state.sr_analysis_sr_status_filter == "All" else sr_status_options.index(st.session_state.sr_analysis_sr_status_filter)
            )
        with filter_cols[3]:
            st.session_state.sr_analysis_search_note = st.text_input("Search in Last Note", st.session_state.sr_analysis_search_note, key='sr_note_search')

        # Apply tab-specific filters
        if st.session_state.sr_analysis_status_filter != "All":
            df_tab_filtered = df_tab_filtered[df_tab_filtered["Triage Status"] == st.session_state.sr_analysis_status_filter]
        if st.session_state.sr_analysis_type_filter != "All":
            df_tab_filtered = df_tab_filtered[df_tab_filtered["Type"] == st.session_state.sr_analysis_type_filter]
        if st.session_state.sr_analysis_sr_status_filter != "All":
            if st.session_state.sr_analysis_sr_status_filter == "N/A (No SR Data)":
                df_tab_filtered = df_tab_filtered[df_tab_filtered["SR Status"].isna()]
            else:
                df_tab_filtered = df_tab_filtered[df_tab_filtered["SR Status"] == st.session_state.sr_analysis_sr_status_filter]
        if st.session_state.sr_analysis_search_note:
            df_tab_filtered = df_tab_filtered[df_tab_filtered['Last Note'].str.contains(st.session_state.sr_analysis_search_note, case=False, na=False)]

        # --- Summary Visualizations ---
        st.markdown("---")
        st.subheader("📊 Summary Dashboards")
        summary_cols = st.columns(3)
        with summary_cols[0]:
            if not df_globally_filtered.empty:
                triage_summary = df_globally_filtered['Triage Status'].value_counts().reset_index()
                triage_summary.columns = ['Triage Status', 'Count']
                fig_triage = px.pie(triage_summary, names='Triage Status', values='Count', title="Triage Status Distribution", hole=0.3)
                fig_triage.update_layout(legend_title_text='Triage Status')
                st.plotly_chart(fig_triage, use_container_width=True)
            else: st.info("No data for Triage Status chart.")
        with summary_cols[1]:
            if not df_globally_filtered.empty and 'Type' in df_globally_filtered.columns:
                type_summary = df_globally_filtered['Type'].value_counts().reset_index()
                type_summary.columns = ['Type', 'Count']
                fig_type = px.bar(type_summary, x='Type', y='Count', title="SR vs Incident Count", color='Type', text_auto=True)
                st.plotly_chart(fig_type, use_container_width=True)
            else: st.info("No data for Type chart.")
        with summary_cols[2]:
            if 'SR Status' in df_globally_filtered.columns and not df_globally_filtered['SR Status'].dropna().empty:
                sr_status_summary = df_globally_filtered['SR Status'].value_counts().reset_index()
                sr_status_summary.columns = ['SR Status', 'Count']
                fig_sr_status = px.pie(sr_status_summary, names='SR Status', values='Count', title="SR Status (from SR file)", hole=0.3)
                st.plotly_chart(fig_sr_status, use_container_width=True)
            else: st.info("SR Status data not available or empty.")

        # --- Detailed Results Table ---
        st.markdown("---")
        st.subheader("📋 Filtered Results Details")
        
        # Dynamic column selection
        all_available_cols = df_tab_filtered.columns.tolist()
        default_cols_sr = ['Case Id', 'Current User Id', 'Case Start Date', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status', 'SR Last Update', 'Age (Days)']
        if st.session_state.sr_analysis_selected_cols is None: # Initialize if not set
            st.session_state.sr_analysis_selected_cols = [col for col in default_cols_sr if col in all_available_cols]

        with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
            st.session_state.sr_analysis_selected_cols = st.multiselect(
                "Select columns to display:",
                options=all_available_cols,
                default=st.session_state.sr_analysis_selected_cols,
                key="sr_col_select"
            )
            if not df_tab_filtered.empty and st.session_state.sr_analysis_selected_cols:
                export_cols = st.columns(2)
                with export_cols[0]:
                    excel_data = generate_excel_download(df_tab_filtered[st.session_state.sr_analysis_selected_cols], "SR_Analysis_Results")
                    st.download_button(label="📥 Download as Excel", data=excel_data,
                                       file_name=f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with export_cols[1]:
                    csv_data = generate_csv_download(df_tab_filtered[st.session_state.sr_analysis_selected_cols])
                    st.download_button(label="📝 Download as CSV", data=csv_data,
                                       file_name=f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                       mime="text/csv")
            elif df_tab_filtered.empty:
                 st.warning("No data to export.")


        st.info(f"Showing {len(df_tab_filtered)} records based on current filters.")
        if not df_tab_filtered.empty and st.session_state.sr_analysis_selected_cols:
            st.dataframe(df_tab_filtered[st.session_state.sr_analysis_selected_cols], height=400, use_container_width=True)
        elif df_tab_filtered.empty:
            st.warning("No data matches the current filter criteria.")
        else:
            st.warning("Please select columns to display or clear filters.")

        # --- Note Viewer / Case Details ---
        st.markdown("---")
        st.subheader("📝 Case Details & Note Viewer")
        if not df_tab_filtered.empty:
            # Use a more robust way to select a case
            case_ids_list = df_tab_filtered['Case Id'].tolist()
            if not case_ids_list:
                st.info("No cases to display in detail view.")
            else:
                # Navigation for case viewer
                nav_cols = st.columns([1,5,1])
                if nav_cols[0].button("⬅️ Previous Case") and st.session_state.sr_analysis_current_case_idx > 0:
                    st.session_state.sr_analysis_current_case_idx -= 1
                if nav_cols[2].button("Next Case ➡️") and st.session_state.sr_analysis_current_case_idx < len(case_ids_list) - 1:
                    st.session_state.sr_analysis_current_case_idx += 1
                
                # Ensure index is within bounds
                if st.session_state.sr_analysis_current_case_idx >= len(case_ids_list):
                    st.session_state.sr_analysis_current_case_idx = len(case_ids_list) -1 if case_ids_list else 0


                selected_case_id_sr = nav_cols[1].selectbox(
                    "Select Case ID to view details (or use Prev/Next buttons):",
                    options=case_ids_list,
                    index=st.session_state.sr_analysis_current_case_idx,
                    key="sr_case_select_box"
                )
                # Update index if selectbox changes
                if selected_case_id_sr != case_ids_list[st.session_state.sr_analysis_current_case_idx]:
                     st.session_state.sr_analysis_current_case_idx = case_ids_list.index(selected_case_id_sr)


                if selected_case_id_sr:
                    case_row = df_tab_filtered[df_tab_filtered['Case Id'] == selected_case_id_sr].iloc[0]
                    details_cols = st.columns(2)
                    with details_cols[0]:
                        st.markdown(f"**Case ID:** {case_row['Case Id']}")
                        st.markdown(f"**Owner:** {case_row.get('Current User Id', 'N/A')}")
                        st.markdown(f"**Start Date:** {case_row.get('Case Start Date', pd.NaT).strftime('%Y-%m-%d %H:%M') if pd.notna(case_row.get('Case Start Date')) else 'N/A'}")
                        st.markdown(f"**Age:** {case_row.get('Age (Days)', 'N/A')} days")
                        st.markdown(f"**Triage Status:** <span class='status-badge badge-{str(case_row.get('Triage Status','unknown')).lower().replace(' ','-')}'>{case_row.get('Triage Status','N/A')}</span>", unsafe_allow_html=True)

                    with details_cols[1]:
                        st.markdown(f"**Ticket Number:** {int(case_row['Ticket Number']) if pd.notna(case_row['Ticket Number']) else 'N/A'}")
                        st.markdown(f"**Type:** {case_row.get('Type', 'N/A')}")
                        st.markdown(f"**SR Status:** {case_row.get('SR Status', 'N/A')}")
                        st.markdown(f"**SR Last Update:** {case_row.get('SR Last Update', pd.NaT).strftime('%Y-%m-%d %H:%M') if pd.notna(case_row.get('SR Last Update')) else 'N/A'}")
                        if 'SR Breach Passed' in case_row and pd.notna(case_row['SR Breach Passed']):
                            breach_text = "Yes ⚠️" if case_row['SR Breach Passed'] == True else "No"
                            st.markdown(f"**SLA Breach:** <span class='status-badge badge-breach'>{breach_text}</span>", unsafe_allow_html=True)

                    st.markdown("##### Last Note:")
                    note_content = str(case_row.get('Last Note', 'No note available.'))
                    if st.session_state.sr_analysis_search_note: # Highlight search term
                        note_content = re.sub(f"({re.escape(st.session_state.sr_analysis_search_note)})", r"<mark>\1</mark>", note_content, flags=re.IGNORECASE)
                    st.markdown(f"<div style='background-color:#f9f9f9; border:1px solid #eee; padding:10px; border-radius:5px; max-height:200px; overflow-y:auto;'>{note_content}</div>", unsafe_allow_html=True)
        else:
            st.info("No data available to display case details. Adjust filters or upload data.")


    # ==============================================================================
    # SLA BREACH TAB
    # ==============================================================================
    elif selected_tab == "SLA Breach":
        st.header("⚠️ SLA Breach Analysis")
        if 'SR Breach Passed' not in df_globally_filtered.columns or df_globally_filtered['SR Breach Passed'].isna().all():
            st.warning("SLA Breach data ('SR Breach Passed' column) not found or is empty in the processed data. Please ensure your SR Status file contains this information and is correctly mapped.")
        else:
            breach_df_all = df_globally_filtered[df_globally_filtered['SR Breach Passed'] == True].copy()
            
            st.markdown("##### Breach Summary Metrics")
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.markdown(f"""<div class="card"><p class="metric-label">Total Breached Cases</p><p class="metric-value">{len(breach_df_all)}</p></div>""", unsafe_allow_html=True)
            with metric_cols[1]:
                open_statuses = ['Open', 'In Progress', 'Pending', 'Assigned'] # Customize as needed
                open_breaches = len(breach_df_all[breach_df_all['SR Status'].isin(open_statuses)]) if 'SR Status' in breach_df_all else 'N/A'
                st.markdown(f"""<div class="card"><p class="metric-label">Open Breached Cases</p><p class="metric-value">{open_breaches}</p></div>""", unsafe_allow_html=True)
            with metric_cols[2]:
                users_affected = breach_df_all['Current User Id'].nunique() if 'Current User Id' in breach_df_all else 'N/A'
                st.markdown(f"""<div class="card"><p class="metric-label">Users with Breaches</p><p class="metric-value">{users_affected}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            breach_filter_cols = st.columns(2)
            with breach_filter_cols[0]:
                status_options_breach = ["All"] + (breach_df_all['SR Status'].dropna().unique().tolist() if 'SR Status' in breach_df_all else [])
                st.session_state.sla_breach_status_filter = st.selectbox("Filter by SR Status", status_options_breach, key='sla_status_filter')
            with breach_filter_cols[1]:
                user_options_breach = ["All"] + (breach_df_all['Current User Id'].dropna().unique().tolist() if 'Current User Id' in breach_df_all else [])
                st.session_state.sla_breach_user_filter = st.selectbox("Filter by User", user_options_breach, key='sla_user_filter')

            df_tab_filtered_breach = breach_df_all.copy()
            if st.session_state.sla_breach_status_filter != "All" and 'SR Status' in df_tab_filtered_breach:
                df_tab_filtered_breach = df_tab_filtered_breach[df_tab_filtered_breach['SR Status'] == st.session_state.sla_breach_status_filter]
            if st.session_state.sla_breach_user_filter != "All" and 'Current User Id' in df_tab_filtered_breach:
                df_tab_filtered_breach = df_tab_filtered_breach[df_tab_filtered_breach['Current User Id'] == st.session_state.sla_breach_user_filter]

            st.markdown("---")
            st.subheader("📋 Breached Cases Details")
            # Columns for breach table
            breach_display_cols_default = ['Case Id', 'Current User Id', 'Ticket Number', 'Type', 'SR Status', 'SR Breach Date', 'Age (Days)', 'Time Since Breach', 'Time to Resolve After Breach']
            breach_display_cols = [col for col in breach_display_cols_default if col in df_tab_filtered_breach.columns]

            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                selected_breach_cols = st.multiselect(
                    "Select columns for breached cases:",
                    options=df_tab_filtered_breach.columns.tolist(),
                    default=breach_display_cols,
                    key="breach_col_select"
                )
                if not df_tab_filtered_breach.empty and selected_breach_cols:
                    export_cols_breach = st.columns(2)
                    with export_cols_breach[0]:
                        excel_data_b = generate_excel_download(df_tab_filtered_breach[selected_breach_cols], "SLA_Breach_Results")
                        st.download_button(label="📥 Download as Excel", data=excel_data_b,
                                        file_name=f"sla_breach_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    with export_cols_breach[1]:
                        csv_data_b = generate_csv_download(df_tab_filtered_breach[selected_breach_cols])
                        st.download_button(label="📝 Download as CSV", data=csv_data_b,
                                        file_name=f"sla_breach_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                        mime="text/csv")
                elif df_tab_filtered_breach.empty:
                    st.warning("No breached cases to export with current filters.")


            st.info(f"Showing {len(df_tab_filtered_breach)} breached records based on current filters.")
            if not df_tab_filtered_breach.empty and selected_breach_cols:
                st.dataframe(df_tab_filtered_breach[selected_breach_cols], height=300, use_container_width=True)
            elif df_tab_filtered_breach.empty:
                 st.warning("No breached cases match current filters.")
            else:
                st.warning("Please select columns to display.")

            # Grouped analysis for breaches
            if not df_tab_filtered_breach.empty:
                st.markdown("---")
                st.subheader("📊 Breach Analysis by Group")
                group_cols = st.columns(2)
                with group_cols[0]:
                    if 'Current User Id' in df_tab_filtered_breach:
                        breach_by_user = df_tab_filtered_breach.groupby('Current User Id').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        fig_breach_user = px.bar(breach_by_user.head(10), x='Current User Id', y='Breach Count', title='Top 10 Users by Breach Count', text_auto=True)
                        st.plotly_chart(fig_breach_user, use_container_width=True)
                with group_cols[1]:
                    if 'Type' in df_tab_filtered_breach:
                        breach_by_type = df_tab_filtered_breach.groupby('Type').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        fig_breach_type = px.pie(breach_by_type, names='Type', values='Breach Count', title='Breaches by Type', hole=0.3)
                        st.plotly_chart(fig_breach_type, use_container_width=True)

    # ==============================================================================
    # TODAY'S ACTIVITY TAB
    # ==============================================================================
    elif selected_tab == "Today's Activity":
        st.header("📅 Today's Activity (Based on Last Note Date)")
        if 'Created Today Flag' not in df_globally_filtered.columns:
            st.warning("'Created Today Flag' column not found. This feature requires 'Last Note Date'.")
        else:
            today_df_all = df_globally_filtered[df_globally_filtered['Created Today Flag'] == True].copy()

            st.markdown("##### Today's Activity Summary")
            today_metric_cols = st.columns(3)
            with today_metric_cols[0]:
                st.markdown(f"""<div class="card"><p class="metric-label">Total Activities Today</p><p class="metric-value">{len(today_df_all)}</p></div>""", unsafe_allow_html=True)
            with today_metric_cols[1]:
                sr_today_count = len(today_df_all[today_df_all['Type'] == 'SR']) if 'Type' in today_df_all else 'N/A'
                st.markdown(f"""<div class="card"><p class="metric-label">SRs Today</p><p class="metric-value">{sr_today_count}</p></div>""", unsafe_allow_html=True)
            with today_metric_cols[2]:
                inc_today_count = len(today_df_all[today_df_all['Type'] == 'Incident']) if 'Type' in today_df_all else 'N/A'
                st.markdown(f"""<div class="card"><p class="metric-label">Incidents Today</p><p class="metric-value">{inc_today_count}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            today_filter_cols = st.columns(2)
            with today_filter_cols[0]:
                type_options_today = ["All", "SR", "Incident"] + ([t for t in today_df_all["Type"].dropna().unique() if t not in ["SR", "Incident"]] if 'Type' in today_df_all else [])
                st.session_state.today_type_filter = st.selectbox("Filter by Type", type_options_today, key='today_type_filter_sel')
            with today_filter_cols[1]:
                user_options_today = ["All"] + (today_df_all['Current User Id'].dropna().unique().tolist() if 'Current User Id' in today_df_all else [])
                st.session_state.today_user_filter = st.selectbox("Filter by User", user_options_today, key='today_user_filter_sel')

            df_tab_filtered_today = today_df_all.copy()
            if st.session_state.today_type_filter != "All" and 'Type' in df_tab_filtered_today:
                df_tab_filtered_today = df_tab_filtered_today[df_tab_filtered_today['Type'] == st.session_state.today_type_filter]
            if st.session_state.today_user_filter != "All" and 'Current User Id' in df_tab_filtered_today:
                df_tab_filtered_today = df_tab_filtered_today[df_tab_filtered_today['Current User Id'] == st.session_state.today_user_filter]

            st.markdown("---")
            st.subheader("📋 Today's Activity Details")
            today_display_cols_default = ['Case Id', 'Current User Id', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status']
            today_display_cols = [col for col in today_display_cols_default if col in df_tab_filtered_today.columns]
            
            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                selected_today_cols = st.multiselect(
                    "Select columns for today's activity:",
                    options=df_tab_filtered_today.columns.tolist(),
                    default=today_display_cols,
                    key="today_col_select"
                )
                if not df_tab_filtered_today.empty and selected_today_cols:
                    # Export Buttons
                    export_cols_today = st.columns(2)
                    with export_cols_today[0]:
                        excel_data_t = generate_excel_download(df_tab_filtered_today[selected_today_cols], "Today_Activity_Results")
                        st.download_button(label="📥 Download as Excel", data=excel_data_t,
                                        file_name=f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    with export_cols_today[1]:
                        csv_data_t = generate_csv_download(df_tab_filtered_today[selected_today_cols])
                        st.download_button(label="📝 Download as CSV", data=csv_data_t,
                                        file_name=f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                        mime="text/csv")
                elif df_tab_filtered_today.empty:
                    st.warning("No data for today's activity to export with current filters.")

            st.info(f"Showing {len(df_tab_filtered_today)} activities from today based on current filters.")
            if not df_tab_filtered_today.empty and selected_today_cols:
                st.dataframe(df_tab_filtered_today[selected_today_cols], height=300, use_container_width=True)
            elif df_tab_filtered_today.empty:
                 st.warning("No activities found for today with current filters.")
            else:
                st.warning("Please select columns to display.")

    # ==============================================================================
    # USER PERFORMANCE TAB
    # ==============================================================================
    elif selected_tab == "User Performance":
        st.header("👥 User Performance Analysis")
        if 'Current User Id' not in df_globally_filtered.columns:
            st.warning("'Current User Id' column not found. This feature is unavailable.")
        else:
            users_for_perf = st.multiselect(
                "Select Users for Performance Analysis (leave blank for all in global filter):",
                options=st.session_state.all_users,
                default=st.session_state.get('user_perf_selected_users', []), # Persist selection
                key='user_perf_users_select'
            )
            st.session_state.user_perf_selected_users = users_for_perf

            df_user_perf = df_globally_filtered.copy()
            if users_for_perf: # If specific users are selected for this tab
                df_user_perf = df_user_perf[df_user_perf['Current User Id'].isin(users_for_perf)]
            
            if df_user_perf.empty:
                st.info("No data for selected users or filters.")
            else:
                # Performance Metrics Calculation
                user_summary_list = []
                for user, group in df_user_perf.groupby('Current User Id'):
                    metrics = {
                        'User': user,
                        'Total Cases': len(group),
                        'SRs': len(group[group['Type'] == 'SR']),
                        'Incidents': len(group[group['Type'] == 'Incident']),
                        'Avg. Age (Open)': group[~group['SR Status'].isin(['Closed', 'Resolved', 'Completed'])]['Age (Days)'].mean() if 'SR Status' in group else group['Age (Days)'].mean(),
                        'Breached Cases': group['SR Breach Passed'].sum() if 'SR Breach Passed' in group else 0,
                        'Avg. Resolution Time (Days)': group['Resolution Time (Days)'].mean() if 'Resolution Time (Days)' in group else np.nan
                    }
                    user_summary_list.append(metrics)
                
                user_summary_df = pd.DataFrame(user_summary_list).round(1) # Round averages
                user_summary_df = user_summary_df.sort_values(by='Total Cases', ascending=False)

                st.subheader("User Performance Overview")
                st.dataframe(user_summary_df, use_container_width=True)

                if not user_summary_df.empty:
                    st.markdown("---")
                    st.subheader("Performance Charts")
                    chart_cols = st.columns(2)
                    with chart_cols[0]:
                        fig_user_cases = px.bar(user_summary_df.head(15), x='User', y=['SRs', 'Incidents'], title='Case Load by User (Top 15)', barmode='stack', text_auto=True)
                        st.plotly_chart(fig_user_cases, use_container_width=True)
                    with chart_cols[1]:
                        if 'Breached Cases' in user_summary_df.columns and user_summary_df['Breached Cases'].sum() > 0:
                             fig_user_breach = px.bar(user_summary_df[user_summary_df['Breached Cases'] > 0].head(15), x='User', y='Breached Cases', title='Breached Cases by User (Top 15)', text_auto=True, color='Breached Cases')
                             st.plotly_chart(fig_user_breach, use_container_width=True)
                        else:
                            st.info("No breached cases data to display for users.")
    
    # ==============================================================================
    # TREND ANALYSIS TAB
    # ==============================================================================
    elif selected_tab == "Trend Analysis":
        st.header("📈 Trend Analysis (Based on Case Start Date)")
        if 'Case Start Date' not in df_globally_filtered.columns or df_globally_filtered['Case Start Date'].isna().all():
            st.warning("'Case Start Date' column not found or is empty. Trend analysis unavailable.")
        else:
            df_trend = df_globally_filtered.copy()
            df_trend['Case Start Date'] = pd.to_datetime(df_trend['Case Start Date'])
            df_trend = df_trend.dropna(subset=['Case Start Date'])
            
            if df_trend.empty:
                st.info("No data with valid 'Case Start Date' for trend analysis.")
            else:
                time_group_options = {'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Q': 'Quarterly'}
                selected_group_key = st.selectbox(
                    "Group trends by:",
                    options=list(time_group_options.keys()),
                    format_func=lambda x: time_group_options[x],
                    key='trend_time_group_select',
                    index=list(time_group_options.keys()).index(st.session_state.trend_time_group) # Persist
                )
                st.session_state.trend_time_group = selected_group_key

                # Resample data
                trends_data = df_trend.set_index('Case Start Date').resample(st.session_state.trend_time_group).agg(
                    Total_Cases=('Case Id', 'count'),
                    SR_Count=('Type', lambda x: (x == 'SR').sum()),
                    Incident_Count=('Type', lambda x: (x == 'Incident').sum()),
                    Breached_Count=('SR Breach Passed', lambda x: x.sum() if 'SR Breach Passed' in df_trend.columns and x.dtype == bool else 0) # Handle missing/non-bool
                ).reset_index()

                st.subheader(f"{time_group_options[st.session_state.trend_time_group]} Trends")
                
                fig_case_trend = px.line(trends_data, x='Case Start Date', y=['Total_Cases', 'SR_Count', 'Incident_Count'],
                                         title='Case Creation Trends', markers=True)
                fig_case_trend.update_layout(yaxis_title="Number of Cases")
                st.plotly_chart(fig_case_trend, use_container_width=True)

                if 'Breached_Count' in trends_data.columns and trends_data['Breached_Count'].sum() > 0:
                    fig_breach_trend = px.line(trends_data, x='Case Start Date', y='Breached_Count',
                                             title='SLA Breach Trends', markers=True, color_discrete_sequence=['red'])
                    fig_breach_trend.update_layout(yaxis_title="Number of Breaches")
                    st.plotly_chart(fig_breach_trend, use_container_width=True)
                else:
                    st.info("No breach data or no breaches to display in trends.")

# --- Footer ---
st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.9em;">
    🚀 SR Analyzer Pro Elite v2.0 | Developed with Streamlit | © """ + str(datetime.now().year) + """
    </div>""",
    unsafe_allow_html=True
)