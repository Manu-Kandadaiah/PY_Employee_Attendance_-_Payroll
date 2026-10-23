"""Regression checks for the 200-employee fictional PyCareer demo dataset."""
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import Department, Employee, LeaveBalance, PayrollEntry, SalaryStructure, User


def test_demo_seed_is_consistent(monkeypatch):
    monkeypatch.setenv('DEMO_PASSWORD', 'LocalTestOnlyPrivatePassword!123')
    app = create_app('testing')
    runner = app.test_cli_runner()
    with app.app_context():
        db.create_all()
        result = runner.invoke(args=['seed-demo'])
        assert result.exit_code == 0, result.output
        assert Employee.query.count() == 200
        assert User.query.count() == 201
        assert Department.query.count() == 8
        assert SalaryStructure.query.count() == 200
        assert LeaveBalance.query.count() == 800
        assert PayrollEntry.query.count() == 200
        assert db.session.execute(text('PRAGMA foreign_key_check')).all() == []
        assert User.query.filter_by(email='admin@pycareer.com').one().check_password('LocalTestOnlyPrivatePassword!123')
        again = runner.invoke(args=['seed-demo'])
        assert again.exit_code == 0
        assert Employee.query.count() == 200
        db.session.remove()
        db.drop_all()
