# Crate Digger

https://crate-digger-app.herokuapp.com/ (live demo)

![GUI](static/Crate%20Digger%20GUI.png)

This website gives users a way to seed Spotify's recommendation algorithm with a simple GUI that allows for greater control over the parameters that filter their search. Users have the ability to create playlists, and add the results of their searches to them. While this website is great for any music lover looking for simple recommendations, the emphasis on song BPM and Key organization (among many other parameters) lends itself to being favored by DJs and producers, who often plan their shows and projects around these attributes.

## The Tech Stack:

- HTML
- CSS
- JavaScript
- jQuery
- Python
- Flask
- PostgreSQL

## API Endpoints used: 

Get Recommendations:
https://api.spotify.com/v1/recommendations

Get Recommendation Genres:
https://api.spotify.com/v1/recommendations/available-genre-seeds

Search for Item:
https://api.spotify.com/v1/search

Get Track Audio Features:
https://api.spotify.com/v1/audio-features

Client Credentials Flow:
https://accounts.spotify.com/api/token