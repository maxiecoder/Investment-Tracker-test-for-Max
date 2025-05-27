import streamlit as st
import pandas as pd

st.set_page_config(page_title="Investment Tracker", layout="wide")
st.title("🏠 Property Investment Calculator")

# ------------------------------
# Input Section
# ------------------------------
st.header("🔢 Input Property Details")

weekly_rent = st.number_input("Weekly Rent ($)", min_value=0.0, step=10.0)
lease_start = st.date_input("Lease Start Date")
lease_period_months = st.number_input("Lease Period (months)", min_value=1, step=1)
lease_weeks = lease_period_months * 4  # Approximate weeks

agent_fee_percent = st.number_input("Agent Fee (% of total rent)", min_value=0.0, step=0.1)

weekly_interest = st.number_input("Weekly Mortgage Interest ($)", min_value=0.0, step=10.0)
weekly_principal = st.number_input("Weekly Mortgage Principal ($)", min_value=0.0, step=10.0)

st.subheader("➕ Other Costs")
other_costs = []
cost_labels = []
n_costs = st.number_input("How many additional costs do you want to add?", min_value=0, step=1)

for i in range(n_costs):
    label = st.text_input(f"Cost {i+1} label", key=f"label_{i}")
    value = st.number_input(f"{label} ($)", min_value=0.0, step=10.0, key=f"value_{i}")
    other_costs.append(value)
    cost_labels.append(label)

# ------------------------------
# Calculations
# ------------------------------
if weekly_rent > 0 and lease_weeks > 0:
    total_rent = weekly_rent * lease_weeks
    total_agent_fee = (agent_fee_percent / 100) * total_rent
    total_interest = weekly_interest * lease_weeks
    total_principal = weekly_principal * lease_weeks
    total_other_costs = sum(other_costs)
    total_mortgage = total_interest + total_principal

    total_costs = total_agent_fee + total_other_costs + total_mortgage
    net_rental_income = total_rent - total_costs

    # ------------------------------
    # Output Section
    # ------------------------------
    st.header("📊 Results Summary")
    st.metric("Total Rent", f"${total_rent:,.2f}")
    st.metric("Agent Fee", f"${total_agent_fee:,.2f}")
    st.metric("Total Interest", f"${total_interest:,.2f}")
    st.metric("Total Principal", f"${total_principal:,.2f}")
    st.metric("Total Other Costs", f"${total_other_costs:,.2f}")
    st.metric("Total Mortgage Payment", f"${total_mortgage:,.2f}")
    st.metric("Net Rental Income", f"${net_rental_income:,.2f}")

    st.subheader("🧾 Cost Breakdown")
    st.write("Additional Costs:")
    for label, value in zip(cost_labels, other_costs):
        st.write(f"- {label}: ${value:,.2f}")
else:
    st.warning("Please enter values for rent and lease period to calculate.")
