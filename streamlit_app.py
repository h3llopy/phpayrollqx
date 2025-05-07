import streamlit as st
import pandas as pd
from datetime import datetime

# =============================================
# PHILIPPINE PAYROLL CALCULATIONS (UPDATED 2024)
# =============================================

def calculate_sss(salary):
    """SSS Contribution Table 2024 (Updated Rates)"""
    brackets = [
        (4250, 180), (4750, 202.50), (5250, 225), (5750, 247.50),
        (6250, 270), (6750, 292.50), (7250, 315), (7750, 337.50),
        (8250, 360), (8750, 382.50), (9250, 405), (9750, 427.50),
        (10250, 450), (10750, 472.50), (11250, 495), (11750, 517.50),
        (12250, 540), (12750, 562.50), (13250, 585), (13750, 607.50),
        (14250, 630), (14750, 652.50), (15250, 675), (15750, 697.50),
        (16250, 720), (16750, 742.50), (17250, 765), (17750, 787.50),
        (18250, 810), (18750, 832.50), (19250, 855), (19750, 877.50),
        (20250, 900), (20750, 922.50), (21250, 945), (21750, 967.50),
        (22250, 990), (22750, 1012.50), (23250, 1035), (23750, 1057.50),
        (24250, 1080), (24750, 1102.50), (float('inf'), 1125)
    ]
    for bracket, contribution in brackets:
        if salary <= bracket:
            return contribution

def calculate_philhealth(salary):
    """PhilHealth Contribution 2024 (4% of monthly salary)"""
    return min(max(salary * 0.04, 400), 3200)  # Min 400, Max 3200

def calculate_pagibig(salary):
    """Pag-IBIG Contribution 2024"""
    return 100 if salary > 5000 else salary * 0.02

def calculate_bir_tax(salary, status="Single"):
    """BIR Withholding Tax Table 2024"""
    if status == "Single":
        if salary <= 20833: return 0
        elif salary <= 33333: return (salary - 20833) * 0.15
        elif salary <= 66667: return 1875 + (salary - 33333) * 0.20
        elif salary <= 166667: return 8541.80 + (salary - 66667) * 0.25
        elif salary <= 666667: return 33541.80 + (salary - 166667) * 0.30
        else: return 183541.80 + (salary - 666667) * 0.35
    # Add other statuses if needed

# =============================================
# STREAMLIT APP WITH ERROR HANDLING
# =============================================

def main():
    st.set_page_config(page_title="PH Payroll System", layout="wide")
    st.title("🇵🇭 Philippine Payroll Calculator")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Employee Data (Excel)", type=["xlsx"])
    
    if uploaded_file:
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Check required columns
            required_cols = {'employee_id', 'full_name', 'basic_salary', 'tax_status'}
            missing_cols = required_cols - set(df.columns)
            
            if missing_cols:
                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                st.write("Available columns:", df.columns.tolist())
                return
            
            # Calculate payroll
            try:
                # Basic calculations
                df['overtime_pay'] = df.get('overtime_hours', 0) * (df['basic_salary']/22/8 * 1.25)
                df['late_deduction'] = (df.get('late_minutes', 0)/60) * (df['basic_salary']/22/8)
                
                # Gross salary
                df['gross_salary'] = df['basic_salary'] + df['overtime_pay'] - df['late_deduction']
                
                # Government contributions
                df['sss'] = df['basic_salary'].apply(calculate_sss)
                df['philhealth'] = df['basic_salary'].apply(calculate_philhealth)
                df['pagibig'] = df['basic_salary'].apply(calculate_pagibig)
                
                # Tax calculation
                df['tax'] = df.apply(
                    lambda row: calculate_bir_tax(row['gross_salary'], row['tax_status']), 
                    axis=1
                )
                
                # Net salary
                df['net_salary'] = df['gross_salary'] - df['sss'] - df['philhealth'] - df['pagibig'] - df['tax']
                
                # 13th month pay
                df['13th_month_pay'] = df['basic_salary'] / 12
                
                # Display results
                st.success("Payroll computed successfully!")
                st.dataframe(df)
                
                # Export to CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Payroll Data (CSV)",
                    data=csv,
                    file_name=f"ph_payroll_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )
                
            except Exception as calc_error:
                st.error(f"Calculation error: {str(calc_error)}")
                
        except Exception as file_error:
            st.error(f"Error reading file: {str(file_error)}")

    # Sample template download
    with st.expander("Need a template?"):
        sample_data = {
            "employee_id": ["EMP-001", "EMP-002"],
            "full_name": ["Juan Dela Cruz", "Maria Santos"],
            "basic_salary": [25000, 35000],
            "tax_status": ["Single", "Married"],
            "sss_number": ["12-3456789-0", "98-7654321-0"],
            "philhealth_number": ["123456789012", "987654321098"],
            "pagibig_number": ["1234-5678-9012", "9876-5432-1098"],
            "days_worked": [22, 20],
            "overtime_hours": [5, 2],
            "late_minutes": [30, 15],
            "allowances": [1000, 1500]
        }
        sample_df = pd.DataFrame(sample_data)
        st.download_button(
            label="Download Sample Template",
            data=sample_df.to_csv(index=False),
            file_name="ph_payroll_template.csv",
            mime='text/csv'
        )

if __name__ == "__main__":
    main()
