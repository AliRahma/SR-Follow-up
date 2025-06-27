import pandas as pd
import io
from datetime import datetime, timedelta
import numpy as np
import streamlit as st # Added import for st.session_state

# Function to classify and extract ticket info (assuming this is for main_df notes)
def classify_and_extract(note): # Removed regex and range params, assuming they are fixed or handled elsewhere if varied
    if not isinstance(note, str):
        return "Not Triaged", None, None

    note_lower = note.lower()
    try:
        import re
        # Standard regex, if specific regex needed per file, this func would need more params
        ticket_regex = r'(tkt|sr|inc|ticket|مرجعي|incident|اس ار|انسدنت)[\s\S]{0,50}?(\d{4,})'
        match = re.search(ticket_regex, note_lower, re.IGNORECASE | re.DOTALL)
    except Exception as e:
        print(f"Regex error: {e}")
        return "Regex Error", None, None

    if match:
        try:
            ticket_num_str = match.group(2)
            if ticket_num_str:
                ticket_num = int(ticket_num_str)
                # Standard SR range, if varied, this needs to be dynamic
                sr_min_range, sr_max_range = 14000, 18000
                ticket_type = "SR" if sr_min_range <= ticket_num <= sr_max_range else "Incident"
                return "Pending SR/Incident", ticket_num, ticket_type
        except (IndexError, ValueError):
            return "Not Triaged", None, None
    return "Not Triaged", None, None

def calculate_age(start_date):
    if pd.isna(start_date) or not isinstance(start_date, datetime):
        return None
    return (datetime.now() - start_date).days

def is_created_today(date_value):
    if pd.isna(date_value): return False
    today = datetime.now().date()
    try:
        note_date = date_value.date() if isinstance(date_value, datetime) else pd.to_datetime(date_value).date()
    except: return False
    return note_date == today

def _get_week_display_str(year_week_str: str) -> str:
    try:
        start_date = datetime.strptime(year_week_str + '-1', "%G-W%V-%u")
        end_date = start_date + timedelta(days=6)
        return f"{year_week_str} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})"
    except ValueError:
        return year_week_str

# --- DataFrame Transformation and Calculation Functions (using NORMALIZED column names) ---

def calculate_team_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    team_col_norm = 'team' # Expected normalized name
    status_col_norm = 'status' # Expected normalized name
    total_incidents_col_norm = 'totalincidents' # Output normalized name

    if team_col_norm in df.columns and status_col_norm in df.columns:
        summary_df = df.groupby([team_col_norm, status_col_norm]).size().reset_index(name=total_incidents_col_norm)
    else:
        summary_df = pd.DataFrame(columns=[team_col_norm, status_col_norm, total_incidents_col_norm])
    return summary_df

def calculate_srs_created_per_week(df: pd.DataFrame) -> pd.DataFrame:
    created_on_norm = 'createdon'
    status_norm = 'status'
    year_week_norm = 'year-week'
    week_display_norm = 'weekdisplay'
    status_category_norm = 'statuscategory'
    number_of_srs_norm = 'numberofsrs'

    if created_on_norm not in df.columns:
        cols = [year_week_norm, week_display_norm, number_of_srs_norm]
        if status_norm in df.columns: cols.insert(2, status_category_norm)
        return pd.DataFrame(columns=cols)

    processed_df = df.copy()
    processed_df[created_on_norm] = pd.to_datetime(processed_df[created_on_norm], errors='coerce')
    processed_df.dropna(subset=[created_on_norm], inplace=True)
    if processed_df.empty: return pd.DataFrame(columns=[year_week_norm, week_display_norm, status_category_norm, number_of_srs_norm] if status_norm in df.columns else [year_week_norm, week_display_norm, number_of_srs_norm])

    processed_df[year_week_norm] = processed_df[created_on_norm].dt.strftime('%G-W%V')
    group_by_cols = [year_week_norm]
    if status_norm in processed_df.columns:
        processed_df[status_category_norm] = np.select([processed_df[status_norm].fillna('').astype(str).str.lower().isin(['closed', 'cancelled'])], ['Closed/Cancelled'], default='New/Pending')
        group_by_cols.append(status_category_norm)

    srs_per_week = processed_df.groupby(group_by_cols).size().reset_index(name=number_of_srs_norm)
    if not srs_per_week.empty: srs_per_week[week_display_norm] = srs_per_week[year_week_norm].apply(_get_week_display_str)
    else: srs_per_week[week_display_norm] = pd.Series(dtype='str')

    srs_per_week = srs_per_week.sort_values(by=group_by_cols).reset_index(drop=True)

    final_cols_order = [year_week_norm, week_display_norm]
    if status_category_norm in srs_per_week.columns: final_cols_order.append(status_category_norm)
    final_cols_order.append(number_of_srs_norm)
    srs_per_week = srs_per_week[[col for col in final_cols_order if col in srs_per_week.columns]]
    return srs_per_week

