import pandas as pd
from datetime import datetime
from utils import calculate_daily_backlog_growth, calculate_breached_incidents_by_month, calculate_incident_status_summary_with_totals

def test_calculate_daily_backlog_growth():
    """Tests for the calculate_daily_backlog_growth function."""
    print("Running test_calculate_daily_backlog_growth...")
    data = {
        'Created On': [datetime(2023, 1, 1), datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'Source': ['Email', 'Phone', 'Email'],
        'Status': ['Open', 'Open', 'New'],
        'Incident': ['INC001', 'INC002', 'INC003']
    }
    df = pd.DataFrame(data)

    # Test for a date with data
    result = calculate_daily_backlog_growth(df, datetime(2023, 1, 1).date())
    expected_data = {'Open': [1, 1, 2], 'Total': [1, 1, 2]}
    expected = pd.DataFrame(expected_data, index=['Email', 'Phone', 'Total'])
    expected.index.name = 'Source'
    expected.columns.name = 'Status'
    pd.testing.assert_frame_equal(result, expected)
    print("  Test Case 1 (Date with data) Passed.")

    # Test for a date with no data
    result = calculate_daily_backlog_growth(df, datetime(2023, 1, 3).date())
    expected = pd.DataFrame()
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
    expected = pd.DataFrame({'Month': ['2023-01', 'Total'], 'Count': [2, 2]})
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
        'Team': ['Team A', 'Team A', 'Team B', 'Team C'],
        'Status': ['Open', 'Closed', 'Open', 'Cancelled']
    }
    df = pd.DataFrame(data)

    result = calculate_incident_status_summary_with_totals(df)

    expected_data = {
        'Team A': {'Open': 1, 'Total': 1},
        'Team B': {'Open': 1, 'Total': 1},
        'Total': {'Open': 2, 'Total': 2}
    }
    expected = pd.DataFrame(expected_data)
    expected.index.name = 'Status'
    expected.columns.name = 'Team'

    pd.testing.assert_frame_equal(result, expected, check_like=True)
    print("  Test Case 1 (Basic functionality) Passed.")

if __name__ == '__main__':
    test_calculate_daily_backlog_growth()
    test_calculate_breached_incidents_by_month()
    test_calculate_incident_status_summary_with_totals()
