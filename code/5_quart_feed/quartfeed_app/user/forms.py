from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length

from quart_wtf import QuartForm


class UserForm(QuartForm):
    """Used for both registration and login."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(max=15)],
        render_kw={"autocomplete": "off"},
    )
    password = PasswordField("Password", validators=[DataRequired()])
