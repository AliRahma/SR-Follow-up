# Intellipen SmartQ Test

This is a Streamlit application designed to analyze Service Requests (SRs) and Incidents efficiently.

## Prerequisites

Before you begin, ensure you have the following installed on your local machine:
- **Python 3.8 or higher**: You can download it from [python.org](https://www.python.org/).
- **pip**: The Python package installer, which usually comes with Python.

## Local Setup Instructions

Follow these steps to host and run the application locally:

### 1. Clone or Download the Repository
If you haven't already, clone this repository or download the source code to a folder on your machine.

### 2. Create a Virtual Environment (Recommended)
It is highly recommended to use a virtual environment to keep your project's dependencies separate from your global Python installation.

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Once the virtual environment is activated, install the required libraries using the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Run the Application
Start the Streamlit server by running the following command in your terminal:

```bash
streamlit run app.py
```

After running this command, the application will start, and a link (usually `http://localhost:8501`) will be displayed in your terminal. Open this link in your web browser to access the application.

## Usage Guide
1. **Upload Main Excel File**: Use the sidebar to upload your primary `.xlsx` data file.
2. **Optional Uploads**: You can also upload SR Status and Incident Report Excel files for more detailed analysis.
3. **Explore Tabs**: Use the navigation menu at the top to switch between different reports and analyses (e.g., Analysis, SLA Breach, Incident Overview).

## Troubleshooting
- **Missing Columns**: Ensure your Excel files contain the expected headers (e.g., 'Case Id', 'Current User Id', 'Status').
- **Pyarrow Errors**: If you encounter errors related to `pyarrow`, ensure your data types are consistent within Excel columns.
- **Port Busy**: If port 8501 is already in use, Streamlit will automatically try to use the next available port (e.g., 8502).

---
*Developed by Ali Babiker | © June 2025*
