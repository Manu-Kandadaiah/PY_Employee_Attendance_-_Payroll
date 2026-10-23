# PyCareer | Employee Attendance & Payroll Management

**Flask • SQLAlchemy • SQLite • Bootstrap 5 • Chart.js • Python • HR technology**

A responsive, role-based workforce operations application redesigned as a **PyCareer portfolio project**. It demonstrates employee attendance tracking, leave approval, shift scheduling, salary structures, payroll generation and protected payslip workflows.

> **Portfolio disclosure:** All 200 employee profiles, email addresses, attendance records and payroll examples are **fictional**. This repository does not contain real personnel data. PyCareer is the demonstration brand. The application is a local learning/portfolio project, not a certified payroll system.

## Features

| Role | What it can do |
|---|---|
| **Administrator** | Account access, roles, department directory and audit activity |
| **HR** | Employee records, shift schedules, leave policies, payroll periods and reports |
| **Manager** | Team attendance, leave/overtime approvals and shift assignment |
| **Employee** | Check in/out, request leave, track attendance and view own payslips |

Additional capabilities include CSRF protection for form submissions, hashed passwords, role-based routes, protected payslip downloads, PDF generation and searchable employee tables.

## Updated UI

- Distinctive PyCareer SVG logo and favicon
- Navy, indigo and teal design with responsive navigation
- Redesigned two-column sign-in page and consistent dashboard cards
- Readable tables, status indicators, forms and chart presentation
- Mobile/tablet layout adjustments

Brand assets: `app/static/img/logo.svg`, `app/static/img/favicon.svg`, `app/static/css/app.css`.

## Demo dataset

The repository also includes a safe, reviewable [`data/pycareer_demo_employees_200_com.csv`](data/pycareer_demo_employees_200_com.csv) preview with exactly 200 fictional employee records. Run the seed command to create **200 fictional employee profiles across eight departments**, 201 users (one administrator plus employee accounts), salary structures and shift assignments, leave balances, generated attendance records, and a **200-entry previous-month payroll preview**. The sample payroll period remains `generated`, not approved or marked paid. See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for full counts and relationships.

Demo email addresses use the reserved `@pycareer.com` domain and **will not receive actual email**. They are placeholders for local authentication only.

## Requirements

- Python **3.12** recommended; Windows / PyCharm or VS Code
- No Docker server or MySQL server required
- Internet access for initial Python package installation and Bootstrap/Chart.js CDN assets

## Setup: Windows / PyCharm

1. Extract the ZIP and open the folder in PyCharm.
2. Open the terminal at project root and create your environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

3. Copy configuration:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

4. Edit `.env`, replacing `SECRET_KEY` with the generated random string and setting a **private `DEMO_PASSWORD` with at least 12 characters**. Keep both values outside GitHub.
5. Initialize SQLite and insert the demonstration dataset:

```powershell
python -m flask --app run.py init-db
python -m flask --app run.py seed-demo
python scripts/verify_demo.py
```

6. Start the application:

```powershell
python run.py
```

7. Visit **http://127.0.0.1:5000/auth/login**.

The default database URI is `sqlite:///pycareer_payroll.db` (Flask stores it under `instance/`). This file is created automatically and excluded from Git.

### Local demonstration logins

All four roles use the **private** password configured in your `.env` (`DEMO_PASSWORD`).

| Role | Local demo email |
|---|---|
| Admin | `admin@pycareer.com` |
| HR | `hr@pycareer.com` |
| Manager | `manager@pycareer.com` |
| Employee | `employee@pycareer.com` |

> These `.com` email addresses are fictional placeholders. Do not send live mail to them. Never publish or reuse the demo password in a live environment.

To start with a **fresh demo database**, stop the server, delete only your local `instance/pycareer_payroll.db` (this permanently erases local records), and rerun initialization and seeding. The seed command is idempotent for a previously seeded database and refuses to overwrite pre-existing users.

## Verify and test

```powershell
python scripts/verify_demo.py
python -m pytest -v
```

`verify_demo.py` validates the expected 200 employee profiles, linked records, and SQLite foreign keys. Automated test modules are under `tests/`.

**Verification status:** Python syntax and Jinja template parsing have been checked during this packaging. The complete Flask runtime/pytest suite has **not** been executed here because Flask dependencies were not available in the packaging runtime. Run the commands above after installing requirements.

## Repository structure

```text
employee-attendance-payroll/
├── app/
│   ├── blueprints/           # auth, admin, HR, employee, manager, API
│   ├── forms/                # WTForms validation
│   ├── models/               # linked relational data models
│   ├── services/             # attendance, payroll, PDF, reporting
│   ├── templates/            # responsive Jinja HTML views
│   ├── static/css/app.css    # PyCareer UI theme
│   └── static/img/           # logo and favicon
├── data/pycareer_demo_employees_200_com.csv
├── scripts/verify_demo.py    # dataset/referential integrity checker
├── tests/                    # Flask app tests
├── docs/DATA_DICTIONARY.md
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## GitHub instructions

Create a new **empty** repository named `pycareer-employee-attendance-payroll`. From the extracted project root:

```powershell
git init
git add .
git status
git commit -m "Build PyCareer employee attendance and payroll app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pycareer-employee-attendance-payroll.git
git push -u origin main
```

Replace `YOUR_USERNAME`. Confirm that `.env`, virtual environments, generated payslips and SQLite files are absent from `git status` before committing. No GitHub upload is performed by this package.

## Security and business limitations

- Demo users and passwords are for **local access only**; do not expose this version to the public internet.
- The app uses simple illustrative PF, tax, salary and leave computations; **real payroll requires legal, tax and HR review**.
- SQLite is appropriate for local demonstration, not high-concurrency enterprise payroll.
- Production rollout would need verified migrations, hardened login/rate limiting and cookies, backup/restore procedures, access audits, and a thorough security review.
- Employee names, attendance, emails and salary figures are synthetic. Avoid presenting them as actual staff or financial results.

## CSV filename and database behavior

The preview CSV is `data/pycareer_demo_employees_200_com.csv`. The current `seed-demo` command generates 200 demo employees from Python logic in `app/cli.py`; it does **not** import rows from the CSV. Editing the CSV alone does not update SQLite. The seed command now uses fictional `@pycareer.com` login addresses. To regenerate a fresh local demo database, stop the app, back up any data you want, delete only the local `instance/pycareer_payroll.db`, then run `init-db` and `seed-demo`.

For a differently named CSV, change references in documentation or your own import code. There is no CSV filename setting in `config.py` for this application.


## Raw data upload and automatic chart reporting

Admin/HR can upload CSV or Excel files at `/analytics/` to clean data and generate downloadable charts and reports. See [ANALYTICS_GUIDE.md](ANALYTICS_GUIDE.md). This does not import into the payroll database.
