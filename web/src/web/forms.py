from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, SelectMultipleField, StringField, IntegerField, BooleanField, HiddenField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import InputRequired, Required, Optional, Email, NumberRange
from wtforms.fields.html5 import EmailField, IntegerField


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class MatchForm(FlaskForm):
    paths = TextAreaField('Paths', validators=[Required()])
    submit = SubmitField('Get Matches')

class DataPathMatchForm(FlaskForm):
    matchpath_key = HiddenField('Match DataPath Key', validators=[Required()])
    matchpath = StringField('Matching DataPath', validators=[InputRequired('Please input a DataPath!')])
    weight = IntegerField('Confidence', validators=[InputRequired('Please enter the weight of the match!'), NumberRange(0, 100, 'Weight must be {min} - {max}!')])
    author = EmailField('Author', validators=[InputRequired('Please enter your email address!'), Email('Email appears invalid!')])
    annotation = TextAreaField('Annotation', validators=[Optional()])
    submit = SubmitField('Add Match')

class DirectForm(FlaskForm):
    path_id = StringField('Path', validators=[Required()])
    submit = SubmitField('Direct!')

class SearchForm(FlaskForm):
    oses = MultiCheckboxField('Operating Systems', validators=[Required()])
    dmls = MultiCheckboxField('Data Model Language', validators=[Required()])
    filter_str = StringField('Filter String', validators=[Required()])
    exclude_config = BooleanField('Exclude Config', validators=[Optional()], default=True)
    only_leaves = BooleanField('Only Leaf Nodes', validators=[Optional()], default=True)
    start_index = IntegerField('Start Index', validators=[Optional()], default=0)
    max_return_count = IntegerField('Maximum Return Count', validators=[Required()], default=10)
    submit = SubmitField('Search')

class SearchFormES(FlaskForm):
    oses = MultiCheckboxField('Operating Systems (Optional)', validators=[Optional()], default=[])
    dmls = MultiCheckboxField('Data Model Language (Optional)', validators=[Optional()], default=[])
    filter_str = StringField('Filter String', validators=[Required()])
    exclude_config = BooleanField('Exclude Config', validators=[Optional()], default=True)
    only_leaves = BooleanField('Leaf Nodes', validators=[Optional()], default=True)
    num_results = IntegerField('Result Limit', validators=[Required()], default=150)
    submit = SubmitField('Search')
