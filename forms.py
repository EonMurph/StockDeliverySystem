from flask_wtf import FlaskForm
from wtforms import (IntegerField, PasswordField, SelectField,
                     SubmitField, ValidationError)
from wtforms.validators import EqualTo, InputRequired


# custom validator code gotten from wtforms docs
# https://wtforms.readthedocs.io/en/3.0.x/validators/#custom-validators
# needed custom `length` as `Length` requires `StringField` and I wanted `IntegerField`
def length(size):

    def _length(form, field):
        if len(str(field.data)) != size:
            raise ValidationError("User id must be 6 digits.")

    return _length


class RegistrationForm(FlaskForm):
    user_id = IntegerField("User id: ",
                           validators=[InputRequired(), length(6)])
    password = PasswordField("Password: ", validators=[InputRequired()])
    password2 = PasswordField("Confirm password: ", validators=[
                              InputRequired(),
                              EqualTo("password", "Your passwords don't match.")])
    submit = SubmitField("Submit")


class LogInForm(FlaskForm):
    user_id = IntegerField("User id: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])

    submit = SubmitField("Submit")


class PermissionsForm(FlaskForm):
    user_ids = SelectField("User to change permissions of: ",
                           choices=[],
                           validators=[])

    admin_submit = SubmitField("Make Admin")
    manager_submit = SubmitField("Make Manager")
