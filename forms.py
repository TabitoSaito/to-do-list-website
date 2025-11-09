from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class AddListForm(FlaskForm):
    title = StringField("List Name", validators=[DataRequired()])
    submit = SubmitField("Add List")


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a form to add comments
class AddTaskForm(FlaskForm):
    title = StringField("Task Name", validators=[DataRequired()])
    description = CKEditorField("Description", validators=[DataRequired()])
    submit = SubmitField("Submit Task")
