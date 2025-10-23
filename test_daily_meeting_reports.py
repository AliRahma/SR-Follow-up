import pandas as pd
from datetime import datetime
from utils import calculate_daily_backlog_growth, calculate_breached_incidents_by_month, calculate_incident_status_summary_with_totals

def test_calculate_daily_backlog_growth():
    """Tests for the calculate_daily_backlog_growth function."""
    print("Running test_calculate_daily_backlog_growth...")
    data = {
        'Created On': [datetime(2023, 1, 1), datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'Source': ['Email', 'Phone', 'Email']
    }
    df = pd.DataFrame(data)

    # Test for a date with data
    result = calculate_daily_backlog_growth(df, datetime(2023, 1, 1).date())
    expected = pd.DataFrame({'Source': ['Email', 'Phone'], 'Count': [1, 1]})
    pd.testing.assert_frame_equal(result, expected)
    print("  Test Case 1 (Date with data) Passed.")

    # Test for a date with no data
    result = calculate_daily_backlog_growth(df, datetime(2023, 1, 3).date())
    expected = pd.DataFrame(columns=['Source', 'Count'])
    pd.testing.assert_frame_equal(result, expected, check_dtype=False)
    print("  Test Case 2 (Date with no data) Passed.")

    # Test with missing columns
    result = calculate_daily_backlog_growth(pd.DataFrame(), datetime(2023, 1, 1).date())
    pd.testing.assert_frame_equal(result, expected, check_dtype=False)
    print("  Test Case 3 (Missing columns) Passed.")

def test_calculate_breached_incidents_by_month():
    """Tests for the calculate_breached_incidents_by_month function."""
    print("Running test_calculate_breached_incidents_by_month...")
    data = {
        'Breach Date': [datetime(2023, 1, 15), datetime(2023, 1, 20), datetime(2023, 2, 10)],
        'Status': ['Open', 'In Progress', 'Closed'],
        'Breach Passed': [True, 'yes', True]
    }
    df = pd.DataFrame(data)

    result = calculate_breached_incidents_by_month(df)
    expected = pd.DataFrame({'Month': ['2023-01'], 'Count': [2]})
    pd.testing.assert_frame_equal(result, expected)
    print("  Test Case 1 (Basic functionality) Passed.")

    # Test with no open breached incidents
    data['Status'] = ['Closed', 'Resolved', 'Closed']
    df = pd.DataFrame(data)
    result = calculate_breached_incidents_by_month(df)
    expected = pd.DataFrame(columns=['Month', 'Count'])
    pd.testing.assert_frame_equal(result, expected, check_dtype=False)
    print("  Test Case 2 (No open breached incidents) Passed.")

def test_calculate_incident_status_summary_with_totals():
    """Tests for the calculate_incident_status_summary_with_totals function."""
    print("Running test_calculate_incident_status_summary_with_totals...")
    data = {
        'Team': ['Team A', 'Team A', 'Team B'],
        'Status': ['Open', 'Closed', 'Open']
    }
    df = pd.DataFrame(data)

    result = calculate_incident_status_summary_with_totals(df)
    expected_data = {
        'Status': ['Closed', 'Open', 'Total'],
        'Team A': [1, 1, 2],
        'Team B': [0, 1, 1],
        'Total': [1, 2, 3]
    }
    expected = pd.DataFrame(expected_data).set_index('Status')
    expected.columns.name = 'Team'
    # The pivot table will have columns as Status and index as Team, let's fix the test
    expected = pd.DataFrame(
        {'Closed': {'Team A': 1, 'Team B': 0, 'Total': 1},
         'Open': {'Team A': 1, 'Team B': 1, 'Total': 2},
         'Total': {'Team A': 2, 'Team B': 1, 'Total': 3}}
    )
    expected.index.name = 'Team'
    expected.columns.name = 'Status'

    pd.testing.assert_frame_equal(result, expected, check_like=True)
    print("  Test Case 1 (Basic functionality) Passed.")

if __name__ == '__main__':
    test_calculate_daily_backlog_growth()
    test_calculate_breached_incidents_by_month()
    test_calculate_incident_status_summary_with_totals()
