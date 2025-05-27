import streamlit as st
import pandas as pd
from datetime import datetime
import os

DATA_FILE = "investment_tracker.csv"

st.set_page_config(page_title="Investment Tracker", layout="wide")
st.title("🏠 Weekly Investment Tracker")

# Load existing data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    # Convert Lease Start Date to datetime safely
    df["Lease Start Date"] = pd.to_datetime(df["Lease Start Date"], errors="coerce")
else:
    df = pd.DataFrame(columns=[
        "Property", "Lease Start Date", "Lease Period (months)",
        "Weekly Rent", "Agent Fee (%)", "Agent Fee Amount", "Mortgage Cost",
        "Net Cash Flow", "Notes"
    ])

# Sidebar input form
st.sidebar.header("Add Weekly Data")
with st.sidebar.form("weekly_form"):
    property_name = st.text_input("Property Name")
    lease_start = st.date_input("Lease Start Date", datetime.today())
    lease_period = st.number_input("Lease Period (months)", min_value=1, step=1)
    weekly_rent = st.number_input("Weekly Rent", min_value=0.0, step=0.01)
    agent_fee_pct = st.number_input("Agent Fee (%)", min_value=0.0, max_value=100.0, step=0.1)
    mortgage_cost = st.number_input("Weekly Mortgage Cost", min_value=0.0, step=0.01)
    notes = st.text_area("Notes (optional)", "")
    submitted = st.form_submit_button("Add Entry")

    if submitted and property_name:
        agent_fee_amount = weekly_rent * (agent_fee_pct / 100)
        net_cash_flow = weekly_rent - agent_fee_amount - mortgage_cost

        new_row = pd.DataFrame([{
            "Property": property_name,
            "Lease Start Date": lease_start,
            "Lease Period (months)": lease_period,
            "Weekly Rent": weekly_rent,
            "Agent Fee (%)": agent_fee_pct,
            "Agent Fee Amount": agent_fee_amount,
            "Mortgage Cost": mortgage_cost,
            "Net Cash Flow": net_cash_flow,
            "Notes": notes
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Entry added!")

# Filter data by Lease Start Date
st.sidebar.markdown("### Filter Data")
properties = df["Property"].dropna().unique().tolist()
selected_props = st.sidebar.multiselect("Select Properties", properties, default=properties)

valid_dates = df["Lease Start Date"].dropna()

if not valid_dates.empty and pd.notnull(valid_dates.min()):
    min_date = valid_dates.min().date()
else:
    min_date = datetime.today().date()

if not valid_dates.empty and pd.notnull(valid_dates.max()):
    max_date = valid_dates.max().date()
else:
    max_date = datetime.today().date()

start_date, end_date = st.sidebar.date_input(
    "Filter by Lease Start Date Range",
    value=[min_date, max_date]
)

filtered = df[
    (df["Property"].isin(selected_props)) &
    (df["Lease Start Date"].notna()) &
    (df["Lease Start Date"].dt.date >= start_date) &
    (df["Lease Start Date"].dt.date <= end_date)
]

# Show filtered data
if not filtered.empty:
    st.subheader("Investment Logs")
    st.dataframe(filtered.sort_values("Lease Start Date", ascending=False))

    st.subheader("Net Cash Flow by Property")
    summary = filtered.groupby("Property").agg({
        "Weekly Rent": "mean",
        "Agent Fee (%)": "mean",
        "Mortgage Cost": "mean",
        "Net Cash Flow": "sum"
    }).reset_index()

    st.dataframe(summary.style.format({
        "Weekly Rent": "${:,.2f}",
        "Agent Fee (%)": "{:.2f}%",
        "Mortgage Cost": "${:,.2f}",
        "Net Cash Flow": "${:,.2f}"
    }))
else:
    st.warning("No data to display with current filters.")
