from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = CLEANED_DIR / "cleaned_ae_performance.csv"

csv_files = sorted(RAW_DIR.glob("*.csv"))

all_data = []

for file in csv_files:
    print(f"Reading: {file.name}")
    df = pd.read_csv(file)

    # Remove empty/junk columns such as Unnamed columns
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    if "a" in df.columns:
        df = df.drop(columns=["a"])

    df["source_file"] = file.name
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

# Rename columns to cleaner names
combined = combined.rename(columns={
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
})

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

for col in numeric_cols:
    combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0)

# Create useful analysis columns
combined["total_ae_attendances"] = (
    combined["ae_attendances_type_1"]
    + combined["ae_attendances_type_2"]
    + combined["ae_attendances_other"]
    + combined["booked_ae_type_1"]
    + combined["booked_ae_type_2"]
    + combined["booked_ae_other"]
)

combined["total_over_4hrs"] = (
    combined["over_4hrs_type_1"]
    + combined["over_4hrs_type_2"]
    + combined["over_4hrs_other"]
    + combined["over_4hrs_booked_type_1"]
    + combined["over_4hrs_booked_type_2"]
    + combined["over_4hrs_booked_other"]
)

combined["total_emergency_admissions"] = (
    combined["emergency_admissions_type_1"]
    + combined["emergency_admissions_type_2"]
    + combined["emergency_admissions_other_ae"]
    + combined["other_emergency_admissions"]
)

combined["over_4hrs_rate"] = (
    combined["total_over_4hrs"] / combined["total_ae_attendances"]
).replace([float("inf"), -float("inf")], 0).fillna(0)

combined["admission_rate"] = (
    combined["total_emergency_admissions"] / combined["total_ae_attendances"]
).replace([float("inf"), -float("inf")], 0).fillna(0)

# Convert rates to percentages
combined["over_4hrs_rate_pct"] = (combined["over_4hrs_rate"] * 100).round(2)
combined["admission_rate_pct"] = (combined["admission_rate"] * 100).round(2)

# Create month field from period text
combined["reporting_month"] = (
    combined["period"]
    .astype(str)
    .str.replace("MSitAE-", "", regex=False)
    .str.title()
)

# Simple performance flag
combined["performance_risk"] = combined["over_4hrs_rate_pct"].apply(
    lambda x: "High Pressure" if x >= 30 else ("Moderate Pressure" if x >= 15 else "Lower Pressure")
)

# Save cleaned dataset
combined.to_csv(OUTPUT_FILE, index=False)

print("\nCleaning complete.")
print(f"Rows: {combined.shape[0]}")
print(f"Columns: {combined.shape[1]}")
print(f"Saved cleaned file to: {OUTPUT_FILE}")

print("\nPreview:")
print(combined[[
    "reporting_month",
    "org_code",
    "org_name",
    "total_ae_attendances",
    "total_over_4hrs",
    "over_4hrs_rate_pct",
    "dta_12hr_plus_waits",
    "total_emergency_admissions",
    "performance_risk"
]].head(10))