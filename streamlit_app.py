import streamlit as st
import pandas as pd

# --- STREAMLIT UI ---
st.title("🇵🇭 AI Payroll Calculator")
uploaded_file = st.file_uploader("Upload Employee Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)  # Read Excel
    st.write("### Raw Data Preview")
    st.write(df.head())

    # --- DEMO CALCULATION: 13th Month Pay ---
    df["13th Month Pay"] = df["Basic Salary"] / 12
    
    st.write("### Payroll Results")
    st.write(df)  # Show computed payroll

    # --- EXPORT TO CSV (For Odoo) ---
    st.download_button(
        label="Download Payroll CSV",
        data=df.to_csv(index=False),
        file_name="payroll_results.csv"
    )
