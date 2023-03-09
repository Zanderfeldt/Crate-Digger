from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, RadioField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, InputRequired, Optional


class SignupForm(FlaskForm):
    """Form for adding users"""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Form for logging in existing user"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class SongForm(FlaskForm):
    """Form for retrieving song recommendations"""

    input_type = RadioField(
        'Type', choices=[('artist', 'Artist'), ('track', 'Track')], default='artist')
    name = StringField('Name')
    genre = SelectField('Genre')
    acousticness = BooleanField('Acoustic Songs')
    danceability = BooleanField('Danceable Music')
    energy = BooleanField('Energetic music')
    instrumentalness = BooleanField('Instrumental Songs')
    liveness = BooleanField('Live Songs')
    speechiness = BooleanField('More Speaking')
    happy = BooleanField('Happy Music')
    key = SelectField('Key', choices=[('', 'Select a Song Key'), ('1', 'C'), ('2', 'C#'), ('3', 'D'), ('4', 'D#'), ('5', 'E'),
                                      ('6', 'F'), ('7', 'F#'), ('8', 'G'), ('9', 'G#'), ('10', 'A'), ('11', 'A#'), ('12', 'B')])
    mode = SelectField('Mode', choices=[
                       ('', 'Select Major or Minor Key'), ('0', 'Minor'), ('1', 'Major')])


class PlaylistForm(FlaskForm):
    """Form for adding playlists."""

    name = StringField("Name", validators=[InputRequired(
        message="Playlist Name cannot be blank"), Length(max=50, message="Playlist name too long")], )
    description = TextAreaField("Description", validators=[
                                Optional(), Length(max=100)])
