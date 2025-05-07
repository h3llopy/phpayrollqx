import streamlit as st
import pandas as pd
from datetime import datetime

# =============================================
# PHILIPPINE PAYROLL CALCULATIONS
# =============================================

def calculate_sss(salary):
    """SSS Contribution Table 2024"""
    if salary <= 4250: return 180
    elif salary <= 4750: return 202.50
    elif salary <= 5250: return 225
    elif salary <= 5750: return 247.50
    elif salary <= 6250: return 270
    elif salary <= 6750: return 292.50
    elif salary <= 7250: return 315
    elif salary <= 7750: return 337.50
    elif salary <= 8250: return 360
    elif salary <= 8750: return 382.50
    elif salary <= 9250: return 405
    elif salary <= 9750: return 427.50
    elif salary <= 10250: return 450
    elif salary <= 10750: return 472.50
    elif salary <= 11250: return 495
    elif salary <= 11750: return 517.50
    elif salary <= 12250: return 540
    elif salary <= 12750: return 562.50
    elif salary <= 13250: return 585
    elif salary <= 13750: return 607.50
    elif salary <= 14250: return 630
    elif salary <= 14750: return 652.50
    elif salary <= 15250: return 675
    elif salary <= 15750: return 697.50
    elif salary <= 16250: return 720
    elif salary <= 16750: return 742.50
    elif salary <= 17250: return 765
    elif salary <= 17750: return 787.50
    elif salary <= 18250: return 810
    elif salary <= 18750: return 832.50
    elif salary <= 19250: return 855
    elif salary <= 19750: return 877.50
    elif salary <= 20250: return 900
    elif salary <= 20750: return 922.50
    elif salary <= 21250: return 945
    elif salary <= 21750: return 967.50
    elif salary <= 22250: return 990
    elif salary <= 22750: return 1012.50
    elif salary <= 23250: return 1035
    elif salary <= 23750: return 1057.50
    elif salary <= 24250: return 1080
    elif salary <= 24750: return 1102.50
    else: return 1125

def calculate_philhealth(salary):
    """PhilHealth Contribution Table 2024"""
    if salary <= 10000: return 450
    elif salary <= 79999: return salary * 0.045
    else: return 3600

def calculate_pagibig(salary):
    """Pag-IBIG Contribution Table 2024"""
    if salary > 5000: return 100
    else: return salary * 0.02

def calculate_bir_tax(salary, status="Single"):
    """BIR Withholding Tax Table 2024"""
    if status == "Single":
        if salary <= 20833: return 0
        elif salary <= 33333: return (salary - 20833) * 0.15
        elif salary <= 66667: return 1875 + (salary - 33333) * 0.20
        elif salary <= 166667: return 8541.80 + (salary - 66667) * 0.25
        elif salary <= 666667: return 33541.80 + (salary - 166667) * 0.30
        else: return 183541.80 + (salary - 666667) * 0.35
    # Add other statuses (Married, Head of Family) as needed

# =============================================
# STREAMLIT APP
# =============================================

st.set_page_config(page_title="PH Payroll Calculator", layout="wide")
st.title("🇵🇭 AI Payroll Calculator")

uploaded_file = st.file_uploader("Upload Employee Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Convert column names to standard format
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.title()
        
        # =============================================
        # PAYROLL CALCULATIONS
        # =============================================
        try:
            # Basic calculations
            df["Overtime_Pay"] = df["Overtime_Hours"] * (df["Basic_Salary"]/22/8 * 1.25)
            df["Late_Deduction"] = (df["Late_Minutes"]/60) * (df["Basic_Salary"]/22/8)
            
            # Gross Salary
            df["Gross_Salary"] = df["Basic_Salary"] + df["Overtime_Pay"] - df["Late_Deduction"]
            
            # Government Contributions
            df["SSS"] = df["Basic_Salary"].apply(calculate_sss)
            df["PhilHealth"] = df["Basic_Salary"].apply(calculate_philhealth)
            df["PagIBIG"] = df["Basic_Salary"].apply(calculate_pagibig)
            
            # Tax Calculation
            df["Tax"] = df.apply(lambda row: calculate_bir_tax(row["Gross_Salary"], row["Tax_Status"]), axis=1)
            
            # Net Salary
            df["Net_Salary"] = df["Gross_Salary"] - df["SSS"] - df["PhilHealth"] - df["PagIBIG"] - df["Tax"]
            
            # 13th Month Pay
            df["13th_Month_Pay"] = df["Basic_Salary"] / 12
            
            # Display results
            st.success("Payroll computed successfully!")
            st.dataframe(df)
            
            # Export options
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV for Odoo",
                data=csv,
                file_name=f"payroll_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
            
        except KeyError as e:
            st.error(f"Missing required column: {e}")
            st.write("Your Excel must contain these columns:")
            st.write("- Employee_ID, Full_Name, Basic_Salary, Tax_Status")
            st.write("- Overtime_Hours, Late_Minutes (optional)")
            st.write("\nActual columns found:", df.columns.tolist())
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

# =============================================
# SAMPLE TEMPLATE DOWNLOAD
# =============================================

st.sidebar.markdown("### Need a template?")
sample_template = pd.DataFrame({
    "Employee_ID": ["EMP-001", "EMP-002"],
    "Full_Name": ["Juan Dela Cruz", "Maria Santos"],
    "Basic_Salary": [25000, 35000],
    "Tax_Status": ["Single", "Married"],
    "SSS_Number": ["12-3456789-0", "98-7654321-0"],
    "PhilHealth_Number": ["123456789012", "987654321098"],
    "PagIBIG_Number": ["1234-5678-9012", "9876-5432-1098"],
    "Days_Worked": [22, 20],
    "Overtime_Hours": [5, 2],
    "Late_Minutes": [30, 15],
    "Allowances": [1000, 1500]
})

st.sidebar.download_button(
    label="Download Sample Template",
    data=sample_template.to_csv(index=False),
    file_name="ph_payroll_template.csv",
    mime='text/csv'
)
