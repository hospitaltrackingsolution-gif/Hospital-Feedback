import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd
from io import BytesIO

# --------------------------
# GOOGLE SHEETS CONNECTION
# --------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)

# Pre-configured Google Sheet link
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1m_Po8j1VclIFIdBDqL0w2GN4gSkl7brZEjtIO7qYE04/edit?usp=sharing")
opd_sheet = spreadsheet.worksheet("OPD_Feedback")
ipd_sheet = spreadsheet.worksheet("IPD_Feedback")

# --------------------------
# STREAMLIT APP
# --------------------------
st.set_page_config(page_title="Hospital Feedback", page_icon="🏥", layout="wide")
menu = st.sidebar.radio("📌 Select Section", ["Feedback Form", "Reports"])

# --------------------------
# FEEDBACK FORM
# --------------------------
if menu == "Feedback Form":
    st.title("🏥 Patient Feedback Form")
    st.write("Please share your feedback to help us improve.")

    name = st.text_input("Patient Name")
    visit_type = st.radio("Visit Type", ["OPD", "IPD"])

    departments = [
        "General Medicine","ICU & Critical Care","Orthopedics","Cardiology",
        "Urology Care","Nephrology & Dialysis","Neurology Care","Radiology",
        "Anesthesiology","Medical Oncology","Gastroenterology","Endocrinology",
        "Obstetrics and Gynecology","Laparoscopic, Bariatric & General Surgery",
        "Paediatrics","Mother & Child Care","Other"
    ]

    department = st.selectbox("Department Visited", departments)
    if department == "Other":
        custom_department = st.text_input("Please specify the department")
        if custom_department.strip() != "":
            department = custom_department

    if visit_type == "OPD":
        questions = [
            "How satisfied are you with the doctor’s consultation?",
            "How was the behavior of the front office staff?",
            "How would you rate the waiting time for consultation?",
            "How clear was the information about diagnosis/treatment?",
            "How likely are you to recommend our hospital?"
        ]
        sheet = opd_sheet
    else:
        questions = [
            "How satisfied are you with the doctor’s treatment and daily rounds?",
            "How would you rate the nursing staff’s care?",
            "How was the cleanliness and comfort of your ward/room?",
            "How satisfied are you with food/pharmacy/diagnostic services?",
            "How was the discharge and billing process?"
        ]
        sheet = ipd_sheet

    st.subheader("Please rate the following:")
    options = ["😀 Excellent (5)", "🙂 Good (4)", "😐 Average (3)", "😟 Poor (2)", "😡 Very Poor (1)"]
    ratings = []
    for i, q in enumerate(questions, 1):
        rating = st.radio(f"{i}. {q}", options, key=f"q{i}")
        ratings.append(rating)

    review = st.text_area("📝 Additional Feedback / Suggestions")

    if st.button("Submit Feedback"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name, department] + ratings + [review])
        st.success("✅ Thank you! Your feedback has been recorded.")
        st.balloons()

# --------------------------
# REPORTS SECTION
# --------------------------
elif menu == "Reports":
    st.title("📊 Feedback Reports")

    report_type = st.radio("Select Feedback Type", ["OPD", "IPD"])
    start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = st.date_input("End Date", datetime.date.today())

    if report_type == "OPD":
        data = opd_sheet.get_all_records()
    else:
        data = ipd_sheet.get_all_records()

    df = pd.DataFrame(data)

    if not df.empty:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        mask = (df["Timestamp"].dt.date >= start_date) & (df["Timestamp"].dt.date <= end_date)
        df = df.loc[mask]

        if df.empty:
            st.warning("⚠️ No feedback found for this date range.")
        else:
            st.subheader("📌 Summary")
            st.write(f"Total Feedback Collected: **{len(df)}**")

            dept_count = df["Department"].value_counts()
            st.bar_chart(dept_count)

            numeric_cols = df.columns[3:-1]
            q_avg = df[numeric_cols].apply(lambda x: x.str.extract(r'(\d)').astype(float).mean())
            st.write("### Average Ratings per Question")
            st.table(q_avg)

            st.write("### 📝 Patient Comments")
            for comment in df["Review"].dropna():
                st.write(f"- {comment}")

            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Download Excel", data=excel_buffer.getvalue(), file_name=f"{report_type}_Report.xlsx")
    else:
        st.warning("⚠️ No feedback data available yet.")
