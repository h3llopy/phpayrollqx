import streamlit as st
import pandas as pd
from datetime import datetime
import io

# =============================================
# 2025 GOVERNMENT CONTRIBUTION CALCULATORS
# =============================================

def calculate_sss(basic_salary):
    """Compute SSS contributions (2025 rates: 15% total, 5% employee share)"""
    try:
        basic_salary = float(basic_salary)
        msc = min(max(basic_salary, 5000), 35000)  # Min 5,000, Max 35,000
        
        employee_share = round(msc * 0.05, 2)  # 5%
        employer_share = round(msc * 0.10, 2)  # 10% (includes EC)
        
        return {
            "employee_share": employee_share,
            "employer_share": employer_share,
            "total": employee_share + employer_share,
            "msc": msc
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0, "msc": 0}

def calculate_philhealth(salary):
    """PhilHealth 2025 contributions (5% total, split 50/50, min 500, max 2500)"""
    try:
        salary = float(salary)
        total = salary * 0.05
        total = max(min(total, 2500), 500)  # Min 500, Max 2500
        share = round(total / 2, 2)
        return {
            "employee_share": share,
            "employer_share": share,
            "total": share * 2
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0}

def calculate_pagibig(salary):
    """Pag-IBIG 2025 contributions (2% each, max compensation 10,000)"""
    try:
        salary = float(salary)
        capped_salary = min(salary, 10000)  # Max compensation 10,000
        employee_share = min(capped_salary * 0.02, 200.00)  # Max 200
        employer_share = min(capped_salary * 0.02, 200.00)  # Max 200
        return {
            "employee_share": employee_share,
            "employer_share": employer_share,
            "total": employee_share + employer_share
        }
    except:
        return {"employee_share": 0, "employer_share": 0, "total": 0}

