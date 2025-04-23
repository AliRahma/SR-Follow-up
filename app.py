import streamlit as st
import pandas as pd
import re
import io
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(page_title="Excel Incident Analyzer", layout="wide")
st.title("📊 Excel Incident Analyzer")

# Upload main Excel file
uploaded_file = st.sidebar.file_uploader("Upload your Excel file (.xlsx)", type="xlsx")
sr_status_file = st.sidebar.file_uploader("Upload SR Status Excel (optional)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Column config
        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'

        # Filter relevant users
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        # Classification function
        def classify_and_extract(note):
            if not isinstance(note, str):
                return "Not Triaged", None, None
            note_lower = note.lower()
            match = re.search(r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})', note_lower)
            if match:
                ticket_num = int(match.group(2))
                if 15000 <= ticket_num <= 16000:
                    return "Pending SR/Incident", ticket_num, "SR"
                else:
                    return "Pending SR/Incident", ticket_num, "Incident"
            else:
                return "Not Triaged", None, None

        df_filtered[['Status', 'Ticket Number', 'Type']] = df_filtered[note_col].apply(
            lambda x: pd.Series(classify_and_extract(x))
        )

        # Sidebar filter: Status
        st.sidebar.markdown("---")
        status_filter = st.sidebar.selectbox("📌 Filter by Triage Status", ["All"] + df_filtered["Status"].dropna().unique().tolist())
        type_filter = st.sidebar.selectbox("📌 Filter by Type", ["All", "SR", "Incident"])

        df_display = df_filtered.copy()
        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]

        # If SR status file uploaded
        if sr_status_file:
            try:
                sr_df = pd.read_excel(sr_status_file)
                sr_df['Ticket Number'] = sr_df['Ticket Number'].astype(str).str.extract(r'(\d{4,})')
                sr_df['Ticket Number'] = sr_df['Ticket Number'].astype(float).astype("Int64")
                df_display['Ticket Number'] = df_display['Ticket Number'].astype("Int64")

                is_sr = df_display['Type'] == "SR"
                df_sr_only = df_display[is_sr].copy()

                df_sr_only = df_sr_only.merge(
                    sr_df[['Ticket Number', 'Status', 'LastModDateTime']],
                    on='Ticket Number', how='left'
                ).rename(columns={'Status': 'SR Status', 'LastModDateTime': 'Last Update'})

                df_display.update(df_sr_only)

                # Reorder columns
                front_cols = ['Type', 'Ticket Number']
                if 'SR Status' in df_display.columns:
                    front_cols += ['SR Status', 'Last Update']
                other_cols = [col for col in df_display.columns if col not in front_cols]
                df_display = df_display[front_cols + other_cols]

                # Sidebar filter for SR Status
                sr_status_options = df_display['SR Status'].dropna().unique().tolist()
                sr_status_filter = st.sidebar.selectbox("📌 Filter by SR Status", ["All"] + sorted(sr_status_options))
                if sr_status_filter != "All":
                    df_display = df_display[df_display['SR Status'] == sr_status_filter]

                # Pie Chart
                st.subheader("🥧 SR Status Distribution")
                sr_pie = df_display[df_display['Type'] == "SR"]['SR Status'].value_counts()
                fig, ax = plt.subplots()
                ax.pie(sr_pie, labels=sr_pie.index, autopct='%1.1f%%', startangle=140)
                ax.axis('equal')
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Error processing SR Status file: {e}")

        # Summary table
        st.subheader("📊 Summary")
        summary = df_display['Status'].value_counts().rename_axis('Status').reset_index(name='Count')
        st.table(summary)

        # Filtered Results
        st.subheader("📋 Filtered Results")
        st.markdown(f"**Total Filtered Rows:** {df_display.shape[0]}")

        # Adjust column order for Pending SR/Incident
        if status_filter == "Pending SR/Incident":
            front_cols = ['Type', 'Ticket Number']
            if 'SR Status' in df_display.columns:
                front_cols += ['SR Status', 'Last Update']
            remaining_cols = [col for col in df_display.columns if col not in front_cols]
            df_display = df_display[front_cols + remaining_cols]

        st.dataframe(df_display)

        # Excel download with highlight
        def generate_excel_download(data):
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            data.to_excel(writer, index=False, sheet_name='Results')
            workbook = writer.book
            worksheet = writer.sheets['Results']
            red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

            for row_num, row in data.iterrows():
                if row.get("Type") == "SR" and pd.isna(row.get("Last Update")):
                    worksheet.set_row(row_num + 1, None, red_format)
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
