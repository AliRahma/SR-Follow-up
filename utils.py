import pandas as pd
import io
from datetime import datetime

# Function to classify and extract ticket info
def classify_and_extract(note, ticket_regex, sr_min_range, sr_max_range):
    if not isinstance(note, str):
        return "Not Triaged", None, None

    note_lower = note.lower()
    try:
        import re # Ensure re is imported if not globally available
        match = re.search(ticket_regex, note_lower, re.IGNORECASE | re.DOTALL)
    except Exception as e: # Catch issues with regex compilation
        # st.error(f"Regex error: {e}") # Would need st here, better to log
        print(f"Regex error: {e}")
        return "Regex Error", None, None

    if match:
        try:
            ticket_num_str = match.group(2) # Assuming group 2 is the number
            if ticket_num_str:
                ticket_num = int(ticket_num_str)
                ticket_type = "SR" if sr_min_range <= ticket_num <= sr_max_range else "Incident"
                return "Pending SR/Incident", ticket_num, ticket_type
        except (IndexError, ValueError):
            # If group 2 doesn't exist or not a number, it's not a valid ticket format
            return "Not Triaged", None, None

    return "Not Triaged", None, None

# Function to calculate case age in days
def calculate_age(start_date):
    if pd.isna(start_date) or not isinstance(start_date, datetime):
        return None
    return (datetime.now() - start_date).days

# Function to determine if a note was created today
def is_created_today(date_value):
    if pd.isna(date_value):
        return False
    today = datetime.now().date()
    try:
        note_date = date_value.date() if isinstance(date_value, datetime) else pd.to_datetime(date_value).date()
    except: # Handle cases where date_value might not be directly convertible
        return False
    return note_date == today

# Function to create downloadable Excel
def generate_excel_download(data, sheet_name='Results'):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name=sheet_name)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1976d2',
            'color': 'white',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center'
        })

        for col_num, value in enumerate(data.columns.values):
            worksheet.write(0, col_num, value, header_format)

        for i, col in enumerate(data.columns):
            column_width = max(data[col].astype(str).apply(len).max(), len(str(col))) + 2
            if column_width > 50: # Cap max width
                column_width = 50
            worksheet.set_column(i, i, column_width)
    output.seek(0)
    return output

# Function to create downloadable CSV
def generate_csv_download(data):
    output = io.StringIO()
    data.to_csv(output, index=False)
    output.seek(0)
    return output.getvalue()

def time_since_breach(breach_date, resolution_date=None):
    if pd.isna(breach_date):
        return None

    breach_dt = pd.to_datetime(breach_date, errors='coerce')
    if pd.isna(breach_dt):
        return None

    if resolution_date and not pd.isna(resolution_date):
        end_dt = pd.to_datetime(resolution_date, errors='coerce')
        if pd.isna(end_dt):
            return "Invalid Resolution Date"
    else:
        end_dt = datetime.now()

    delta = end_dt - breach_dt
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days < 0: # Breach hasn't happened yet or resolution before breach (data issue)
        return "Breach Not Reached / Resolved Before"

    return f"{days}d {hours}h {minutes}m"

def time_to_resolve_after_breach(breach_date, resolution_date):
    if pd.isna(breach_date) or pd.isna(resolution_date):
        return None

    breach_dt = pd.to_datetime(breach_date, errors='coerce')
    res_dt = pd.to_datetime(resolution_date, errors='coerce')

    if pd.isna(breach_dt) or pd.isna(res_dt) or res_dt < breach_dt:
        return None # Or "Resolved before breach / Invalid dates"

    delta = res_dt - breach_dt
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

