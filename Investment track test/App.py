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
    repayment_frequency = st.selectbox("Repayment Frequency", options=["Weekly", "Fortnightly", "Monthly"])
    extra_repayment = st.number_input("Extra Repayment per Period ($)", min_value=0.0, format="%.2f")

    amort_start_date = st.date_input("Amortization Start Date", value=datetime.today())

    # Map frequency to payments per year and days per period
    freq_map = {
        "Weekly": (52, 7),
        "Fortnightly": (26, 14),
        "Monthly": (12, 30)
    }
    payments_per_year, days_per_period = freq_map[repayment_frequency]
    total_payments = loan_term_years * payments_per_year

    if st.button("Generate Amortization Schedule"):
        if loan_amount <= 0:
            st.error("Please enter a positive loan amount.")
        elif annual_interest_rate < 0:
            st.error("Interest rate cannot be negative.")
        else:
            # Periodic interest rate
            periodic_interest_rate = (annual_interest_rate / 100) / payments_per_year

            # Calculate fixed repayment amount (annuity formula)
            if periodic_interest_rate > 0:
                repayment = loan_amount * (periodic_interest_rate * (1 + periodic_interest_rate) ** total_payments) / ((1 + periodic_interest_rate) ** total_payments - 1)
            else:
                repayment = loan_amount / total_payments

            repayment += extra_repayment

            st.markdown(f"### Estimated {repayment_frequency} Repayment Amount: **${repayment:,.2f}**")

            balance = loan_amount
            schedule = []
            total_interest_paid = 0.0
            total_principal_paid = 0.0
            current_date = amort_start_date

            for n in range(1, total_payments + 1):
                interest_payment = balance * periodic_interest_rate
                principal_payment = repayment - interest_payment

                # Prevent overpayment on last payment
                if principal_payment > balance:
                    principal_payment = balance
                    repayment_actual = interest_payment + principal_payment
                else:
                    repayment_actual = repayment

                balance -= principal_payment
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment

                schedule.append({
                    "Payment Number": n,
                    "Date": current_date,
                    "Payment": repayment_actual,
                    "Interest": interest_payment,
                    "Principal": principal_payment,
                    "Remaining Balance": max(balance, 0)
                })

                if balance <= 0:
                    break

                current_date += timedelta(days=days_per_period)

            schedule_df = pd.DataFrame(schedule)
            schedule_df["Date"] = pd.to_datetime(schedule_df["Date"]).dt.date

            st.subheader("Amortization Schedule")
            st.dataframe(schedule_df.style.format({
                "Payment": "${:,.2f}",
                "Interest": "${:,.2f}",
                "Principal": "${:,.2f}",
                "Remaining Balance": "${:,.2f}"
            }), height=400)

            st.subheader("Summary")
            st.write(f"**Total Interest Paid:** ${total_interest_paid:,.2f}")
            st.write(f"**Total Principal Paid:** ${total_principal_paid:,.2f}")
            st.write(f"**Total Payments:** ${total_interest_paid + total_principal_paid:,.2f}")
            st.write(f"**Loan Payoff Date:** {schedule_df['Date'].iloc[-1]}")
