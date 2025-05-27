import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Investment & Amortization Tracker", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["🏠 Investment Tracker", "📉 Amortization Calculator"])

# ------------------------------
# Investment Tracker Page
# ------------------------------
if page == "🏠 Investment Tracker":
    st.title("🏠 Property Investment Calculator")

    st.header("🔢 Input Property Details")

    weekly_rent = st.number_input("Weekly Rent ($)", min_value=0.0, step=10.0)
    lease_start = st.date_input("Lease Start Date", value=datetime.today())
    lease_period_months = st.number_input("Lease Period (months)", min_value=1, step=1)

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

    # Calculations
    if weekly_rent > 0 and lease_period_months > 0:
        total_rent = weekly_rent * (52 / 12) * lease_period_months
        total_agent_fee = (agent_fee_percent / 100) * total_rent
        lease_weeks = (52 / 12) * lease_period_months
        total_interest = weekly_interest * lease_weeks
        total_principal = weekly_principal * lease_weeks
        total_other_costs = sum(other_costs)
        total_mortgage = total_interest + total_principal

        total_costs = total_agent_fee + total_other_costs + total_mortgage
        net_rental_income = total_rent - total_costs

        st.header("📊 Results Summary")
        st.metric("Total Rent", f"${total_rent:,.2f}")
        st.metric("Agent Fee", f"${total_agent_fee:,.2f}")
        st.metric("Total Interest", f"${total_interest:,.2f}")
        st.metric("Total Principal", f"${total_principal:,.2f}")
        st.metric("Total Other Costs", f"${total_other_costs:,.2f}")
        st.metric("Total Mortgage Payment", f"${total_mortgage:,.2f}")
        st.metric("Net Rental Income", f"${net_rental_income:,.2f}")

        st.subheader("🧾 Cost Breakdown")
        if other_costs:
            st.write("Additional Costs:")
            for label, value in zip(cost_labels, other_costs):
                st.write(f"- {label}: ${value:,.2f}")
    else:
        st.warning("Please enter values for rent and lease period to calculate.")

# ------------------------------
# Amortization Calculator Page
# ------------------------------
elif page == "📉 Amortization Calculator":
    st.title("📉 Mortgage Amortization Calculator")

    st.subheader("Enter Loan Details")

    loan_amount = st.number_input("Loan Amount ($)", min_value=0.0, format="%.2f")
    loan_term_years = st.number_input("Loan Term (Years)", min_value=1, step=1, value=30)
    annual_interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, format="%.4f")
    extra_repayment = st.number_input("Weekly Extra Repayment ($)", min_value=0.0, format="%.2f")

    amort_start_date = st.date_input("Amortization Start Date", value=datetime.today())
    amort_period_weeks = st.number_input("Amortization Period (Weeks)", min_value=1, max_value=loan_term_years * 52, value=52)

    if st.button("Generate Amortization Schedule"):
        if loan_amount <= 0:
            st.error("Please enter a positive loan amount.")
        elif annual_interest_rate < 0:
            st.error("Interest rate cannot be negative.")
        else:
            # Calculate weekly interest rate
            weekly_interest_rate = (annual_interest_rate / 100) / 52

            balance = loan_amount
            schedule = []
            total_interest_paid = 0.0
            total_principal_paid = 0.0

            current_date = amort_start_date

            for week in range(1, amort_period_weeks + 1):
                interest_payment = balance * weekly_interest_rate
                # Assume a fixed weekly payment for simplicity:
                # Payment enough to amortize loan in loan_term_years * 52 weeks without extra repayment
                total_weeks = loan_term_years * 52
                if weekly_interest_rate > 0:
                    # Calculate fixed weekly payment using annuity formula
                    weekly_payment = loan_amount * (weekly_interest_rate * (1 + weekly_interest_rate) ** total_weeks) / ((1 + weekly_interest_rate) ** total_weeks - 1)
                else:
                    weekly_payment = loan_amount / total_weeks

                # Add extra repayment
                payment = weekly_payment + extra_repayment

                principal_payment = payment - interest_payment
                if principal_payment > balance:
                    principal_payment = balance
                    payment = interest_payment + principal_payment

                balance -= principal_payment
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment

                schedule.append({
                    "Week": current_date,
                    "Payment": payment,
                    "Interest Paid": interest_payment,
                    "Principal Paid": principal_payment,
                    "Remaining Balance": max(balance, 0)
                })

                if balance <= 0:
                    break

                current_date += timedelta(days=7)

            schedule_df = pd.DataFrame(schedule)
            st.subheader("Amortization Schedule")
            st.dataframe(schedule_df.style.format({
                "Payment": "${:,.2f}",
                "Interest Paid": "${:,.2f}",
                "Principal Paid": "${:,.2f}",
                "Remaining Balance": "${:,.2f}",
            }))

            st.subheader("Summary")
            st.write(f"Total Interest Paid: ${total_interest_paid:,.2f}")
            st.write(f"Total Principal Paid: ${total_principal_paid:,.2f}")
