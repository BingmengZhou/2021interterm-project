from wtforms import Form, BooleanField, StringField, PasswordField, validators

class UserForm(Form):
    username = StringField('username', [validators.Length(min=2, max=50)])
    # email = StringField('Email Address', [validators.Length(min=6, max=35)])
    # password = PasswordField('New Password', [
    #     validators.DataRequired(),
    #     validators.EqualTo('repassword', message='Passwords must match')
    # ])
    # repassword = PasswordField('Repeat Password')
    # accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])