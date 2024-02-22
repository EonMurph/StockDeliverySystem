from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import EqualTo, InputRequired


class RegistrationForm(FlaskForm):
    user_id = StringField("Username: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])
    password2 = PasswordField("Confirm password: ", validators=[
                              InputRequired(), EqualTo("password")])
    submit = SubmitField("Submit")