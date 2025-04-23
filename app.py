import streamlit as st
import pandas as pd
import re
import io
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(page_title="Excel Incident Analyzer", layout="wide")
st.title("📊 SR Analyzer")

# Sidebar uploads
uploaded_file = st.sidebar.file_uploader("📂 Upload Main Excel File (.xlsx)", type="xlsx")
sr_status_file = st.sidebar.file_uploader("📂 Upload SR Status Excel (optional)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        # Classification
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

        df_display = df_filtered.copy()

        # Sidebar filters
        st.sidebar.markdown("---")
        status_filter = st.sidebar.selectbox("📌 Filter by Triage Status", ["All"] + df_filtered["Status"].dropna().unique().tolist())
        type_filter = st.sidebar.selectbox("📌 Filter by Type", ["All", "SR", "Incident"])

        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]

        # Process SR Status file
        if sr_status_file:
            try:
                sr_df = pd.read_excel(sr_status_file)

                # Extract and normalize ticket numbers
                sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d{4,})')
                sr_df['Ticket Number'] = sr_df['Service Request'].astype(float).astype("Int64")

                df_display['Ticket Number'] = df_display['Ticket Number'].astype(str).str.extract(r'(\d{4,})')
                df_display['Ticket Number'] = df_display['Ticket Number'].astype(float).astype("Int64")

                df_sr_only = df_display[df_display['Type'] == 'SR'].copy()

                required_cols = ['Ticket Number', 'Status', 'LastModDateTime']
                missing = [col for col in required_cols if col not in sr_df.columns]
                if missing:
                    st.error(f"Missing column(s) in SR Status file: {', '.join(missing)}")
                else:
                    df_sr_only = df_sr_only.merge(
                        sr_df[required_cols],
                        on='Ticket Number', how='left'
                    ).rename(columns={
                        'Status': 'SR Status',
                        'LastModDateTime': 'Last Update'
                    })

                    if 'SR Status' not in df_sr_only.columns:
                        st.warning("Merge didn't return SR Status info — no matching Ticket Numbers found.")
                    else:
                        df_display.update(df_sr_only)

                        # Optional SR Status filter
                        if 'SR Status' in df_display.columns:
                            sr_status_options = df_display['SR Status'].dropna().unique().tolist()
                            sr_status_filter = st.sidebar.selectbox("📌 Filter by SR Status", ["All"] + sorted(sr_status_options))
                            if sr_status_filter != "All":
                                df_display = df_display[df_display['SR Status'] == sr_status_filter]

                        # Final display limited to specified columns
                        final_columns = ['Ticket Number', 'Case Id', 'Last Note Date', 'Current User Id', 'SR Status', 'Last Update']
                        existing_cols = [col for col in final_columns if col in df_display.columns]
                        df_display = df_display[existing_cols]

            except Exception as e:
                st.error(f"Error processing SR Status file: {e}")

        # Summary and Results
        st.subheader("📊 Summary")
        summary = df_filtered['Status'].value_counts().rename_axis('Status').reset_index(name='Count')
        st.table(summary)

        st.subheader("📋 Filtered Results")
        st.markdown(f"**Total Filtered Rows:** {df_display.shape[0]}")
        st.dataframe(df_display)

        # Download
        def generate_excel_download(data):
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            data.to_excel(writer, index=False, sheet_name='Results')
            writer.close()
            output.seek(0)
            return output

        excel_data = generate_excel_download(df_display)
        st.download_button(
            label="📥 Download Filtered Data to Excel",
            data=excel_data,
            file_name="filtered_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Something went wrong: {e}")
