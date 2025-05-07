import streamlit as st
import pandas as pd
from datetime import datetime

# =============================================
# 2025 PHILIPPINE CONTRIBUTION CALCULATIONS
# =============================================

def calculate_sss(salary):
    """SSS Contribution Table 2025 (Updated Jan 2025)"""
    # Employee share: 4.5% of salary, Employer: 9.5%
    employee_share = min(salary * 0.045, 1350)  # Max ₱1,350
    employer_share = min(salary * 0.095, 2850)  # Max ₱2,850
    return {"employee": round(employee_share, 2), "employer": round(employer_share, 2)}

def calculate_philhealth(salary):
    """PhilHealth Contribution 2025 (Updated Jan 2025)"""
    # Employee/Employer split: 50/50
    if salary <= 10000:
        total = 400  # Min ₱400
    elif salary <= 80000:
        total = salary * 0.04  # 4% of salary
    else:
        total = 3200  # Max ₱3,200
    share = round(total / 2, 2)
    return {"employee": share, "employer": share}

def calculate_pagibig(salary):
    """Pag-IBIG Contribution 2025 (Updated Jan 2025)"""
    # Employee share: 1-2%, Employer: 2%
    if salary > 5000:
        employee_share = 100  # Fixed ₱100
    else:
        employee_share = salary * 0.01 if salary <= 1500 else salary * 0.02
    employer_share = salary * 0.02 if salary <= 1500 else 100
    return {"employee": employee_share, "employer": employer_share}

def calculate_bir_tax(salary, status="Single"):
    """BIR Withholding Tax Table 2025 (Effective Jan 2025)"""
    if status == "Single":
        if salary <= 25000: return 0
        elif salary <= 40000: return (salary - 25000) * 0.15
        elif salary <= 80000: return 2250 + (salary - 40000) * 0.20
        elif salary <= 180000: return 10250 + (salary - 80000) * 0.25
        elif salary <= 700000: return 35250 + (salary - 180000) * 0.30
        else: return 202250 + (salary - 700000) * 0.35
    # Add other statuses as needed

# =============================================
# STREAMLIT APPLICATION
# =============================================

def main():
    st.set_page_config(page_title="2025 PH Payroll System", layout="wide")
    st.title("🇵🇭 2025 Philippine Payroll Calculator")
    
    with st.expander("ℹ️ Current 2025 Contribution Rates"):
        st.markdown("""
        **SSS (Monthly):**
        - Employee: 4.5% of salary (max ₱1,350)
        - Employer: 9.5% of salary (max ₱2,850)
        
        **PhilHealth:**
        - Total: 4% of salary (min ₱400, max ₱3,200)
        - Split 50/50 between employee/employer
        
        **Pag-IBIG:**
        - Employee: 1-2% (₱100 if salary >₱5,000)
        - Employer: 2% (₱100 if salary >₱1,500)
        """)
    
    uploaded_file = st.file_uploader("Upload Employee Data (Excel)", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Check required columns
            required_cols = {'employee_id', 'full_name', 'basic_salary', 'tax_status'}
            if missing := required_cols - set(df.columns):
                st.error(f"Missing columns: {', '.join(missing)}")
                return
            
            # Calculate contributions
            df['sss'] = df['basic_salary'].apply(lambda x: calculate_sss(x)['employee'])
            df['sss_employer'] = df['basic_salary'].apply(lambda x: calculate_sss(x)['employer'])
            
            df['philhealth'] = df['basic_salary'].apply(lambda x: calculate_philhealth(x)['employee'])
            df['philhealth_employer'] = df['basic_salary'].apply(lambda x: calculate_philhealth(x)['employer'])
            
            df['pagibig'] = df['basic_salary'].apply(lambda x: calculate_pagibig(x)['employee'])
            df['pagibig_employer'] = df['basic_salary'].apply(lambda x: calculate_pagibig(x)['employer'])
            
            # Calculate taxes and net pay
            df['tax'] = df.apply(lambda r: calculate_bir_tax(r['basic_salary'], r['tax_status']), axis=1)
            df['total_deductions'] = df['sss'] + df['philhealth'] + df['pagibig'] + df['tax']
            df['net_pay'] = df['basic_salary'] - df['total_deductions']
            
            # Employer costs
            df['total_employer_cost'] = (df['basic_salary'] + df['sss_employer'] + 
                                       df['philhealth_employer'] + df['pagibig_employer'])
            
            # Display results
            st.success("2025 Payroll Computed Successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Employee Deductions", f"₱{df['total_deductions'].sum():,.2f}")
            with col2:
                st.metric("Total Employer Cost", f"₱{df['total_employer_cost'].sum():,.2f}")
            
            st.dataframe(df.style.format({
                'basic_salary': '₱{:,.2f}',
                'net_pay': '₱{:,.2f}',
                'total_employer_cost': '₱{:,.2f}'
            }))
            
            # Export options
            st.download_button(
                label="Download Full Report (CSV)",
                data=df.to_csv(index=False),
                file_name=f"ph_payroll_2025_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