def calculate_srs_created_and_closed_per_week(df: pd.DataFrame) -> pd.DataFrame:
    created_on_norm = 'createdon'
    last_mod_dt_norm = 'lastmoddatetime'
    status_norm = 'status'
    year_week_norm = 'year-week' # Internal grouping key
    week_display_norm = 'WeekDisplay' # User-facing display
    count_norm = 'Count'
    category_norm = 'Category'

    required_cols = [created_on_norm, last_mod_dt_norm, status_norm]
    if not all(col in df.columns for col in required_cols):
        return pd.DataFrame(columns=[year_week_norm, week_display_norm, count_norm, category_norm])

    # Created SRs
    df_created = df.copy()
    df_created[created_on_norm] = pd.to_datetime(df_created[created_on_norm], errors='coerce', dayfirst=True, infer_datetime_format=True)
    df_created.dropna(subset=[created_on_norm], inplace=True)
    if not df_created.empty:
        df_created[year_week_norm] = df_created[created_on_norm].dt.strftime('%G-W%V')
        srs_created_weekly = df_created.groupby(year_week_norm).size().reset_index(name=count_norm)
        srs_created_weekly[category_norm] = 'Created'
    else: srs_created_weekly = pd.DataFrame(columns=[year_week_norm, count_norm, category_norm])

    # Closed SRs
    df_closed = df.copy()
    df_closed[status_norm] = df_closed[status_norm].astype(str).str.lower().str.strip()
    closed_statuses = ["closed","completed", "cancelled", "approval rejected", "rejected by ps"]
    df_closed = df_closed[df_closed[status_norm].isin(closed_statuses)]
    df_closed[last_mod_dt_norm] = pd.to_datetime(df_closed[last_mod_dt_norm], errors='coerce', dayfirst=True, infer_datetime_format=True)
    df_closed.dropna(subset=[last_mod_dt_norm], inplace=True)
    if not df_closed.empty:
        df_closed[year_week_norm] = df_closed[last_mod_dt_norm].dt.strftime('%G-W%V')
        srs_closed_weekly = df_closed.groupby(year_week_norm).size().reset_index(name=count_norm)
        srs_closed_weekly[category_norm] = 'Closed'
    else: srs_closed_weekly = pd.DataFrame(columns=[year_week_norm, count_norm, category_norm])

    combined_df = pd.concat([srs_created_weekly, srs_closed_weekly], ignore_index=True)
    if combined_df.empty: return pd.DataFrame(columns=[year_week_norm, week_display_norm, count_norm, category_norm])
    
    combined_df[week_display_norm] = combined_df[year_week_norm].apply(_get_week_display_str)
    combined_df = combined_df.sort_values(by=[year_week_norm, category_norm]).reset_index(drop=True)
    return combined_df[[year_week_norm, week_display_norm, count_norm, category_norm]]


# --- Display Helper ---
def get_df_with_original_column_names(df_to_display: pd.DataFrame, df_type_key: str) -> pd.DataFrame:
    if df_to_display is None: return None
    if 'column_mappings' not in st.session_state or df_type_key not in st.session_state.column_mappings:
        return df_to_display.copy()

    mapping = st.session_state.column_mappings[df_type_key] # norm_col -> orig_col
    df_copy = df_to_display.copy()
    rename_dict = {norm_col: orig_col for norm_col, orig_col in mapping.items() if norm_col in df_copy.columns}
    df_copy.rename(columns=rename_dict, inplace=True)
    return df_copy

# --- Test functions (using NORMALIZED column names internally for test data) ---
def test_case_count_calculation_and_filtering():
    # Normalized column names for test data setup
    ticket_number_norm = 'ticketnumber'
    type_norm = 'type'
    case_count_norm = 'casecount'
    other_data_norm = 'otherdata' # Example other column
    details_norm = 'details' # Example other column
    
    # Test Case Count Calculation
    case_count_data = { ticket_number_norm: ['INC100', 'SR200', 'INC100', 'SR300', 'INC100', 'SR200'], type_norm: ['Incident', 'SR', 'Incident', 'SR', 'Incident', 'SR'], other_data_norm: [1,2,3,4,5,6]}
    df_case_count_test = pd.DataFrame(case_count_data)
    df_case_count_test[case_count_norm] = df_case_count_test.groupby([ticket_number_norm, type_norm])[ticket_number_norm].transform('size')
    expected_case_counts = pd.Series([3, 2, 3, 1, 3, 2], name=case_count_norm)
    pd.testing.assert_series_equal(df_case_count_test[case_count_norm], expected_case_counts, check_dtype=False)

    # Test Filtering Logic for Linked Cases
    filtering_data = {ticket_number_norm: ['INC001', 'SR002', 'INC003', 'SR004', 'INC001', None, 'SR005', 'SR002'], type_norm: ['Incident', 'SR', 'Incident', 'SR', 'Incident', 'SR', 'SR', 'SR'], case_count_norm: [3,2,1,1,3,2,4,2], details_norm: ['A','B','C','D','E','F','G','H']}
    df_filtering_test = pd.DataFrame(filtering_data)
    min_linked_cases = 2
    linked_cases_df = df_filtering_test[(df_filtering_test[case_count_norm] >= min_linked_cases) & (df_filtering_test[ticket_number_norm].notna())]
    linked_summary_df = linked_cases_df[[ticket_number_norm, type_norm, case_count_norm]].drop_duplicates().sort_values(by=case_count_norm, ascending=False).reset_index(drop=True) if not linked_cases_df.empty else pd.DataFrame(columns=[ticket_number_norm, type_norm, case_count_norm])
    expected_summary_data = {ticket_number_norm: ['SR005', 'INC001', 'SR002'], type_norm: ['SR', 'Incident', 'SR'], case_count_norm: [4,3,2]}
    df_expected_summary = pd.DataFrame(expected_summary_data)
    pd.testing.assert_frame_equal(linked_summary_df, df_expected_summary, check_dtype=False)
    print("test_case_count_calculation_and_filtering PASSED")

