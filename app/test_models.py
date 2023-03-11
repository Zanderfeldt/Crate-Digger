"""User model tests"""
from app import app
from flask import session
from models import db, User, Playlist, PlaylistSong, Song
from utilities import get_id, get_genres
from unittest import TestCase
from unittest.mock import patch, Mock
import os
# os.environ['DATABASE_URL'] = 'postgresql:///crate-digger-test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///crate-digger-test'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
db.create_all()


class IntegrationTests(TestCase):
    """Test functionality of user model"""

    def setUp(self):
        db.drop_all()
        db.create_all()

        u1 = User.signup('test1', 'test1@email.com', 'test1234')
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup('test2', 'test2@email.com', 'test2345')
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
# ===============TESTS USER MODEL===============

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email='test@test.com',
                 username='test',
                 password='password')

        db.session.add(u)
        db.session.commit()

        # new user should have no playlists
        self.assertEqual(len(u.playlists), 0)

    def test_valid_pw_authentication(self):
        u = User.authenticate(self.u1.username, "test1234")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("wronguser", "test1234"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpass"))

# ===============TESTS ACCESS TOKEN===============
    def test_access_token(self):
        """tests that a valid access token is retrieved from api"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1
            resp = c.get('/auth', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("token", session)
            self.assertIn('1. Search for artists or songs to add', html)

# ===============TESTS FOR THE API===============

    def test_artist_or_track_search_for_artist(self):
        """Tests our API for an artist search."""
        with self.client as c:
            resp = c.get('/auth')
            artist = 'Calibretto'
            type = 'artist'
            resp = get_id(artist, type)
            self.assertIn('Calibretto 13', resp['artists']['items'][0]['name'])

    def test_artist_or_track_search_for_track(self):
        """Tests our API for a track search."""
        with self.client as c:
            c.get('/auth')
            track = "cmon girl"
            type = 'track'
            resp = get_id(track, type)
            self.assertIn("C'mon Girl", resp['tracks']['items'][0]['name'])

    def test_get_genres(self):
        """Tests our API for genre list retrieval"""
        with self.client as c:
            c.get('/auth')
            resp = get_genres()
            self.assertIn("Ambient", str(resp))
            self.assertIn("Chill", str(resp))

# ===============TESTS PLAYLISTS===============

    def test_create_playlist(self):
        """Tests that a new playlist can be created successfully"""

        playlist1 = Playlist(
            name='test_list', description='test', user_id=self.uid1)

        db.session.add(playlist1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1
            resp = c.get('/playlists')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # user should have 1 playlist
            self.assertEqual(len(self.u1.playlists), 1)
            # new playlist should start empty
            self.assertEqual(len(playlist1.songs), 0)
            # new playlist should appear on playlists page
            self.assertIn('test_list', html)

        playlist2 = Playlist(
            name='test_list2', description='test2', user_id=self.uid1)

        db.session.add(playlist2)
        db.session.commit()
        # user should now have 2 playlists
        self.assertEqual(len(self.u1.playlists), 2)

    def test_delete_playlist(self):
        """Tests that a playlist can be deleted successfully"""

        playlist1 = Playlist(
            name='test_list', description='test', user_id=self.uid1)
        playlist1.id = 1234

        db.session.add(playlist1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1
            resp = c.post('/delete/1234', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.u1.playlists), 0)
            self.assertNotIn('test_list', html)

    def test_add_song_to_playlist(self):
        """Tests that a song is successfully added to a playlist"""

        playlist1 = Playlist(
            name='test_list', description='test', user_id=self.uid1)
        playlist1.id = 1234

        test_song = Song(song_name='test_song',
                         song_seed='3HVUvLe8yJ4WXLNMmfuisL',
                         artist_name='Artist',
                         artist_seed='3KKiTDneH2x2sLtVPnTSOh',
                         bpm='666666',
                         key='F')
        test_song.id = 333
        db.session.add(playlist1)
        db.session.add(test_song)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1
            resp = c.post(
                '/add',
                data={'playlist': '1234', 'songs': '333'},
                follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('test_list', html)
            self.assertIn('3HVUvLe8yJ4WXLNMmfuisL', html)
            self.assertIn('666666', html)

            query = PlaylistSong.query.filter_by(
                playlist_id=1234, song_id=333).first()

            self.assertIsNotNone(query)

    def test_delete_song_from_playlist(self):
        """Tests that a song is successfully deleted from playlist"""

        playlist1 = Playlist(
            name='test_list', description='test', user_id=self.uid1)
        playlist1.id = 1234

        test_song = Song(song_name='test_song',
                         song_seed='3HVUvLe8yJ4WXLNMmfuisL',
                         artist_name='Artist',
                         artist_seed='3KKiTDneH2x2sLtVPnTSOh',
                         bpm='666666',
                         key='F')
        test_song.id = 333
        db.session.add(playlist1)
        db.session.add(test_song)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1
            resp = c.post(
                '/delete/1234/333',
                follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('test_list', html)
            self.assertNotIn('3HVUvLe8yJ4WXLNMmfuisL', html)
            self.assertNotIn('666666', html)
            self.assertEqual(len(playlist1.songs), 0)

            query = PlaylistSong.query.filter_by(
                playlist_id=1234, song_id=333).first()

            self.assertIsNone(query)

# ===============TESTS FOR DIRECT/UNAUTHORIZED VIEWS===============

    def test_get_homepage(self):
        """Tests unauthorized view for home page."""
        with self.client as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(
                'You should be redirected automatically to the target URL: <a href="/signup">/signup</a>', html)

    def test_unauthorized_playlist_view(self):
        """Tests that one user cannot view the playlists of another user"""

        playlist1 = Playlist(
            name='test_list1', description='test1', user_id=self.uid1)
        playlist1.id = 111
        playlist2 = Playlist(
            name='test_list2', description='test2', user_id=self.uid2)
        playlist2.id = 222
        db.session.add(playlist1)
        db.session.add(playlist2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1

            resp = c.get('/playlists/222')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(
                'You should be redirected automatically to the target URL: <a href="/">/</a>', html)

    def test_unauthorized_playlist_delete(self):
        """Tests that one user cannot delete the playlists of another user"""

        playlist1 = Playlist(
            name='test_list1', description='test1', user_id=self.uid1)
        playlist1.id = 111
        playlist2 = Playlist(
            name='test_list2', description='test2', user_id=self.uid2)
        playlist2.id = 222
        db.session.add(playlist1)
        db.session.add(playlist2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.uid1

            resp = c.post('/delete/222')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(
                'You should be redirected automatically to the target URL: <a href="/">/</a>', html)

            query = Playlist.query.get(222)
            self.assertIsNotNone(query)

    # def test_show_recommendations_testing_genre(self):
        #     """Tests seeding based on genre."""
        #     with self.client as c:
        #         with c.session_transaction() as sess:
        #             sess['curr_user'] = self.uid1
        #         g.user = self.uid1
        #         c.get('/auth')
        #         resp = c.post(
        #             '/seed',
        #             data={'track': '3HVUvLe8yJ4WXLNMmfuisL'},
        #             follow_redirects=True
        #         )
        #         html = resp.get_data(as_text=True)
        #         import pdb
        #         pdb.set_trace()
        #         self.assertIn(
        #             '<iframe src="https://open.spotify.com/embed/track/', html)
        # @patch("requests.get")
        # def test_music_search_by_genre(self, mock_recommend):
        #     """test that music recommendation search returns songs and can
        #     be added to a playlist"""
        #     mock_response = Mock()
        #     mock_response.json.return_value = {
        #         "tracks": [
        #             {
        #                 "album": {
        #                     "album_type": "ALBUM",
        #                     "artists": [
        #                         {
        #                             "external_urls": {
        #                                 "spotify": "https://open.spotify.com/artist/0OpWIlokQeE7BNQMhuu2Nx"
        #                             },
        #                             "href": "https://api.spotify.com/v1/artists/0OpWIlokQeE7BNQMhuu2Nx",
        #                                     "id": "0OpWIlokQeE7BNQMhuu2Nx",
        #                                     "name": "Colt Ford",
        #                                     "type": "artist",
        #                                     "uri": "spotify:artist:0OpWIlokQeE7BNQMhuu2Nx"
        #                         }
        #                     ],
        #                     "external_urls": {
        #                         "spotify": "https://open.spotify.com/album/1tTBhenakqixXeU4gSfWGQ"
        #                     },
        #                     "href": "https://api.spotify.com/v1/albums/1tTBhenakqixXeU4gSfWGQ",
        #                             "id": "1tTBhenakqixXeU4gSfWGQ",
        #                             "images": [
        #                                 {
        #                                     "height": 640,
        #                                     "url": "https://i.scdn.co/image/ab67616d0000b2734e1ddf4f8c5cfe8c526031d9",
        #                                     "width": 640
        #                                 },
        #                                 {
        #                                     "height": 300,
        #                                     "url": "https://i.scdn.co/image/ab67616d00001e024e1ddf4f8c5cfe8c526031d9",
        #                                     "width": 300
        #                                 },
        #                                 {
        #                                     "height": 64,
        #                                     "url": "https://i.scdn.co/image/ab67616d000048514e1ddf4f8c5cfe8c526031d9",
        #                                     "width": 64
        #                                 }
        #                     ],
        #                     "name": "Love Hope Faith",
        #                             "release_date": "2017-05-05",
        #                             "release_date_precision": "day",
        #                             "total_tracks": 13,
        #                             "type": "album",
        #                             "uri": "spotify:album:1tTBhenakqixXeU4gSfWGQ"
        #                 },
        #                 "artists": [
        #                     {
        #                         "external_urls": {
        #                             "spotify": "https://open.spotify.com/artist/0OpWIlokQeE7BNQMhuu2Nx"
        #                         },
        #                         "href": "https://api.spotify.com/v1/artists/0OpWIlokQeE7BNQMhuu2Nx",
        #                                 "id": "0OpWIlokQeE7BNQMhuu2Nx",
        #                                 "name": "Colt Ford",
        #                                 "type": "artist",
        #                                 "uri": "spotify:artist:0OpWIlokQeE7BNQMhuu2Nx"
        #                     },
        #                     {
        #                         "external_urls": {
        #                             "spotify": "https://open.spotify.com/artist/58nB2Z6IiDdTUTwHYw56xI"
        #                         },
        #                         "href": "https://api.spotify.com/v1/artists/58nB2Z6IiDdTUTwHYw56xI",
        #                                 "id": "58nB2Z6IiDdTUTwHYw56xI",
        #                                 "name": "Taylor Ray Holbrook",
        #                                 "type": "artist",
        #                                 "uri": "spotify:artist:58nB2Z6IiDdTUTwHYw56xI"
        #                     }
        #                 ],
        #                 "disc_number": 1,
        #                 "duration_ms": 179693,
        #                 "explicit": 'false',
        #                 "external_ids": {
        #                             "isrc": "QMDPP1700476"
        #                 },
        #                 "external_urls": {
        #                     "spotify": "https://open.spotify.com/track/1BjQ4UMtFEevraJaLt0Ode"
        #                 },
        #                 "href": "https://api.spotify.com/v1/tracks/1BjQ4UMtFEevraJaLt0Ode",
        #                         "id": "1BjQ4UMtFEevraJaLt0Ode",
        #                         "is_local": 'false',
        #                         "is_playable": 'true',
        #                         "linked_from": {
        #                             "external_urls": {
        #                                 "spotify": "https://open.spotify.com/track/4PKPYaqznLL7PVwM6U3vWq"
        #                             },
        #                             "href": "https://api.spotify.com/v1/tracks/4PKPYaqznLL7PVwM6U3vWq",
        #                             "id": "4PKPYaqznLL7PVwM6U3vWq",
        #                             "type": "track",
        #                             "uri": "spotify:track:4PKPYaqznLL7PVwM6U3vWq"
        #                 },
        #                 "name": "Reload",
        #                         "popularity": 58,
        #                         "preview_url": "https://p.scdn.co/mp3-preview/052053a6afbe22658025fb997172563e8e56ed9b?cid=774b29d4f13844c495f206cafdad9c86",
        #                         "track_number": 1,
        #                         "type": "track",
        #                         "uri": "spotify:track:1BjQ4UMtFEevraJaLt0Ode"
        #             }]}
        #     mock_recommend.return_value = mock_response

        #     with self.client as c:
        #         with c.session_transaction() as sess:
        #             sess['curr_user'] = self.uid1
        #         g.user = self.uid1
        #         c.get('/auth', follow_redirects=True)

        #         result = c.get(
        #             '/seed',
        #             data={'seed_genre': 'punk-rock',
        #                   'seed_track': '3HVUvLe8yJ4WXLNMmfuisL'},
        #             follow_redirects=True)

        #         html = result.get_data(as_text=True)

        #         self.assertIn(
        #             '<iframe src="https://open.spotify.com/embed/track/', html)
