import pandas as pd
from datetime import datetime

# =============================================
# 2023 GOVERNMENT CONTRIBUTION CALCULATORS
# =============================================

def calculate_sss(msc):
    """
    Compute SSS contributions (2023 rates)
    MSC Range: ₱3,250 to ₱25,000
    Returns: {employee_share, employer_share, total}
    """
    msc_brackets = [
        3250, 3750, 4250, 4750, 5250, 5750, 6250, 6750, 
        7250, 7750, 8250, 8750, 9250, 9750, 10250, 10750,
        11250, 11750, 12250, 12750, 13250, 13750, 14250,
        14750, 15250, 15750, 16250, 16750, 17250, 17750,
        18250, 18750, 19250, 19750, 20250, 20750, 21250,
        21750, 22250, 22750, 23250, 23750, 24250, 24750, 25000
    ]
    
    msc = min(b for b in msc_brackets if b >= msc)  # Round up to nearest bracket
    
    # Regular Social Security
    regular_ss = msc * 0.045  # 4.5% of MSC
    employer_ss = msc * 0.095  # 9.5% of MSC
    
    # Employees' Compensation
    ec = 10.00 if msc <= 15000 else 30.00
    
    return {
        "employee_share": round(regular_ss, 2),
        "employer_share": round(employer_ss + ec, 2),
        "total": round(regular_ss + employer_ss + ec, 2),
        "msc": msc
    }

def calculate_philhealth(salary):
    """PhilHealth 2023 contributions (3% total, split 50/50)"""
    if salary <= 10000:
        total = 400.00
    elif salary <= 80000:
        total = salary * 0.03  # 3% of salary
    else:
        total = 2400.00
    share = round(total / 2, 2)
    return {
        "employee_share": share,
        "employer_share": share,
        "total": share * 2
    }

def calculate_pagibig(salary):
    """Pag-IBIG 2023 contributions"""
    # Employee share
    employee_share = min(salary * 0.02, 100.00)  # Max ₱100
    
    # Employer share
    employer_share = 100.00 if salary >= 5000 else salary * 0.02
    
    return {
        "employee_share": employee_share,
        "employer_share": employer_share,
        "total": employee_share + employer_share
    }

def calculate_bir_tax(annual_taxable_income):
    """
    2023 Unified BIR Withholding Tax Table
    (No distinction between filing statuses)
    """
    if annual_taxable_income <= 250000:
        return 0
    elif annual_taxable_income <= 400000:
        return (annual_taxable_income - 250000) * 0.15
    elif annual_taxable_income <= 800000:
        return 22500 + (annual_taxable_income - 400000) * 0.20
    elif annual_taxable_income <= 2000000:
        return 102500 + (annual_taxable_income - 800000) * 0.25
    elif annual_taxable_income <= 8000000:
        return 402500 + (annual_taxable_income - 2000000) * 0.30
    else:
        return 2202500 + (annual_taxable_income - 8000000) * 0.35

# =============================================
# CORE PAYROLL PROCESSOR
# =============================================

def process_payroll(employee_data, period):
    """
    Process payroll for multiple employees
    Args:
        employee_data: List of dictionaries with employee info
        period: Payroll period (YYYY-MM)
    Returns:
        DataFrame with complete payroll breakdown
    """
    results = []
    
    for emp in employee_data:
        # Basic info
        emp_id = emp.get('employee_id')
        name = emp.get('full_name')
        basic = emp.get('basic_salary', 0)
        allowances = emp.get('allowances', 0)
        deps = min(emp.get('dependents', 0), 4)  # Max 4 dependents
        
        # Gross salary
        gross = basic + allowances
        
        # Government contributions
        sss = calculate_sss(basic)
        philhealth = calculate_philhealth(gross)
        pagibig = calculate_pagibig(gross)
        
        # Taxable income (after non-taxable benefits)
        nontaxable = sss['employee_share'] + philhealth['employee_share'] + pagibig['employee_share']
        taxable = gross - nontaxable
        
        # Withholding tax (annualized)
        annual_taxable = taxable * 12
        standard_deduction = 90000
        dependent_deduction = 25000 * deps
        annual_taxable_income = max(annual_taxable - standard_deduction - dependent_deduction, 0)
        annual_tax = calculate_bir_tax(annual_taxable_income)
        monthly_tax = annual_tax / 12
        
        # Net pay
        deductions = nontaxable + monthly_tax
        net_pay = gross - deductions
        
        # Employer cost
        employer_cost = gross + sss['employer_share'] + philhealth['employer_share'] + pagibig['employer_share']
        
        results.append({
            'period': period,
            'employee_id': emp_id,
            'full_name': name,
            'basic_salary': basic,
            'allowances': allowances,
            'gross_salary': gross,
            'sss_employee': sss['employee_share'],
            'sss_employer': sss['employer_share'],
            'philhealth_employee': philhealth['employee_share'],
            'philhealth_employer': philhealth['employer_share'],
            'pagibig_employee': pagibig['employee_share'],
            'pagibig_employer': pagibig['employer_share'],
            'taxable_income': taxable,
            'withholding_tax': monthly_tax,
            'total_deductions': deductions,
            'net_pay': net_pay,
            'employer_cost': employer_cost,
            'dependents': deps
        })
    
    return pd.DataFrame(results)

# =============================================
# SAMPLE USAGE
# =============================================

if __name__ == "__main__":
    # Sample employee data
    employees = [
        {
            'employee_id': 'EMP-001',
            'full_name': 'Juan Dela Cruz',
            'basic_salary': 25000,
            'allowances': 5000,
            'dependents': 1
        },
        {
            'employee_id': 'EMP-002',
            'full_name': 'Maria Santos',
            'basic_salary': 35000,
            'allowances': 8000,
            'dependents': 2
        }
    ]
    
    # Process payroll
    payroll_period = datetime.now().strftime('%Y-%m')
    payroll_df = process_payroll(employees, payroll_period)
    
    # Export to CSV
    payroll_df.to_csv(f'payroll_{payroll_period}.csv', index=False)
    
    # Print results
    print(payroll_df[['employee_id', 'full_name', 'gross_salary', 'total_deductions', 'net_pay']])
