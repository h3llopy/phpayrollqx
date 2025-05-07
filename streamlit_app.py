import streamlit as st
import pandas as pd
from datetime import datetime
import io

# =============================================
# 2023 GOVERNMENT CONTRIBUTION CALCULATORS
# =============================================

def calculate_sss(basic_salary):
    """Compute SSS contributions (2023 rates)"""
    try:
        basic_salary = float(basic_salary)
        msc_brackets = [
            3250, 3750, 4250, 4750, 5250, 5750, 6250, 6750, 7250, 7750,
            8250, 8750, 9250, 9750, 10250, 10750, 11250, 11750, 12250, 12750,
            13250, 13750, 14250, 14750, 15250, 15750, 16250, 16750, 17250, 17750,
            18250, 18750, 19250, 19750, 20250, 20750, 21250, 21750, 22250, 22750,
            23250, 23750, 24250, 24750, 25000
        ]
        
        msc = min((b for b in msc_brackets if b >= basic_salary), default=25000)
        
        employee_share = round(msc * 0.045, 2)  # 4.5%
        employer_share = round(msc * 0.095, 2)  # 9.5%
        ec = 10.00 if msc <= 15000 else 30.00   # Employees' Compensation
        
        return {
            "employee_share": employee_share,
            "employer_share": employer_share + ec,
            "total": employee_share + employer_share + ec,
            "msc": msc
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0, "msc": 0}

def calculate_philhealth(salary):
    """PhilHealth 2023 contributions (3% total, split 50/50)"""
    try:
        salary = float(salary)
        if salary <= 10000:
            total = 400.00
        elif salary <= 80000:
            total = salary * 0.03
        else:
            total = 2400.00
        share = round(total / 2, 2)
        return {
            "employee_share": share,
            "employer_share": share,
            "total": share * 2
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0}

def calculate_pagibig(salary):
    """Pag-IBIG 2023 contributions"""
    try:
        salary = float(salary)
        employee_share = min(salary * 0.02, 100.00)
        employer_share = 100.00 if salary >= 5000 else salary * 0.02
        return {
            "employee_share": employee_share,
            "employer_share": employer_share,
            "total": employee_share + employer_share
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0}

def calculate_bir_tax(annual_taxable):
    """2023 Unified BIR Withholding Tax Table"""
    try:
        annual_taxable = float(annual_taxable)
        if annual_taxable <= 250000:
            return 0
        elif annual_taxable <= 400000:
            return (annual_taxable - 250000) * 0.15
        elif annual_taxable <= 800000:
            return 22500 + (annual_taxable - 400000) * 0.20
        elif annual_taxable <= 2000000:
            return 102500 + (annual_taxable - 800000) * 0.25
        elif annual_taxable <= 8000000:
            return 402500 + (annual_taxable - 2000000) * 0.30
        else:
            return 2202500 + (annual_taxable - 8000000) * 0.35
    except:
        return 0

# =============================================
# PAYROLL PROCESSOR
# =============================================

def process_payroll(df):
    """Process payroll for all employees"""
    results = []
    
    for _, row in df.iterrows():
        try:
            # Basic info
            basic = float(row.get('Basic Salary', 0))
            allowances = float(row.get('Allowances', 0))
            deps = min(int(row.get('Dependents', 0)), 4)
            
            # Gross pay
            gross = basic + allowances
            
            # Government contributions
            sss = calculate_sss(basic)
            philhealth = calculate_philhealth(gross)
            pagibig = calculate_pagibig(gross)
            
            # Taxable income
            nontaxable = sss['employee_share'] + philhealth['employee_share'] + pagibig['employee_share']
            taxable = max(gross - nontaxable, 0)
            
            # Withholding tax
            annual_taxable = taxable * 12
            deductions = 90000 + (25000 * deps)  # Standard + dependent deductions
            annual_net_taxable = max(annual_taxable - deductions, 0)
            annual_tax = calculate_bir_tax(annual_net_taxable)
            monthly_tax = annual_tax / 12
            
            # Net pay and employer cost
            total_deductions = nontaxable + monthly_tax
            net_pay = gross - total_deductions
            employer_cost = gross + sss['employer_share'] + philhealth['employer_share'] + pagibig['employer_share']
            
            results.append({
                **row.to_dict(),
                'Gross Salary': gross,
                'SSS Employee': sss['employee_share'],
                'SSS Employer': sss['employer_share'],
                'PhilHealth Employee': philhealth['employee_share'],
                'PhilHealth Employer': philhealth['employer_share'],
                'PagIBIG Employee': pagibig['employee_share'],
                'PagIBIG Employer': pagibig['employer_share'],
                'Taxable Income': taxable,
                'Withholding Tax': monthly_tax,
                'Total Deductions': total_deductions,
                'Net Pay': net_pay,
                'Employer Cost': employer_cost
            })
            
        except Exception as e:
            st.error(f"Error processing {row.get('Employee ID')}: {str(e)}")
    
    return pd.DataFrame(results)

# =============================================
# STREAMLIT APP
# =============================================

def generate_template():
    """Create Excel template for payroll"""
    template_data = {
        'Employee ID': ['EMP-001', 'EMP-002'],
        'Full Name': ['Juan Dela Cruz', 'Maria Santos'],
        'Basic Salary': [25000, 35000],
        'Allowances': [5000, 8000],
        'Dependents': [1, 2],
        'Tax Status': ['Single', 'Married']
    }
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Data')
        writer.book.create_sheet('Instructions')
        ws = writer.book['Instructions']
        ws.append(['Required Fields:'])
        ws.append(['- Employee ID', '- Full Name', '- Basic Salary (numeric)'])
        ws.append(['- Allowances (numeric)', '- Dependents (0-4)', '- Tax Status'])
    return output.getvalue()

def main():
    st.set_page_config(page_title="PH Payroll System 2023", layout="wide")
    st.title("🇵🇭 Philippine Payroll Calculator 2023")
    
    # Template download
    with st.expander("📥 Download Excel Template"):
        st.download_button(
            label="Download Payroll Template",
            data=generate_template(),
            file_name="PH_Payroll_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # File upload
    uploaded_file = st.file_uploader("Upload Employee Data (Excel)", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            required_cols = {'Employee ID', 'Full Name', 'Basic Salary'}
            
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                st.error(f"Missing required columns: {', '.join(missing)}")
                return
            
            # Process payroll
            with st.spinner("Processing payroll..."):
                payroll_df = process_payroll(df)
            
            # Display results
            st.success("Payroll processed successfully!")
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Employees", len(payroll_df))
            col2.metric("Total Net Pay", f"₱{payroll_df['Net Pay'].sum():,.2f}")
            col3.metric("Total Employer Cost", f"₱{payroll_df['Employer Cost'].sum():,.2f}")
            
            # Detailed view
            st.dataframe(payroll_df)
            
            # Export options
            csv = payroll_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Payroll Report (CSV)",
                data=csv,
                file_name=f"Payroll_Report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
