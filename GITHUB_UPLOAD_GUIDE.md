# GitHub upload guide — PyCareer Employee Attendance & Payroll

## Upload

Source under `app/`, `run.py`, `config.py`, `requirements.txt`, `tests/`, `scripts/`, `docs/`, README, `.gitignore`, `.env.example`, `Makefile`. SVG logo and favicon are part of `app/static/img/`.

## Never upload

`.env`, `instance/*.db`, `.venv/`, `__pycache__/`, `uploads/` contents, confidential personnel records, actual employee bank numbers or credentials, or production-generated payslips.

## Commands

```powershell
git init
git add .
git status
git commit -m "Build PyCareer employee attendance and payroll app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pycareer-employee-attendance-payroll.git
git push -u origin main
```

Verify demo seed and app in PyCharm using the commands from `README.md` before describing it as tested or deployment-ready.
