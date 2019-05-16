from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
# from flask_wtf.file import FileField, FileRequired, FileAllowed
# from werkzeug.utils import secure_filename


class CuisineForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Save')


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')


class RecipeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description',
                                validators=[DataRequired(),
                                            Length(min=0, max=250)])
    submit = SubmitField('Save')
