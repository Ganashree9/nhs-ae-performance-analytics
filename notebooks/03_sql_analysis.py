from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_FILE = PROJECT_ROOT / "data" / "cleaned" / "cleaned_ae_performance.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = PROJECT_ROOT / "data" / "cleaned" / "nhs_ae_performance.db"
REPORT_FILE = REPORTS_DIR / "sql_analysis_results.md"

df = pd.read_csv(CLEANED_FILE)

connection = sqlite3.connect(DB_FILE)
df.to_sql("ae_performance", connection, if_exists="replace", index=False)

queries = {
    "Total A&E Attendances by Month": """
        SELECT 
            reporting_month,
            SUM(total_ae_attendances) AS total_attendances,
            SUM(total_over_4hrs) AS total_over_4hrs,
            ROUND(AVG(over_4hrs_rate_pct), 2) AS avg_over_4hrs_rate_pct
        FROM ae_performance
        GROUP BY reporting_month
        ORDER BY total_attendances DESC;
    """,

    "Top 10 Organisations by A&E Attendances": """
        SELECT 
            org_name,
            SUM(total_ae_attendances) AS total_attendances,
            SUM(total_over_4hrs) AS total_over_4hrs,
            ROUND(AVG(over_4hrs_rate_pct), 2) AS avg_over_4hrs_rate_pct
        FROM ae_performance
        GROUP BY org_name
        ORDER BY total_attendances DESC
        LIMIT 10;
    """,

    "Top 10 Organisations by 12 Hour DTA Waits": """
        SELECT 
            org_name,
            SUM(dta_12hr_plus_waits) AS total_12hr_plus_waits,
            SUM(dta_4_12hr_waits) AS total_4_12hr_waits,
            SUM(total_emergency_admissions) AS total_emergency_admissions
        FROM ae_performance
        GROUP BY org_name
        ORDER BY total_12hr_plus_waits DESC
        LIMIT 10;
    """,

    "Performance Risk Breakdown": """
        SELECT 
            performance_risk,
            COUNT(*) AS records,
            SUM(total_ae_attendances) AS total_attendances,
            ROUND(AVG(over_4hrs_rate_pct), 2) AS avg_over_4hrs_rate_pct
        FROM ae_performance
        GROUP BY performance_risk
        ORDER BY records DESC;
    """
}

with open(REPORT_FILE, "w", encoding="utf-8") as report:
    report.write("# NHS A&E SQL Analysis Results\n\n")

    for title, query in queries.items():
        result = pd.read_sql_query(query, connection)

        report.write(f"## {title}\n\n")
        report.write(result.to_markdown(index=False))
        report.write("\n\n")

        print(f"\n{title}")
        print(result)

connection.close()

print(f"\nSQL analysis complete.")
print(f"Database saved to: {DB_FILE}")
print(f"Report saved to: {REPORT_FILE}")