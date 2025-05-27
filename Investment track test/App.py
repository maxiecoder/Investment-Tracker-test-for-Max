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
