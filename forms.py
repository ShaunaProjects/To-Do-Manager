from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, DateTimeLocalField
from wtforms.validators import DataRequired, Email
from flask_ckeditor import CKEditorField
import email_validator

class RegisterUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[Email(), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ToDoForm(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired()])
    description = CKEditorField("Description of Task", validators=[DataRequired()])
    start_date = DateTimeLocalField("Start Date", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeLocalField("End Date", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField("Add Task")
