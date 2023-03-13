from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    playlists = db.relationship(
        'Playlist', cascade='all, delete', backref='user')

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user. Hashes password and adds user to database"""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(username=username, email=email, password=hashed_pwd)

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Playlist(db.Model):
    "Playlist."

    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    songs = db.relationship('Song', secondary='playlists_songs',
                            cascade='all, delete', backref='playlists')

    @classmethod
    def count_songs(cls, id):

        playlist = PlaylistSong.query.filter(
            PlaylistSong.playlist_id == id).count()
        return playlist


class Song(db.Model):
    """Song"""

    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    song_name = db.Column(db.String, nullable=False)
    song_seed = db.Column(db.String, nullable=False, unique=True)
    artist_name = db.Column(db.String, nullable=False)
    artist_seed = db.Column(db.String, nullable=False)
    bpm = db.Column(db.Integer)
    key = db.Column(db.String)


class PlaylistSong(db.Model):
    """Mapping of a playlist to a song."""

    __tablename__ = 'playlists_songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey(
        'playlists.id', ondelete='CASCADE'))
    song_id = db.Column(db.Integer, db.ForeignKey(
        'songs.id', ondelete='CASCADE'))
