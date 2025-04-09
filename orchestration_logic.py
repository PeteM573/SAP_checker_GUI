import pandas as pd
import os
from collections import Counter 

def load_sap_data(excel_file_path: str) -> pd.DataFrame:
    """
    Loads data from the specified Excel file path into a pandas DataFrame.
    Assumes the relevant data is on the first sheet.
    """
    try:
        df = pd.read_excel(excel_file_path)
        print(f"Successfully loaded data from {excel_file_path}")
        # Optional: Add basic validation (e.g., check for required columns)
        required_cols = ['Repair Number', 'Movement Code']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Excel file missing required columns: {required_cols}")
        print("Required columns found.")
        return df
    except FileNotFoundError:
        print(f"Error: File not found at {excel_file_path}")
        # In a real app, you might raise the error or return None/empty DataFrame
        # For the sprint, printing and returning an empty DF might be okay to avoid stopping flow
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred while loading the Excel file: {e}")
        return pd.DataFrame()
        
def find_anomalous_repairs(data: pd.DataFrame) -> list[dict]:
    """
    Identifies and categorizes anomalies for Repair Numbers.
    Checks for exactly one of each movement code (251, 161, 252) and total count of 3.
    Provides structured details about anomalies.

    Args:
        data: Pandas DataFrame with 'Repair Number' and 'Movement Code' columns.

    Returns:
        A list of dictionaries detailing anomalous repairs including missing, extra,
        and unexpected codes. Returns empty list if no anomalies or invalid data.
    """
    if data.empty or 'Repair Number' not in data.columns or 'Movement Code' not in data.columns:
        print("Warning: Input data is empty or missing required columns. Cannot process.")
        return []

    anomalous_details = []
    required_codes = {251, 161, 252} # Define the expected codes

    grouped = data.groupby('Repair Number')
    print(f"--- Analyzing {len(grouped)} unique Repair Numbers ---")

    for repair_num, group_df in grouped:
        movement_codes = group_df['Movement Code'].tolist()
        total_count = len(movement_codes)
        code_counts = Counter(movement_codes)

        # Check for perfection first (avoids unnecessary calculation)
        is_perfect = (
            total_count == 3 and
            all(code_counts.get(code, 0) == 1 for code in required_codes) and
            all(code in required_codes for code in code_counts) # No unexpected codes
        )

        if is_perfect:
            continue # Skip perfect repairs

        # --- If not perfect, calculate specific deviations ---
        missing_required = sorted([code for code in required_codes if code_counts.get(code, 0) == 0])
        extra_required = sorted([code for code in required_codes if code_counts.get(code, 0) > 1])
        unexpected_found = sorted([code for code in code_counts if code not in required_codes])

        # We always add the anomaly if it wasn't perfect
        anomaly_info = {
            "Repair Number": repair_num,
            "Movement Codes Found": dict(code_counts), # Keep raw counts
            "Missing Codes": missing_required,
            "Extra Codes": extra_required, # Required codes with count > 1
            "Unexpected Codes": unexpected_found,
            "Total Count": total_count
        }
        anomalous_details.append(anomaly_info)

    print(f"Found {len(anomalous_details)} anomalous repair numbers with details.")
    return anomalous_details

def write_results_to_file(detailed_anomalies: list[dict], output_file_path: str = "flagged_repairs_detailed.txt") -> str:
    """
    Writes a concise summary of anomalies to a text file.
    Handles the case where the list is empty.
    Returns a status message.
    """
    try:
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
             os.makedirs(output_dir)

        # Optional: Sort by Repair Number
        detailed_anomalies.sort(key=lambda x: x.get('Repair Number', ''))

        with open(output_file_path, 'w') as f:
            if not detailed_anomalies:
                f.write("No anomalous repair numbers found based on the detailed criteria.\n")
                status_message = f"No anomalies found. Results summary written to {output_file_path}"
            else:
                f.write("Concise Anomaly Report:\n")
                f.write("="*60 + "\n")

                for anomaly in detailed_anomalies:
                    parts = [f"Repair: {anomaly.get('Repair Number', 'N/A')}"] # Start with Repair Number
                    missing = anomaly.get("Missing Codes", [])
                    extra = anomaly.get("Extra Codes", [])
                    unexpected = anomaly.get("Unexpected Codes", [])
                    total_count = anomaly.get("Total Count", -1)

                    # Build the reason string concisely
                    if missing:
                        parts.append(f"Missing: {', '.join(map(str, missing))}")
                    if extra:
                        # Mention the specific codes that have extra counts
                        extra_details = [f"{code}({anomaly['Movement Codes Found'].get(code,'?')})" for code in extra]
                        parts.append(f"Extra Count(s): {', '.join(extra_details)}")
                    if unexpected:
                        unexpected_details = [f"{code}({anomaly['Movement Codes Found'].get(code,'?')})" for code in unexpected]
                        parts.append(f"Unexpected Code(s): {', '.join(unexpected_details)}")

                    # Add total count only if it deviates and wasn't explained by above
                    # Or simply always add it if different from 3 for clarity
                    #if total_count != 3:
                    #    parts.append(f"(Total: {total_count})")

                    output_string = ", ".join(parts) # Join all parts with a comma and space
                    f.write(output_string + "\n")

                f.write("="*60 + "\n")
                f.write(f"\nTotal flagged: {len(detailed_anomalies)}\n")
                status_message = f"Found {len(detailed_anomalies)} anomalies. Concise report written to {output_file_path}"

        print(status_message)
        return status_message
    except Exception as e:
        error_message = f"Error writing concise results to file {output_file_path}: {e}"
        print(error_message)
        return error_message


# --- Update the test section ---
if __name__ == "__main__":
    test_file = 'synthetic_sap_data.xlsx'
    print("--- Testing Data Loading ---")
    data = load_sap_data(test_file)
    flagged_list = [] # Initialize empty list

    if not data.empty:
        print("\n--- Data Loaded (First 5 Rows): ---")
        print(data.head())
        print("\n--- Testing Anomaly Detection ---")
        flagged_list = find_anomalous_repairs(data)
        print("\n--- Flagged Repair Numbers (from function): ---")
        print(flagged_list)
        print("\n--- Testing Output Writing ---")
        output_message = write_results_to_file(flagged_list, "test_output.txt") # Use a test filename
        print(f"Output function returned: {output_message}")
        # Simple check against our example ground truth
        expected_anomalies = ['R100024', 'R100058', 'R100327'] # Based on example data
        # Sort both lists for consistent comparison
        flagged_list.sort()
        expected_anomalies.sort()
        if flagged_list == expected_anomalies:
             print("\nSUCCESS: Output matches expected anomalies for the example data!")
        else:
             print(f"\nMISMATCH: Output was {flagged_list}, expected {expected_anomalies}")