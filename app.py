import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import os
import hmac
import hashlib
from dotenv import load_dotenv
from analysis_engine import ExamAnalyzer
from report_generator import ReportGenerator
from data_validator import DataValidator
from dashboard_component import render_dashboard

load_dotenv()

APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")


def _generate_auth_token() -> str:
    """Generate deterministic auth token from configured credentials."""
    payload = f"{APP_USERNAME}:{APP_PASSWORD}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _get_query_auth_token() -> str:
    """Read auth token from query params safely."""
    token = st.query_params.get("auth", "")
    if isinstance(token, list):
        return token[0] if token else ""
    return token or ""

def normalize_column_name(col_name: str) -> str:
    """Normalize column name for flexible matching"""
    return col_name.lower().strip().replace(' ', '_').replace('-', '_')

def matches_identifier(col_name: str) -> bool:
    """Check if column matches any identifier column"""
    normalized = normalize_column_name(col_name)
    identifier_patterns = [
        'student_id', 'studentid', 'student id',
        'student_name', 'studentname', 'student name',
        'reg_no', 'regno', 'reg no', 'registration_no', 'registrationno',
        'roll_no', 'rollno', 'roll no', 'roll_number', 'rollnumber',
        'total', 'grand_total', 'grandtotal', 'sum',
        'average', 'avg', 'mean',
        'percentage', 'percent', '%'
    ]
    return normalized in identifier_patterns

