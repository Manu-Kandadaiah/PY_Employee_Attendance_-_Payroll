# HR/Admin Manual Attendance and Charts

Sign in as admin or HR and open **HR & Payroll → Mark attendance & chart** (`/hr/attendance/manage`). Select an employee, date, status, optional check-in/check-out times, and save. Existing employee/day records are updated, with changes written to the existing audit log. The page shows a monthly attendance status bar chart, daily records and a monthly CSV download.

Run using the existing README instructions. No new database table is needed. The chart uses Chart.js from a CDN, so the browser needs internet access to render it.

Manual changes do not automatically recalculate previously generated payroll. Review and regenerate eligible payroll before approval. Bulk Excel attendance import is not included. This feature is for local demonstration and should be reviewed and tested before production use.
