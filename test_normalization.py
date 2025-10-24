import pandas as pd
import pytest # Using pytest for better test structure if available, otherwise will use basic asserts
from utils import calculate_team_status_summary, calculate_srs_created_and_closed_per_week
# Add other necessary imports from app.py if we were to test data loading directly

# Test the normalization function itself
# def test_normalize_column_name():
#     assert normalize_column_name("First Name") == "first_name"
#     assert normalize_column_name("EMAIL Address") == "email_address"
#     assert normalize_column_name("Column With Spaces") == "column_with_spaces"
#     assert normalize_column_name("Already_Normalized_Column") == "already_normalized_column" # Should remain lowercase
#     assert normalize_column_name("col_with_#$_special-chars") == "col_with_special_chars"
#     assert normalize_column_name("  leading and trailing spaces  ") == "leading_and_trailing_spaces"
#     assert normalize_column_name("__leading_underscores") == "leading_underscores"
#     assert normalize_column_name("trailing_underscores__") == "trailing_underscores"
#     assert normalize_column_name("column___multiple___underscores") == "column_multiple_underscores"
#     assert normalize_column_name("اسم العميل") == "اسم_العميل" # Arabic characters with space
#     assert normalize_column_name("ID") == "id"
#     assert normalize_column_name(123) == "123" # Non-string input
#     assert normalize_column_name(None) == "none" # Non-string input (current behavior converts to str)
#     assert normalize_column_name("") == "" # Empty string
#     assert normalize_column_name("_") == "" # Single underscore becoming empty
#     assert normalize_column_name(" _ ") == "" # Space underscore space becoming empty


# Placeholder for testing data loading and initial normalization (would typically involve app.py's load_data)
# This would be more of an integration test. For now, conceptual.
def test_data_loading_normalizes_columns():
    # Conceptual:
    # 1. Create a dummy Excel file with non-normalized column names.
    #    e.g., "First Name", "Last Update Time", "SR Number"
    # 2. Load it using a simplified version or by calling app.load_data if possible in test context.
    # 3. Assert that the loaded DataFrame has columns: "first_name", "last_update_time", "sr_number"
    pass # Requires file I/O and potentially Streamlit context or refactoring load_data

# Test utility functions that now expect normalized column names
def test_calculate_team_status_summary_with_normalized_names():
    # calculate_team_status_summary expects 'Team' and 'Status'
    team_col_norm = 'Team'
    status_col_norm = 'Status'

    sample_data = {
        team_col_norm: ['Alpha', 'Alpha', 'Bravo', 'Alpha', 'Bravo', 'Charlie'],
        status_col_norm: ['Open', 'Closed', 'Open', 'Open', 'In Progress', 'Open'],
        'ID_col': [1, 2, 3, 4, 5, 6] # Another column
    }
    test_df = pd.DataFrame(sample_data)
    summary = calculate_team_status_summary(test_df)

    assert not summary.empty
    # The output columns of calculate_team_status_summary are 'Team', 'Status', 'Total Incidents' (not normalized)
    assert 'Team' in summary.columns
    assert 'Status' in summary.columns
    assert 'Total Incidents' in summary.columns
    assert summary[(summary['Team'] == 'Alpha') & (summary['Status'] == 'Open')]['Total Incidents'].iloc[0] == 2

def test_calculate_srs_created_and_closed_per_week_with_normalized_names():
    created_on_norm = "Created On"
    last_mod_dt_norm = "LastModDateTime"
    status_norm = "Status"

    data = {
        created_on_norm: pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-08']),
        last_mod_dt_norm: pd.to_datetime([None, '2023-01-03', '2023-01-10']),
        status_norm: ['Open', 'Closed', 'Cancelled']
    }
    df = pd.DataFrame(data)
    result = calculate_srs_created_and_closed_per_week(df)
    assert not result.empty
    assert 'Year-Week' in result.columns
    assert 'WeekDisplay' in result.columns
    assert 'Count' in result.columns
    assert 'Category' in result.columns
    # Add more specific assertions based on expected output for these dates/statuses

# Manual Testing Checklist (Conceptual - to be performed by user or through UI automation if available)
# - Upload Excel files with various column name styles:
#   - All uppercase
#   - All lowercase
#   - Mixed case
#   - Spaces between words
#   - Underscores between words
#   - Special characters (e.g., '#', '-', '/') in column names
#   - Leading/trailing spaces in column names
#   - Column names in different languages (e.g., Arabic)
# - Verify for each tab:
#   - Data displays correctly in tables.
#   - Filters work as expected (user selection, date ranges, status dropdowns, etc.).
#   - Summaries and counts are accurate.
#   - Charts are generated correctly.
#   - Note viewer displays the correct information.
#   - Downloaded Excel files contain the expected data with reasonable column headers (currently exported with normalized names).
# - Specific checks for Incident Overview:
#   - "Customer" column from input is correctly renamed to "Creator" and used in filters/display.
# - Specific checks for SR Overview:
#   - Weekly created/closed charts are correct.
#   - Filterable SR data and Closed SRs tables work with date/week filters.

if __name__ == "__main__":
    # Basic test execution without pytest, for simplicity if pytest is not in environment
    print("Running normalization tests...")
    # try:
    #     test_normalize_column_name()
    #     print("test_normalize_column_name PASSED")
    # except AssertionError as e:
    #     print(f"test_normalize_column_name FAILED: {e}")

    # Conceptual tests are not run here directly
    print("Conceptual test_data_loading_normalizes_columns (manual check needed or integration test)")

    # try:
    #     test_calculate_team_status_summary_with_normalized_names()
    #     print("test_calculate_team_status_summary_with_normalized_names PASSED")
    # except AssertionError as e:
    #     print(f"test_calculate_team_status_summary_with_normalized_names FAILED: {e}")
    # except Exception as e:
    #     print(f"test_calculate_team_status_summary_with_normalized_names ERRORED: {e}")

    # try:
    #     test_calculate_srs_created_and_closed_per_week_with_normalized_names()
    #     print("test_calculate_srs_created_and_closed_per_week_with_normalized_names PASSED")
    # except AssertionError as e:
    #     print(f"test_calculate_srs_created_and_closed_per_week_with_normalized_names FAILED: {e}")
    # except Exception as e:
    #     print(f"test_calculate_srs_created_and_closed_per_week_with_normalized_names ERRORED: {e}")

    print("\nMANUAL TESTING IS CRITICAL FOR UI AND END-TO-END FUNCTIONALITY.")
