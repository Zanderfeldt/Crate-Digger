from flask import Flask, session
from access import CLIENT_ID, CLIENT_SECRET
import requests


def get_id(input_name, input_type):
    """Returns JSON object from Spotify with track/artist data"""

    headers = {'Authorization': 'Bearer ' + session['token']}
    params = {
        'q': input_name,
        'type': input_type,
        'limit': 10
    }
    resp = requests.get('https://api.spotify.com/v1/search',
                        params=params, headers=headers).json()
    resp['input_type'] = input_type
    return resp


def get_genres():
    """Returns a list of Spotify music genre tuples in format [('house','House')]"""

    headers = {'Authorization': 'Bearer ' + session['token']}
    raw = requests.get(
        'https://api.spotify.com/v1/recommendations/available-genre-seeds', headers=headers).json()
    genres = [(genre, genre.capitalize()) for genre in raw['genres']]
    genres[0] = ('', 'Genre (optional)')
    return genres


def get_keys():
    """Returns a list of tuples of music notational keys as defined by Spotify"""

    keys = [('', 'Select a Song Key'), ('1', 'C'), ('2', 'C#'), ('3', 'D'), ('4', 'D#'), ('5', 'E'),
            ('6', 'F'), ('7', 'F#'), ('8', 'G'), ('9', 'G#'), ('10', 'A'), ('11', 'A#'), ('12', 'B')]
    return keys


def get_modes():
    """Returns a list of tuples of modes as defined by Spotify"""

    modes = [('', 'Select Major or Minor Key'), ('0', 'Minor'), ('1', 'Major')]
    return modes
