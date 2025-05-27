import streamlit as st
import pandas as pd
from datetime import datetime
import os

DATA_FILE = "investment_data.csv"

st.set_page_config(page_title="Investment Tracker", layout="wide")
st.title("🏠 Investment Property Tracker")

# Load existing data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Property",
        "Weekly Rent",
        "Lease Start Date",
        "Lease Period (Months)",
        "Agent Fee (%)",
        "Other Costs (comma-separated)",
        "Mortgage Interest",
        "Mortgage Principal",
        "Residual Loan Balance",
        "Notes"
    ])

# Convert Lease Start Date to datetime, handle errors safely
df["Lease Start Date"] = pd.to_datetime(df["Lease Start Date"], errors="coerce")
valid_dates = df["Lease Start Date"].dropna()
if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
else:
    min_date = datetime.today().date()
    max_date = datetime.today().date()

# Sidebar input form
st.sidebar.header("Add New Property Investment")

with st.sidebar.form("input_form"):
    property_name = st.text_input("Property Name")
    weekly_rent = st.number_input("Weekly Rent (£)", min_value=0.0, format="%.2f")
    lease_start = st.date_input("Lease Start Date", value=datetime.today())
    lease_period = st.number_input("Lease Period (Months)", min_value=1, step=1)
    agent_fee_pct = st.number_input("Agent Fee (%)", min_value=0.0, max_value=100.0, format="%.2f")
    other_costs_str = st.text_area("Other Costs During Period (comma-separated £ amounts)", "")
    mortgage_interest = st.number_input("Mortgage Interest (£)", min_value=0.0, format="%.2f")
    mortgage_principal = st.number_input("Mortgage Principal (£)", min_value=0.0, format="%.2f")
    residual_loan_balance = st.number_input("Residual Loan Balance (£)", min_value=0.0, format="%.2f")
    notes = st.text_area("Notes (optional)", "")

    submitted = st.form_submit_button("Add / Update Investment")

    if submitted and property_name:
        # Parse other costs into list of floats, ignoring invalid entries
        other_costs_list = []
        if other_costs_str.strip():
            try:
                other_costs_list = [float(x.strip()) for x in other_costs_str.split(",") if x.strip()]
            except:
                st.error("Please enter valid numbers separated by commas for Other Costs.")
                st.stop()

        # Calculate totals
        total_rent = weekly_rent * 4.345 * lease_period  # Approx weeks per month * months
        agent_cost = total_rent * (agent_fee_pct / 100)
        total_other_costs = sum(other_costs_list)
        total_mortgage = mortgage_interest + mortgage_principal

        # Net cash flow calculation
        net_cash_flow = total_rent - agent_cost - total_other_costs - total_mortgage

        new_entry = {
            "Property": property_name,
            "Weekly Rent": weekly_rent,
            "Lease Start Date": lease_start,
            "Lease Period (Months)": lease_period,
            "Agent Fee (%)": agent_fee_pct,
            "Other Costs (comma-separated)": other_costs_str,
            "Mortgage Interest": mortgage_interest,
            "Mortgage Principal": mortgage_principal,
            "Residual Loan Balance": residual_loan_balance,
            "Notes": notes,
            "Total Rent": total_rent,
            "Agent Cost": agent_cost,
            "Total Other Costs": total_other_costs,
            "Total Mortgage Cost": total_mortgage,
            "Net Cash Flow": net_cash_flow
        }

        # Append to df and save
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"Property '{property_name}' added successfully!")

# Filters to view data
st.sidebar.markdown("---")
st.sidebar.header("Filter Investments")

properties = df["Property"].unique().tolist()
selected_properties = st.sidebar.multiselect("Select Properties", properties, default=properties)

start_date_filter, end_date_filter = st.sidebar.date_input(
    "Filter by Lease Start Date Range",
    value=(min_date, max_date)
)

# Filter dataframe
filtered_df = df[
    (df["Property"].isin(selected_properties)) &
    (df["Lease Start Date"].between(pd.to_datetime(start_date_filter), pd.to_datetime(end_date_filter)))
]

if filtered_df.empty:
    st.warning("No investment data matches the filters.")
else:
    st.subheader("Investment Summary")
    display_cols = [
        "Property", "Weekly Rent", "Lease Start Date", "Lease Period (Months)",
        "Agent Fee (%)", "Total Rent", "Agent Cost", "Total Other Costs",
        "Mortgage Interest", "Mortgage Principal", "Total Mortgage Cost",
        "Residual Loan Balance", "Net Cash Flow", "Notes"
    ]
    st.dataframe(filtered_df[display_cols].sort_values("Lease Start Date", ascending=False))

    st.subheader("Net Cash Flow by Property")
    net_cash = filtered_df.groupby("Property")["Net Cash Flow"].sum()
    st.bar_chart(net_cash)

    st.subheader("Residual Loan Balances")
    residuals = filtered_df.groupby("Property")["Residual Loan Balance"].last()
    st.bar_chart(residuals)
