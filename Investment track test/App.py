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

    # Load existing data with fallback rename for week column
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE)
        if "Week Start" not in df_all.columns and "Week Ending" in df_all.columns:
            df_all = df_all.rename(columns={"Week Ending": "Week Start"})
        df_all["Week Start"] = pd.to_datetime(df_all["Week Start"])
    else:
        df_all = pd.DataFrame(columns=["Week Start", "Property", "Rent", "Expenses", "Interest", "Net Cash Flow", "Notes"])

    # Input form in sidebar
    st.sidebar.header("Log Weekly Data")
    with st.sidebar.form("weekly_form"):
        date = st.date_input("Week Start", datetime.today())
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
                    "Week Start": pd.to_datetime(date),
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

    # Filters
    st.sidebar.markdown("### 🔎 Filter Data")
    properties = df_all["Property"].unique().tolist() if not df_all.empty else []
    selected_properties = st.sidebar.multiselect("Filter by Property", properties, default=properties)

    if not df_all.empty:
        valid_dates = df_all["Week Start"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            start_date, end_date = st.sidebar.date_input("Filter by Date Range", [min_date, max_date])
        else:
            start_date, end_date = datetime.today(), datetime.today()
    else:
        start_date, end_date = datetime.today(), datetime.today()

    # Apply filters
    if not df_all.empty:
        filtered_df = df_all[
            (df_all["Property"].isin(selected_properties)) &
            (df_all["Week Start"].dt.date >= start_date) &
            (df_all["Week Start"].dt.date <= end_date)
        ]
    else:
        filtered_df = pd.DataFrame()

    # Show filtered data
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values("Week Start", ascending=False)
        st.subheader("📋 Weekly Property Log")
        st.dataframe(filtered_df)

        # Total period weeks for calculations
        period_weeks = (end_date - start_date).days / 7
        if period_weeks < 1:
            period_weeks = 1

        st.subheader("📊 Aggregated Summary for Selected Period")

        summary_df = filtered_df.groupby("Property")[["Rent", "Expenses", "Interest"]].sum().reset_index()

        # Total rent already summed for period (weekly sums)
        summary_df["Total Rent"] = summary_df["Rent"]
        summary_df["Agent Cost (5%)"] = summary_df["Total Rent"] * 0.05  # example 5% agent fee

        summary_df["Other Costs"] = summary_df["Expenses"]

        # Estimate principal from net cash flow + interest
        filtered_df["Principal"] = filtered_df["Rent"] - filtered_df["Expenses"] - filtered_df["Interest"] - filtered_df["Net Cash Flow"]
        principal_sum = filtered_df.groupby("Property")["Principal"].sum().reset_index()
        summary_df = summary_df.merge(principal_sum, on="Property", how="left")
        summary_df = summary_df.rename(columns={"Principal": "Estimated Principal"})

        # Net rental income = total rent - agent cost - other costs - interest - principal
        summary_df["Net Rental Income"] = summary_df["Total Rent"] - summary_df["Agent Cost (5%)"] - summary_df["Other Costs"] - summary_df["Interest"] - summary_df["Estimated Principal"].fillna(0)

        st.dataframe(summary_df.style.format({
            "Total Rent": "${:,.2f}",
            "Agent Cost (5%)": "${:,.2f}",
            "Other Costs": "${:,.2f}",
            "Interest": "${:,.2f}",
            "Estimated Principal": "${:,.2f}",
            "Net Rental Income": "${:,.2f}",
        }))

    else:
        st.warning("No data matches your filters. Try adjusting the date range or property selection.")

# -----------------------------------
# Amortization Calculator Tab
# -----------------------------------
if page == "📉 Amortization Calculator":
    st.title("📉 Mortgage Amortization Calculator")

    # Load weekly data with fallback rename
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE)
        if "Week Start" not in df_all.columns and "Week Ending" in df_all.columns:
            df_all = df_all.rename(columns={"Week Ending": "Week Start"})
        df_all["Week Start"] = pd.to_datetime(df_all["Week Start"])
    else:
        st.warning("No data file found. Please enter weekly logs first in the Tracker.")
        st.stop()

    properties = df_all["Property"].unique().tolist()
    if not properties:
        st.warning("No properties found. Add at least one in the Tracker.")
        st.stop()

    selected_property = st.selectbox("Select Property", properties)

    st.subheader("Loan Details (Manual Input)")
    loan_amount = st.number_input("Original Loan Amount", min_value=0.0, format="%.2f")
    loan_term_years = st.number_input("Loan Term (Years)", min_value=1, step=1, value=30)
    interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, format="%.3f")
    extra_repayment = st.number_input("Weekly Extra Repayment (Optional)", min_value=0.0, format="%.2f")

    amort_start_date = st.date_input("Amortization Start Date", datetime.today())
    amort_period_weeks = st.number_input("Amortization Period (Weeks)", min_value=1, max_value=loan_term_years * 52, value=52)

    if st.button("Generate Amortization Schedule"):
        property_df = df_all[df_all["Property"] == selected_property].sort_values("Week Start")

        if property_df.empty:
            st.warning("No weekly data for this property.")
            st.stop()

        schedule = []
        balance = loan_amount
        total_interest = 0.0
        total_principal = 0.0

        # Filter logs to amort_start_date and next amort_period_weeks
        property_df = property_df[property_df["Week Start"].dt.date >= amort_start_date]
        property_df = property_df.head(amort_period_weeks)

        if property_df.empty:
            st.warning("No weekly data for the amortization period selected.")
            st.stop()

        for _, row in property_df.iterrows():
            interest = row.get("Interest", 0)
            # Calculate principal from net cash flow and interest + extra repayment
            principal = row.get("Rent", 0) - row.get("Expenses", 0) + extra_repayment
            principal = max(principal, 0)
            principal = min(principal, balance)  # Can't pay more than balance

            balance -= principal
            total_interest += interest
            total_principal += principal

            schedule.append({
                "Week": row["Week Start"].date(),
                "Interest Paid": interest,
                "Principal Paid": principal,
                "Total Payment": interest + principal,
                "Remaining Balance": balance
            })

            if balance <= 0:
                break

        schedule_df = pd.DataFrame(schedule)

        st.subheader("📋 Amortization Schedule")
        st.dataframe(schedule_df)

        st.subheader("📊 Remaining Loan Balance Over Time")
        st.line_chart(schedule_df.set_index("Week")["Remaining Balance"])

        st.success(f"Total Interest Paid: ${total_interest:,.2f}")
        st.success(f"Total Principal Paid: ${total_principal:,.2f}")

        csv_data = schedule_df.to_csv(index=False)
        st.download_button("⬇️ Download Amortization CSV", data=csv_data, file_name="amortization_schedule.csv", mime="text/csv")
