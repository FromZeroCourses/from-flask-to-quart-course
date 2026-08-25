from quart_wtf import QuartForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired, Length


class CommentForm(QuartForm):
    comment = TextAreaField(
        "Add a comment",
        validators=[DataRequired(), Length(max=500)],
    )
