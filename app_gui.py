import streamlit as st
import pandas as pd
import os
import tempfile # To handle temporary file saving for the chain
import io         # To capture print statements
import contextlib # To capture print statements

# --- Core Logic Import ---
# Import the pre-built chain from your run_orchestration script
# IMPORTANT: Make sure run_orchestration.py uses 'if __name__ == "__main__":'
#            to protect its command-line execution parts from running on import.
try:
    from run_orchestration import chain as analysis_chain
    # We might need the output file name defined in the logic/run script
    # If it's fixed, define it here, otherwise import if needed.
    # For now, assume the output name from the logic.
    DEFAULT_OUTPUT_FILE = "flagged_repairs_detailed.txt" # Or .csv if you changed it
except ImportError as e:
    st.error(f"Error importing chain from run_orchestration.py: {e}")
    st.error("Ensure run_orchestration.py is in the same directory and has the chain defined.")
    st.stop() # Stop the app if we can't import the core component
except Exception as e:
    st.error(f"An unexpected error occurred during import: {e}")
    st.stop()

# --- Streamlit App Definition ---

st.set_page_config(page_title="SAP Repair Analyzer", layout="centered")
st.title("🔎 SAP Repair Variance Analyzer")

st.write("""
Upload your SAP export Excel file below. The tool will analyze it
using the predefined logic (checking for exactly one of each: 251, 161, 252 per repair)
and generate a report file listing any anomalies found.
""")

uploaded_file = st.file_uploader("Choose an Excel file (.xlsx)", type="xlsx")

if uploaded_file is not None:
    st.info(f"File uploaded: **{uploaded_file.name}**")

    if st.button("Run Analysis"):
        # --- Processing ---
        # The current chain expects a file PATH. Streamlit provides an in-memory
        # file object. We need to save it temporarily to disk for the chain.
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)

        try:
            # Save the uploaded file bytes to the temporary path
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.write(f"🔄 Copied uploaded file to temporary location: {temp_file_path}")

            # Capture print statements from the chain's execution
            final_result = None

            with st.spinner('Analyzing file... Please wait.'):
                    try:
                        # Invoke the LangChain chain with the temporary file path
                        final_result = analysis_chain.invoke(temp_file_path)

                    except Exception as chain_error:
                        st.error(f"An error occurred during chain execution:")
                        st.exception(chain_error) # Show detailed traceback in the app
                        final_result = None # Ensure we know it failed

            if final_result:
                 st.success(f"Analysis Complete! Status: {final_result}")
                 # Try to determine the actual output file name (it might be defined in results_outputter)
                 # For simplicity, using the default/expected name for now.
                 st.info(f"Results file should be generated as **{DEFAULT_OUTPUT_FILE}** in the same directory where you ran the Streamlit app.")
                 st.subheader("Generated Report Content:")
                 output_file_path = DEFAULT_OUTPUT_FILE # Use the defined path

                 try:
                     # Attempt to read the content of the generated file
                     with open(output_file_path, 'r', encoding='utf-8') as f: # Added encoding
                         report_content = f.read()

                     # Display the content in a text area
                     st.text_area("Report:", value=report_content, height=300, disabled=True)

                 except FileNotFoundError:
                     st.warning(f"Could not automatically display report content. The file '{output_file_path}' was not found where expected.")
                 except Exception as read_error:
                     st.error(f"An error occurred while trying to read '{output_file_path}':")
                     st.exception(read_error)
                 # --- NEW BLOCK END ---

            else:
                 st.warning("Analysis did not complete successfully or returned no status.")

        except Exception as e:
            st.error("An unexpected error occurred during file handling or analysis setup:")
            st.exception(e)
        finally:
            # Clean up the temporary file and directory
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                st.write(f"🧹 Cleaned up temporary file: {temp_file_path}")
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir) # Will fail if dir not empty, but usually is
                except OSError:
                    st.warning(f"Could not remove temporary directory {temp_dir}. It might contain unexpected files.")


else:
    st.info("Please upload a file to begin analysis.")

st.markdown("---")
st.markdown("Developed with LangChain & Streamlit")