def test_calculate_team_status_summary():
    team_col_norm = 'team'; status_col_norm = 'status'; id_col_norm = 'id'; total_incidents_col_norm = 'totalincidents'
    sample_data = {team_col_norm: ['Alpha', 'Alpha', 'Bravo', 'Alpha', 'Bravo', 'Charlie'], status_col_norm: ['Open', 'Closed', 'Open', 'Open', 'In Progress', 'Open'], id_col_norm: [1,2,3,4,5,6]}
    test_df = pd.DataFrame(sample_data)
    summary = calculate_team_status_summary(test_df)
    assert not summary.empty and summary.shape==(5,3) and list(summary.columns)==[team_col_norm,status_col_norm,total_incidents_col_norm]
    assert summary[(summary[team_col_norm]=='Alpha')&(summary[status_col_norm]=='Open')][total_incidents_col_norm].iloc[0]==2
    print("test_calculate_team_status_summary PASSED")

def test_calculate_srs_created_per_week():
    created_on_norm = 'createdon'; status_norm = 'status'; year_week_norm = 'year-week'; week_display_norm = 'weekdisplay'; status_category_norm = 'statuscategory'; number_of_srs_norm = 'numberofsrs'
    data1 = {created_on_norm: pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-08', '2023-01-08'])}
    df1 = pd.DataFrame(data1); result1 = calculate_srs_created_per_week(df1)
    expected1_data = {year_week_norm:['2022-W52','2023-W01'], week_display_norm:[_get_week_display_str('2022-W52'), _get_week_display_str('2023-W01')], number_of_srs_norm:[1,3]}
    expected1 = pd.DataFrame(expected1_data); pd.testing.assert_frame_equal(result1, expected1)
    print("test_calculate_srs_created_per_week PASSED")

def test_calculate_srs_created_and_closed_per_week():
    created_on_norm = 'createdon'; last_mod_dt_norm = 'lastmoddatetime'; status_norm = 'status'; year_week_norm = 'year-week'; week_display_norm = 'WeekDisplay'; count_norm = 'Count'; category_norm = 'Category'
    data1 = {created_on_norm: pd.to_datetime(['2023-01-01','2023-01-02','2023-01-08','2023-01-09']), last_mod_dt_norm: pd.to_datetime([None,'2023-01-03','2023-01-10','2023-01-10']), status_norm: ['Open','Closed','Cancelled','Rejected by PS']}
    df1 = pd.DataFrame(data1); result1 = calculate_srs_created_and_closed_per_week(df1)
    expected1_data = [{year_week_norm:'2022-W52', week_display_norm:_get_week_display_str('2022-W52'), count_norm:1, category_norm:'Created'}, {year_week_norm:'2023-W01', week_display_norm:_get_week_display_str('2023-W01'), count_norm:2, category_norm:'Created'}, {year_week_norm:'2023-W01', week_display_norm:_get_week_display_str('2023-W01'), count_norm:1, category_norm:'Closed'}, {year_week_norm:'2023-W02', week_display_norm:_get_week_display_str('2023-W02'), count_norm:1, category_norm:'Created'}, {year_week_norm:'2023-W02', week_display_norm:_get_week_display_str('2023-W02'), count_norm:2, category_norm:'Closed'}]
    expected1 = pd.DataFrame(expected1_data).sort_values(by=[year_week_norm, category_norm]).reset_index(drop=True)
    pd.testing.assert_frame_equal(result1, expected1, check_like=True)
    print("test_calculate_srs_created_and_closed_per_week PASSED")

if __name__ == '__main__':
    test_calculate_team_status_summary()
    test_case_count_calculation_and_filtering()
    test_calculate_srs_created_per_week()
    test_calculate_srs_created_and_closed_per_week()
    print("All utils.py tests passed successfully when run directly.")
