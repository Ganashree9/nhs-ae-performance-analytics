
from pathlib import Path
import pandas as pd

# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

CLEANED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = CLEANED_DIR / "cleaned_ae_performance.csv"

# ============================================================
# 2. LOAD RAW NHS CSV FILES
# ============================================================

csv_files = sorted(RAW_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in: {RAW_DIR}"
    )

print(f"Found {len(csv_files)} CSV files.")

all_data = []

for file in csv_files:
    print(f"Reading: {file.name}")

    df = pd.read_csv(file, low_memory=False)

    # Remove unnamed columns and unnecessary column "a"
    df = df.loc[
        :,
        ~df.columns.astype(str).str.startswith("Unnamed")
    ]

    if "a" in df.columns:
        df = df.drop(columns=["a"])

    # Track the original source file
    df["source_file"] = file.name

    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

print(f"Initial rows: {len(combined)}")

# ============================================================
# 3. STANDARDISE COLUMN NAMES
# ============================================================

combined.columns = combined.columns.astype(str).str.strip()

column_mapping = {
    "Period": "period",
    "Org Code": "org_code",
    "Parent Org": "parent_org",
    "Org name": "org_name",

    "A&E attendances Type 1": "ae_attendances_type_1",
    "A&E attendances Type 2": "ae_attendances_type_2",
    "A&E attendances Other A&E Department": "ae_attendances_other",

    "A&E attendances Booked Appointments Type 1": "booked_ae_type_1",
    "A&E attendances Booked Appointments Type 2": "booked_ae_type_2",
    "A&E attendances Booked Appointments Other Department": "booked_ae_other",

    "Attendances over 4hrs Type 1": "over_4hrs_type_1",
    "Attendances over 4hrs Type 2": "over_4hrs_type_2",
    "Attendances over 4hrs Other Department": "over_4hrs_other",

    "Attendances over 4hrs Booked Appointments Type 1": "over_4hrs_booked_type_1",
    "Attendances over 4hrs Booked Appointments Type 2": "over_4hrs_booked_type_2",
    "Attendances over 4hrs Booked Appointments Other Department": "over_4hrs_booked_other",

    "Patients who have waited 4-12 hs from DTA to admission": "dta_4_12hr_waits",
    "Patients who have waited 12+ hrs from DTA to admission": "dta_12hr_plus_waits",

    "Emergency admissions via A&E - Type 1": "emergency_admissions_type_1",
    "Emergency admissions via A&E - Type 2": "emergency_admissions_type_2",
    "Emergency admissions via A&E - Other A&E department": "emergency_admissions_other_ae",
    "Other emergency admissions": "other_emergency_admissions"
}

combined = combined.rename(columns=column_mapping)

# ============================================================
# 4. VALIDATE REQUIRED COLUMNS
# ============================================================

numeric_cols = [
    "ae_attendances_type_1",
    "ae_attendances_type_2",
    "ae_attendances_other",
    "booked_ae_type_1",
    "booked_ae_type_2",
    "booked_ae_other",

    "over_4hrs_type_1",
    "over_4hrs_type_2",
    "over_4hrs_other",
    "over_4hrs_booked_type_1",
    "over_4hrs_booked_type_2",
    "over_4hrs_booked_other",

    "dta_4_12hr_waits",
    "dta_12hr_plus_waits",

    "emergency_admissions_type_1",
    "emergency_admissions_type_2",
    "emergency_admissions_other_ae",
    "other_emergency_admissions"
]

required_cols = [
    "period",
    "org_code",
    "org_name",
] + numeric_cols

missing_cols = [
    col for col in required_cols
    if col not in combined.columns
]

if missing_cols:
    raise ValueError(
        f"Required columns missing: {missing_cols}"
    )

print("Required column validation passed.")

# ============================================================
# 5. REMOVE AGGREGATE TOTAL ROWS
# ============================================================

combined["org_name_clean"] = (
    combined["org_name"]
    .astype("string")
    .str.strip()
    .str.upper()
)

combined["period_clean"] = (
    combined["period"]
    .astype("string")
    .str.strip()
    .str.upper()
)

initial_rows = len(combined)

combined = combined[
    (combined["org_name_clean"] != "TOTAL")
    & (combined["period_clean"] != "TOTAL")
].copy()

combined = combined.drop(
    columns=["org_name_clean", "period_clean"]
)

print(
    f"Aggregate rows removed: "
    f"{initial_rows - len(combined)}"
)

# ============================================================
# 6. REMOVE EXACT DUPLICATE RECORDS
# ============================================================

# Exclude source_file so identical records across source
# files can be detected. Review duplicates before removal
# if your source files contain legitimate repeated records.

duplicate_cols = [
    col for col in combined.columns
    if col != "source_file"
]

duplicate_count = combined.duplicated(
    subset=duplicate_cols
).sum()

print(f"Exact duplicate records found: {duplicate_count}")

if duplicate_count:
    print(
        "WARNING: Duplicate records were detected. "
        "Review whether they are genuine duplicates."
    )

# Do not automatically delete duplicates without verifying
# that they represent the same provider and reporting period.

