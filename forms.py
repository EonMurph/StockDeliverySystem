from ast import In
from flask_wtf import FlaskForm
from wtforms import (IntegerField, PasswordField, SelectField,
                     StringField, FileField,
                     SubmitField, ValidationError)
from wtforms.validators import EqualTo, InputRequired, Regexp, Optional


# custom validator code gotten from wtforms docs
# https://wtforms.readthedocs.io/en/3.0.x/validators/#custom-validators
# needed custom `length` as `Length` requires `StringField` and I wanted `IntegerField`
def valid_id(size):

    def _valid_id(form, field):
        if len(str(field.data)) != size and str(field.data)[0] != 0:
            raise ValidationError(
                "User id must be 6 digits and must not start with 0.")

    return _valid_id


def not_equal_to(compare_field):

    def _not_equal(form, field):
        if field.data == form[compare_field].data:
            raise ValidationError("To and from stores must be different.")

    return _not_equal


class RegistrationForm(FlaskForm):
    user_id = IntegerField("User id: ",
                           validators=[InputRequired(), valid_id(6)])
    password = PasswordField("Password: ", validators=[InputRequired()])
    password2 = PasswordField("Confirm password: ", validators=[
                              InputRequired(),
                              EqualTo("password", "Your passwords don't match.")])
    store_id = SelectField("Employee's store: ",
                           choices=[],
                           validators=[InputRequired()])

    submit = SubmitField("Register Account")


class LogInForm(FlaskForm):
    user_id = IntegerField("User id: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])

    submit = SubmitField("Log In")


class PermissionsForm(FlaskForm):
    user_ids = SelectField("User to change permissions of: ",
                           choices=[],
                           validators=[InputRequired()])
    store_id = SelectField("Manages Store: \n(only used for manager)",
                           choices=[],
                           validators=[Optional()])

    admin_submit = SubmitField("Make Admin")
    manager_submit = SubmitField("Make Manager")


class ProductForm(FlaskForm):
    product_name = StringField("Product name: ",
                               validators=[InputRequired()])
    product_image = FileField("Product Image",
                              validators=[Regexp(r"(^[0-9a-zA-Z_-]+\b.png\b$)|(^[0-9a-zA-Z_-]+\b.jpg\b$)", message="Only JPG and PNG accepted.")])

    submit = SubmitField("Create Product")


class StoreForm(FlaskForm):
    manager_id = SelectField("Store Manager: ",
                             choices=[],
                             validators=[InputRequired()])

    submit = SubmitField("Create Store")


class DeliveriesForm(FlaskForm):
    to_store = SelectField("Starting Store: ",
                           choices=[],
                           validators=[InputRequired()])
    from_store = SelectField("Destination Store: ",
                             choices=[],
                             validators=[InputRequired(), not_equal_to("to_store")])
    day = SelectField("Delivery Day: ",
                      choices=["Sun", "Mon", "Tue",
                               "Wed", "Thurs", "Fri", "Sat"],
                      validators=[InputRequired()])

    submit = SubmitField("Add Delivery Schedule")
