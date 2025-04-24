import streamlit as st
import pandas as pd
import re
import io
import base64
import streamlit.components.v1 as components

# Page must be set at the top
st.set_page_config(page_title="SR Follow up", layout="wide")

# Optional dark-themed background
def set_background_dark(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)),
                    url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: #f0f0f0 !important;
    }}
    .stDataFrame div, .stTable, .stMarkdown, .stSelectbox, .stDownloadButton {{
        background-color: rgba(0, 0, 0, 0.5) !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Example: set_background_dark("GPSSA.jpg")

# UI setup
st.title("📊 SR Analyzer")

uploaded_file = st.sidebar.file_uploader("📂 Upload Main Excel File (.xlsx)", type="xlsx")
sr_status_file = st.sidebar.file_uploader("📂 Upload SR Status Excel (optional)", type="xlsx")

# Store selected ticket in session state
if "selected_ticket" not in st.session_state:
    st.session_state.selected_ticket = None

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Basic filtering and classification
        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        def classify_and_extract(note):
            if not isinstance(note, str):
                return "Not Triaged", None, None
            note_lower = note.lower()
            match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
            if match:
                ticket_num = int(match.group(2))
                return "Pending SR/Incident", ticket_num, "SR" if 14000 <= ticket_num <= 16000 else "Incident"
            return "Not Triaged", None, None

        df_filtered[['Status', 'Ticket Number', 'Type']] = df_filtered[note_col].apply(
            lambda x: pd.Series(classify_and_extract(x))
        )

        # Merge SR status if uploaded
        if sr_status_file:
            sr_df = pd.read_excel(sr_status_file)
            sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d{4,})')
            sr_df['Service Request'] = sr_df['Service Request'].astype(float).astype("Int64")
            sr_df = sr_df.rename(columns={'Status': 'SR Status', 'LastModDateTime': 'Last Update'})

            df_filtered['Ticket Number'] = df_filtered['Ticket Number'].astype("Int64")
            df_filtered = df_filtered.merge(
                sr_df[['Service Request', 'SR Status', 'Last Update']],
                how='left', left_on='Ticket Number', right_on='Service Request'
            ).drop(columns=['Service Request'])

        # Filters
        st.sidebar.markdown("---")
        status_filter = st.sidebar.selectbox("📌 Filter by Triage Status", ["All"] + df_filtered["Status"].dropna().unique().tolist())
        type_filter = st.sidebar.selectbox("📌 Filter by Type", ["All", "SR", "Incident"])
        sr_status_options = df_filtered['SR Status'].dropna().unique().tolist()
        sr_status_filter = st.sidebar.selectbox("📌 Filter by SR Status", ["All"] + sr_status_options)

        df_display = df_filtered.copy()
        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]
        if sr_status_filter != "All":
            df_display = df_display[df_display["SR Status"] == sr_status_filter]

        # Summary Sections
        st.subheader("📊 Summary Counts")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🔸 Triage Status Count**")
            triage_summary = df_filtered['Status'].value_counts().loc[['Pending SR/Incident', 'Not Triaged']]
            triage_df = triage_summary.rename_axis('Triage Status').reset_index(name='Count')
            triage_total = pd.DataFrame([{'Triage Status': 'Total', 'Count': triage_df['Count'].sum()}])
            df_triage = pd.concat([triage_df, triage_total], ignore_index=True)
            st.dataframe(df_triage.style.apply(lambda x: ['background-color: #cce5ff; font-weight: bold' if x.name == len(df_triage)-1 else '' for _ in x], axis=1))

        with col2:
            st.markdown("**🔹 SR vs Incident Count**")
            type_summary = df_filtered['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
            type_total = pd.DataFrame([{'Type': 'Total', 'Count': type_summary['Count'].sum()}])
            type_df = pd.concat([type_summary, type_total], ignore_index=True)
            st.dataframe(type_df.style.apply(lambda x: ['background-color: #cce5ff; font-weight: bold' if x.name == len(type_df)-1 else '' for _ in x], axis=1))

        with col3:
            st.markdown("**🟢 SR Status Count**")
            sr_status_summary = df_filtered['SR Status'].value_counts().rename_axis('SR Status').reset_index(name='Count')
            sr_total = pd.DataFrame([{'SR Status': 'Total', 'Count': sr_status_summary['Count'].sum()}])
            sr_df = pd.concat([sr_status_summary, sr_total], ignore_index=True)
            st.dataframe(sr_df.style.apply(lambda x: ['background-color: #cce5ff; font-weight: bold' if x.name == len(sr_df)-1 else '' for _ in x], axis=1))

        # Filtered results
        st.subheader("📋 Filtered Results")
        st.markdown(f"**Total Filtered Rows:** {df_display.shape[0]}")
        shown_cols = ['Ticket Number', 'Case Id', 'Last Note', 'Current User Id', 'SR Status', 'Last Update']
        for col in shown_cols:
            if col not in df_display.columns:
                df_display[col] = None
        st.dataframe(df_display[shown_cols])

        excel_data = generate_excel_download(df_display[shown_cols])
        st.download_button("📥 Download Filtered Data to Excel", data=excel_data, file_name="filtered_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