# --- Professional CSS Theme ---
st.markdown('''
    <style>
    /* Global Styles */
    * {
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #2f2f2f;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    
    [data-testid="stSidebar"] {
        background: #2f2f2f;
        box-shadow: 2px 0 12px rgba(0, 0, 0, 0.4);
    }

    [data-testid="stSidebar"] {
        color: #e5e7eb !important;
    }

    [data-testid="stSidebar"] section {
        color: #e5e7eb !important;
    }

    [data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }

    [data-testid="stSidebar"] div {
        color: #e5e7eb !important;
    }

    [data-testid="stSidebar"] p {
        color: #cbd5e1 !important;
        font-size: 0.9rem;
    }
    
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #ffffff !important;
        border-bottom: 3px solid #ffffff;
        padding-bottom: 0.75rem;
        margin-top: 1.5rem;
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    [data-testid="stSidebar"] h2 span,
    [data-testid="stSidebar"] h3 span,
    [data-testid="stSidebar"] h4 span {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] h2 *,
    [data-testid="stSidebar"] h3 *,
    [data-testid="stSidebar"] h4 * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .css-10trblm {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .st-emotion-cache-10trblm {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stHeading"] {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 0.5rem !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #261CC1 0%, #261CC1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Main Content */
    .main {
        background-color: #2f2f2f;
        color: #e5e7eb;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #1e3a8a;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
        padding-bottom: 0.25rem;
        border-bottom: none;
    }

    .app-subtitle {
        color: #cbd5e1;
        font-size: 1rem;
        margin-top: -0.3rem;
        margin-bottom: 1.2rem;
    }

    .login-wrapper {
        max-width: 980px;
        margin: 2.2rem auto 0 auto;
    }

    .login-title {
        color: #ffffff;
        font-size: 1.65rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        text-align: left;
    }

    .login-subtitle {
        color: #cbd5e1;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }

    .login-panel {
        background: linear-gradient(145deg, #3b3b3b 0%, #2f2f2f 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 4px solid #261CC1;
        border-radius: 0.9rem;
        padding: 1.4rem;
        min-height: 260px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.30);
    }

    .login-panel h4 {
        color: #ffffff;
        margin-bottom: 0.8rem;
    }

    .login-panel ul {
        padding-left: 1.1rem;
        margin: 0;
    }

    .login-panel li {
        color: #dbe4f0;
        margin-bottom: 0.45rem;
        line-height: 1.4;
    }

    .login-card {
        background: linear-gradient(135deg, #3a3a3a 0%, #2f2f2f 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-top: 3px solid #261CC1;
        border-radius: 0.9rem;
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }

    .login-card-title {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    .login-note {
        color: #cbd5e1;
        font-size: 0.9rem;
        margin-top: 0.6rem;
        text-align: left;
    }

    .login-form-shift {
        margin-top: -10px;
    }
    
    /* Section Banners */
    .section-banner {
        background: linear-gradient(135deg, #261CC1 0%, #261CC1 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        margin-top: 2rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        border-left: 4px solid #261CC1;
        letter-spacing: 0.3px;
    }
    
    /* Metrics */
    .stMetric {
        background: transparent;
        padding: 1.5rem 1.5rem;
        border-radius: 0;
        border: none;
        border-left: 4px solid #261CC1;
        border-bottom: 1px solid #e5e7eb;
        box-shadow: none;
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        border-left-color: #261CC1;
        background: rgba(37, 99, 235, 0.02);
        border-bottom-color: #261CC1;
    }
    
    .stMetric label {
        color: #cbd5e1 !important;
        font-weight: 500;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stMetric span {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 1.75rem;
    }
    
    /* Data Frames */
    .stDataFrame {
        border: none;
        border-top: 3px solid #3a3a3a;
        border-radius: 0;
        overflow: hidden;
        box-shadow: none;
    }

    .stDataFrame thead tr th {
        background: #3a3a3a !important;
        color: #e5e7eb !important;
        font-weight: 600;
        padding: 1rem !important;
        border-color: #3a3a3a !important;
        text-align: left;
        border-bottom: 2px solid #3a3a3a;
    }

    .stDataFrame tbody tr {
        border-bottom: 1px solid rgba(255,255,255,0.06);
        background-color: #2f2f2f !important;
    }

    .stDataFrame tbody tr:hover {
        background-color: #3a3a3a !important;
        color: #e5e7eb !important;
    }

    .stDataFrame tbody tr td {
        padding: 0.75rem 1rem !important;
        color: #e5e7eb !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #261CC1 0%, #261CC1 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
    }
    
    /* Sidebar Header */
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        padding-bottom: 0.75rem;
    }
    
    /* Input Fields */
    .stSlider, .stTextInput, .stSelectbox, .stFileUploader {
        background: #3a3a3a;
        border-radius: 0.5rem;
    }
    
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stFileUploader {
        background: #3a3a3a !important;
    }
    
    [data-testid="stSidebar"] .stSlider input,
    [data-testid="stSidebar"] .stSelectbox input,
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #2f2f2f !important;
        color: #e5e7eb !important;
        border-radius: 1.0rem !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox select {
        background-color: #2f2f2f !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 1.0rem !important;
    }

    /* Highlight the sidebar slider label (e.g. "Default Pass Percentage") */
    [data-testid="stSidebar"] .stSlider label {
        color: #e5e7eb !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        background: #3a3a3a !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 0.35rem !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        display: block !important;
        margin-bottom: 0.25rem !important;
    }

    /* Highlight the sidebar selectbox label (e.g. "Decimal Places") */
    [data-testid="stSidebar"] .stSelectbox label {
        color: #e5e7eb !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        background: #3a3a3a !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 0.35rem !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        display: block !important;
        margin-bottom: 5px !important;
    }

    /* Make slider value text lighter for contrast */
    [data-testid="stSidebar"] .stSlider .stSlider > div > div {
        color: #e5e7eb !important;
    }

    /* File uploader (sidebar) - emphasize label and make more visible */
    [data-testid="stSidebar"] .stFileUploader,
    [data-testid="stSidebar"] .stFileUploader label,
    [data-testid="stSidebar"] .stFileUploader div[role="button"] {
        color: #ffffff !important;
        background: rgba(255,255,255,0.06) !important;
        padding: 0.55rem 0.75rem !important;
        border-radius: 0.5rem !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        display: block !important;
        text-align: left !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stSidebar"] .stFileUploader label span {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] .stFileUploader p,
    [data-testid="stSidebar"] .stFileUploader small {
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.85rem !important;
        margin-top: 0.15rem !important;
        display: block !important;
    }

    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #261CC1, transparent);
        margin: 2rem 0;
    }
    
    /* Text content */
    p {
        color: #4b5563;
        line-height: 1.6;
    }
    
    /* Subheader styling */
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stFileUploader label {
        color: white !important;
        font-weight: 600;
    }
    
    /* Alert and message styling */
    .stAlert {
        background-color: #3a3a3a !important;
        color: #e5e7eb !important;
        border: 1px solid #4a4a4a !important;
        border-radius: 0.5rem !important;
    }
    
    [data-testid="stAlert"] {
        background-color: #3a3a3a !important;
        color: #e5e7eb !important;
    }
    
    /* Force warning/look for various Streamlit versions and DOM shapes */
    div[data-testid="stWarningCallout"],
    div[data-testid="stWarningCallout"] > div,
    [data-testid="stWarningCallout"],
    [data-testid="stWarningCallout"] > div,
    /* generic alert role used by some Streamlit builds */
    div[role="alert"],
    div[role="alert"] > div,
    /* fallback for the stAlert wrapper */
    .stAlert,
    .stAlert > div {
        background: linear-gradient(135deg, #261CC1 0%, #261CC1 100%) !important;
        color: #ffffff !important;
        border-color: #261CC1 !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15) !important;
    }
    
    [data-testid="stErrorCallout"] {
        background-color: #3a3a3a !important;
        border-color: #261CC1 !important;
    }
    
    [data-testid="stInfoCallout"] {
        background-color: #3a3a3a !important;
        border-color: #261CC1 !important;
    }
    
    [data-testid="stSuccessCallout"] {
        background-color: #3a3a3a !important;
        border-color: #48A111 !important;
    }
    
    .stAlert > div {
        color: #ffffff !important;
    }
    
    .stAlert svg {
        color: #e5e7eb !important;
    }
    /* Ensure all text and icons inside warning callouts are white */
    div[data-testid="stWarningCallout"] *,
    [data-testid="stWarningCallout"] *,
    div[role="alert"] *,
    .stAlert *,
    .stAlert > div * {
        color: #ffffff !important;
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    div[data-testid="stWarningCallout"] svg,
    [data-testid="stWarningCallout"] svg,
    div[role="alert"] svg,
    .stAlert svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    
    /* Dashboard card styles */
    .dashboard-card {
        background: linear-gradient(135deg, #3a3a3a 0%, #2f2f2f 100%);
        border: 1px solid rgba(37, 99, 235, 0.3);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        border-color: rgba(37, 99, 235, 0.6);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* KPI styles */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, #3a3a3a 0%, #2f2f2f 100%);
        border-left: 4px solid #261CC1;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #261CC1;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 0.85rem;
        color: #cbd5e1;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    </style>
''', unsafe_allow_html=True)

