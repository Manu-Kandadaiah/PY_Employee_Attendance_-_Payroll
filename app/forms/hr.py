from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, DateField, DecimalField, IntegerField, PasswordField, SelectField,
    StringField, SubmitField, TextAreaField, TimeField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError


class EmployeeForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Work email", validators=[DataRequired(), Email(), Length(max=150)])
    employee_code = StringField("Employee code", validators=[DataRequired(), Length(max=30)])
    department_id = SelectField("Department", coerce=int, validators=[DataRequired()])
    manager_id = SelectField("Reporting manager", coerce=int, validators=[Optional()])
    designation = StringField("Designation", validators=[DataRequired(), Length(max=120)])
    role = SelectField("Portal role", choices=[("employee", "Employee"), ("manager", "Manager"), ("hr", "HR")], validators=[DataRequired()])
    date_of_joining = DateField("Date of joining", validators=[DataRequired()], default=date.today)
    employment_type = SelectField("Employment type", choices=[("full_time", "Full time"), ("part_time", "Part time"), ("contract", "Contract"), ("intern", "Intern")])
    status = SelectField("Status", choices=[("active", "Active"), ("probation", "Probation"), ("notice", "Notice period"), ("inactive", "Inactive")])
    password = PasswordField("Initial password", validators=[Optional(), Length(min=10, max=72)])
    basic = DecimalField("Basic salary", validators=[DataRequired(), NumberRange(min=0)], places=2)
    hra = DecimalField("HRA", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    conveyance = DecimalField("Conveyance", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    medical = DecimalField("Medical", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    special_allowance = DecimalField("Special allowance", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    variable_pay = DecimalField("Variable pay", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    pf_percent = DecimalField("PF %", validators=[NumberRange(min=0, max=100)], places=2, default=12)
    professional_tax = DecimalField("Professional tax", validators=[NumberRange(min=0)], places=2, default=200)
    income_tax_percent = DecimalField("Income tax %", validators=[NumberRange(min=0, max=100)], places=2, default=0)
    other_deduction = DecimalField("Other monthly deduction", validators=[NumberRange(min=0)], places=2, default=0)
    overtime_multiplier = DecimalField("Overtime multiplier", validators=[NumberRange(min=1, max=5)], places=2, default=1.5)
    submit = SubmitField("Save employee")


class ShiftForm(FlaskForm):
    name = StringField("Shift name", validators=[DataRequired(), Length(max=80)])
    code = StringField("Code", validators=[DataRequired(), Length(max=20)])
    start_time = TimeField("Start time", validators=[DataRequired()])
    end_time = TimeField("End time", validators=[DataRequired()])
    grace_minutes = IntegerField("Grace minutes", validators=[NumberRange(min=0, max=120)], default=10)
    break_minutes = IntegerField("Break minutes", validators=[NumberRange(min=0, max=240)], default=60)
    minimum_half_day_minutes = IntegerField("Minimum half-day minutes", validators=[NumberRange(min=60, max=720)], default=240)
    overtime_threshold_minutes = IntegerField("Overtime starts after minutes", validators=[NumberRange(min=60, max=1000)], default=480)
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save shift")


class HolidayForm(FlaskForm):
    holiday_date = DateField("Date", validators=[DataRequired()])
    name = StringField("Holiday name", validators=[DataRequired(), Length(max=120)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    is_optional = BooleanField("Optional holiday")
    submit = SubmitField("Save holiday")


class LeaveTypeForm(FlaskForm):
    name = StringField("Leave name", validators=[DataRequired(), Length(max=80)])
    code = StringField("Code", validators=[DataRequired(), Length(max=20)])
    is_paid = BooleanField("Paid leave", default=True)
    default_days = DecimalField("Annual allocation", validators=[NumberRange(min=0, max=365)], places=2, default=0)
    requires_document = BooleanField("Supporting document required")
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save leave type")


class ShiftAssignmentForm(FlaskForm):
    employee_id = SelectField("Employee", coerce=int, validators=[DataRequired()])
    shift_id = SelectField("Shift", coerce=int, validators=[DataRequired()])
    effective_from = DateField("Effective from", validators=[DataRequired()], default=date.today)
    effective_to = DateField("Effective to", validators=[Optional()])
    submit = SubmitField("Assign shift")

    def validate_effective_to(self, field):
        if field.data and self.effective_from.data and field.data < self.effective_from.data:
            raise ValidationError("End date cannot be before start date.")


class PayrollPeriodForm(FlaskForm):
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)], default=date.today().year)
    month = SelectField("Month", coerce=int, choices=[(i, __import__('calendar').month_name[i]) for i in range(1,13)], validators=[DataRequired()], default=date.today().month)
    notes = StringField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Create payroll period")
