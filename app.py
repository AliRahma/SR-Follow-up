import streamlit as st
import pandas as pd
import re

# Page setup
st.set_page_config(page_title="Excel Incident Analyzer", layout="wide")
st.title("📊 Excel Intellipen Analyzer")

# Sidebar filters
st.sidebar.header("🔧 Filters")
uploaded_file = st.sidebar.file_uploader("Upload your Excel file (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)

        # Define columns
        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'

        # Filter for target users
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()

        # Convert to datetime
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        # Classification function
        def classify_and_extract(note):
            if not isinstance(note, str):
                return "Not Triaged", None, None

            note_lower = note.lower()
            match = re.search(
                r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})',
                note_lower
            )

            if match:
                number = int(match.group(2))
                if 15000 <= number <= 16000:
                    return "Pending SR/Incident", "SR", number
                else:
                    return "Pending SR/Incident", "Incident", number
            else:
                return "Not Triaged", None, None

        # Apply function
        df_filtered[['Status', 'Type', 'Ticket Number']] = df_filtered[note_col].apply(
            lambda x: pd.Series(classify_and_extract(x))
        )

        # Sidebar filters
        type_filter = st.sidebar.selectbox(
            "📂 Filter by Case Type",
            ["All", "SR", "Incident"]
        )
        status_filter = st.sidebar.selectbox(
            "📌 Filter by Status",
            ["All", "Pending SR/Incident", "Not Triaged"]
        )

        # Apply filters
        df_display = df_filtered.copy()
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]
        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]

        # Metrics
        st.subheader("📈 Summary Metrics")
        total_srs = df_filtered[df_filtered["Type"] == "SR"].shape[0]
        total_incidents = df_filtered[df_filtered["Type"] == "Incident"].shape[0]

        col1, col2 = st.columns(2)
        col1.metric("Total SRs", total_srs)
        col2.metric("Total Incidents", total_incidents)

        # Status Summary
        st.subheader("🧮 Status Breakdown")
        summary = df_filtered['Status'].value_counts().rename_axis('Status').reset_index(name='Count')
        st.table(summary)

        # Final results
        st.subheader("📋 Filtered Results")
        st.markdown(f"**Total Filtered Rows:** {df_display.shape[0]}")
        st.dataframe(df_display)

        # Reorder columns if status is "Pending SR/Incident"
        if status_filter == "Pending SR/Incident":
            front_cols = ['Type', 'Ticket Number']
            remaining_cols = [col for col in df_display.columns if col not in front_cols]
            df_display = df_display[front_cols + remaining_cols]

        st.dataframe(df_display)


    except Exception as e:
        st.error(f"Something went wrong: {e}")
