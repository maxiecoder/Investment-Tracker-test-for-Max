import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

try:
    from fpdf import FPDF
    fpdf_available = True
except ImportError:
    fpdf_available = False

DATA_FILE = "tracker_data.csv"

st.set_page_config(page_title="Investment Property Tracker", layout="wide")

page = st.sidebar.radio("📂 Select Page", ["🏘️ Weekly Tracker", "📉 Amortization Calculator"])

if page == "🏘️ Weekly Tracker":
    st.title("📅 Weekly Property Investment Tracker")

    # Load existing data
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE, parse_dates=["Week Ending"])
    else:
        df_all = pd.DataFrame(columns=["Week Ending", "Property", "Rent", "Expenses", "Interest", "Net Cash Flow", "Notes"])

    # Input form in sidebar
    st.sidebar.header("Log Weekly Data")
    with st.sidebar.form("weekly_form"):
        date = st.date_input("Week Ending", datetime.today())
        property_name = st.text_input("Property Name")
        rent = st.number_input("Weekly Rent Income", min_value=0.0)
        expenses = st.number_input("Other Weekly Expenses", min_value=0.0)
        interest = st.number_input("Weekly Mortgage Interest", min_value=0.0)
        notes = st.text_area("Notes (optional)", "")
        submitted = st.form_submit_button("Add Weekly Log")

        if submitted:
            if not property_name:
                st.error("Property Name is required!")
            else:
                net = rent - expenses - interest
                new_entry = pd.DataFrame([{
                    "Week Ending": pd.to_datetime(date),
                    "Property": property_name,
