from flask_wtf import FlaskForm
from wtforms import (IntegerField, PasswordField, SelectField,
                     StringField, FileField,
                     SubmitField, ValidationError)
from wtforms.validators import EqualTo, InputRequired, Regexp


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
    submit = SubmitField("Register Account")


class LogInForm(FlaskForm):
    user_id = IntegerField("User id: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])

    submit = SubmitField("Log In")


class PermissionsForm(FlaskForm):
    user_ids = SelectField("User to change permissions of: ",
                           choices=[],
                           validators=[InputRequired()])

    admin_submit = SubmitField("Make Admin")
    manager_submit = SubmitField("Make Manager")


class ProductForm(FlaskForm):
    product_name = StringField("Product name: ",
                               validators=[InputRequired()])
    product_image = FileField("Product Image",
                              validators=[Regexp(r"(^[0-9a-zA-Z_-]+\b.png\b$)|(^[0-9a-zA-Z_-]+\b.jpg\b$)", message="Only JPG and PNG accepted.")])

    submit = SubmitField("Create Product")
