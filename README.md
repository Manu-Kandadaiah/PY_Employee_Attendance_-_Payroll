# PyCareer — Employee Attendance & Payroll Management System

**A role-based HR operations web application built with Python, Flask, SQLite, Bootstrap 5 and Chart.js.**

**Tech stack:** `Python` · `Flask` · `SQLAlchemy` · `SQLite` · `Flask-Login` · `Bootstrap 5` · `Chart.js` · `ReportLab`

> **Portfolio disclosure:** PyCareer is the demonstration brand. All employee records, email addresses, attendance history and payroll examples are **fictional**. This repository does not publish actual employee data or prove statutory payroll compliance. The project is intended for learning and portfolio demonstration, not live salary disbursement.

## Project at a glance

PyCareer Employee Attendance & Payroll Management brings common HR workflows into one browser-based interface. Administrators, HR personnel, managers and employees receive role-specific functionality to handle attendance, leave requests, employee records, shift schedules and payroll information.

The redesigned application uses a responsive interface with a PyCareer logo, sign-in screen, dashboards, data tables and charts. A repeatable demo seeding process is designed to populate a **200-employee** dataset so reviewers can explore realistic workflows without using confidential information.

| Area | What the project demonstrates |
| --- | --- |
| Employee management | Employee directory, departments and reporting relationships |
| Attendance | Check-in/check-out tracking and attendance records |
| Leave & overtime | Leave requests, leave balances and approval workflows |
| Scheduling | Shifts and employee shift assignments |
| Payroll | Salary structures, generated payroll periods and employee payroll entries |
| Payslips | PDF generation with restricted download access |
| Reporting | Dashboard indicators, charts and HR views |
| Access control | Distinct Administrator, HR, Manager and Employee roles |

## Demo data

The project includes [`data/pycareer_demo_employees_200.csv`](data/pycareer_demo_employees_200.csv), a **200-row fictional employee preview** with unique employee codes and addresses using the non-deliverable `@pycareer.example` domain.

The `seed-demo` command is designed to create related records in a local SQLite database:

| Record type | Expected initial demo count |
| --- | ---: |
| Departments | 8 |
| Employee profiles | 200 |
| Application users | 201 (200 employee-linked users + 1 administrator) |
| Shift assignments | 200 |
| Salary structures | 200 |
| Leave balances | 800 |
| Sample payroll entries | 200 |

