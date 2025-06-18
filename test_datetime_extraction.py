import pandas as pd
from datetime import datetime
import re
import os # For os.path.splitext

# Mock for st.error, st.warning, st.cache_data - they are not essential for this test's logic
class MockST:
    def error(self, message):
        print(f"Streamlit Error: {message}")
    def warning(self, message):
        print(f"Streamlit Warning: {message}")
    def cache_data(self, func):
        return func # Return the function undecorated

st = MockST()

# Copied load_data function from app.py (version that returns (df, parsed_dt))
@st.cache_data
def load_data(file):
    if file is None:
        return None, None

    parsed_datetime_str = None
    df = None
    try:
        file_name = file.name
        file_extension = os.path.splitext(file_name)[1].lower()
        match = re.search(r'_(\d{8})_(\d{6})\.', file_name)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            try:
                dt_object = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                parsed_datetime_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass # parsed_datetime_str remains None

        # Simplified pd.read_excel for mock files, assuming .xlsx
        # In a real scenario, file object would be an UploadedFile instance
        if file_extension == '.xlsx':
            # Mocking DataFrame creation for test purposes
            # If file.content is bytes, use io.BytesIO(file.content)
            # For this test, we'll assume file objects have a 'content_df' attribute for simplicity
            if file.content_df is _SENTINEL: # content_df not provided by test case for this MockUploadedFile
                df = pd.DataFrame({'A': [1]}) # Default success with placeholder
            else: # content_df was provided by test case
                df = file.content_df # This will be None if test case passed content_df=None, or the actual df
        elif file_extension == '.xls': # Basic handling for .xls if needed by test cases
            if file.content_df is _SENTINEL:
                df = pd.DataFrame({'A': [1]})
            else:
                df = file.content_df
        else:
            st.error(f"Unsupported file type: {file_extension}.")
            return None, parsed_datetime_str
        return df, parsed_datetime_str
    except Exception as e:
        st.error(f"Error loading file '{file.name}': {e}")
        return None, parsed_datetime_str

_SENTINEL = object()
class MockUploadedFile:
    def __init__(self, name, content_df=_SENTINEL):
        self.name = name
        self.content_df = content_df

# Test scenarios
def run_all_tests():
    test_results = []
    all_tests_passed = True

    # Helper to run a scenario
    def run_scenario(scenario_name, files, expected_datetime):
        nonlocal all_tests_passed
        session_state = {'report_datetime': None} # Simulate st.session_state

        # Main file
        if files.get('main'):
            df, parsed_dt = load_data(files['main'])
            if df is not None and parsed_dt: # Key: df must be successfully loaded
                session_state['report_datetime'] = parsed_dt

        # SR file
        if files.get('sr'):
            sr_df, parsed_dt_sr = load_data(files['sr'])
            if sr_df is not None and session_state['report_datetime'] is None and parsed_dt_sr:
                session_state['report_datetime'] = parsed_dt_sr

        # Incident file
        if files.get('incident'):
            incident_df, parsed_dt_incident = load_data(files['incident'])
            if incident_df is not None and session_state['report_datetime'] is None and parsed_dt_incident:
                session_state['report_datetime'] = parsed_dt_incident

        actual_datetime = session_state['report_datetime']
        if actual_datetime == expected_datetime:
            test_results.append(f"PASSED: {scenario_name} - Expected {expected_datetime}, Got {actual_datetime}")
        else:
            test_results.append(f"FAILED: {scenario_name} - Expected {expected_datetime}, Got {actual_datetime}")
            all_tests_passed = False

    # Scenario 1: Main file only (with DT)
    run_scenario("Main only (with DT)",
                 {'main': MockUploadedFile('MainFile_20230101_120000.xlsx')},
                 '2023-01-01 12:00:00')

    # Scenario 2: Main file only (no DT)
    run_scenario("Main only (no DT)",
                 {'main': MockUploadedFile('MainFile_NoDateTime.xlsx')},
                 None)

    # Scenario 3: Main (with DT), SR (no DT)
    run_scenario("Main (DT), SR (no DT)",
                 {'main': MockUploadedFile('Main_20230101_120000.xlsx'), 'sr': MockUploadedFile('SR_NoDT.xlsx')},
                 '2023-01-01 12:00:00')

    # Scenario 4: Main (no DT), SR (with DT)
    run_scenario("Main (no DT), SR (DT)",
                 {'main': MockUploadedFile('Main_NoDT.xlsx'), 'sr': MockUploadedFile('SR_20230202_140000.xlsx')},
                 '2023-02-02 14:00:00')

    # Scenario 5: Main (no DT), SR (no DT), Incident (with DT)
    run_scenario("Main (no DT), SR (no DT), Inc (DT)",
                 {'main': MockUploadedFile('Main_NoDT.xlsx'), 'sr': MockUploadedFile('SR_NoDT.xlsx'), 'incident': MockUploadedFile('Inc_20230303_160000.xlsx')},
                 '2023-03-03 16:00:00')

    # Scenario 6: Main (with DT), SR (with different DT)
    run_scenario("Main (DT), SR (diff DT)",
                 {'main': MockUploadedFile('Main_20230101_120000.xlsx'), 'sr': MockUploadedFile('SR_20230202_140000.xlsx')},
                 '2023-01-01 12:00:00')

    # Scenario 7: Main (no DT), SR (with DT), Incident (with different DT)
    run_scenario("Main (no DT), SR (DT), Inc (diff DT)",
                 {'main': MockUploadedFile('Main_NoDT.xlsx'), 'sr': MockUploadedFile('SR_20230202_140000.xlsx'), 'incident': MockUploadedFile('Inc_20230303_160000.xlsx')},
                 '2023-02-02 14:00:00')

    # Scenario 8: No files with parsable DT
    run_scenario("All files (no DT)",
                 {'main': MockUploadedFile('Main_NoDT.xlsx'), 'sr': MockUploadedFile('SR_NoDT.xlsx'), 'incident': MockUploadedFile('Inc_NoDT.xlsx')},
                 None)

    # Scenario 9: Main file fails to load (df is None), but filename has DT
    # load_data returns (None, parsed_dt). Sidebar logic: if df is not None...
    # So, if df is None, its parsed_dt should not be used.
    run_scenario("Main fails load (has DT), SR (has DT)",
                 {'main': MockUploadedFile('Main_20230101_120000.xlsx', content_df=None), # Simulate df load failure
                  'sr': MockUploadedFile('SR_20230202_140000.xlsx')},
                 '2023-02-02 14:00:00')

    print("\n--- Test Summary ---")
    for res in test_results:
        print(res)

    if all_tests_passed:
        print("\nAll datetime extraction tests PASSED.")
    else:
        print("\nSome datetime extraction tests FAILED.")

if __name__ == '__main__':
    run_all_tests()
