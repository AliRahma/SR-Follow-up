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
        background-color: #28a745;
    }
    .stDownloadButton>button:hover { background-color: #218838; }
    
    /* Badges */
    .status-badge { padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: 600; display: inline-block;}
    .badge-pending-sr-incident { background-color: #FFF3CD; color: #856404; } /* Specific for "Pending SR/Incident" */
    .badge-not-triaged { background-color: #E2E3E5; color: #4F545C; }
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
        'all_users': [], 'selected_sbar_users': None, # Will be set with defaults later
        'sbar_date_range': (None, None),
        # Configurable values
        'config_ticket_regex': r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})',
        'config_sr_min_range': 14000, 'config_sr_max_range': 17000,
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
        st.error(f"Error loading Excel file: {e}")
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

    # Ensure expected columns exist post-merge or if SR file was skipped
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
    st.session_state.config_ticket_regex = st.text_input("Ticket Regex Pattern", value=st.session_state.config_ticket_regex)
    c1, c2 = st.columns(2)
    st.session_state.config_sr_min_range = c1.number_input("SR Min Number", value=st.session_state.config_sr_min_range, step=1)
    st.session_state.config_sr_max_range = c2.number_input("SR Max Number", value=st.session_state.config_sr_max_range, step=1)

    st.subheader("📁 Data Import")
    uploaded_main_file = st.file_uploader("Upload Main Excel File", type=["xlsx", "xls"], key="main_uploader_key")
    uploaded_sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type=["xlsx", "xls"], key="sr_uploader_key")

    if st.button("🔄 Process Uploaded Data", use_container_width=True, key="process_data_button"):
        if uploaded_main_file:
            with st.spinner("Loading and processing data..."):
                main_df_raw = load_data(uploaded_main_file)
                sr_df_raw = load_data(uploaded_sr_status_file) if uploaded_sr_status_file else None

                if main_df_raw is not None:
                    processed_df = process_and_enrich_data(main_df_raw, sr_df_raw)
                    if processed_df is not None:
                        st.session_state.main_df_raw = main_df_raw
                        st.session_state.sr_df_raw = sr_df_raw
                        st.session_state.processed_df = processed_df
                        st.session_state.data_loaded = True
                        st.session_state.last_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        if 'Current User Id' in processed_df.columns:
                            st.session_state.all_users = sorted(processed_df['Current User Id'].dropna().unique().tolist())
                        else:
                            st.session_state.all_users = []
                        
                        # Set default users for the first time or if list changed
                        default_users_list = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
                        # Filter defaults to only those present in the data
                        actual_default_users = [u for u in default_users_list if u in st.session_state.all_users]
                        # Only set if 'selected_sbar_users' hasn't been set by user action yet or if users changed
                        if st.session_state.selected_sbar_users is None or not all(u in st.session_state.all_users for u in st.session_state.selected_sbar_users):
                             st.session_state.selected_sbar_users = actual_default_users

                        st.success(f"Data processed: {len(processed_df)} records.")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to process data. Check columns and format.")
                else:
                    st.error("Main data file could not be loaded.")
        else:
            st.warning("Please upload the Main Excel File.")
    
    if st.session_state.data_loaded:
        st.info(f"Last update: {st.session_state.last_upload_time}")
        st.markdown("---")
        st.subheader("GLOBAL FILTERS")

        # User filter - respecting prior selections if they exist and are valid
        current_selection = st.session_state.selected_sbar_users
        if current_selection is None or not all(u in st.session_state.all_users for u in current_selection):
            # This happens on first load or if dataset changes invalidating previous selection
            default_users_list = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
            current_selection = [u for u in default_users_list if u in st.session_state.all_users]

        st.session_state.selected_sbar_users = st.multiselect(
            "Filter by Users (Global)",
            options=st.session_state.all_users,
            default=current_selection,
            key="global_user_multiselect"
        )

        if 'Case Start Date' in st.session_state.processed_df.columns:
            min_d = st.session_state.processed_df['Case Start Date'].min()
            max_d = st.session_state.processed_df['Case Start Date'].max()
            if pd.NaT not in [min_d, max_d] and min_d <= max_d:
                current_date_range = st.session_state.sbar_date_range
                if current_date_range == (None, None) or \
                   not (isinstance(current_date_range[0], type(min_d.date())) and isinstance(current_date_range[1], type(max_d.date()))): # type check for date objects
                    current_date_range = (min_d.date(), max_d.date())
                
                st.session_state.sbar_date_range = st.date_input(
                    "Filter by Case Start Date (Global)",
                    value=current_date_range,
                    min_value=min_d.date(), max_value=max_d.date(),
                    key="global_date_range_picker"
                )
    else:
        st.warning("Upload and process data to enable filters.")