The example payroll is generated for the previous month and remains in **`generated` status**—it is **not approved or paid**. Attendance counts depend on the date when the seed runs. For details, see [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## User roles

- **Administrator:** user access, role management, departments and audit activity.
- **HR:** employee records, scheduling, leave policies, payroll periods and reports.
- **Manager:** team attendance, leave/overtime approvals and shift assignments.
- **Employee:** attendance check-in/out, leave requests and access to their own payslips.

## Interface and security design

- Responsive layout with custom PyCareer SVG logo, favicon and CSS theme.
- Role-protected Flask routes and authenticated sessions.
- Password hashing, CSRF protection for HTML forms and restricted payslip access.
- Searchable tables, status indicators and dashboard charts.
- Secrets configured locally through `.env`, which is excluded from Git.

**Security limitation:** This is a demonstration system. The included protections are not a substitute for penetration testing, production security configuration, or an independent payroll/legal review.

## Run locally using PyCharm (Windows)

**Prerequisites:** Python 3.12, PyCharm or VS Code, and internet access to install Python packages. Docker and MySQL are not required.

### 1. Clone and install

```powershell
git clone https://github.com/YOUR_USERNAME/pycareer-employee-attendance-payroll.git
cd pycareer-employee-attendance-payroll
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Replace `YOUR_USERNAME` with your GitHub username. If you downloaded the project ZIP instead, open its extracted root folder and skip the clone commands.

### 2. Configure your environment

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edit `.env` and set:

- `SECRET_KEY` to the newly generated random string.
- `DEMO_PASSWORD` to a private password containing **at least 12 characters**.
- `DATABASE_URL` to the included default `sqlite:///pycareer_payroll.db` unless you have a specific reason to change it.

**Never commit `.env` or publish the demo password.**

### 3. Initialize and seed SQLite

```powershell
python -m flask --app run.py init-db
python -m flask --app run.py seed-demo
python scripts/verify_demo.py
```

The verification script checks the expected employee count and related database records. The database file is created locally under `instance/` and is ignored by Git.

### 4. Start the web application

```powershell
python run.py
```

Open **http://127.0.0.1:5000/auth/login**.

| Demo role | Login email |
| --- | --- |
| Administrator | `admin@pycareer.example` |
| HR | `hr@pycareer.example` |
| Manager | `manager@pycareer.example` |
| Employee | `employee@pycareer.example` |

These role accounts use the private `DEMO_PASSWORD` configured in your `.env`. The `.example` domain is reserved for documentation and does not deliver real email.

## Tests and verification

Run locally after installing dependencies:

```powershell
python scripts/verify_demo.py
python -m pytest -v
```

**Verification performed when this portfolio package was prepared:**

- Python syntax parsing for 50 source/test files.
- Jinja parsing for 34 templates.
- Validation of 200 demo CSV rows, unique employee IDs/emails, eight departments and manager references.
- ZIP integrity and inspection of the SQLite configuration.

**Not yet verified in the packaging environment:** Complete Flask startup, database seeding through the ORM, full pytest execution, end-to-end payroll generation and interactive browser workflows. Dependency installation was unavailable in that environment. See [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) for the exact test limitations.

## Repository structure

```text
PyCareer_Employee_Attendance_Payroll/
├── app/
│   ├── blueprints/            # Role-based web routes and API
│   ├── forms/                 # Input validation
│   ├── models/                # Database models and relationships
│   ├── services/              # Attendance, leave, payroll and PDF logic
│   ├── templates/             # Jinja pages and role dashboards
│   └── static/                # PyCareer CSS, logo and favicon
├── data/
│   └── pycareer_demo_employees_200.csv
├── docs/                     # Architecture, API and data dictionary
├── scripts/verify_demo.py    # Demo integrity verification
├── tests/                    # Automated test cases
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
├── SECURITY.md
└── README.md
```

## Recruiter quick tour

1. **Explore the interface:** Run the application and sign in as HR or an employee to view role-specific pages.
2. **Review the dataset:** Open [`data/pycareer_demo_employees_200.csv`](data/pycareer_demo_employees_200.csv) to inspect the fictional employee records.
3. **Read the backend:** Inspect `app/blueprints/`, `app/models/` and `app/services/` for the Flask and database implementation.
4. **Review verification:** See `tests/` and `VERIFICATION_REPORT.md` for what is included versus what has been executed.
5. **Understand design decisions:** Browse `docs/ARCHITECTURE.md`, `docs/API.md` and `docs/DATA_DICTIONARY.md`.

## Upload to GitHub

Create an empty repository named **`pycareer-employee-attendance-payroll`**. In the project folder, run:

```powershell
git init
git add .
git status
git commit -m "Add PyCareer attendance and payroll portfolio project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pycareer-employee-attendance-payroll.git
git push -u origin main
```

**Upload:** source code, templates, static assets, requirements, `.env.example`, fictional CSV, tests and documentation. **Do not upload:** `.env`, `instance/`, SQLite databases, virtual environments, uploaded payslips, caches, secrets or real HR/payroll information.

## Limitations and next steps

- Payroll calculations are **illustrative**; legal, tax, PF, leave and statutory rules require professional review before real use.
- The SQLite configuration is suited to local portfolio demonstration rather than high-concurrency payroll operations.
- Production deployment would require validated migrations, hardened authentication/cookies, backups, audit reviews and security testing.
- Add authentic dashboard screenshots only after running and capturing the actual application—do not substitute mockups or claim an unverified deployment.

---

**Portfolio focus:** Full-stack Python development · Flask · Relational databases · HR workflow automation · Role-based dashboards · Documentation and testing.
