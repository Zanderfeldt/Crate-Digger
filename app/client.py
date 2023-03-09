from flask import Flask, session
from access import CLIENT_ID, CLIENT_SECRET
import requests


class SpotifyClient:
    """methods for retrieving necessary data from Spotify API"""

    def __init__(self, payload, headers):
        self.payload = payload
        self.headers = headers

    def get_recommendations(self):
        resp = requests.get(
            'https://api.spotify.com/v1/recommendations',
            params=self.payload,
            headers=self.headers).json()
        return resp

    def get_bpms(self):
        resp = requests.get(
            'https://api.spotify.com/v1/audio-features',
            params=self.payload,
            headers=self.headers).json()
        return resp
