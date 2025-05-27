import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Optional PDF export dependency
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
        valid_dates = df_all["Week Ending"].dropna()
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
            (df_all["Week Ending"].dt.date >= start_date) &
            (df_all["Week Ending"].dt.date <= end_date)
        ]
    else:
        filtered_df = pd.DataFrame()

    # Display table and charts
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values("Week Ending", ascending=False)
        st.subheader("📋 Weekly Property Log")
        st.dataframe(filtered_df)

        st.subheader("📈 Total Net Cash Flow Over Time")
        cashflow_chart = filtered_df.groupby("Week Ending")["Net Cash Flow"].sum().reset_index()
        st.line_chart(cashflow_chart.set_index("Week Ending"))

        st.subheader("🏘️ Compare Properties Side-by-Side")
        summary_df = filtered_df.groupby("Property")[["Rent", "Expenses", "Interest", "Net Cash Flow"]].sum().reset_index()
        # Calculate ROI (%) = (Net Cash Flow annualized) / (Total costs) * 100
        # Use 52 weeks per year and 12 months per year conversion
        summary_df["ROI (%)"] = ((summary_df["Net Cash Flow"] * 52) / (summary_df["Rent"] * 52 + summary_df["Expenses"] + summary_df["Interest"])) * 100
        summary_df = summary_df.sort_values("Net Cash Flow", ascending=False)
        st.dataframe(summary_df.style.format({"ROI (%)": "{:.2f}"}))

    else:
        st.warning("No data matches your filters. Try adjusting the date range or property selection.")

# -----------------------------------
# Amortization Calculator Tab
# -----------------------------------
if page == "📉 Amortization Calculator":
    st.title("📉 Mortgage Amortization Calculator")

    # Load weekly data
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE, parse_dates=["Week Ending"])
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

    if st.button("Generate Amortization Schedule"):
        property_df = df_all[df_all["Property"] == selected_property].sort_values("Week Ending")

        if property_df.empty:
            st.warning("No weekly data for this property.")
            st.stop()

        schedule = []
        balance = loan_amount
        total_interest = 0.0
        total_principal = 0.0

        for _, row in property_df.iterrows():
            interest = row.get("Interest", 0)
            principal = row.get("Rent", 0) - row.get("Expenses", 0) - interest + extra_repayment

            principal = max(principal, 0)  # prevent negative principal
            principal = min(principal, balance)  # cannot pay more than balance
            balance -= principal
            total_interest += interest
            total_principal += principal

            schedule.append({
                "Week": row["Week Ending"].date(),
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

        if fpdf_available:
            if st.button("📄 Export Amortization Schedule as PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Amortization Schedule for {selected_property}", ln=True, align="C")
                pdf.ln(10)

                # Table headers
                pdf.cell(30, 10, "Week", 1)
                pdf.cell(40, 10, "Interest Paid", 1)
                pdf.cell(40, 10, "Principal Paid", 1)
                pdf.cell(40, 10, "Total Payment", 1)
                pdf.cell(40, 10, "Remaining Balance", 1)
                pdf.ln()

                # Table rows
                for _, row in schedule_df.iterrows():
                    pdf.cell(30, 10, str(row["Week"]), 1)
                    pdf.cell(40, 10, f"${row['Interest Paid']:.2f}", 1)
                    pdf.cell(40, 10, f"${row['Principal Paid']:.2f}", 1)
                    pdf.cell(40, 10, f"${row['Total Payment']:.2f}", 1)
                    pdf.cell(40, 10, f"${row['Remaining Balance']:.2f}", 1)
                    pdf.ln()

                pdf_output_path = "amortization_schedule.pdf"
                pdf.output(pdf_output_path)

                with open(pdf_output_path, "rb") as f:
                    st.download_button("📥 Download PDF", data=f, file_name=pdf_output_path, mime="application/pdf")

        else:
            st.info("To enable PDF export, install fpdf: pip install fpdf")
