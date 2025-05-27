import streamlit as st
import pandas as pd
from datetime import datetime
import os

DATA_FILE = "investment_tracker.csv"

st.set_page_config(page_title="Investment Tracker", layout="wide")
st.title("🏠 Investment Tracker with Detailed Costs")

# Load data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df["Lease Start Date"] = pd.to_datetime(df["Lease Start Date"], errors="coerce")
else:
    df = pd.DataFrame(columns=[
        "Property", "Lease Start Date", "Lease Period (months)",
        "Weekly Rent", "Total Rent", "Agent Fee (%)", "Agent Cost",
        "Other Costs", "Mortgage Cost", "Residual Loan Balance",
        "Net Cash Flow", "Rental Return (%)", "Notes"
    ])

# Sidebar: Input form
st.sidebar.header("Add Investment Data")
with st.sidebar.form("input_form"):
    property_name = st.text_input("Property Name")
    lease_start = st.date_input("Lease Start Date", datetime.today())
    lease_period = st.number_input("Lease Period (months)", min_value=1, step=1)
    weekly_rent = st.number_input("Weekly Rent ($)", min_value=0.0, step=0.01)
    agent_fee_pct = st.number_input("Agent Fee (%)", min_value=0.0, max_value=100.0, step=0.1)

    # Dynamic Other Costs input
    st.write("### Other Costs (add multiple)")
    other_costs = []
    num_other_costs = st.number_input("Number of other cost items", min_value=0, max_value=10, step=1, key="num_other_costs")
    for i in range(num_other_costs):
        label = st.text_input(f"Cost item #{i+1} label", key=f"label_{i}")
        amount = st.number_input(f"Cost item #{i+1} amount ($)", min_value=0.0, step=0.01, key=f"amount_{i}")
        other_costs.append({"label": label, "amount": amount})

    mortgage_cost = st.number_input("Mortgage Cost (Interest + Principal) for period ($)", min_value=0.0, step=0.01)
    residual_loan_balance = st.number_input("Residual Loan Balance ($)", min_value=0.0, step=0.01)
    notes = st.text_area("Notes (optional)")

    submitted = st.form_submit_button("Add Entry")

    if submitted and property_name:
        weeks_per_month = 4.33  # approximate average weeks per month
        total_weeks = lease_period * weeks_per_month
        total_rent = weekly_rent * total_weeks
        agent_cost = total_rent * (agent_fee_pct / 100)
        total_other_costs = sum(item["amount"] for item in other_costs)
        net_cash_flow = total_rent - agent_cost - total_other_costs - mortgage_cost

        # Rental return % = Net Cash Flow / (Residual Loan Balance + total other costs + agent cost)
        denominator = residual_loan_balance + total_other_costs + agent_cost
        rental_return_pct = (net_cash_flow / denominator * 100) if denominator != 0 else 0.0

        # Store other costs as a string summary
        other_costs_str = "; ".join(f"{item['label']}: ${item['amount']:.2f}" for item in other_costs)

        new_row = pd.DataFrame([{
            "Property": property_name,
            "Lease Start Date": lease_start,
            "Lease Period (months)": lease_period,
            "Weekly Rent": weekly_rent,
            "Total Rent": total_rent,
            "Agent Fee (%)": agent_fee_pct,
            "Agent Cost": agent_cost,
            "Other Costs": other_costs_str,
            "Mortgage Cost": mortgage_cost,
            "Residual Loan Balance": residual_loan_balance,
            "Net Cash Flow": net_cash_flow,
            "Rental Return (%)": rental_return_pct,
            "Notes": notes
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Entry added!")

# Filter data
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

# Display filtered data
if not filtered.empty:
    st.subheader("Investment Logs")
    st.dataframe(filtered.sort_values("Lease Start Date", ascending=False))

    st.subheader("Summary by Property")
    summary = filtered.groupby("Property").agg({
        "Total Rent": "sum",
        "Agent Cost": "sum",
        "Mortgage Cost": "sum",
        "Net Cash Flow": "sum",
        "Rental Return (%)": "mean"
    }).reset_index()

    st.dataframe(summary.style.format({
        "Total Rent": "${:,.2f}",
        "Agent Cost": "${:,.2f}",
        "Mortgage Cost": "${:,.2f}",
        "Net Cash Flow": "${:,.2f}",
        "Rental Return (%)": "{:.2f}%"
    }))
else:
    st.warning("No data to display with current filters.")
