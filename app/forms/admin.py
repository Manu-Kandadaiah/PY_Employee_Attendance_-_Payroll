from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class UserForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    role = SelectField("Role", choices=[("admin", "Admin"), ("hr", "HR"), ("manager", "Manager"), ("employee", "Employee")])
    password = PasswordField("Password", validators=[Optional(), Length(min=10, max=72)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save user")


class DepartmentForm(FlaskForm):
    name = StringField("Department name", validators=[DataRequired(), Length(max=100)])
    code = StringField("Code", validators=[DataRequired(), Length(max=20)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=255)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save department")