# Configure page
st.set_page_config(
    page_title="Results Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not APP_USERNAME or not APP_PASSWORD:
    st.error("Authentication is not configured.")
    st.info("Set APP_USERNAME and APP_PASSWORD environment variables, then restart the app.")
    st.stop()

EXPECTED_AUTH_TOKEN = _generate_auth_token()

# Main title
st.markdown('<div class="main-title">📊 Results Analyser</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Comprehensive academic analytics dashboard for exam result insights</div>', unsafe_allow_html=True)
st.markdown("---")

if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

query_token = _get_query_auth_token()
if query_token and hmac.compare_digest(query_token, EXPECTED_AUTH_TOKEN):
    st.session_state.is_authenticated = True

if not st.session_state.is_authenticated:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Welcome to Results Analyser</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Professional examination analytics and reporting platform</div>', unsafe_allow_html=True)

    info_col, form_col = st.columns([1.25, 1])

    with info_col:
        st.markdown('''
            <div class="login-panel">
                <h4>What you can do</h4>
                <ul>
                    <li>Upload and validate examination data instantly</li>
                    <li>Visualize performance trends with interactive charts</li>
                    <li>Generate detailed reports and downloadable exports</li>
                </ul>
            </div>
        ''', unsafe_allow_html=True)

    with form_col:
        st.markdown('<div class="login-form-shift">', unsafe_allow_html=True)
        st.markdown('<div class="login-card-title">🔐 Sign In</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            login_clicked = st.form_submit_button("Login", type="primary", use_container_width=True)

        if login_clicked:
            if username == APP_USERNAME and password == APP_PASSWORD:
                st.session_state.is_authenticated = True
                st.query_params["auth"] = EXPECTED_AUTH_TOKEN
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.markdown('<div class="login-note">Enter your credentials to access the dashboard.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Sidebar for file upload and configuration
with st.sidebar:
    st.header("Configuration")
    if st.button("Logout"):
        st.session_state.is_authenticated = False
        st.session_state.analysis_requested = False
        st.query_params.clear()
        st.rerun()
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel File",
        type=['xlsx', 'xls'],
        help="Upload an Excel file containing student marks data"
    )
    
    # Initialize session state for pass marks
    if 'subject_pass_marks' not in st.session_state:
        st.session_state.subject_pass_marks = {}
    
    # Pass criteria configuration
    st.subheader("Pass Criteria Management")
    
    # Global pass percentage (fallback)
    global_pass_percentage = st.slider(
        "Default Pass Percentage",
        min_value=1,
        max_value=100,
        value=40,
        help="Default percentage for subjects without specific pass marks"
    )
    
    # Subject-specific pass marks
    if uploaded_file is not None:
        # Load data to get subject columns
        try:
            temp_df = pd.read_excel(uploaded_file)
            temp_validator = DataValidator()
            
            # Get subject columns
            required_cols = temp_validator.required_columns
            optional_cols = temp_validator.optional_columns
            subject_columns = [col for col in temp_df.columns if col not in required_cols + optional_cols]
            
            if subject_columns:
                st.write("**Subject-Specific Pass Marks:**")
                
                # Create input fields for each subject
                updated_pass_marks = {}
                for subject in subject_columns:
                    current_value = st.session_state.subject_pass_marks.get(subject, global_pass_percentage)
                    pass_mark = st.number_input(
                        f"{subject}",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(current_value),
                        step=1.0,
                        key=f"pass_mark_{subject}"
                    )
                    updated_pass_marks[subject] = pass_mark
                
                # Update session state
                st.session_state.subject_pass_marks = updated_pass_marks
                
                # Reset to default button
                if st.button("Reset All to Default"):
                    for subject in subject_columns:
                        st.session_state.subject_pass_marks[subject] = global_pass_percentage
                    st.rerun()
        except Exception as e:
            st.write("Upload a file to configure subject-specific pass marks")
    
    # Analysis options
    st.subheader("Analysis Options")
    
    round_decimals = st.selectbox(
        "Decimal Places",
        options=[0, 1, 2, 3],
        index=2,
        help="Number of decimal places for percentage calculations"
    )
    
    # Privacy options
    st.subheader("Privacy Settings")
    anonymize_data = st.checkbox("Anonymize Student Names", value=False)

# Main content area
if uploaded_file is not None:
    try:
        if 'analysis_requested' not in st.session_state:
            st.session_state.analysis_requested = False
        if 'last_uploaded_filename' not in st.session_state:
            st.session_state.last_uploaded_filename = None

        current_uploaded_filename = uploaded_file.name
        if st.session_state.last_uploaded_filename != current_uploaded_filename:
            st.session_state.analysis_requested = False
            st.session_state.last_uploaded_filename = current_uploaded_filename

        if not st.session_state.analysis_requested:
            if st.button("Show Dashboard", type="primary"):
                st.session_state.analysis_requested = True
                st.rerun()
            st.info("Upload is ready. Click 'Show Dashboard' to start analysis.")
            st.stop()

        # Initialize components
        validator = DataValidator(st.session_state.subject_pass_marks)
        analyzer = ExamAnalyzer(global_pass_percentage, st.session_state.subject_pass_marks)
        report_generator = ReportGenerator(round_decimals)
        
        # Load and validate data
        with st.spinner("Loading and validating data..."):
            df = pd.read_excel(uploaded_file)
            
            # Ensure Student_ID and Student_Name columns exist
            if 'Student_ID' not in df.columns:
                df['Student_ID'] = [f"Student_{i+1}" for i in range(len(df))]
            if 'Student_Name' not in df.columns:
                df['Student_Name'] = df['Student_ID']
            
            # Anonymize if requested
            if anonymize_data:
                df['Student_Name'] = [f"Student_{i+1}" for i in range(len(df))]
            
            # Validate data
            validation_result = validator.validate_data(df)
            
            if not validation_result['is_valid']:
                st.error("❌ Data Validation Failed")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                st.stop()
            
            # Show warnings if any
            if validation_result['warnings']:
                st.warning("⚠️ Data Warnings:")
                for warning in validation_result['warnings']:
                    st.warning(f"• {warning}")
        
        # Perform analysis
        with st.spinner("Analyzing examination results..."):
            analysis_results = analyzer.analyze_results(df)
        
        render_dashboard(
            df=df,
            analysis_results=analysis_results,
            round_decimals=round_decimals,
            subject_pass_marks=st.session_state.subject_pass_marks,
            global_pass_percentage=global_pass_percentage,
            matches_identifier=matches_identifier,
            analyzer=analyzer,
            report_generator=report_generator,
        )
    
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please ensure your Excel file has the correct format with student data.")

else:
    # Instructions when no file is uploaded
    st.info("👆 Please upload an Excel file to begin analysis")
    st.subheader("📋 File Format Requirements")
    st.markdown("""
    Your Excel file should contain:
    - **Student_ID** column (optional)
    - **Student_Name** column (optional)
    - **Subject columns** with numerical scores (0-100)
    """)
    
    # Sample format table
    sample_data = {
        'Student_ID': ['S001', 'S002', 'S003'],
        'Student_Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Mathematics': [85, 92, 78],
        'Physics': [78, 88, 85],
        'Chemistry': [92, 85, 90]
    }
    st.dataframe(pd.DataFrame(sample_data), use_container_width=True)
    


# --- Footer ---
st.markdown("""
<hr style='margin-top:2em;margin-bottom:0.5em;border:1px solid #e3f0fc;'>
<div style='text-align:center;font-size:1.1rem;padding:0.5em 0;color:#2d6cdf;'>
  📊 Developed by <b>THOMAS SHELBY</b>
</div>
""", unsafe_allow_html=True)