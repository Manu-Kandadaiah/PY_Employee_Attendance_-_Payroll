from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class EmployeeProfileForm(FlaskForm):
    phone = StringField("Phone", validators=[Optional(), Length(max=25)])
    date_of_birth = DateField("Date of birth", validators=[Optional()])
    gender = SelectField("Gender", choices=[("", "Select"), ("male", "Male"), ("female", "Female"), ("other", "Other")], validators=[Optional()])
    address = TextAreaField("Address", validators=[Optional(), Length(max=1000)])
    emergency_contact = StringField("Emergency contact", validators=[Optional(), Length(max=120)])
    bank_name = StringField("Bank name", validators=[Optional(), Length(max=120)])
    bank_account = StringField("Bank account", validators=[Optional(), Length(max=60)])
    bank_ifsc = StringField("IFSC", validators=[Optional(), Length(max=20)])
    pan_number = StringField("PAN", validators=[Optional(), Length(max=20)])
    uan_number = StringField("UAN", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Save profile")


class LeaveRequestForm(FlaskForm):
    leave_type_id = SelectField("Leave type", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start date", validators=[DataRequired()])
    end_date = DateField("End date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=1000)])
    submit = SubmitField("Submit request")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")


class OvertimeRequestForm(FlaskForm):
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=5, max=255)])
    submit = SubmitField("Request approval")
