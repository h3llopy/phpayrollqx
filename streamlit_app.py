import streamlit as st
import pandas as pd
from datetime import datetime

# =============================================
# 2025 GOVERNMENT CONTRIBUTION CALCULATORS
# =============================================

def calculate_sss(msc):
    """
    Compute SSS contributions based on Monthly Salary Credit (2025)
    MSC Range: ₱5,000 to ₱35,000
    Returns: {employee_share, employer_share, total}
    """
    # Validate MSC range
    msc_brackets = [5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 
                   13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000,
                   21000, 22000, 23000, 24000, 25000, 26000, 27000, 28000,
                   29000, 30000, 31000, 32000, 33000, 34000, 35000]
    
    msc = min(b for b in msc_brackets if b >= msc)  # Round up to nearest bracket
    
    # Regular Social Security
    regular_ss = msc * 0.15  # 15% of MSC
    employer_ss = regular_ss * (2/3)  # Employer covers 2/3
    employee_ss = regular_ss * (1/3)  # Employee covers 1/3
    
    # Employees' Compensation
    ec = 10.00 if msc <= 20000 else 30.00
    
    # Mandatory Provident Fund (for MSC > 20k)
    mpf = max(msc - 20000, 0) * 0.05
    
    return {
        "employee_share": round(employee_ss + (mpf/2), 2),
        "employer_share": round(employer_ss + ec + (mpf/2), 2),
        "total": round(regular_ss + ec + mpf, 2),
        "msc": msc
    }

def calculate_philhealth(salary):
    """PhilHealth 2025 contributions (4% total, split 50/50)"""
    if salary <= 10000:
        total = 400.00
    elif salary <= 80000:
        total = salary * 0.04
    else:
        total = 3200.00
    share = round(total / 2, 2)
    return {
        "employee_share": share,
        "employer_share": share,
        "total": share * 2
    }

def calculate_pagibig(salary):
    """Pag-IBIG 2025 contributions"""
    # Employee share
    if salary <= 1500:
        employee_share = salary * 0.01
    else:
        employee_share = min(salary * 0.02, 100.00)
    
    # Employer share
    if salary <= 1500:
        employer_share = salary * 0.02
    else:
        employer_share = 100.00
    
    return {
        "employee_share": employee_share,
        "employer_share": employer_share,
        "total": employee_share + employer_share
    }

def calculate_bir_tax(salary, status="Single"):
    """BIR Withholding Tax Table 2025"""
    if status == "Single":
        if salary <= 25000: return 0
        elif salary <= 40000: return (salary - 25000) * 0.15
        elif salary <= 80000: return 2250 + (salary - 40000) * 0.20
        elif salary <= 180000: return 10250 + (salary - 80000) * 0.25
        elif salary <= 700000: return 35250 + (salary - 180000) * 0.30
        else: return 202250 + (salary - 700000) * 0.35
    # Add other statuses as needed

# =============================================
# STREAMLIT PAYROLL APPLICATION
# =============================================

def main():
    st.set_page_config(page_title="2025 PH Payroll System", layout="wide")
    st.title("🇵🇭 2025 Philippine Payroll Calculator")
    
    # Contribution rate reference
    with st.expander("📌 2025 Contribution Rates"):
        st.markdown("""
        **SSS (Based on MSC):**
        - Employee: 1/3 of 15% MSC + MPF (if applicable)
        - Employer: 2/3 of 15% MSC + EC (P10/P30) + MPF
        
        **PhilHealth:**
        - Total: 4% of salary (min ₱400, max ₱3,200)
        - Split 50/50 between employee/employer
        
        **Pag-IBIG:**
        - Employee: 1% (≤₱1,500) or 2% (max ₱100)
        - Employer: 2% (≤₱1,500) or ₱100
        """)
    
    uploaded_file = st.file_uploader("📤 Upload Employee Data (Excel)", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Check required columns
            required_cols = {'employee_id', 'full_name', 'basic_salary', 'tax_status'}
            if missing := required_cols - set(df.columns):
                st.error(f"❌ Missing required columns: {', '.join(missing)}")
                st.write("ℹ️ Available columns:", df.columns.tolist())
                return
            
            # Calculate payroll components
            results = []
            for _, row in df.iterrows():
                salary = row['basic_salary']
                
                # Get contributions
                sss = calculate_sss(salary)
                philhealth = calculate_philhealth(salary)
                pagibig = calculate_pagibig(salary)
                tax = calculate_bir_tax(salary, row['tax_status'])
                
                # Compute totals
                employee_deductions = sss['employee_share'] + philhealth['employee_share'] + pagibig['employee_share'] + tax
                employer_cost = salary + sss['employer_share'] + philhealth['employer_share'] + pagibig['employer_share']
                
                results.append({
                    **row.to_dict(),
                    **{'sss_employee': sss['employee_share'], 'sss_employer': sss['employer_share'], 'sss_msc': sss['msc']},
                    **{'philhealth_employee': philhealth['employee_share'], 'philhealth_employer': philhealth['employer_share']},
                    **{'pagibig_employee': pagibig['employee_share'], 'pagibig_employer': pagibig['employer_share']},
                    'tax': tax,
                    'net_pay': salary - employee_deductions,
                    'employer_cost': employer_cost
                })
            
            # Create results dataframe
            results_df = pd.DataFrame(results)
            
            # Display results
            st.success("✅ Payroll computed successfully!")
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Employee Deductions", f"₱{results_df['net_pay'].sum() - results_df['basic_salary'].sum():,.2f}")
            with col2:
                st.metric("Total Employer Costs", f"₱{results_df['employer_cost'].sum():,.2f}")
            with col3:
                st.metric("Average Net Pay", f"₱{results_df['net_pay'].mean():,.2f}")
            
            # Detailed view
            st.dataframe(results_df.style.format({
                'basic_salary': '₱{:,.2f}',
                'net_pay': '₱{:,.2f}',
                'employer_cost': '₱{:,.2f}'
            }))
            
            # Export options
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download Full Payroll Data (CSV)",
                data=csv,
                file_name=f"ph_payroll_2025_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
            
        except Exception as e:
            st.error(f"⚠️ Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
