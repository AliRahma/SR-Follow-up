import streamlit as st
import pandas as pd
import numpy as np
import re
import io
# import base64 # Not used, can be removed
from datetime import datetime, timedelta # timedelta not used, can be removed
from streamlit_option_menu import option_menu

# --- Assume utils.py is in the same directory and contains:
# load_data, process_main_df, classify_and_extract, calculate_age,
# is_created_today, generate_excel_download, track_row (from your original code)
# ---

# For demonstration, I'll include a simplified track_row if utils is not provided by user
# If you have your utils.py, remove this dummy function
if 'track_row' not in globals():
    def track_row(row_data):
        case_id = row_data['Case Id']
        # Check if row is already tracked
        is_tracked = any(row['Case Id'] == case_id for row in st.session_state.tracked_rows)
        if is_tracked:
            st.session_state.tracked_rows = [row for row in st.session_state.tracked_rows if row['Case Id'] != case_id]
        else:
            st.session_state.tracked_rows.append(row_data.to_dict())

# Set page configuration
st.set_page_config(
    page_title="SR Analyzer Pro",
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
    .badge-pending { /* Example, you might need more specific ones for Triage Status */
        background-color: #ffecb3;
        color: #b17825;
    }
    .badge-pending-sr-incident { background-color: #ffecb3; color: #b17825; }
    .badge-not-triaged { background-color: #e2e3e5; color: #4f545c; }
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
    div[data-testid="stDataFrame"] table { /* Ensure data_editor also gets full width */
        width: 100%;
    }
    /* Removed fixed width for first child as data_editor handles selection differently */
    .st-ch { /* Checkbox label style from your original, might not be needed */
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

set_custom_theme()

# Initialize session state
if 'data_loaded' not in st.session_state: st.session_state.data_loaded = False
if 'main_df' not in st.session_state: st.session_state.main_df = None
if 'sr_df' not in st.session_state: st.session_state.sr_df = None
if 'filtered_df' not in st.session_state: st.session_state.filtered_df = None # Holds df_enriched
if 'last_upload_time' not in st.session_state: st.session_state.last_upload_time = None
if 'selected_users' not in st.session_state: st.session_state.selected_users = []
if 'tracked_rows' not in st.session_state: st.session_state.tracked_rows = []
# For SR Analysis tab column selection
if 'sr_selected_display_cols' not in st.session_state: st.session_state.sr_selected_display_cols = []


# --- UTILITY FUNCTIONS (Copied from your original for completeness if utils.py is not used) ---
@st.cache_data
def load_data(file):
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

def process_main_df(df):
    date_columns = ['Case Start Date', 'Last Note Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
    if 'Current User Id' in df.columns: # This was indented incorrectly in original
        st.session_state.all_users = sorted(df['Current User Id'].dropna().unique().tolist())
    return df

def classify_and_extract(note):
    if not isinstance(note, str):
        return "Not Triaged", None, None
    note_lower = note.lower()
    match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
    if match:
        ticket_num = int(match.group(2))
        ticket_type = "SR" if 14000 <= ticket_num <= 17000 else "Incident" # Adjust range as needed
        return "Pending SR/Incident", ticket_num, ticket_type
    return "Not Triaged", None, None

def calculate_age(start_date):
    if pd.isna(start_date): return None
    return (datetime.now() - start_date).days

def is_created_today(date_value):
    if pd.isna(date_value): return False
    today = datetime.now().date()
    note_date = date_value.date() if isinstance(date_value, datetime) else pd.to_datetime(date_value, errors='coerce').date()
    return note_date == today

def generate_excel_download(data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Results')
        workbook = writer.book
        worksheet = writer.sheets['Results']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#1976d2', 'color': 'white', 'border': 1})
        for col_num, value in enumerate(data.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for i, col in enumerate(data.columns):
            max_len = max(data[col].astype(str).apply(len).max(), len(str(col))) + 2
            worksheet.set_column(i, i, min(max_len, 50)) # Cap width
    output.seek(0)
    return output

# --- Sidebar ---
with st.sidebar:
    st.title("📊 SR Analyzer Pro")
    st.markdown("---")
    st.subheader("📁 Data Import")
    uploaded_file = st.file_uploader("Upload Main Excel File (.xlsx)", type=["xlsx","xls"], key="main_uploader_sidebar")
    sr_status_file = st.file_uploader("Upload SR Status Excel (optional)", type="xlsx", key="sr_uploader_sidebar")

    if uploaded_file:
        if st.session_state.get('last_main_file_id') != uploaded_file.file_id: # Process if new file
            with st.spinner("Loading main data..."):
                df_loaded = load_data(uploaded_file)
                if df_loaded is not None:
                    st.session_state.main_df = process_main_df(df_loaded)
                    st.session_state.last_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.data_loaded = True
                    st.session_state.last_main_file_id = uploaded_file.file_id
                    st.success(f"Main data loaded: {len(st.session_state.main_df)} records")
                else:
                    st.session_state.data_loaded = False # Failed to load
    
    if sr_status_file:
        if st.session_state.get('last_sr_file_id') != sr_status_file.file_id: # Process if new file
            with st.spinner("Loading SR status data..."):
                df_sr_loaded = load_data(sr_status_file)
                if df_sr_loaded is not None:
                    st.session_state.sr_df = df_sr_loaded
                    st.session_state.last_sr_file_id = sr_status_file.file_id
                    st.success(f"SR status data loaded: {len(st.session_state.sr_df)} records")
                    # If main data already loaded, may need to re-enrich
                    if st.session_state.data_loaded: st.session_state.filtered_df = None # Trigger re-enrichment
                
    if st.session_state.last_upload_time:
        st.info(f"Last main data update: {st.session_state.last_upload_time}")
    
    st.markdown("---")
    if st.session_state.data_loaded:
        st.subheader("🔍 Filters")
        df_main_for_filters = st.session_state.main_df.copy()
        all_users_list = st.session_state.get('all_users', []) # Get from state if populated by process_main_df
        
        default_users_filter = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        actual_default_users = [u for u in default_users_filter if u in all_users_list]
        
        st.session_state.selected_users = st.multiselect(
            "Select Users", options=all_users_list, default=actual_default_users, key="user_multiselect_sidebar"
        )
        
        if 'Case Start Date' in df_main_for_filters.columns:
            min_date_val = df_main_for_filters['Case Start Date'].min()
            max_date_val = df_main_for_filters['Case Start Date'].max()
            if pd.NaT not in [min_date_val, max_date_val] and min_date_val <= max_date_val:
                date_range_val = st.date_input(
                    "Date Range", value=(min_date_val.date(), max_date_val.date()),
                    min_value=min_date_val.date(), max_value=max_date_val.date(), key="date_range_sidebar"
                )
            else:
                st.caption("Date range cannot be determined from 'Case Start Date'.")

# --- Main Content ---
if not st.session_state.data_loaded:
    st.title("📊 SR Analyzer Pro")
    st.markdown("### Welcome! Upload your Excel files via the sidebar to begin analysis.")
else:
    # Enrich data if not already done or if dependencies changed (e.g. sr_df loaded later)
    if st.session_state.filtered_df is None or \
       (st.session_state.sr_df is not None and 'SR Status' not in st.session_state.filtered_df.columns):
        
        # Apply global filters before enrichment
        df_globally_filtered = st.session_state.main_df.copy()
        if st.session_state.selected_users:
            df_globally_filtered = df_globally_filtered[df_globally_filtered['Current User Id'].isin(st.session_state.selected_users)]
        
        if 'date_range_val' in locals() and 'Case Start Date' in df_globally_filtered.columns:
            start_date_filter, end_date_filter = date_range_val
            df_globally_filtered = df_globally_filtered[
                (df_globally_filtered['Case Start Date'].dt.date >= start_date_filter) & 
                (df_globally_filtered['Case Start Date'].dt.date <= end_date_filter)
            ]

        # Function to further process and enrich data (needs to be defined or accessible here)
        def enrich_data(df_to_enrich, sr_status_df): # Renamed to avoid conflict
            df_enriched_local = df_to_enrich.copy()
            df_enriched_local[['Status', 'Ticket Number', 'Type']] = pd.DataFrame(
                df_enriched_local['Last Note'].apply(lambda x: pd.Series(classify_and_extract(x))).values
            )
            if 'Case Start Date' in df_enriched_local.columns:
                df_enriched_local['Age (Days)'] = df_enriched_local['Case Start Date'].apply(calculate_age)
            if 'Last Note Date' in df_enriched_local.columns:
                df_enriched_local['Created Today'] = df_enriched_local['Last Note Date'].apply(is_created_today)
            
            if sr_status_df is not None:
                sr_df_copy = sr_status_df.copy()
                if 'Service Request' in sr_df_copy.columns:
                    sr_df_copy['Service Request'] = sr_df_copy['Service Request'].astype(str).str.extract(r'(\d{4,})')
                    sr_df_copy['Service Request'] = pd.to_numeric(sr_df_copy['Service Request'], errors='coerce')
                    sr_df_copy = sr_df_copy.rename(columns={'Status': 'SR Status', 'LastModDateTime': 'Last Update'})
                    
                    df_enriched_local['Ticket Number'] = pd.to_numeric(df_enriched_local['Ticket Number'], errors='coerce')
                    df_enriched_local = df_enriched_local.merge(
                        sr_df_copy[['Service Request', 'SR Status', 'Last Update']],
                        how='left', left_on='Ticket Number', right_on='Service Request'
                    ).drop(columns=['Service Request'], errors='ignore')
                else:
                    st.warning("'Service Request' column not found in SR Status file. Cannot merge SR details.")
            return df_enriched_local

        with st.spinner("Processing and enriching data..."):
            st.session_state.filtered_df = enrich_data(df_globally_filtered, st.session_state.sr_df)
    
    df_enriched_main = st.session_state.filtered_df # Use the enriched and globally filtered data

    selected_tab = option_menu(
        menu_title=None,
        options=["SR Analysis", "Not Resolved SR", "Today's SR/Incidents"],
        icons=["kanban", "clipboard-check", "calendar-date"],
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "margin": "0!important", "background-color": "#f5f7fa"},
            "icon": {"color": "#1565c0", "font-size": "14px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#1976d2", "color": "white"},
        }
    )

    # ========================== SR ANALYSIS TAB ==========================
    if selected_tab == "SR Analysis":
        st.title("🔍 SR Analysis")
        st.markdown(f"**Last data update:** {st.session_state.last_upload_time}")
        
        df_display_sr = df_enriched_main.copy() # Start with globally filtered, enriched data

        filter_col1_sr, filter_col2_sr, filter_col3_sr = st.columns(3)
        with filter_col1_sr:
            status_options_sr = ["All"] + df_display_sr["Status"].dropna().unique().tolist()
            status_filter_sr = st.selectbox("Filter by Triage Status", status_options_sr, key="sr_status_sel")
        with filter_col2_sr:
            type_options_sr = ["All", "SR", "Incident"] # Assuming these are primary
            type_filter_sr = st.selectbox("Filter by Type", type_options_sr, key="sr_type_sel")
        with filter_col3_sr:
            sr_status_filter_sr = "All" # Default if SR data not present
            if 'SR Status' in df_display_sr.columns:
                sr_status_options_sr = ["All"] + df_display_sr['SR Status'].dropna().unique().tolist() + ["None (No SR Match)"]
                sr_status_filter_sr = st.selectbox("Filter by SR Status", sr_status_options_sr, key="sr_file_status_sel")

        if status_filter_sr != "All": df_display_sr = df_display_sr[df_display_sr["Status"] == status_filter_sr]
        if type_filter_sr != "All": df_display_sr = df_display_sr[df_display_sr["Type"] == type_filter_sr]
        if 'SR Status' in df_display_sr.columns and sr_status_filter_sr != "All":
            if sr_status_filter_sr == "None (No SR Match)": df_display_sr = df_display_sr[df_display_sr["SR Status"].isna()]
            else: df_display_sr = df_display_sr[df_display_sr["SR Status"] == sr_status_filter_sr]
        
        st.subheader("📊 Summary Analysis")
        summary_col1_disp, summary_col2_disp, summary_col3_disp = st.columns(3)
        with summary_col1_disp:
            st.markdown("**🔸 Triage Status Count**")
            triage_summary = df_enriched['Status'].value_counts().rename_axis('Triage Status').reset_index(name='Count')
            triage_total = {'Triage Status': 'Total', 'Count': triage_summary['Count'].sum()}
            triage_df = pd.concat([triage_summary, pd.DataFrame([triage_total])], ignore_index=True)
            
            st.dataframe(
                triage_df.style.apply(
                    lambda x: ['background-color: #bbdefb; font-weight: bold' if x.name == len(triage_df)-1 else '' for _ in x],
                    axis=1
                )
            )
        with summary_col2_disp:
            st.markdown("**🔹 SR vs Incident Count**")
            type_summary_disp = df_enriched_main['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
            st.dataframe(type_summary_disp.style.set_properties(**{'background-color': 'white'}), use_container_width=True)
        with summary_col3_disp:
            st.markdown("**🟢 SR Status Summary**")
            if 'SR Status' in df_enriched_main.columns:
                df_status_valid_disp = df_enriched_main.dropna(subset=['SR Status'])
                sr_all_counts_disp = df_status_valid_disp['SR Status'].value_counts().rename_axis('SR Status').reset_index(name='Cases Count')
                sr_unique_disp = df_status_valid_disp.dropna(subset=['Ticket Number'])[['Ticket Number', 'SR Status']].drop_duplicates()
                sr_unique_counts_disp = sr_unique_disp['SR Status'].value_counts().rename_axis('SR Status').reset_index(name='Unique SR Count')
                merged_sr_disp = pd.merge(sr_all_counts_disp, sr_unique_counts_disp, on='SR Status', how='outer').fillna(0)
                merged_sr_disp[['Cases Count', 'Unique SR Count']] = merged_sr_disp[['Cases Count', 'Unique SR Count']].astype(int)
                st.dataframe(merged_sr_disp.style.set_properties(**{'background-color': 'white'}), use_container_width=True)
            else: st.info("Upload SR Status file for this summary.")

        st.subheader("📋 Filtered Results")
        results_count_col, dl_button_col = st.columns([3,1])
        results_count_col.markdown(f"**Total Filtered Records:** {len(df_display_sr)}")

        # --- NEW: Customize Displayed Columns & Export Expander ---
        with st.expander("⚙️ Customize Displayed Columns & Export", expanded=False):
            all_available_cols_sr = df_display_sr.columns.tolist()
            # Define default columns, ensuring 'Case Id' is present for tracking logic
            default_cols_for_sr_display = ['Case Id', 'Current User Id', 'Case Start Date', 'Status', 'Type', 'Ticket Number', 'Last Note']
            if 'SR Status' in all_available_cols_sr: default_cols_for_sr_display.append('SR Status')
            if 'Last Update' in all_available_cols_sr: default_cols_for_sr_display.append('Last Update')
            
            # Filter defaults to only those available in df_display_sr
            default_cols_for_sr_display = [col for col in default_cols_for_sr_display if col in all_available_cols_sr]

            # Initialize session state for selected columns if not already or if context changed
            if not st.session_state.sr_selected_display_cols or \
               not all(col in all_available_cols_sr for col in st.session_state.sr_selected_display_cols):
                st.session_state.sr_selected_display_cols = default_cols_for_sr_display

            st.session_state.sr_selected_display_cols = st.multiselect(
                "Select columns to display in the table below:",
                options=all_available_cols_sr,
                default=st.session_state.sr_selected_display_cols,
                key="sr_col_multiselect"
            )
            if not df_display_sr.empty and st.session_state.sr_selected_display_cols:
                df_to_download_sr = df_display_sr[st.session_state.sr_selected_display_cols]
                excel_data_sr_dl = generate_excel_download(df_to_download_sr)
                st.download_button(
                    label="📥 Download Selected Columns (Excel)",
                    data=excel_data_sr_dl,
                    file_name=f"sr_analysis_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_custom_sr_excel"
                )
            elif df_display_sr.empty:
                st.caption("No data to export.")
        # --- END NEW EXPANDER ---
        
        # Download button for ALL columns of filtered data (original position)
        if not df_display_sr.empty:
            excel_data_full_sr = generate_excel_download(df_display_sr)
            dl_button_col.download_button(
                label="📥 Download All Columns",
                data=excel_data_full_sr,
                file_name=f"sr_analysis_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_full_sr_excel"
            )
        
        if not df_display_sr.empty:
            if not st.session_state.sr_selected_display_cols: # If user deselects all, show a message
                st.warning("Please select at least one column to display in the table.")
            else:
                # Ensure 'Case Id' is in the selected columns for the editor if not already handled by default
                # For the current setup, data_editor will get selected columns + a new 'Select_Track' column
                
                df_for_editor_sr = df_display_sr[st.session_state.sr_selected_display_cols].copy()
                
                # Add a 'Select_Track' column for the checkbox, initialized based on current tracking status
                tracked_case_ids_sr = {row['Case Id'] for row in st.session_state.tracked_rows}
                # 'Case Id' must be in df_for_editor_sr for this to work. Add it if user deselected.
                if 'Case Id' not in df_for_editor_sr.columns:
                    # This is a fallback, ideally 'Case Id' is a fixed part of selection for this table type
                    df_for_editor_sr['Case Id'] = df_display_sr['Case Id']


                df_for_editor_sr['Select_Track'] = df_for_editor_sr['Case Id'].apply(lambda cid: cid in tracked_case_ids_sr)

                edited_df_sr = st.data_editor(
                    df_for_editor_sr,
                    column_config={
                        "Select_Track": st.column_config.CheckboxColumn(
                            "Track",
                            help="Check to select for tracking update",
                            default=False, 
                        )
                    },
                    hide_index=True,
                    key="sr_selection_table_editor",
                    use_container_width=True,
                    # Control column order: checkbox first, then user selected.
                    # Need to reorder df_for_editor_sr before passing to data_editor
                    # Example: column_order=["Select_Track"] + st.session_state.sr_selected_display_cols
                )
                # Reorder columns for display in data_editor (Checkbox first)
                cols_for_editor_ordered = ["Select_Track"] + [col for col in st.session_state.sr_selected_display_cols if col != 'Select_Track']
                # Ensure all columns in cols_for_editor_ordered exist in df_for_editor_sr
                # This might require df_for_editor_sr to be constructed with these cols specifically.
                # For now, let's pass df_for_editor_sr as is and rely on column_config for the special column.
                # The order will be original columns + the added 'Select_Track' at the end by default.
                # User can reorder manually in UI if data_editor supports it, or we can force order.


                if st.button("Apply Checkbox Changes to Tracking", key="apply_sr_checkbox_tracking"):
                    num_changes_sr = 0
                    tracked_case_ids_before_apply_sr = {item['Case Id'] for item in st.session_state.tracked_rows}

                    for _idx, editor_row_sr in edited_df_sr.iterrows():
                        case_id_sr = editor_row_sr['Case Id'] 
                        should_be_tracked_sr = editor_row_sr['Select_Track']
                        is_currently_tracked_sr = case_id_sr in tracked_case_ids_before_apply_sr
                        
                        # Fetch full data for tracking from the main filtered df_display_sr
                        case_data_for_tracking_sr = df_display_sr[df_display_sr['Case Id'] == case_id_sr].iloc[0]

                        if should_be_tracked_sr and not is_currently_tracked_sr:
                            track_row(case_data_for_tracking_sr) 
                            num_changes_sr +=1
                        elif not should_be_tracked_sr and is_currently_tracked_sr:
                            track_row(case_data_for_tracking_sr) 
                            num_changes_sr +=1
                    
                    if num_changes_sr > 0:
                        st.success(f"Applied {num_changes_sr} changes to tracking status!")
                        st.rerun()
                    else:
                        st.info("No changes in tracking status based on checkboxes.")

                col_track_all, col_untrack_all = st.columns(2)
                if col_track_all.button("Track All Visible in Table", key="track_all_sr_visible"):
                    visible_case_ids_sr = edited_df_sr['Case Id'].tolist() # Use Case IDs from the table shown
                    tracked_count = 0
                    for case_id_to_track in visible_case_ids_sr:
                        if case_id_to_track not in {item['Case Id'] for item in st.session_state.tracked_rows}:
                            case_data = df_display_sr[df_display_sr['Case Id'] == case_id_to_track].iloc[0]
                            track_row(case_data) # track_row adds if not present
                            tracked_count +=1
                    if tracked_count > 0: st.success(f"Added {tracked_count} visible items to tracking!")
                    else: st.info("All visible items already tracked or no new items to track.")
                    st.rerun()
                
                if col_untrack_all.button("Untrack All Visible in Table", key="untrack_all_sr_visible"):
                    visible_case_ids_sr = edited_df_sr['Case Id'].tolist()
                    untracked_count = 0
                    initial_tracked_ids = {item['Case Id'] for item in st.session_state.tracked_rows}
                    for case_id_to_untrack in visible_case_ids_sr:
                        if case_id_to_untrack in initial_tracked_ids:
                            # track_row toggles, so calling it will untrack
                            case_data = df_display_sr[df_display_sr['Case Id'] == case_id_to_untrack].iloc[0]
                            track_row(case_data)
                            untracked_count += 1
                    if untracked_count > 0: st.success(f"Removed {untracked_count} visible items from tracking!")
                    else: st.info("No visible items were currently tracked.")
                    st.rerun()
        else:
            st.info("No data to display for SR Analysis with current filters.")

        st.subheader("📝 Note Details")
        if not df_display_sr.empty:
            # Use a selectbox for choosing a case from the filtered list
            available_case_ids_note = df_display_sr['Case Id'].unique().tolist()
            if available_case_ids_note:
                selected_case_note = st.selectbox(
                    "Select a case to view notes:",
                    options=available_case_ids_note,
                    key="sr_note_case_select"
                )
                if selected_case_note:
                    case_row_note = df_display_sr[df_display_sr['Case Id'] == selected_case_note].iloc[0]
                    case_details_note = {
                        "Field": ["Case ID", "Owner", "Start Date", "Age", "Ticket Number", "Type"],
                        "Value": [
                            case_row_note['Case Id'], case_row_note['Current User Id'],
                            case_row_note['Case Start Date'].strftime('%Y-%m-%d') if pd.notna(case_row_note['Case Start Date']) else 'N/A',
                            f"{case_row_note['Age (Days)']} days" if pd.notna(case_row_note.get('Age (Days)')) else 'N/A',
                            int(case_row_note['Ticket Number']) if pd.notna(case_row_note['Ticket Number']) else 'N/A',
                            case_row_note['Type'] if pd.notna(case_row_note['Type']) else 'N/A'
                        ]
                    }
                    if 'SR Status' in case_row_note and pd.notna(case_row_note['SR Status']):
                        case_details_note["Field"].extend(["SR Status", "Last Update"])
                        case_details_note["Value"].extend([
                            case_row_note['SR Status'], 
                            case_row_note['Last Update'].strftime('%Y-%m-%d %H:%M') if pd.notna(case_row_note.get('Last Update')) else 'N/A'
                        ])
                    st.table(pd.DataFrame(case_details_note))
                    
                    is_tracked_note = case_row_note['Case Id'] in {item['Case Id'] for item in st.session_state.tracked_rows}
                    track_button_label_note = "🔄 Untrack this Case" if is_tracked_note else "✅ Track this Case"
                    if st.button(track_button_label_note, key="note_track_button"):
                        track_row(case_row_note)
                        st.rerun()

                    st.markdown("### Last Note")
                    st.text_area("Note Content", case_row_note.get('Last Note', 'No notes available.'), height=200, key="sr_note_content_area")
                    
                    excel_data_case_dl = generate_excel_download(df_display_sr[df_display_sr['Case Id'] == selected_case_note])
                    st.download_button(
                        label="📥 Download Case Details", data=excel_data_case_dl,
                        file_name=f"case_{selected_case_note}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_single_case_sr"
                    )
            else:
                st.info("No cases available in the current filtered view to select for note details.")
        else:
            st.info("No data to display notes from.")


    # ========================== NOT RESOLVED SR TAB ==========================
    elif selected_tab == "Not Resolved SR":
        st.title("📋 Tracked Service Requests")
        if not st.session_state.tracked_rows:
            st.info("No service requests are currently being tracked. Add SRs from the 'SR Analysis' tab.")
        else:
            tracked_df_display = pd.DataFrame(st.session_state.tracked_rows)
            
            # Convert date columns back to datetime if they were stringified in to_dict
            for date_col_tracked in ['Case Start Date', 'Last Note Date', 'Last Update']:
                if date_col_tracked in tracked_df_display.columns:
                    tracked_df_display[date_col_tracked] = pd.to_datetime(tracked_df_display[date_col_tracked], errors='coerce')

            st.subheader("📊 Tracked SR Statistics")
            stats_dict_tracked = {
                "Metric": ["Total Tracked Items", "Service Requests", "Incidents"],
                "Count": [
                    len(tracked_df_display),
                    len(tracked_df_display[tracked_df_display['Type'] == 'SR']),
                    len(tracked_df_display[tracked_df_display['Type'] == 'Incident'])
                ]
            }
            st.table(pd.DataFrame(stats_dict_tracked))
            
            st.download_button(
                label="📥 Download Tracked Items", data=generate_excel_download(tracked_df_display),
                file_name=f"tracked_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_tracked_excel"
            )
            
            st.subheader("📋 Tracked Items List")
            display_cols_tracked = ['Case Id', 'Current User Id', 'Case Start Date', 'Status', 'Type', 'Ticket Number', 'Age (Days)']
            if 'SR Status' in tracked_df_display.columns: display_cols_tracked.extend(['SR Status', 'Last Update'])
            display_cols_tracked_final = [col for col in display_cols_tracked if col in tracked_df_display.columns]
            
            # Add a 'Select_Untrack' column for checkboxes
            tracked_df_display['Select_Untrack'] = False # Initialize all to False

            edited_tracked_df_display = st.data_editor(
                tracked_df_display, # Pass the full df with Select_Untrack
                column_order = ["Select_Untrack"] + display_cols_tracked_final, # Checkbox first
                column_config={"Select_Untrack": st.column_config.CheckboxColumn("Untrack?", help="Select to remove from tracking",default=False)},
                hide_index=True, key="tracked_items_editor", use_container_width=True
            )
            
            if st.button("Remove Selected from Tracking", key="untrack_selected_button"):
                selected_to_untrack_ids = edited_tracked_df_display[edited_tracked_df_display["Select_Untrack"] == True]['Case Id'].tolist()
                if selected_to_untrack_ids:
                    st.session_state.tracked_rows = [
                        row for row in st.session_state.tracked_rows if row['Case Id'] not in selected_to_untrack_ids
                    ]
                    st.success(f"Removed {len(selected_to_untrack_ids)} items from tracking!")
                    st.rerun()
                else:
                    st.warning("No items selected for untracking.")
            
            if st.button("Clear All Tracked Items", key="clear_all_tracked_button"):
                st.session_state.tracked_rows = []
                st.success("All tracked items cleared!")
                st.rerun()
            
            st.subheader("🔍 Tracked Item Details")
            if not tracked_df_display.empty:
                available_tracked_ids = tracked_df_display['Case Id'].unique().tolist()
                if available_tracked_ids:
                    selected_tracked_case_details = st.selectbox(
                        "Select a tracked case for details:", options=available_tracked_ids, key="tracked_case_detail_select"
                    )
                    if selected_tracked_case_details:
                        tracked_case_row_details = tracked_df_display[tracked_df_display['Case Id'] == selected_tracked_case_details].iloc[0]
                        col1_td, col2_td = st.columns(2)
                        with col1_td:
                            st.markdown("### Case Information")
                            details_tracked_item = {
                                "Field": ["Case ID", "Owner", "Start Date", "Age"],
                                "Value": [
                                    tracked_case_row_details['Case Id'], tracked_case_row_details['Current User Id'],
                                    tracked_case_row_details['Case Start Date'].strftime('%Y-%m-%d') if pd.notna(tracked_case_row_details.get('Case Start Date')) else 'N/A',
                                    f"{tracked_case_row_details['Age (Days)']} days" if pd.notna(tracked_case_row_details.get('Age (Days)')) else 'N/A'
                                ]
                            }
                            if pd.notna(tracked_case_row_details.get('Ticket Number')):
                                details_tracked_item["Field"].extend(["Ticket Number", "Type"])
                                details_tracked_item["Value"].extend([int(tracked_case_row_details['Ticket Number']), tracked_case_row_details['Type']])
                            if pd.notna(tracked_case_row_details.get('SR Status')):
                                details_tracked_item["Field"].append("SR Status")
                                details_tracked_item["Value"].append(tracked_case_row_details['SR Status'])
                                if pd.notna(tracked_case_row_details.get('Last Update')):
                                    details_tracked_item["Field"].append("Last Update")
                                    details_tracked_item["Value"].append(tracked_case_row_details['Last Update'].strftime('%Y-%m-%d %H:%M') if pd.notna(tracked_case_row_details.get('Last Update')) else 'N/A')
                            st.table(pd.DataFrame(details_tracked_item))
                        with col2_td:
                            st.markdown("### Last Note")
                            st.text_area("Note Content", tracked_case_row_details.get('Last Note', 'No notes.'), height=250, key="tracked_item_note_area")
                        
                        if st.button("Remove This Item from Tracking", key="remove_single_tracked_detail"):
                            st.session_state.tracked_rows = [
                                r for r in st.session_state.tracked_rows if r['Case Id'] != selected_tracked_case_details
                            ]
                            st.success(f"Removed case {selected_tracked_case_details} from tracking!")
                            st.rerun()
                else:
                    st.info("No tracked items to display details for.")
            else:
                st.info("Track list is empty.")

    # ========================== TODAY'S SR/INCIDENTS TAB ==========================
    elif selected_tab == "Today's SR/Incidents":
        st.title("📆 Today's New SR/Incidents")
        df_today_tab = df_enriched_main[df_enriched_main['Created Today'] == True].copy() if 'Created Today' in df_enriched_main else pd.DataFrame()

        st.subheader("📊 Today's Activity Summary")
        col1_today_sum, col2_today_sum, col3_today_sum = st.columns(3)
        with col1_today_sum:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            sr_count_today = len(df_today_tab[df_today_tab['Type'] == 'SR']) if 'Type' in df_today_tab else 0
            st.markdown(f'<p class="metric-value">{sr_count_today}</p><p class="metric-label">New Service Requests Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2_today_sum:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            incident_count_today = len(df_today_tab[df_today_tab['Type'] == 'Incident']) if 'Type' in df_today_tab else 0
            st.markdown(f'<p class="metric-value">{incident_count_today}</p><p class="metric-label">New Incidents Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3_today_sum:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            total_count_today = len(df_today_tab)
            st.markdown(f'<p class="metric-value">{total_count_today}</p><p class="metric-label">Total New Items Today</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("📋 Today's New Items")
        if df_today_tab.empty:
            st.info("No new SR/Incidents found for today based on current global filters.")
        else:
            today_filter_col1_disp, today_filter_col2_disp = st.columns(2)
            with today_filter_col1_disp:
                today_type_filter_disp = st.selectbox("Filter by Type", ["All", "SR", "Incident"], key="today_type_filter_disp")
            with today_filter_col2_disp:
                user_options_today = ["All"] + df_today_tab['Current User Id'].dropna().unique().tolist()
                today_user_filter_disp = st.selectbox("Filter by User", user_options_today, key="today_user_filter_disp")

            df_today_filtered_disp = df_today_tab.copy()
            if today_type_filter_disp != "All": df_today_filtered_disp = df_today_filtered_disp[df_today_filtered_disp['Type'] == today_type_filter_disp]
            if today_user_filter_disp != "All": df_today_filtered_disp = df_today_filtered_disp[df_today_filtered_disp['Current User Id'] == today_user_filter_disp]
            
            st.markdown(f"**Filtered Results:** {len(df_today_filtered_disp)} items")
            if not df_today_filtered_disp.empty:
                st.download_button(
                    label="📥 Download Today's Items", data=generate_excel_download(df_today_filtered_disp),
                    file_name=f"today_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_today_items_excel"
                )
            
            display_cols_today = ['Case Id', 'Case Start Date','Last Note', 'Last Note Date', 'Status', 'Type', 'Ticket Number']
            if 'SR Status' in df_today_filtered_disp.columns: display_cols_today.extend(['SR Status', 'Last Update'])
            display_cols_today_final = [col for col in display_cols_today if col in df_today_filtered_disp.columns]
            st.dataframe(df_today_filtered_disp[display_cols_today_final], hide_index=True, use_container_width=True)
            
            st.subheader("🔍 Track Today's Items")
            if not df_today_filtered_disp.empty:
                available_today_ids = df_today_filtered_disp['Case Id'].unique().tolist()
                if available_today_ids:
                    selected_case_today_track = st.selectbox(
                        "Select a case to view details or track:", options=available_today_ids, key="today_case_track_select"
                    )
                    if selected_case_today_track:
                        today_case_row_track = df_today_filtered_disp[df_today_filtered_disp['Case Id'] == selected_case_today_track].iloc[0]
                        st.markdown("### Case Details")
                        col1_today_detail, col2_today_detail = st.columns(2)
                        with col1_today_detail:
                            details_today_item = {
                                "Field": ["Case ID", "Owner", "Start Date"],
                                "Value": [
                                    today_case_row_track['Case Id'], today_case_row_track['Current User Id'],
                                    today_case_row_track['Case Start Date'].strftime('%Y-%m-%d') if pd.notna(today_case_row_track.get('Case Start Date')) else 'N/A'
                                ]
                            }
                            if pd.notna(today_case_row_track.get('Ticket Number')):
                                details_today_item["Field"].extend(["Ticket Number", "Type"])
                                details_today_item["Value"].extend([int(today_case_row_track['Ticket Number']), today_case_row_track['Type']])
                            if pd.notna(today_case_row_track.get('SR Status')):
                                details_today_item["Field"].append("SR Status")
                                details_today_item["Value"].append(today_case_row_track['SR Status'])
                                if pd.notna(today_case_row_track.get('Last Update')):
                                    details_today_item["Field"].append("Last Update")
                                    details_today_item["Value"].append(today_case_row_track['Last Update'].strftime('%Y-%m-%d %H:%M') if pd.notna(today_case_row_track.get('Last Update')) else 'N/A')
                            st.table(pd.DataFrame(details_today_item))
                        with col2_today_detail:
                            st.markdown("### Last Note")
                            st.text_area("Note Content", today_case_row_track.get('Last Note', 'No notes.'), height=250, key="today_item_note_area")
                        
                        is_tracked_today = today_case_row_track['Case Id'] in {item['Case Id'] for item in st.session_state.tracked_rows}
                        track_button_label_today = "🔄 Untrack this Case" if is_tracked_today else "✅ Track this Case"
                        if st.button(track_button_label_today, key="today_track_detail_button"):
                            track_row(today_case_row_track)
                            st.rerun()
                else:
                    st.info("No items from today to select for tracking in the current filtered view.")
            else:
                st.info("No items from today to track.")

# --- Footer ---
st.markdown("<hr style='margin: 2em 0; border-color: #ddd;'>", unsafe_allow_html=True)
st.markdown(
    """<div style="text-align:center; color:#888; font-size:0.8em;">
    SR Analyzer Pro | Developed with Streamlit | © """ + str(datetime.now().year) + """
    </div>""",
    unsafe_allow_html=True
)