"""Read-only verification of the local PyCareer fictional demo database."""
from sqlalchemy import text, func, select
from app import create_app
from app.extensions import db
from app.models import (Attendance, Department, Employee, LeaveBalance,
                        PayrollEntry, PayrollPeriod, SalaryStructure,
                        ShiftAssignment, User)


def main():
    app = create_app()
    with app.app_context():
        counts = {
            'users': db.session.scalar(select(func.count()).select_from(User)),
            'employees': db.session.scalar(select(func.count()).select_from(Employee)),
            'departments': db.session.scalar(select(func.count()).select_from(Department)),
            'salary structures': db.session.scalar(select(func.count()).select_from(SalaryStructure)),
            'shift assignments': db.session.scalar(select(func.count()).select_from(ShiftAssignment)),
            'leave balances': db.session.scalar(select(func.count()).select_from(LeaveBalance)),
            'attendance rows': db.session.scalar(select(func.count()).select_from(Attendance)),
            'payroll periods': db.session.scalar(select(func.count()).select_from(PayrollPeriod)),
            'payroll entries': db.session.scalar(select(func.count()).select_from(PayrollEntry)),
        }
        for name, count in counts.items():
            print(f'{name:20s} {count}')
        expected = {'users': 201, 'employees': 200, 'departments': 8,
                    'salary structures': 200, 'shift assignments': 200,
                    'leave balances': 800, 'payroll periods': 1,
                    'payroll entries': 200}
        for name, count in expected.items():
            if counts[name] != count:
                raise AssertionError(f'{name}: expected {count}; got {counts[name]}')
        if not counts['attendance rows']:
            raise AssertionError('Expected attendance records')
        if db.engine.dialect.name != 'sqlite':
            raise AssertionError('Expected SQLite database')
        foreign_key_errors = db.session.execute(text('PRAGMA foreign_key_check')).all()
        if foreign_key_errors:
            raise AssertionError(f'SQLite foreign key errors: {foreign_key_errors[:5]}')
        duplicates = db.session.execute(text('SELECT employee_code, COUNT(*) FROM employees GROUP BY employee_code HAVING COUNT(*) > 1')).all()
        if duplicates:
            raise AssertionError(f'Duplicate employee codes: {duplicates}')
        print('PASS: all expected counts, SQLite relationships and employee codes verified.')


if __name__ == '__main__':
    main()