# ============================================================
# 7. CONVERT NUMERIC COLUMNS
# ============================================================

for col in numeric_cols:
    combined[col] = pd.to_numeric(
        combined[col],
        errors="coerce"
    )

missing_counts = combined[numeric_cols].isna().sum()
missing_counts = missing_counts[missing_counts > 0]

if not missing_counts.empty:
    print("\nMissing or invalid numeric values:")
    print(missing_counts.to_string())
    print(
        "\nWARNING: Missing values are preserved as NaN. "
        "Check source data before deciding how to handle them."
    )
else:
    print("Numeric validation passed: no missing values.")

negative_counts = (
    combined[numeric_cols] < 0
).sum()

negative_counts = negative_counts[negative_counts > 0]

if not negative_counts.empty:
    print("\nWARNING: Negative counts detected:")
    print(negative_counts.to_string())

# ============================================================
# 8. CALCULATE A&E KPIs
# ============================================================

attendance_cols = [
    "ae_attendances_type_1",
    "ae_attendances_type_2",
    "ae_attendances_other",
    "booked_ae_type_1",
    "booked_ae_type_2",
    "booked_ae_other"
]

over_4hrs_cols = [
    "over_4hrs_type_1",
    "over_4hrs_type_2",
    "over_4hrs_other",
    "over_4hrs_booked_type_1",
    "over_4hrs_booked_type_2",
    "over_4hrs_booked_other"
]

admission_cols = [
    "emergency_admissions_type_1",
    "emergency_admissions_type_2",
    "emergency_admissions_other_ae",
    "other_emergency_admissions"
]

# min_count requires every component to be present.
# This prevents missing counts being silently treated as 0.

combined["total_ae_attendances"] = (
    combined[attendance_cols].sum(
        axis=1,
        min_count=len(attendance_cols)
    )
)

combined["total_over_4hrs"] = (
    combined[over_4hrs_cols].sum(
        axis=1,
        min_count=len(over_4hrs_cols)
    )
)

combined["total_emergency_admissions"] = (
    combined[admission_cols].sum(
        axis=1,
        min_count=len(admission_cols)
    )
)

# These KPI definitions follow the original project.
# Verify category definitions against the NHS source
# documentation before interpreting the results.

valid_denominator = (
    combined["total_ae_attendances"]
    .where(combined["total_ae_attendances"] > 0)
)

combined["over_4hrs_rate"] = (
    combined["total_over_4hrs"] / valid_denominator
)

combined["admission_rate"] = (
    combined["total_emergency_admissions"]
    / valid_denominator
)

combined["over_4hrs_rate_pct"] = (
    combined["over_4hrs_rate"] * 100
).round(2)

combined["admission_rate_pct"] = (
    combined["admission_rate"] * 100
).round(2)

# ============================================================
# 9. CREATE REPORTING MONTH
# ============================================================

combined["reporting_month"] = (
    combined["period"]
    .astype("string")
    .str.strip()
    .str.replace(
        r"^MSitAE-",
        "",
        regex=True,
        case=False
    )
    .str.title()
)

# ============================================================
# 10. CREATE PERFORMANCE PRESSURE CATEGORIES
# ============================================================

# These are custom project thresholds, not official
# NHS performance classifications.

def classify_pressure(rate):
    if pd.isna(rate):
        return "Unknown"
    if rate >= 30:
        return "High Pressure"
    if rate >= 15:
        return "Moderate Pressure"
    return "Lower Pressure"


combined["performance_risk"] = (
    combined["over_4hrs_rate_pct"]
    .apply(classify_pressure)
)

# ============================================================
# 11. FINAL DATA QUALITY CHECKS
# ============================================================

print("\nData Quality Summary")
print("-" * 40)

print(f"Total rows: {len(combined)}")
print(f"Total columns: {len(combined.columns)}")

print(
    "Unique organisations: "
    f"{combined['org_code'].nunique()}"
)

print(
    "Unique reporting periods: "
    f"{combined['period'].nunique()}"
)

print(
    "Rows with missing attendance totals: "
    f"{combined['total_ae_attendances'].isna().sum()}"
)

print(
    "Rows with zero attendance totals: "
    f"{combined['total_ae_attendances'].eq(0).sum()}"
)

print(
    "Rows with unavailable 4-hour rates: "
    f"{combined['over_4hrs_rate_pct'].isna().sum()}"
)

# ============================================================
# 12. EXPORT CLEANED DATASET
# ============================================================

combined.to_csv(OUTPUT_FILE, index=False)

print("\nCleaning complete.")
print(f"Saved cleaned file to: {OUTPUT_FILE}")

# ============================================================
# 13. DISPLAY DATA PREVIEW
# ============================================================

preview_cols = [
    "reporting_month",
    "org_code",
    "org_name",
    "total_ae_attendances",
    "total_over_4hrs",
    "over_4hrs_rate_pct",
    "dta_12hr_plus_waits",
    "total_emergency_admissions",
    "performance_risk"
]

print("\nCleaned Dataset Preview:")
print(combined[preview_cols].head(10).to_string(index=False))
