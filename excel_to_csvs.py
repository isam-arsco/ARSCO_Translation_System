import pandas as pd
import os

EXCEL_FILE = "input_data.xlsx"
OUTPUT_DIR = "csv"  # Folder name

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

excel_data = pd.ExcelFile(EXCEL_FILE)

for sheet_name in excel_data.sheet_names:
    df = excel_data.parse(sheet_name)
    csv_filename = os.path.join(OUTPUT_DIR, f"{sheet_name}.csv")
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"Saved '{sheet_name}' to '{csv_filename}'")

print(f"\nCSV files generated in the '{OUTPUT_DIR}' folder.")