import streamlit as st
import pandas as pd
import re
import io

# Page setup
st.set_page_config(page_title="Excel Incident Analyzer", layout="wide")
st.title("📊 SR Analyzer")

# Sidebar uploads
uploaded_file = st.sidebar.file_uploader("📂 Upload Main Excel File (.xlsx)", type="xlsx")
sr_status_file = st.sidebar.file_uploader("📂 Upload SR Status Excel (optional)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Column setup
        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        # Classification logic
        def classify_and_extract(note):
            if not isinstance(note, str):
                return "Not Triaged", None, None
            note_lower = note.lower()
            match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
            if match:
                ticket_num = int(match.group(2))
                return "Pending SR/Incident", ticket_num, "SR" if 15000 <= ticket_num <= 16000 else "Incident"
            return "Not Triaged", None, None

        df_filtered[['Status', 'Ticket Number', 'Type']] = df_filtered[note_col].apply(
            lambda x: pd.Series(classify_and_extract(x))
        )

        # Sidebar filters
        st.sidebar.markdown("---")
        status_filter = st.sidebar.selectbox("📌 Filter by Triage Status", ["All"] + df_filtered["Status"].dropna().unique().tolist())
        type_filter = st.sidebar.selectbox("📌 Filter by Type", ["All", "SR", "Incident"])

        df_display = df_filtered.copy()
        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]

        # Search
        st.subheader("🔎 Search for Ticket Number")
        search_input = st.text_input("Enter SR or Incident Number (e.g., 15023):")
        if search_input.isdigit():
            search_number = int(search_input)
            df_display = df_display[df_display['Ticket Number'] == search_number]

        # Add SR Status from second Excel if uploaded
        if sr_status_file:
            try:
                sr_df = pd.read_excel(sr_status_file)
                sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d{4,})')
                sr_df['Service Request'] = sr_df['Service Request'].astype(float).astype("Int64")

                sr_df = sr_df.rename(columns={
                    'Status': 'SR Status',
                    'LastModDateTime': 'Last Update'
                })

                df_display['Ticket Number'] = df_display['Ticket Number'].astype("Int64")
                df_display = df_display.merge(
                    sr_df[['Service Request', 'SR Status', 'Last Update']],
                    how='left',
                    left_on='Ticket Number',
                    right_on='Service Request'
                ).drop(columns=['Service Request'])

            except Exception as e:
                st.error(f"Error merging SR Status file: {e}")

        # SR vs Incident count table
        st.subheader("📊 SR vs Incident Count")
        type_summary = df_filtered['Type'].value_counts().rename_axis('Type').reset_index(name='Count')
        st.table(type_summary)

        # Final result table
        st.subheader("📋 Filtered Results")
        st.markdown(f"**Total Filtered Rows:** {df_display.shape[0]}")
        shown_cols = ['Ticket Number', 'Case Id', 'Last Note', 'Current User Id']
        if 'SR Status' in df_display.columns and 'Last Update' in df_display.columns:
            shown_cols += ['SR Status', 'Last Update']
        for col in shown_cols:
            if col not in df_display.columns:
                df_display[col] = None
        st.dataframe(df_display[shown_cols])

        # Excel download
        def generate_excel_download(data):
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            data.to_excel(writer, index=False, sheet_name='Results')
            writer.close()
            output.seek(0)
            return output

        excel_data = generate_excel_download(df_display[shown_cols])
        st.download_button(
            label="📥 Download Filtered Data to Excel",
            data=excel_data,
            file_name="filtered_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Something went wrong: {e}")

# SR Status file separate display
if sr_status_file:
    try:
        sr_df = pd.read_excel(sr_status_file)
        st.subheader("📋 SR Status File Results")
        required_cols = ['Service Request', 'Status', 'LastModDateTime']
        missing = [col for col in required_cols if col not in sr_df.columns]
        if missing:
            st.error(f"Missing column(s) in SR Status file: {', '.join(missing)}")
        else:
            st.dataframe(sr_df[required_cols])
    except Exception as e:
        st.error(f"Error processing SR Status file: {e}")