def calculate_bir_tax(annual_taxable):
    """2023 BIR Withholding Tax Table (Note: Adjust for 2025 if rates change)"""
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
    working_days_per_year = 313  # DOLE standard working days per year
    working_days_per_month = working_days_per_year / 12  # 26.08 days per month
    max_monthly_days = 22  # Cap for monthly salary calculation
    
    # Fill NaN values with 0 for numeric columns
    numeric_cols = [
        'basic_salary', 'allowances', 'days_worked',
        'regular_overtime_hours', 'rest_day_overtime_hours',
        'holiday_overtime_hours', 'special_holiday_overtime_hours',
        'late_minutes', 'absent_days', 'leave_with_pay_days', 'loans'
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    for _, row in df.iterrows():
        try:
            # Basic info
            basic = float(row.get('basic_salary', 0))
            allowances = float(row.get('allowances', 0))
            days_worked = min(float(row.get('days_worked', 22)), max_monthly_days)  # Cap at 22
            regular_overtime_hours = float(row.get('regular_overtime_hours', 0))
            rest_day_overtime_hours = float(row.get('rest_day_overtime_hours', 0))
            holiday_overtime_hours = float(row.get('holiday_overtime_hours', 0))
            special_holiday_overtime_hours = float(row.get('special_holiday_overtime_hours', 0))
            late_minutes = float(row.get('late_minutes', 0))
            absent_days = float(row.get('absent_days', 0))
            leave_with_pay_days = float(row.get('leave_with_pay_days', 0))
            loans = float(row.get('loans', 0))
            
            # Calculate daily rate using DOLE standard
            daily_rate = basic / working_days_per_month
            adjusted_basic = basic  # Monthly salary, not scaled by days worked
            
            # Absent deduction
            absent_deduction = daily_rate * absent_days
            
            # Overtime pay calculations
            hourly_rate = daily_rate / 8
            
            # Regular day overtime: 125%
            regular_overtime_rate = hourly_rate * 1.25
            regular_overtime_pay = regular_overtime_rate * regular_overtime_hours
            
            # Rest day overtime: 130% * 130%
            rest_day_overtime_rate = hourly_rate * 1.30 * 1.30
            rest_day_overtime_pay = rest_day_overtime_rate * rest_day_overtime_hours
            
            # Regular holiday overtime: 200% * 130%
            holiday_overtime_rate = hourly_rate * 2.00 * 1.30
            holiday_overtime_pay = holiday_overtime_rate * holiday_overtime_hours
            
            # Special holiday overtime: 130% * 130%
            special_holiday_overtime_rate = hourly_rate * 1.30 * 1.30
            special_holiday_overtime_pay = special_holiday_overtime_rate * special_holiday_overtime_hours
            
            # Total overtime pay
            total_overtime_pay = (regular_overtime_pay + rest_day_overtime_pay +
                                holiday_overtime_pay + special_holiday_overtime_pay)
            
            # Late deduction
            minute_rate = hourly_rate / 60
            late_deduction = minute_rate * late_minutes
            
            # Gross pay (adjusted for absent days, leave with pay does not deduct)
            gross = adjusted_basic + allowances + total_overtime_pay - late_deduction - absent_deduction
            
            # Government contributions
            sss = calculate_sss(basic)
            philhealth = calculate_philhealth(basic)
            pagibig = calculate_pagibig(basic)
            
            # Taxable income
            nontaxable = sss['employee_share'] + philhealth['employee_share'] + pagibig['employee_share']
            taxable = max(gross - nontaxable, 0)
            
            # Withholding tax
            annual_taxable = taxable * 12
            deductions = 90000  # Standard deduction only
            annual_net_taxable = max(annual_taxable - deductions, 0)
            annual_tax = calculate_bir_tax(annual_net_taxable)
            monthly_tax = annual_tax / 12
            
            # Net pay and employer cost
            total_deductions = nontaxable + monthly_tax + loans
            net_pay = gross - total_deductions
            employer_cost = gross + sss['employer_share'] + philhealth['employer_share'] + pagibig['employer_share']
            
            # 13th month pay (monthly equivalent)
            thirteenth_month = basic / 12
            
            results.append({
                **row.to_dict(),
                'Regular Overtime Pay': round(regular_overtime_pay, 2),
                'Rest Day Overtime Pay': round(rest_day_overtime_pay, 2),
                'Holiday Overtime Pay': round(holiday_overtime_pay, 2),
                'Special Holiday Overtime Pay': round(special_holiday_overtime_pay, 2),
                'Total Overtime Pay': round(total_overtime_pay, 2),
                'Late Deduction': round(late_deduction, 2),
                'Absent Deduction': round(absent_deduction, 2),
                'Gross Salary': round(gross, 2),
                'SSS Employee': sss['employee_share'],
                'SSS Employer': sss['employer_share'],
                'PhilHealth Employee': philhealth['employee_share'],
                'PhilHealth Employer': philhealth['employer_share'],
                'PagIBIG Employee': pagibig['employee_share'],
                'PagIBIG Employer': pagibig['employer_share'],
                'Taxable Income': round(taxable, 2),
                'Withholding Tax': round(monthly_tax, 2),
                'Total Deductions': round(total_deductions, 2),
                'Loans': round(loans, 2),
                'Net Pay': round(net_pay, 2),
                'Employer Cost': round(employer_cost, 2),
                '13th Month Pay': round(thirteenth_month, 2)
            })
            
        except Exception as e:
            st.error(f"Error processing {row.get('employee_id')}: {str(e)}")
    
    return pd.DataFrame(results)

# =============================================
# STREAMLIT APP
# =============================================

def generate_template():
    """Create Excel template for payroll"""
    template_data = {
        'employee_id': ['EMP-001', 'EMP-002'],
        'full_name': ['Juan Dela Cruz', 'Maria Santos'],
        'basic_salary': [25000, 35000],
        'allowances': [5000, 8000],
        'days_worked': [22, 22],
        'regular_overtime_hours': [0, 0],
        'rest_day_overtime_hours': [0, 0],
        'holiday_overtime_hours': [0, 0],
        'special_holiday_overtime_hours': [0, 0],
        'late_minutes': [0, 0],
        'absent_days': [0, 0],
        'leave_with_pay_days': [0, 0],
        'loans': [0, 0]
    }
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Data')
        writer.book.create_sheet('Instructions')
        ws = writer.book['Instructions']
        ws.append(['Required Fields:'])
        ws.append(['- employee_id', '- full_name', '- basic_salary (numeric)'])
        ws.append(['- allowances (numeric)', '- days_worked (numeric)'])
        ws.append(['- regular_overtime_hours (numeric)', '- rest_day_overtime_hours (numeric)'])
        ws.append(['- holiday_overtime_hours (numeric)', '- special_holiday_overtime_hours (numeric)'])
        ws.append(['- late_minutes (numeric)', '- absent_days (numeric)'])
        ws.append(['- leave_with_pay_days (numeric)', '- loans (numeric)'])
    return output.getvalue()

def main():
    st.set_page_config(page_title="PH Payroll System 2025", layout="wide")
    st.title("🇵🇭 Philippine Payroll Calculator 2025")
    
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
            required_cols = {'employee_id', 'full_name', 'basic_salary'}
            
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
