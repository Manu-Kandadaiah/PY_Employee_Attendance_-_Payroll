# Data Cleaning & Chart Reports

After starting the Flask app, sign in as **admin** or **HR** and select **Data Cleaning & Charts**. Upload a `.csv` or `.xlsx` file (first Excel worksheet only, max 10 MB, 50,000 data rows, 100 columns).

The system automatically trims whitespace, normalizes column headings, removes empty rows and exact duplicate rows, and counts missing values. It does **not** fill missing values, infer types for the cleaned CSV, or alter the payroll database.

It creates one private directory per upload under `instance/analytics_outputs/<user_id>/<job_id>/` with `cleaned_data.csv`, `cleaning_report.json`, `report.html`, up to eight `chart_*.png`, and `report_bundle.zip`. Download the ZIP in the app, extract it and open `report.html` to see charts.

## Security and limits
Only authenticated admin/HR users can upload or download their own reports. The report directory is Git-ignored. Avoid uploading sensitive real employee data to a public/demo server. Production deployment needs virus scanning, storage retention/deletion, secure backups and role/department authorization review.

## Installation
Install updated dependencies: `pip install -r requirements.txt`. The new report page is `/analytics/`. No database migration is required.

## Scope
This is automatic **chart reporting**, not an AI chatbot. It produces chart PNGs and an HTML report, not natural-language question answering. Employee records in the application are unchanged by uploads.
