from quart_wtf import FileAllowed, FileField, QuartForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired, Length


class PostForm(QuartForm):
    message = TextAreaField(
        "What's on your mind?",
        validators=[DataRequired(), Length(max=500)],
    )
    image = FileField(
        "Photo",
        validators=[FileAllowed(["png", "jpg", "jpeg"], "Images only!")],
    )
