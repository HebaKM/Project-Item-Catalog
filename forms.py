from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
# from flask_wtf.file import FileField, FileRequired, FileAllowed
# from werkzeug.utils import secure_filename


class CuisineForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class DeleteCuisineForm(FlaskForm):
    submit = SubmitField('Delete')