def calculate_team_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the summary of incidents grouped by Team and Status.

    Args:
        df: Input DataFrame, expected to have 'Team' and 'Status' columns.

    Returns:
        A DataFrame with columns ['Team', 'Status', 'Total Incidents']
        summarizing the count of incidents. Returns an empty DataFrame
        with these columns if 'Team' or 'Status' is missing in the input.
    """
    if 'Team' in df.columns and 'Status' in df.columns:
        summary_df = df.groupby(['Team', 'Status']).size().reset_index(name='Total Incidents')
    else:
        summary_df = pd.DataFrame(columns=['Team', 'Status', 'Total Incidents'])
    return summary_df

def test_case_count_calculation_and_filtering():
    """Tests for Case Count calculation and linked cases filtering logic."""
    print("Running test_case_count_calculation_and_filtering...")

    # 1. Test Case Count Calculation
    print("  Testing Case Count Calculation...")
    case_count_data = {
        'Ticket Number': ['INC100', 'SR200', 'INC100', 'SR300', 'INC100', 'SR200'],
        'Type': ['Incident', 'SR', 'Incident', 'SR', 'Incident', 'SR'],
        'OtherData': [1, 2, 3, 4, 5, 6]
    }
    df_case_count_test = pd.DataFrame(case_count_data)
    df_case_count_test['Case Count'] = df_case_count_test.groupby(['Ticket Number', 'Type'])['Ticket Number'].transform('size')

    expected_case_counts = pd.Series([3, 2, 3, 1, 3, 2], name='Case Count')
    pd.testing.assert_series_equal(df_case_count_test['Case Count'], expected_case_counts, check_dtype=False)
    print("  Case Count Calculation Test Passed.")

    # 2. Test Filtering Logic for Linked Cases
    print("  Testing Linked Cases Filtering Logic...")
    filtering_data = {
        'Ticket Number': ['INC001', 'SR002', 'INC003', 'SR004', 'INC001', None, 'SR005', 'SR002'],
        'Type': ['Incident', 'SR', 'Incident', 'SR', 'Incident', 'SR', 'SR', 'SR'],
        'Case Count': [3, 2, 1, 1, 3, 2, 4, 2],
        'Details': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    }
    df_filtering_test = pd.DataFrame(filtering_data)
    min_linked_cases = 2

    # Apply filtering as done in app.py
    linked_cases_df = df_filtering_test[
        (df_filtering_test['Case Count'] >= min_linked_cases) &
        (df_filtering_test['Ticket Number'].notna())
    ]

    # Create summary as done in app.py
    if not linked_cases_df.empty:
        linked_summary_df = linked_cases_df[['Ticket Number', 'Type', 'Case Count']].drop_duplicates().sort_values(
            by='Case Count', ascending=False
        ).reset_index(drop=True)
    else:
        linked_summary_df = pd.DataFrame(columns=['Ticket Number', 'Type', 'Case Count'])

    expected_summary_data = {
        'Ticket Number': ['SR005', 'INC001', 'SR002'],
        'Type': ['SR', 'Incident', 'SR'],
        'Case Count': [4, 3, 2]
    }
    df_expected_summary = pd.DataFrame(expected_summary_data)

    pd.testing.assert_frame_equal(linked_summary_df, df_expected_summary, check_dtype=False)
    print("  Linked Cases Filtering Logic Test Passed.")

    # Test Filtering Logic - Edge case: No items meet criteria
    print("  Testing Linked Cases Filtering Logic (Edge Case: No items)...")
    min_linked_cases_high = 5
    linked_cases_df_edge = df_filtering_test[
        (df_filtering_test['Case Count'] >= min_linked_cases_high) &
        (df_filtering_test['Ticket Number'].notna())
    ]
    if not linked_cases_df_edge.empty:
        linked_summary_df_edge = linked_cases_df_edge[['Ticket Number', 'Type', 'Case Count']].drop_duplicates().sort_values(
            by='Case Count', ascending=False
        ).reset_index(drop=True)
    else:
        linked_summary_df_edge = pd.DataFrame(columns=['Ticket Number', 'Type', 'Case Count'])

    df_expected_empty_summary = pd.DataFrame(columns=['Ticket Number', 'Type', 'Case Count'])
    pd.testing.assert_frame_equal(linked_summary_df_edge, df_expected_empty_summary, check_dtype=False)
    print("  Linked Cases Filtering Logic (Edge Case: No items) Test Passed.")

    print("All test_case_count_calculation_and_filtering tests passed.")

def test_calculate_team_status_summary():
    """Tests for the calculate_team_status_summary function."""
    print("Running test_calculate_team_status_summary...")
    # Test with valid data
    sample_data = {
        'Team': ['Alpha', 'Alpha', 'Bravo', 'Alpha', 'Bravo', 'Charlie'],
        'Status': ['Open', 'Closed', 'Open', 'Open', 'In Progress', 'Open'],
        'ID': [1, 2, 3, 4, 5, 6]
    }
    test_df = pd.DataFrame(sample_data)
    summary = calculate_team_status_summary(test_df)

    assert not summary.empty, "Test Case 1 Failed: Summary should not be empty for valid data."
    assert summary.shape == (5, 3), f"Test Case 1 Failed: Expected shape (5, 3), got {summary.shape}"

    # Check a specific row: Alpha, Open should be 2
    alpha_open_count_series = summary[(summary['Team'] == 'Alpha') & (summary['Status'] == 'Open')]['Total Incidents']
    assert not alpha_open_count_series.empty, "Test Case 1 Failed: 'Alpha' team with 'Open' status not found."
    alpha_open_count = alpha_open_count_series.iloc[0]
    assert alpha_open_count == 2, f"Test Case 1 Failed: Expected Alpha-Open count 2, got {alpha_open_count}"

    # Check another specific row: Bravo, In Progress should be 1
    bravo_in_progress_series = summary[(summary['Team'] == 'Bravo') & (summary['Status'] == 'In Progress')]['Total Incidents']
    assert not bravo_in_progress_series.empty, "Test Case 1 Failed: 'Bravo' team with 'In Progress' status not found."
    bravo_in_progress_count = bravo_in_progress_series.iloc[0]
    assert bravo_in_progress_count == 1, f"Test Case 1 Failed: Expected Bravo-In Progress count 1, got {bravo_in_progress_count}"

    print("Test Case 1 (Valid Data) Passed.")

    # Test with missing columns
    sample_data_missing_cols = {
        'Group': ['A', 'B'],
        'Value': [10, 20]
    }
    test_df_missing = pd.DataFrame(sample_data_missing_cols)
    summary_missing = calculate_team_status_summary(test_df_missing)

    assert summary_missing.empty, "Test Case 2 Failed: Summary should be empty when columns are missing."
    expected_cols = ['Team', 'Status', 'Total Incidents']
    assert list(summary_missing.columns) == expected_cols, \
        f"Test Case 2 Failed: Expected columns {expected_cols}, got {list(summary_missing.columns)}"
    print("Test Case 2 (Missing Columns) Passed.")

    # Test with empty dataframe but correct columns
    empty_df_with_cols = pd.DataFrame(columns=['Team', 'Status', 'ID'])
    summary_empty_df = calculate_team_status_summary(empty_df_with_cols)
    assert summary_empty_df.empty, "Test Case 3 Failed: Summary should be empty for an empty input DataFrame."
    assert list(summary_empty_df.columns) == expected_cols, \
        f"Test Case 3 Failed: Expected columns {expected_cols} for empty input, got {list(summary_empty_df.columns)}"
    print("Test Case 3 (Empty DataFrame with Columns) Passed.")

    print("All test_calculate_team_status_summary tests passed.")

def calculate_srs_created_per_week(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the number of SRs created per week from a DataFrame.

    Args:
        df: DataFrame containing SR data with a 'Created On' column.

    Returns:
        A DataFrame with columns ['Year-Week', 'Number of SRs']
        sorted by 'Year-Week'. Returns an empty DataFrame if 'Created On'
        is missing or data cannot be processed.
    """
    if 'Created On' not in df.columns:
        return pd.DataFrame(columns=['Year-Week', 'Number of SRs'])

    processed_df = df.copy()
    # Convert 'Created On' to datetime, handling potential errors by coercing them to NaT
    processed_df['Created On'] = pd.to_datetime(processed_df['Created On'], errors='coerce')

    # Drop rows where 'Created On' could not be parsed
    processed_df.dropna(subset=['Created On'], inplace=True)

    if processed_df.empty:
        return pd.DataFrame(columns=['Year-Week', 'Number of SRs'])

    # Extract year and week number (ISO week date)
    # %G is ISO year, %V is ISO week number
    processed_df['Year-Week'] = processed_df['Created On'].dt.strftime('%G-W%V')

    # Count SRs per week
    srs_per_week = processed_df.groupby('Year-Week').size().reset_index(name='Number of SRs')

    # Sort by Year-Week to ensure chronological order in the chart
    srs_per_week = srs_per_week.sort_values(by='Year-Week').reset_index(drop=True)

    return srs_per_week

