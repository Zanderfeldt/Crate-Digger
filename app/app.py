from flask import Flask, redirect, render_template, request, session, flash, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Playlist, PlaylistSong, Song
from access import CLIENT_ID, CLIENT_SECRET
from forms import SignupForm, LoginForm, SongForm, PlaylistForm
from utilities import get_id, get_genres,  get_keys
from client import SpotifyClient
import requests

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///crate-digger'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

app.config['SECRET_KEY'] = "I'LL NEVER TELL!!"


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

######################## - USER ROUTES and FUNCTIONS - #########################


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    if 'track_id_list' in session:
        del session['track_id_list']
    # On log out, delete the 'lost n found', which consists of songs users didnt add to a playlist
    save_songs = [s.id for s in Song.query.filter(Song.playlists).all()]
    Song.query.filter(Song.id.notin_(save_songs)).delete()
    db.session.commit()


@app.route('/')
def homepage():
    """Show music recommendation form if user logged in. If not,
    redirect to sign up or login form"""

    if g.user:
        return redirect('/seed')

    else:
        return redirect('/signup')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign up new user"""

    form = SignupForm()

    if form.validate_on_submit():
        try:
            user = User.signup(username=form.username.data,
                               email=form.email.data,
                               password=form.password.data)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect('/auth')

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/auth")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user"""

    do_logout()
    flash("Logout Successful", "success")
    return redirect('/login')

################# -AUTHORIZATION ROUTES -############################


@app.route('/auth')
def get_token():
    """Authenticates the app with Spotify's API"""

    if 'token' in session:
        session.pop('token')

    resp = requests.post('https://accounts.spotify.com/api/token',
                         {'grant_type': 'client_credentials',
                          'client_id': CLIENT_ID,
                          'client_secret': CLIENT_SECRET}).json()
    token = resp['access_token']
    session['token'] = token

    return redirect('/')

################## -SEARCH ROUTES- ###################################


@app.route('/search')
def artist_or_track_search():
    """Sends request to API with track or artist query and returns a list of
    tuples with with Spotify ID and corresponding track/artist name"""

    try:
        name = request.args.get('q')
        type = request.args.get('type')
        resp = get_id(name, type)
        return resp

    except KeyError:
        return redirect('/')


@app.route('/seed', methods=['GET', 'POST'])
def get_music():
    """Displays and handles form for getting music recommendations"""

    if not g.user:
        return redirect('/')

    form = SongForm()
    user = User.query.get_or_404(session[CURR_USER_KEY])

    # populate genre select field with choice from Spotify
    try:
        form.genre.choices = get_genres()
    # if access token expires, a key error is raised. In that case, request new token and display form
    except KeyError:
        return redirect('/auth')

    if form.validate_on_submit():
        try:
            headers = {'Authorization': 'Bearer ' + session['token']}
            payload = {}

            # gets artist ids for search, if any
            if request.form.get('artist'):
                artist_list = ''
                for artist in request.form.getlist('artist'):
                    artist_list += f"{artist},"
                payload['seed_artists'] = artist_list

            # gets track ids for search, if any
            if request.form.get('track'):
                track_list = ''
                for track in request.form.getlist('track'):
                    track_list += f"{track},"
                payload['seed_tracks'] = track_list

            # get genres for search if selected
            if form.genre.data:
                payload['seed_genres'] = form.genre.data

            # get additional attributes to narrow search. If search value is 1.0,
            # songs that match that attribute will be favored in search
            if form.acousticness.data:
                payload['target_acousticness'] = 1.0
            if form.danceability.data:
                payload['target_danceability'] = 1.0
            if form.energy.data:
                payload['target_energy'] = 1.0
            if form.instrumentalness.data:
                payload['target_instrumentalness'] = 1.0
            if form.liveness.data:
                payload['target_liveness'] = 1.0
            if form.speechiness.data:
                payload['target_speechiness'] = 1.0
            if form.happy.data:
                payload['target_valence'] = 1.0

            # get attribute parameters from range fields
            if request.form.get('include_min_duration'):
                payload['min_duration_ms'] = int(
                    request.form.get('min_duration'))
            if request.form.get('include_max_duration'):
                payload['max_duration_ms'] = int(
                    request.form.get('max_duration'))
            if request.form.get('include_loudness'):
                payload['target_loudness'] = float(
                    request.form.get('loudness'))
            if request.form.get('include_popularity'):
                payload['target_popularity'] = int(
                    request.form.get('popularity'))
            if request.form.get('include_tempo'):
                payload['target_tempo'] = float(
                    request.form.get('tempo'))
            if request.form.get('include_tempo'):
                payload['target_tempo'] = float(
                    request.form.get('tempo'))

            # get key and mode for search
            if form.key.data:
                payload['target_key'] = int(form.key.data)
            if form.mode.data:
                payload['target_mode'] = int(form.mode.data)

            # call API for song recommendations
            resp = SpotifyClient(
                payload=payload, headers=headers).get_recommendations()

            # following code is to retrieve tempo data for each song, which isn't provided in previous response
            track_ids = ''
            for track in resp['tracks']:
                track_ids += f"{track['id']},"

            track_id_payload = {'ids': track_ids}

            # call API for bpms of each track retrieved from previous API call
            bpm_resp = SpotifyClient(
                payload=track_id_payload, headers=headers).get_bpms()
            bpm_dict = {
                track['id']: [round(track['tempo']), track['key']] for track in bpm_resp['audio_features']}
            # import pdb
            # pdb.set_trace()
            # save track ids, tempos, and keys to session for use in results view
            session['track_id_list'] = track_id_payload['ids']
            session['bpm_dict'] = bpm_dict
            keys = get_keys()[1:]
            # add songs with their bpm/key to database
            for song in resp['tracks']:
                try:
                    db.session.add(Song(song_name=song['name'],
                                        song_seed=song['id'],
                                        artist_name=song['artists'][0]['name'],
                                        artist_seed=song['artists'][0]['id'],
                                        bpm=bpm_dict[song['id']][0],
                                        key=keys[bpm_dict[song['id']][1]][1]))
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

            return redirect('/results')

        except KeyError:
            flash('Please enter an artist, song, or genre', 'danger')
            return render_template('find-music.html', form=form, user=user)

    return render_template('find-music.html', form=form, user=user)


