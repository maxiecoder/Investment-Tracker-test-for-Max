import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Investment & Amortization Tracker", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["🏠 Investment Tracker", "📉 Amortization Calculator"])

# ------------------------------
# Investment Tracker Page (unchanged)
# ------------------------------
if page == "🏠 Investment Tracker":
    st.title("🏠 Property Investment Calculator")
    # (Your existing investment tracker code here...)
    st.info("Use the Amortization Calculator page for detailed loan analysis and positive gearing date.")

# ------------------------------
# Amortization Calculator Page with all requested features
# ------------------------------
elif page == "📉 Amortization Calculator":
    st.title("📉 Mortgage Amortization & Positive Gearing Calculator")

    st.subheader("Enter Loan Details")

    # To reset inputs, we use session state on a button
    if 'reset' not in st.session_state:
        st.session_state.reset = False

    def reset_inputs():
        for key in ['loan_amount', 'loan_term_years', 'annual_interest_rate', 'extra_repayment', 'amort_start_date',
                    'amort_period_weeks', 'weekly_rent', 'agent_fee_percent', 'rent_start_date',
                    'cost_count'] + [f"cost_label_{i}" for i in range(20)] + [f"cost_value_{i}" for i in range(20)]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.reset = True

    st.button("Reset All Inputs", on_click=reset_inputs)

    loan_amount = st.number_input("Loan Amount ($)", min_value=0.0, format="%.2f", key="loan_amount")
    loan_term_years = st.number_input("Loan Term (Years)", min_value=1, step=1, value=30, key="loan_term_years")
    annual_interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, format="%.4f", key="annual_interest_rate")
    extra_repayment = st.number_input("Weekly Extra Repayment ($)", min_value=0.0, format="%.2f", key="extra_repayment")

    amort_start_date = st.date_input("Amortization Start Date", value=datetime.today(), key="amort_start_date")
    amort_period_weeks = st.number_input("Amortization Period (Weeks)", min_value=1, max_value=loan_term_years * 52, value=52, key="amort_period_weeks")

    st.subheader("Enter Rental & Cost Details for Positive Gearing Calculation")

    weekly_rent = st.number_input("Weekly Rent ($)", min_value=0.0, step=10.0, key="weekly_rent")
    agent_fee_percent = st.number_input("Agent Fee (% of total rent)", min_value=0.0, step=0.1, key="agent_fee_percent")

    rent_start_date = st.date_input("Rent Start Date (can be after loan start)", value=amort_start_date, key="rent_start_date")

    st.markdown("**Additional Weekly Costs** (e.g., maintenance, insurance)")
    n_costs = st.number_input("Number of Additional Weekly Costs", min_value=0, step=1, max_value=20, key="cost_count")

    other_weekly_costs = []
    cost_labels = []
    for i in range(n_costs):
        label = st.text_input(f"Cost {i+1} Label", key=f"cost_label_{i}")
        value = st.number_input(f"{label or 'Cost'} Amount ($)", min_value=0.0, step=1.0, key=f"cost_value_{i}")
        other_weekly_costs.append(value)
        cost_labels.append(label)

    if st.button("Generate Amortization Schedule & Positive Gearing Info"):
        if loan_amount <= 0:
            st.error("Please enter a positive loan amount.")
        elif annual_interest_rate < 0:
            st.error("Interest rate cannot be negative.")
        elif amort_period_weeks < 1:
            st.error("Amortization period must be at least 1 week.")
        elif rent_start_date < amort_start_date:
            st.error("Rent start date cannot be before amortization start date.")
        else:
            weekly_interest_rate = (annual_interest_rate / 100) / 52
            balance = loan_amount
            schedule = []
            total_interest_paid = 0.0
            total_principal_paid = 0.0

            current_date = amort_start_date
            total_weeks = loan_term_years * 52
            if weekly_interest_rate > 0:
                fixed_weekly_payment = loan_amount * (weekly_interest_rate * (1 + weekly_interest_rate) ** total_weeks) / ((1 + weekly_interest_rate) ** total_weeks - 1)
            else:
                fixed_weekly_payment = loan_amount / total_weeks

            # Calculate weekly agent fee amount
            weekly_agent_fee = (agent_fee_percent / 100) * weekly_rent
            total_other_costs = sum(other_weekly_costs)

            positive_gear_week = None
            positive_gear_date = None

            for week in range(1, amort_period_weeks + 1):
                interest_payment = balance * weekly_interest_rate
                payment = fixed_weekly_payment + extra_repayment

                principal_payment = payment - interest_payment
                if principal_payment > balance:
                    principal_payment = balance
                    payment = interest_payment + principal_payment

                balance -= principal_payment
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment

                # Calculate net cash flow this week
                # Rent only counts if current_date >= rent_start_date
                rent_income = weekly_rent if current_date >= rent_start_date else 0.0

                total_weekly_costs = payment + weekly_agent_fee + total_other_costs
                net_cash_flow = rent_income - total_weekly_costs

                schedule.append({
                    "Week": current_date,
                    "Payment": payment,
                    "Interest Paid": interest_payment,
                    "Principal Paid": principal_payment,
                    "Remaining Balance": max(balance, 0),
                    "Weekly Rent Income": rent_income,
                    "Agent Fee": weekly_agent_fee,
                    "Other Weekly Costs": total_other_costs,
                    "Net Cash Flow": net_cash_flow
                })

                # Check if positive gearing achieved (net cash flow >= 0) first time
                if positive_gear_week is None and net_cash_flow >= 0:
                    positive_gear_week = week
                    positive_gear_date = current_date

                if balance <= 0:
                    break

                current_date += timedelta(days=7)

            schedule_df = pd.DataFrame(schedule)

            # Show amortization schedule table
            st.subheader("Amortization Schedule")
            st.dataframe(schedule_df.style.format({
                "Payment": "${:,.2f}",
                "Interest Paid": "${:,.2f}",
                "Principal Paid": "${:,.2f}",
                "Remaining Balance": "${:,.2f}",
                "Weekly Rent Income": "${:,.2f}",
                "Agent Fee": "${:,.2f}",
                "Other Weekly Costs": "${:,.2f}",
                "Net Cash Flow": "${:,.2f}"
            }))

            # Weekly cost breakdown
            st.subheader("Weekly Cost Breakdown")
            st.write(f"- Weekly Loan Payment (incl. extra): ${fixed_weekly_payment + extra_repayment:,.2f}")
            st.write(f"- Weekly Agent Fee: ${weekly_agent_fee:,.2f}")
            st.write(f"- Other Weekly Costs: ${total_other_costs:,.2f}")
            total_weekly_costs_all = (fixed_weekly_payment + extra_repayment) + weekly_agent_fee + total_other_costs
            st.markdown(f"**Total Weekly Costs: ${total_weekly_costs_all:,.2f}**")

            # Cumulative Net Cash Flow
            schedule_df['Cumulative Net Cash Flow'] = schedule_df['Net Cash Flow'].cumsum()
            st.subheader("Cumulative Net Cash Flow Over Time")
            st.line_chart(data=schedule_df.set_index('Week')['Cumulative Net Cash Flow'])

            # Download button for schedule CSV
            csv = schedule_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Amortization Schedule CSV",
                data=csv,
                file_name='amortization_schedule.csv',
                mime='text/csv'
            )

            # Summary output
            st.subheader("Summary")
            st.write(f"Total Interest Paid: ${total_interest_paid:,.2f}")
            st.write(f"Total Principal Paid: ${total_principal_paid:,.2f}")

            if positive_gear_week:
                st.success(f"Your property becomes positively geared after {positive_gear_week} weeks, on {positive_gear_date.date()}.")
            else:
                st.warning("The property does not become positively geared within the amortization period provided.")
