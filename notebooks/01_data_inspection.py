from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

csv_files = sorted(RAW_DIR.glob("*.csv"))

print(f"Found {len(csv_files)} CSV files:\n")

for file in csv_files:
    print("=" * 80)
    print(f"File: {file.name}")
    
    try:
        df = pd.read_csv(file)
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")
        print("Column names:")
        print(list(df.columns))
        print("\nFirst 3 rows:")
        print(df.head(3))
    except Exception as e:
        print(f"Error reading file: {e}")