def test_calculate_srs_created_per_week():
    """Tests for the calculate_srs_created_per_week function."""
    print("Running test_calculate_srs_created_per_week...")

    # 1. Basic functionality
    data1 = {'Created On': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-08', '2023-01-08'])}
    df1 = pd.DataFrame(data1)
    result1 = calculate_srs_created_per_week(df1)
    expected1_data = {'Year-Week': ['2022-W52', '2023-W01'], 'Number of SRs': [1, 3]}
    expected1 = pd.DataFrame(expected1_data)
    pd.testing.assert_frame_equal(result1, expected1)
    print("  Test Case 1 (Basic functionality) Passed.")

    # 2. Missing 'Created On' column
    df2 = pd.DataFrame({'SomeOtherColumn': [1, 2]})
    result2 = calculate_srs_created_per_week(df2)
    expected2 = pd.DataFrame(columns=['Year-Week', 'Number of SRs'])
    pd.testing.assert_frame_equal(result2, expected2)
    print("  Test Case 2 (Missing 'Created On' column) Passed.")

    # 3. Dates that cannot be parsed (some valid)
    data3 = {'Created On': [
        pd.Timestamp('2023-01-01'),
        None,
        pd.Timestamp('2023-01-03'),
        'completely invalid date string',
        pd.Timestamp('2023-01-09 10:00:00')
    ]}
    df3 = pd.DataFrame(data3)
    result3 = calculate_srs_created_per_week(df3)
    expected3_data = {'Year-Week': ['2022-W52', '2023-W01', '2023-W02'], 'Number of SRs': [1, 1, 1]}
    expected3 = pd.DataFrame(expected3_data)
    pd.testing.assert_frame_equal(result3, expected3)
    print("  Test Case 3 (Some unparseable dates) Passed.")

    # 4. All dates invalid
    data4 = {'Created On': ['not a date', None, '']}
    df4 = pd.DataFrame(data4)
    result4 = calculate_srs_created_per_week(df4)
    expected4 = pd.DataFrame(columns=['Year-Week', 'Number of SRs'])
    pd.testing.assert_frame_equal(result4, expected4)
    print("  Test Case 4 (All dates invalid) Passed.")

    # 5. Empty input DataFrame
    df5 = pd.DataFrame(columns=['Created On'])
    result5 = calculate_srs_created_per_week(df5)
    expected5 = pd.DataFrame(columns=['Year-Week', 'Number of SRs'])
    pd.testing.assert_frame_equal(result5, expected5)
    print("  Test Case 5 (Empty input DataFrame) Passed.")

    # 6. Correct sorting (weeks not in order in input)
    data6 = {'Created On': pd.to_datetime(['2023-01-15', '2023-01-01', '2023-01-08'])}
    df6 = pd.DataFrame(data6)
    result6 = calculate_srs_created_per_week(df6)
    expected6_data = {'Year-Week': ['2022-W52', '2023-W01', '2023-W02'], 'Number of SRs': [1, 1, 1]}
    expected6 = pd.DataFrame(expected6_data)
    pd.testing.assert_frame_equal(result6, expected6)
    print("  Test Case 6 (Correct sorting) Passed.")

    # 7. Different date/time formats (pandas should handle)
    # Using ISO strings to avoid pd.to_datetime parsing issues in test setup
    data7 = {'Created On': [
        '2024-01-01T00:00:00',  # 2024-W01
        '2025-07-05T07:33:00',  # 2025-W27 (July 5th)
        '2025-07-06T08:00:00'   # 2025-W27 (July 6th)
    ]}
    df7 = pd.DataFrame(data7)
    result7 = calculate_srs_created_per_week(df7)
    expected7_data = {'Year-Week': ['2024-W01', '2025-W27'], 'Number of SRs': [1, 2]}
    expected7 = pd.DataFrame(expected7_data)
    pd.testing.assert_frame_equal(result7, expected7)
    print("  Test Case 7 (Different date formats including user example) Passed.")

    # 8. Year boundary (ISO week)
    data8 = {'Created On': pd.to_datetime(['2023-12-31', '2024-01-01', '2024-12-29', '2024-12-30', '2025-01-01'])}
    df8 = pd.DataFrame(data8)
    result8 = calculate_srs_created_per_week(df8)
    expected8_data = {'Year-Week': ['2023-W52', '2024-W01', '2024-W52', '2025-W01'], 'Number of SRs': [1, 1, 1, 2]}
    expected8 = pd.DataFrame(expected8_data)
    pd.testing.assert_frame_equal(result8, expected8)
    print("  Test Case 8 (Year boundary ISO week) Passed.")

    print("All test_calculate_srs_created_per_week tests passed.")

if __name__ == '__main__':
    test_calculate_team_status_summary()
    test_case_count_calculation_and_filtering()
    test_calculate_srs_created_per_week()
    print("All utils.py tests passed successfully when run directly.")
