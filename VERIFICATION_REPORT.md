# PyCareer payroll project — verification report

## Performed in the packaging runtime

- **PASS:** Parsed all 50 Python source/test files with Python's `ast` parser.
- **PASS:** Parsed all 34 Jinja HTML templates with Jinja2, including the redesigned login.
- **PASS:** Validated 200 fictional employee rows in `data/pycareer_demo_employees_200.csv`.
- **PASS:** Confirmed unique fictional employee codes and email addresses, eight departments, and valid manager reference codes in the CSV preview.
- **PASS:** Confirmed local SQLite is the default in `config.py` and removed runtime PyMySQL and Docker Makefile dependencies.
- **PASS:** ZIP integrity checked after packaging.

## Not completed

- **NOT RUN:** Complete Flask application startup, interactive dashboard rendering, SQLite ORM seeding and payroll generation in the runtime environment.
- **NOT RUN:** Existing Flask test suite and new seed regression test. Running `python -m pytest -q tests/test_demo_seed.py` failed at import with `ModuleNotFoundError: No module named 'flask'`.
- **BLOCKED:** Attempt to install dependencies from PyPI failed because external package downloads/DNS were unavailable.
- **NOT PERFORMED:** Upload to GitHub, actual production payroll calculation, security audit, legal/statutory payroll compliance validation.

## Validate locally in PyCharm

After following `README.md` and installing dependencies, run:

```powershell
python -m flask --app run.py init-db
python -m flask --app run.py seed-demo
python scripts/verify_demo.py
python -m pytest -v
python run.py
```

The seeding routine is coded to create 200 employee profiles, linked salary/attendance/leave records and 200 previous-month generated payroll entries. Counts in the actual SQLite database must be confirmed via `scripts/verify_demo.py` on your machine. Demo payroll is **not** approved or paid.
