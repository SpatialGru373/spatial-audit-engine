import streamlit as st
import pandas as pd
import os
import subprocess

st.set_page_config(page_title="Spatial Audit Engine", page_icon="🌍", layout="centered")

st.title("🌍 Spatial Audit & Site Viability Engine")
st.write("Upload your client site coordinates below to run live OpenStreetMap infrastructure analysis and generate a 100-point MCDA ranking report.")

# Step 1: File Uploader Widget for Client CSV
uploaded_file = st.file_uploader("Upload client_sites.csv", type=["csv"])

if uploaded_file is not None:
    # Save the uploaded file directly into the engine's inputs folder
    input_path = r"C:\Users\HP VICTUS\Downloads\SpatialAuditEngine\inputs\client_sites.csv"
    
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success("Client site data successfully uploaded and synced to engine!")
    
    # Preview the uploaded data
    df = pd.read_csv(input_path)
    st.write("### Target Sites Preview:")
    st.dataframe(df)

    # Step 2: Run Audit Button
    if st.button("🚀 Run Live Spatial Audit"):
        with st.spinner("Connecting to OpenStreetMap via osmnx and computing MCDA scores... Please wait."):
            
            # Execute your existing engine script via command subprocess
            engine_dir = r"C:\Users\HP VICTUS\Downloads\SpatialAuditEngine"
            python_env_path = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
            script_path = os.path.join(engine_dir, "engine.py")
            
            result = subprocess.run(
                [python_env_path, script_path],
                capture_output=True,
                text=True,
                cwd=engine_dir
            )
            
        if result.returncode == 0:
            st.success("Audit successfully computed!")
            
            # Step 3: Display Results
            output_report_path = r"C:\Users\HP VICTUS\Downloads\SpatialAuditEngine\outputs\Spatial_Audit_Executive_Summary.txt"
            if os.path.exists(output_report_path):
                with open(output_report_path, "r") as report_file:
                    report_text = report_file.read()
                    
                st.write("### 📄 Executive Summary Report")
                st.text_area("Generated Output", report_text, height=300)
                
                # Provide a download button for the client report
                st.download_button(
                    label="📥 Download Certified Audit Report (TXT)",
                    data=report_text,
                    file_name="Spatial_Audit_Executive_Summary.txt",
                    mime="text/plain"
                )
        else:
            st.error("Error executing spatial engine script:")
            st.text(result.stderr)