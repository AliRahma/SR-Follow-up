import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(page_title="Excel Incident Analyzer", layout="wide")
st.title("📊 Excel Incident Analyzer")

uploaded_file = st.sidebar.file_uploader("Upload your Incident Excel file (.xlsx)", type="xlsx")
sr_status_file = st.sidebar.file_uploader("Optional: Upload SR Status file (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Define columns
        user_col = 'Current User Id'
        note_col = 'Last Note'
        date_col = 'Case Start Date'

        # Filter target users
        target_users = ['ali.babiker', 'anas.hasan', 'ahmed.mostafa']
        df_filtered = df[df[user_col].isin(target_users)].copy()
        df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')

        def classify_and_extract(note):
            if not isinstance(note, str):
                return "Not Triaged", None, None
            note_lower = note.lower()
            match = re.search(
                r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\\d{4,})',
                note_lower
            )
            if match:
                ticket_number = int(match.group(2))
                ticket_type = "SR" if 15000 <= ticket_number <= 16000 else "Incident"
                return "Pending SR/Incident", ticket_number, ticket_type
            else:
                return "Not Triaged", None, None

        df_filtered[['Status', 'Ticket Number', 'Type']] = df_filtered[note_col].apply(
            lambda x: pd.Series(classify_and_extract(x))
        )

        st.subheader("📊 Summary")
        summary = df_filtered['Status'].value_counts().rename_axis('Status').reset_index(name='Count')
        st.table(summary)

        st.sidebar.subheader("🔍 Filters")
        status_filter = st.sidebar.selectbox("Filter by Status", ["All"] + df_filtered['Status'].dropna().unique().tolist())
        type_filter = st.sidebar.selectbox("Filter by Type", ["All"] + df_filtered['Type'].dropna().unique().tolist())

        df_display = df_filtered.copy()
        if status_filter != "All":
            df_display = df_display[df_display["Status"] == status_filter]
        if type_filter != "All":
            df_display = df_display[df_display["Type"] == type_filter]

        if status_filter == "Pending SR/Incident":
            front_cols = ['Type', 'Ticket Number']
            other_cols = [col for col in df_display.columns if col not in front_cols]
            df_display = df_display[front_cols + other_cols]

        # Process SR Status file
        if sr_status_file:
            try:
                sr_df = pd.read_excel(sr_status_file)
                sr_df['Service Request'] = sr_df['Service Request'].astype(str).str.extract(r'(\d{4,})')
                sr_df['Ticket Number'] = sr_df['Service Request'].astype(float).astype("Int64")
                df_display['Ticket Number'] = df_display['Ticket Number'].astype("Int64")

                is_sr = df_display['Type'] == "SR"
                df_sr_only = df_display[is_sr].copy()

                required_cols = ['Ticket Number', 'Status', 'LastModDateTime']
                missing = [col for col in required_cols if col not in sr_df.columns]
                if missing:
                    st.error(f"Missing column(s) in SR Status file: {', '.join(missing)}")
                else:
                    df_sr_only = df_sr_only.merge(
                        sr_df[required_cols],
                        on='Ticket Number', how='left'
                    ).rename(columns={'Status': 'SR Status', 'LastModDateTime': 'Last Update'})

                    if 'SR Status' not in df_sr_only.columns:
                        st.warning("Merge didn't return SR Status info — no matching Ticket Numbers found.")
                    else:
                        df_display.update(df_sr_only)

                        front_cols = ['Type', 'Ticket Number']
                        if 'SR Status' in df_display.columns and 'Last Update' in df_display.columns:
                            front_cols += ['SR Status', 'Last Update']

                            sr_status_options = df_display['SR Status'].dropna().unique().tolist()
                            sr_status_filter = st.sidebar.selectbox(
                                "📌 Filter by SR Status", ["All"] + sorted(sr_status_options)
                            )
                            if sr_status_filter != "All":
                                df_display = df_display[df_display['SR Status'] == sr_status_filter]

                            st.subheader("🥧 SR Status Distribution")
                            sr_pie = df_display[df_display['Type'] == "SR"]['SR Status'].value_counts()
                            fig, ax = plt.subplots()
                            ax.pie(sr_pie, labels=sr_pie.index, autopct='%1.1f%%', startangle=140)
                            ax.axis('equal')
                            st.pyplot(fig)

                        other_cols = [col for col in df_display.columns if col not in front_cols]
                        df_display = df_display[front_cols + other_cols]

            except Exception as e:
                st.error(f"Error processing SR Status file: {e}")

        st.subheader(f"📋 Filtered Results (Total: {len(df_display)})")
        st.dataframe(df_display)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
