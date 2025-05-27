import streamlit as st

import pandas as pd

from datetime import datetime

import os

 

DATA_FILE = "tracker_data.csv"

 

st.set_page_config(page_title="Weekly Property Tracker", layout="wide")

st.title("📅 Weekly Property Investment Tracker")

 

# ---------------------------

# 🔁 Load existing data from CSV

# ---------------------------

if os.path.exists(DATA_FILE):

    df_all = pd.read_csv(DATA_FILE, parse_dates=["Week Ending"])

else:

    df_all = pd.DataFrame(columns=["Week Ending", "Property", "Rent", "Expenses", "Interest", "Net Cash Flow", "Notes"])

 

# ---------------------------

# 📝 Input Form (Sidebar)

# ---------------------------

st.sidebar.header("Log Weekly Data")

with st.sidebar.form("weekly_form"):

    date = st.date_input("Week Ending", datetime.today())

    property_name = st.text_input("Property Name")

    rent = st.number_input("Weekly Rent Income", min_value=0.0)

    expenses = st.number_input("Other Weekly Expenses", min_value=0.0)

    interest = st.number_input("Weekly Mortgage Interest", min_value=0.0)

    notes = st.text_area("Notes (optional)", "")

    submitted = st.form_submit_button("Add Weekly Log")

 

    if submitted and property_name:

        net = rent - expenses - interest

        new_entry = pd.DataFrame([{

            "Week Ending": pd.to_datetime(date),

            "Property": property_name,

            "Rent": rent,

            "Expenses": expenses,

            "Interest": interest,

            "Net Cash Flow": net,

            "Notes": notes

        }])

        df_all = pd.concat([df_all, new_entry], ignore_index=True)

        df_all.to_csv(DATA_FILE, index=False)

        st.success("Weekly log added and saved!")

 

# ---------------------------

# 🔍 Filters (Property + Date)

# ---------------------------

st.sidebar.markdown("### 🔎 Filter Data")

 

# Property filter

properties = df_all["Property"].unique().tolist()

selected_properties = st.sidebar.multiselect("Filter by Property", properties, default=properties)

 

# Date range filter

if not df_all.empty:

    min_date = df_all["Week Ending"].min().date()

    max_date = df_all["Week Ending"].max().date()

    start_date, end_date = st.sidebar.date_input("Filter by Date Range", [min_date, max_date])

else:

    start_date, end_date = datetime.today(), datetime.today()

 

# Apply filters

filtered_df = df_all[

    (df_all["Property"].isin(selected_properties)) &

    (df_all["Week Ending"].dt.date >= start_date) &

    (df_all["Week Ending"].dt.date <= end_date)

]

 

# ---------------------------

# 📊 Weekly Log Table

# ---------------------------

if not filtered_df.empty:

    filtered_df = filtered_df.sort_values("Week Ending", ascending=False)

    st.subheader("📋 Weekly Property Log")

    st.dataframe(filtered_df)

 

    # Net cash flow over time

    st.subheader("📈 Total Net Cash Flow Over Time")

    cashflow_chart = filtered_df.groupby("Week Ending")["Net Cash Flow"].sum().reset_index()

    st.line_chart(cashflow_chart.set_index("Week Ending"))

 

    # Compare properties side-by-side

    st.subheader("🏘️ Compare Properties Side-by-Side")

    summary_df = filtered_df.groupby("Property")[["Rent", "Expenses", "Interest", "Net Cash Flow"]].sum().reset_index()

    summary_df["ROI (%)"] = ((summary_df["Net Cash Flow"] * 52) / (summary_df["Rent"] * 52 + summary_df["Expenses"] + summary_df["Interest"])) * 100

    summary_df = summary_df.sort_values("Net Cash Flow", ascending=False)

    st.dataframe(summary_df.style.format({"ROI (%)": "{:.2f}"}))

else:

    st.warning("No data matches your filters. Try adjusting the date range or property selection.")