@app.route('/results')
def show_results():
    """Displays results of music search form submission"""

    if not g.user:
        return redirect('/')
    if 'track_id_list' not in session:
        return redirect('/')

    track_id_list = [id for id in session.get(
        'track_id_list').split(',') if id]
    tracks = Song.query.filter(Song.song_seed.in_(track_id_list)).all()
    if len(tracks) == 0:
        return redirect('/')
    user = g.user
    playlists = Playlist.query.filter(Playlist.user_id == user.id).all()

    return render_template('results.html', tracks=tracks, playlists=playlists)

################### - PLAYLIST ROUTES - ##############################


@app.route('/add', methods=["POST"])
def add_track_to_playlist():
    """Adds a track to selected playlist"""

    playlist = Playlist.query.get_or_404(request.form.get('playlist'))
    songs = request.form.getlist('songs')
    if len(songs) == 0:
        flash('You must select songs to add to playlist', 'info')
        return redirect('/results')

    curr_on_playlist = [str(s.id) for s in playlist.songs]
    songs_to_add = [s for s in songs if s not in curr_on_playlist]

    for song in songs_to_add:
        try:
            db.session.add(PlaylistSong(playlist_id=playlist.id, song_id=song))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    return redirect(f'/playlists/{playlist.id}')


@app.route('/playlists')
def show_playlists():
    """Displays current user's playlists, and option to create new one"""

    if not g.user:
        return redirect('/')

    user = g.user
    playlists = Playlist.query.filter(Playlist.user_id == user.id).all()
    # import pdb
    # pdb.set_trace()
    return render_template('playlists.html', user=user, playlists=playlists)


@app.route('/playlist-create', methods=['GET', 'POST'])
def create_playlist():
    """Create a new playlist"""

    if not g.user:
        return redirect('/')

    user = g.user
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist = Playlist(
            name=request.form.get('name'),
            description=request.form.get('description'),
            user_id=user.id)

        db.session.add(playlist)
        db.session.commit()
        return redirect('/playlists')

    return render_template('create-playlist.html', form=form, user=user)


@app.route('/delete/<int:playlist_id>', methods=['GET', 'POST'])
def delete_playlist(playlist_id):
    """Delete entire playlist"""

    if not g.user:
        return redirect('/')

    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != g.user.id:
        flash("You don't have access to that playlist", 'danger')
        return redirect('/')

    Playlist.query.filter_by(id=playlist_id).delete()
    db.session.commit()
    return redirect('/playlists')


@app.route('/playlists/<int:playlist_id>')
def show_playlist(playlist_id):
    """Show all the songs in a playlist"""

    if not g.user:
        return redirect('/')

    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != g.user.id:
        flash("You don't have access to that playlist", 'danger')
        return redirect('/')

    return render_template('show-playlist.html', playlist=playlist)


@app.route('/delete/<int:playlist_id>/<int:song_id>', methods=['GET', 'POST'])
def delete_song_from_playlist(playlist_id, song_id):
    """Deletes song from a playlist"""

    if not g.user:
        return redirect('/')

    playlist = Playlist.query.get_or_404(playlist_id)

    if playlist.user_id != g.user.id:
        flash("You don't have access to that playlist", 'danger')
        return redirect('/')

    PlaylistSong.query.filter(PlaylistSong.playlist_id ==
                              playlist_id, PlaylistSong.song_id == song_id).delete()
    db.session.commit()
    return redirect(f'/playlists/{playlist_id}')


@app.route('/lost-n-found')
def show_lost_and_found():
    """Show tracks that the user was presented in previous searches"""

    if not g.user:
        return redirect('/')
    user = g.user
    songs = Song.query.order_by(Song.id.desc()).all()

    if len(songs) == 0:
        flash("Nothing in Lost n' Found yet", "danger")
        return redirect('/')
    playlists = Playlist.query.filter(Playlist.user_id == user.id).all()

    return render_template('lost-and-found.html', songs=songs, playlists=playlists)