# --- Main Content ---
if not st.session_state.data_loaded:
    st.title("📊 SR Analyzer Pro")
    st.markdown("### Welcome! Please upload your data via the sidebar to begin analysis.")
else:
    df_globally_filtered = st.session_state.processed_df.copy()
    if st.session_state.selected_sbar_users:
        df_globally_filtered = df_globally_filtered[df_globally_filtered['Current User Id'].isin(st.session_state.selected_sbar_users)]

    if 'Case Start Date' in df_globally_filtered.columns and \
       st.session_state.sbar_date_range and \
       st.session_state.sbar_date_range[0] is not None and \
       st.session_state.sbar_date_range[1] is not None:
        start_dt_sbar, end_dt_sbar = st.session_state.sbar_date_range
        df_globally_filtered['Case Start Date'] = pd.to_datetime(df_globally_filtered['Case Start Date'], errors='coerce')
        df_globally_filtered = df_globally_filtered[
            (df_globally_filtered['Case Start Date'].dt.date >= start_dt_sbar) &
            (df_globally_filtered['Case Start Date'].dt.date <= end_dt_sbar)
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
        st.session_state.sr_analysis_status_filter = f_cols_sr[0].selectbox("Triage Status", ["All"] + df_tab_filtered_sr["Triage Status"].dropna().unique().tolist(), key='sr_an_ts_sel', index=(["All"] + df_tab_filtered_sr["Triage Status"].dropna().unique().tolist()).index(st.session_state.sr_analysis_status_filter) if st.session_state.sr_analysis_status_filter in (["All"] + df_tab_filtered_sr["Triage Status"].dropna().unique().tolist()) else 0)
        st.session_state.sr_analysis_type_filter = f_cols_sr[1].selectbox("Type (SR/Incident)", ["All", "SR", "Incident"] + [t for t in df_tab_filtered_sr["Type"].dropna().unique() if t not in ["SR", "Incident"]], key='sr_an_ty_sel', index=(["All", "SR", "Incident"] + [t for t in df_tab_filtered_sr["Type"].dropna().unique() if t not in ["SR", "Incident"]]).index(st.session_state.sr_analysis_type_filter) if st.session_state.sr_analysis_type_filter in (["All", "SR", "Incident"] + [t for t in df_tab_filtered_sr["Type"].dropna().unique() if t not in ["SR", "Incident"]]) else 0)
        sr_stat_opts = ["All"] + df_tab_filtered_sr['SR Status'].dropna().unique().tolist() + ["N/A (No SR Data)"]
        st.session_state.sr_analysis_sr_status_filter = f_cols_sr[2].selectbox("SR Status (from SR file)", sr_stat_opts, key='sr_an_srs_sel', index=sr_stat_opts.index(st.session_state.sr_analysis_sr_status_filter) if st.session_state.sr_analysis_sr_status_filter in sr_stat_opts else 0)
        st.session_state.sr_analysis_search_note = f_cols_sr[3].text_input("Search in Last Note", st.session_state.sr_analysis_search_note, key='sr_an_search_inp')

        if st.session_state.sr_analysis_status_filter != "All": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["Triage Status"] == st.session_state.sr_analysis_status_filter]
        if st.session_state.sr_analysis_type_filter != "All": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["Type"] == st.session_state.sr_analysis_type_filter]
        if st.session_state.sr_analysis_sr_status_filter != "All":
            if st.session_state.sr_analysis_sr_status_filter == "N/A (No SR Data)": df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["SR Status"].isna()]
            else: df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr["SR Status"] == st.session_state.sr_analysis_sr_status_filter]
        if st.session_state.sr_analysis_search_note: df_tab_filtered_sr = df_tab_filtered_sr[df_tab_filtered_sr['Last Note'].str.contains(st.session_state.sr_analysis_search_note, case=False, na=False)]

        st.markdown("---")
        st.subheader("📊 Summary Tables")
        summary_cols_sr = st.columns(3)
        with summary_cols_sr[0]:
            st.markdown("**Triage Status Count**")
            triage_summary = df_globally_filtered['Triage Status'].value_counts().reset_index().rename(columns={'index': 'Triage Status', 'Triage Status': 'Count'})
            st.dataframe(triage_summary.set_index('Triage Status'), use_container_width=True)
        with summary_cols_sr[1]:
            st.markdown("**Type (SR/Incident) Count**")
            type_summary = df_globally_filtered['Type'].value_counts().reset_index().rename(columns={'index': 'Type', 'Type': 'Count'})
            st.dataframe(type_summary.set_index('Type'), use_container_width=True)
        with summary_cols_sr[2]:
            st.markdown("**SR Status Count (from SR file)**")
            if 'SR Status' in df_globally_filtered.columns and not df_globally_filtered['SR Status'].dropna().empty:
                sr_status_summary = df_globally_filtered['SR Status'].value_counts().reset_index().rename(columns={'index': 'SR Status', 'SR Status': 'Count'})
                st.dataframe(sr_status_summary.set_index('SR Status'), use_container_width=True)
            else: st.info("SR Status data not available or empty.")

        st.markdown("---")
        st.subheader("📋 Filtered Results Details")
        all_cols_sr = df_tab_filtered_sr.columns.tolist()
        def_cols_sr = ['Case Id', 'Current User Id', 'Case Start Date', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status', 'SR Last Update', 'Age (Days)']
        if st.session_state.sr_analysis_selected_cols is None:
            st.session_state.sr_analysis_selected_cols = [col for col in def_cols_sr if col in all_cols_sr]

        with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
            st.session_state.sr_analysis_selected_cols = st.multiselect("Select columns:", all_cols_sr, default=st.session_state.sr_analysis_selected_cols, key="sr_an_col_sel")
            if not df_tab_filtered_sr.empty and st.session_state.sr_analysis_selected_cols:
                ex_c1, ex_c2 = st.columns(2)
                excel_data_sr = generate_excel_download(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols], "SR_Analysis")
                ex_c1.download_button("📥 Excel", excel_data_sr, f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                csv_data_sr = generate_csv_download(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols])
                ex_c2.download_button("📝 CSV", csv_data_sr, f"sr_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")
            elif df_tab_filtered_sr.empty: st.warning("No data to export.")
        
        st.info(f"Showing {len(df_tab_filtered_sr)} records.")
        if not df_tab_filtered_sr.empty and st.session_state.sr_analysis_selected_cols:
            st.dataframe(df_tab_filtered_sr[st.session_state.sr_analysis_selected_cols], height=400, use_container_width=True)
        elif df_tab_filtered_sr.empty: st.warning("No data matches filters.")
        else: st.warning("Select columns to display.")

        st.markdown("---")
        st.subheader("📝 Case Details & Note Viewer")
        if not df_tab_filtered_sr.empty:
            ids_sr = df_tab_filtered_sr['Case Id'].tolist()
            if ids_sr:
                nav_c1, nav_c2, nav_c3 = st.columns([1,5,1])
                if nav_c1.button("⬅️ Prev", key="sr_prev_case") and st.session_state.sr_analysis_current_case_idx > 0: st.session_state.sr_analysis_current_case_idx -= 1
                if nav_c3.button("Next ➡️", key="sr_next_case") and st.session_state.sr_analysis_current_case_idx < len(ids_sr) - 1: st.session_state.sr_analysis_current_case_idx += 1
                
                st.session_state.sr_analysis_current_case_idx = min(max(0, st.session_state.sr_analysis_current_case_idx), len(ids_sr)-1 if ids_sr else 0)

                sel_id_sr = nav_c2.selectbox("Select Case ID:", ids_sr, index=st.session_state.sr_analysis_current_case_idx, key="sr_an_case_sel")
                if sel_id_sr != ids_sr[st.session_state.sr_analysis_current_case_idx]: st.session_state.sr_analysis_current_case_idx = ids_sr.index(sel_id_sr)

                case_row_sr = df_tab_filtered_sr[df_tab_filtered_sr['Case Id'] == sel_id_sr].iloc[0]
                det_c1, det_c2 = st.columns(2)
                triage_stat_html_class = str(case_row_sr.get('Triage Status','unknown')).lower().replace(' ','-').replace('/','-')
                with det_c1:
                    st.markdown(f"**Case ID:** {case_row_sr['Case Id']}")
                    st.markdown(f"**Owner:** {case_row_sr.get('Current User Id', 'N/A')}")
                    st.markdown(f"**Start Date:** {case_row_sr.get('Case Start Date', pd.NaT).strftime('%Y-%m-%d %H:%M') if pd.notna(case_row_sr.get('Case Start Date')) else 'N/A'}")
                    st.markdown(f"**Triage Status:** <span class='status-badge badge-{triage_stat_html_class}'>{case_row_sr.get('Triage Status','N/A')}</span>", unsafe_allow_html=True)
                with det_c2:
                    st.markdown(f"**Ticket Number:** {int(case_row_sr['Ticket Number']) if pd.notna(case_row_sr['Ticket Number']) else 'N/A'}")
                    st.markdown(f"**Type:** {case_row_sr.get('Type', 'N/A')}")
                    st.markdown(f"**SR Status:** {case_row_sr.get('SR Status', 'N/A')}")
                    if 'SR Breach Passed' in case_row_sr and pd.notna(case_row_sr['SR Breach Passed']):
                        breach_txt = "Yes ⚠️" if case_row_sr['SR Breach Passed'] else "No"
                        breach_class = "badge-breach-yes" if case_row_sr['SR Breach Passed'] else "badge-breach-no"
                        st.markdown(f"**SLA Breach:** <span class='status-badge {breach_class}'>{breach_txt}</span>", unsafe_allow_html=True)
                
                st.markdown("##### Last Note:")
                note_sr = str(case_row_sr.get('Last Note', 'No note.'))
                if st.session_state.sr_analysis_search_note: note_sr = re.sub(f"({re.escape(st.session_state.sr_analysis_search_note)})", r"<mark>\1</mark>", note_sr, flags=re.IGNORECASE)
                st.markdown(f"<div style='background-color:#f9f9f9; border:1px solid #eee; padding:10px; border-radius:5px; max-height:200px; overflow-y:auto;'>{note_sr}</div>", unsafe_allow_html=True)
            else: st.info("No cases to display in detail view for current filters.")
        else: st.info("No data for case details. Adjust filters or upload data.")

    # ========================== SLA BREACH TAB ==========================
    elif selected_tab == "SLA Breach":
        st.header("⚠️ SLA Breach Analysis")
        if 'SR Breach Passed' not in df_globally_filtered.columns or df_globally_filtered['SR Breach Passed'].isna().all():
            st.warning("SLA Breach data ('SR Breach Passed') not found or empty. Ensure SR Status file has this.")
        else:
            breach_df_all = df_globally_filtered[df_globally_filtered['SR Breach Passed'] == True].copy()
            
            st.markdown("##### Breach Summary Metrics")
            met_c1, met_c2, met_c3 = st.columns(3)
            met_c1.markdown(f"""<div class="card"><p class="metric-label">Total Breached Cases</p><p class="metric-value">{len(breach_df_all)}</p></div>""", unsafe_allow_html=True)
            open_stats = ['Open', 'In Progress', 'Pending', 'Assigned']
            open_b = len(breach_df_all[breach_df_all['SR Status'].isin(open_stats)]) if 'SR Status' in breach_df_all else 'N/A'
            met_c2.markdown(f"""<div class="card"><p class="metric-label">Open Breached Cases</p><p class="metric-value">{open_b}</p></div>""", unsafe_allow_html=True)
            users_aff = breach_df_all['Current User Id'].nunique() if 'Current User Id' in breach_df_all else 'N/A'
            met_c3.markdown(f"""<div class="card"><p class="metric-label">Users with Breaches</p><p class="metric-value">{users_aff}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            bf_c1, bf_c2 = st.columns(2)
            s_opts_b = ["All"] + (breach_df_all['SR Status'].dropna().unique().tolist() if 'SR Status' in breach_df_all else [])
            st.session_state.sla_breach_status_filter = bf_c1.selectbox("Filter by SR Status", s_opts_b, key='sla_b_stat_sel', index=s_opts_b.index(st.session_state.sla_breach_status_filter) if st.session_state.sla_breach_status_filter in s_opts_b else 0)
            u_opts_b = ["All"] + (breach_df_all['Current User Id'].dropna().unique().tolist() if 'Current User Id' in breach_df_all else [])
            st.session_state.sla_breach_user_filter = bf_c2.selectbox("Filter by User", u_opts_b, key='sla_b_user_sel', index=u_opts_b.index(st.session_state.sla_breach_user_filter) if st.session_state.sla_breach_user_filter in u_opts_b else 0)

            df_tab_filtered_breach = breach_df_all.copy()
            if st.session_state.sla_breach_status_filter != "All" and 'SR Status' in df_tab_filtered_breach: df_tab_filtered_breach = df_tab_filtered_breach[df_tab_filtered_breach['SR Status'] == st.session_state.sla_breach_status_filter]
            if st.session_state.sla_breach_user_filter != "All" and 'Current User Id' in df_tab_filtered_breach: df_tab_filtered_breach = df_tab_filtered_breach[df_tab_filtered_breach['Current User Id'] == st.session_state.sla_breach_user_filter]

            st.markdown("---")
            st.subheader("📋 Breached Cases Details")
            def_cols_b = ['Case Id', 'Current User Id', 'Ticket Number', 'Type', 'SR Status', 'SR Breach Date', 'Age (Days)', 'Time Since Breach', 'Time to Resolve After Breach']
            if st.session_state.sla_breach_selected_cols is None:
                st.session_state.sla_breach_selected_cols = [col for col in def_cols_b if col in df_tab_filtered_breach.columns]
            
            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                st.session_state.sla_breach_selected_cols = st.multiselect("Select columns:", df_tab_filtered_breach.columns.tolist(), default=st.session_state.sla_breach_selected_cols, key="sla_b_col_sel")
                if not df_tab_filtered_breach.empty and st.session_state.sla_breach_selected_cols:
                    bex_c1, bex_c2 = st.columns(2)
                    excel_data_b = generate_excel_download(df_tab_filtered_breach[st.session_state.sla_breach_selected_cols], "SLA_Breaches")
                    bex_c1.download_button("📥 Excel", excel_data_b, f"sla_breaches_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    csv_data_b = generate_csv_download(df_tab_filtered_breach[st.session_state.sla_breach_selected_cols])
                    bex_c2.download_button("📝 CSV", csv_data_b, f"sla_breaches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")
                elif df_tab_filtered_breach.empty: st.warning("No breached cases to export.")

            st.info(f"Showing {len(df_tab_filtered_breach)} breached records.")
            if not df_tab_filtered_breach.empty and st.session_state.sla_breach_selected_cols:
                st.dataframe(df_tab_filtered_breach[st.session_state.sla_breach_selected_cols], height=300, use_container_width=True)
            elif df_tab_filtered_breach.empty: st.warning("No breached cases match filters.")
            else: st.warning("Select columns to display.")

            if not df_tab_filtered_breach.empty:
                st.markdown("---")
                st.subheader("📊 Breach Analysis by Group (Tables)")
                gb_c1, gb_c2 = st.columns(2)
                with gb_c1:
                    if 'Current User Id' in df_tab_filtered_breach:
                        st.markdown("**Breaches by User**")
                        breach_by_user_tb = df_tab_filtered_breach.groupby('Current User Id').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        st.dataframe(breach_by_user_tb.set_index('Current User Id').head(10), use_container_width=True) # Top 10
                with gb_c2:
                    if 'Type' in df_tab_filtered_breach:
                        st.markdown("**Breaches by Type**")
                        breach_by_type_tb = df_tab_filtered_breach.groupby('Type').size().reset_index(name='Breach Count').sort_values('Breach Count', ascending=False)
                        st.dataframe(breach_by_type_tb.set_index('Type'), use_container_width=True)

    # ========================== TODAY'S ACTIVITY TAB ==========================
    elif selected_tab == "Today's Activity":
        st.header("📅 Today's Activity (Based on Last Note Date)")
        if 'Created Today Flag' not in df_globally_filtered.columns:
            st.warning("'Created Today Flag' column not found. Requires 'Last Note Date'.")
        else:
            today_df_all = df_globally_filtered[df_globally_filtered['Created Today Flag'] == True].copy()

            st.markdown("##### Today's Activity Summary")
            tm_c1, tm_c2, tm_c3 = st.columns(3)
            tm_c1.markdown(f"""<div class="card"><p class="metric-label">Total Activities Today</p><p class="metric-value">{len(today_df_all)}</p></div>""", unsafe_allow_html=True)
            sr_td_c = len(today_df_all[today_df_all['Type'] == 'SR']) if 'Type' in today_df_all else 'N/A'
            tm_c2.markdown(f"""<div class="card"><p class="metric-label">SRs Today</p><p class="metric-value">{sr_td_c}</p></div>""", unsafe_allow_html=True)
            inc_td_c = len(today_df_all[today_df_all['Type'] == 'Incident']) if 'Type' in today_df_all else 'N/A'
            tm_c3.markdown(f"""<div class="card"><p class="metric-label">Incidents Today</p><p class="metric-value">{inc_td_c}</p></div>""", unsafe_allow_html=True)

            st.markdown("##### Filters for this view:")
            tdf_c1, tdf_c2 = st.columns(2)
            t_opts_td = ["All", "SR", "Incident"] + ([t for t in today_df_all["Type"].dropna().unique() if t not in ["SR", "Incident"]] if 'Type' in today_df_all else [])
            st.session_state.today_type_filter = tdf_c1.selectbox("Filter by Type", t_opts_td, key='td_type_sel', index=t_opts_td.index(st.session_state.today_type_filter) if st.session_state.today_type_filter in t_opts_td else 0)
            u_opts_td = ["All"] + (today_df_all['Current User Id'].dropna().unique().tolist() if 'Current User Id' in today_df_all else [])
            st.session_state.today_user_filter = tdf_c2.selectbox("Filter by User", u_opts_td, key='td_user_sel', index=u_opts_td.index(st.session_state.today_user_filter) if st.session_state.today_user_filter in u_opts_td else 0)

            df_tab_filtered_today = today_df_all.copy()
            if st.session_state.today_type_filter != "All" and 'Type' in df_tab_filtered_today: df_tab_filtered_today = df_tab_filtered_today[df_tab_filtered_today['Type'] == st.session_state.today_type_filter]
            if st.session_state.today_user_filter != "All" and 'Current User Id' in df_tab_filtered_today: df_tab_filtered_today = df_tab_filtered_today[df_tab_filtered_today['Current User Id'] == st.session_state.today_user_filter]

            st.markdown("---")
            st.subheader("📋 Today's Activity Details")
            def_cols_td = ['Case Id', 'Current User Id', 'Last Note Date', 'Triage Status', 'Type', 'Ticket Number', 'SR Status']
            if st.session_state.today_selected_cols is None:
                st.session_state.today_selected_cols = [col for col in def_cols_td if col in df_tab_filtered_today.columns]

            with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
                st.session_state.today_selected_cols = st.multiselect("Select columns:", df_tab_filtered_today.columns.tolist(), default=st.session_state.today_selected_cols, key="td_col_sel")
                if not df_tab_filtered_today.empty and st.session_state.today_selected_cols:
                    tex_c1, tex_c2 = st.columns(2)
                    excel_data_td = generate_excel_download(df_tab_filtered_today[st.session_state.today_selected_cols], "Today_Activity")
                    tex_c1.download_button("📥 Excel", excel_data_td, f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    csv_data_td = generate_csv_download(df_tab_filtered_today[st.session_state.today_selected_cols])
                    tex_c2.download_button("📝 CSV", csv_data_td, f"today_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")
                elif df_tab_filtered_today.empty: st.warning("No data for today to export.")
            
            st.info(f"Showing {len(df_tab_filtered_today)} activities from today.")
            if not df_tab_filtered_today.empty and st.session_state.today_selected_cols:
                st.dataframe(df_tab_filtered_today[st.session_state.today_selected_cols], height=300, use_container_width=True)
            elif df_tab_filtered_today.empty: st.warning("No activities found for today with current filters.")
            else: st.warning("Select columns to display.")

# --- Footer ---
st.markdown("---")
st.markdown(f"""<div style="text-align:center; color:#888; font-size:0.9em;">
📊 SR Analyzer Pro | © {datetime.now().year}
</div>""", unsafe_allow_html=True)