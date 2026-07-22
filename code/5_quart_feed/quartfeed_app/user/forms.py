from quart_wtf import FileAllowed, FileField, QuartForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length


class UserForm(QuartForm):
    """Used for both registration and login."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(max=15)],
        render_kw={"autocomplete": "off"},
    )
    password = PasswordField("Password", validators=[DataRequired()])


class ProfileEditForm(QuartForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=15)])
    image = FileField(
        "Profile image",
        validators=[FileAllowed(["png", "jpg", "jpeg"], "Images only!")],
    )
