import base64
import datetime
import json
import logging
import re
import requests
# import toolz
from credentials import spotify_credentials

logging.basicConfig(filename='log.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

request_vars = {
    'access_token': 'BQD-4lZYkWV4hbQtqGeq6BY_RC_JIcKvi7tCca_2n6Nyaee78K1C2jZGfiZWrVfeeTj-6Y8drN9dm7ZoCQJw172hUL_fA9UEwDnqHvgSauQla2Y8Z0fFEQZckigR7OZDf3vXSMLSWyo4XHL1GlhPeTsRt5Nl-7NYAXzoAmpTXPr4haeUVeFa77r0u2QmoRQQOBUA',
    'expires_at': '1544440207303',
    'redirect_url': 'https://localhost:8888/callback',
    'refresh_token': 'AQC5Sn-QP1DW_VhgVVZRQun0haVI3fmof6t7CXR-HvZfexjMri6IQwysyi0hObtdWkFWKObnUwsf433eCivewXC9VoUZCdsbcVRxX21_ww_uORTgXIsk0mcZdtL7OvsKh_7h_w',
    'scope': 'playlist-modify-public',
    'token_type': 'Bearer',
    'token_url': 'https://accounts.spotify.com/api/token'
}


def create_playlist(submission, spotify_urls, request_vars=request_vars):
    try:
        ensure_fresh_tokens(request_vars)
        playlist = instantiate_playlist(submission, request_vars)
        track_ids = collect_track_ids(spotify_urls, request_vars)
        add_to_playlist(playlist, track_ids, request_vars)
        return "https://open.spotify.com/playlist/" + playlist['id']
    except Exception as error:
        logger.error(error)
        raise Exception


def ensure_fresh_tokens(request_vars):
    try:
        current_utc_ms = int(
            round(datetime.datetime.utcnow().timestamp() * 1000))

        if ((current_utc_ms + 600000) >= int(request_vars['expires_at'])):
            get_new_tokens(request_vars)
    except Exception as error:
        return error


def get_new_tokens(request_vars):
    try:
        base_url = 'https://accounts.spotify.com/api/token'

        client_string = base64.b64encode(
            (spotify_credentials.CLIENT_ID + ':' + spotify_credentials.CLIENT_SECRET).encode()).decode("utf-8")

        headers = {
            'Authorization': 'Basic ' + client_string,
            'content-type': 'application/x-www-form-urlencoded'
        }

        body = {
            'grant_type': 'refresh_token',
            'refresh_token': request_vars['refresh_token']
        }

        response = requests.request(
            'POST', base_url, params=body, headers=headers).json()

        request_vars['access_token'] = response['access_token']
        request_vars['expires_at'] = str(int(round(datetime.datetime.utcnow().timestamp()
                                                   * 1000)) + response['expires_in'])
    except Exception as error:
        return error


def instantiate_playlist(submission, request_vars):
    try:
        user_id = requests.get('https://api.spotify.com/v1/me', headers={
            'Authorization': 'Bearer ' + request_vars['access_token']
        }).json()['id']

        timestamp = datetime.datetime.now()

        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        body = {
            "name": submission.title,
            "description": "A playlist based on the " + submission.title + " reddit thread. Created " + timestamp.strftime("%A") + ", " + timestamp.strftime("%B %d %Y") + ", " + timestamp.strftime("%Y")
        }

        return requests.request('POST', 'https://api.spotify.com/v1/users/' +
                                user_id + '/playlists', json=body, headers=headers).json()
    except Exception as error:
        return error


# def find_playlist_ids(link):
#     return re.findall(r"(?<=playlist\/)[^\s?]*", link)


def find_album_ids(link):
    return re.findall(r"(?<=album\/)[^\s?]*", link)


def get_album_tracks(album_id, request_vars):
    try:
        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        limit = '50'

        response = requests.request('GET', 'https://api.spotify.com/v1/albums/' +
                                    album_id + '/tracks?limit=' + limit, headers=headers).json()

        return list(map(lambda item: item['id'], response['items']))
    except Exception as error:
        return error


def find_track_ids(link):
    return re.findall(r"(?<=track\/)[^\s?]*", link)


def collect_track_ids(spotify_urls, request_vars):
    # print(spotify_urls)
    # playlist_ids = sum(
    #     list(map(lambda link: 'spotify:playlist:' + re.findall(r"(?<=playlist\/)[^\s?]*", link),
    #              list(filter(lambda link: re.findall(
    #                  r"(?<=playlist\/)[^\s?]*", link), spotify_urls))
    #              )), [])
    # print(playlist_ids)
    album_ids = sum(
        list(map(find_album_ids, list(filter(find_album_ids, spotify_urls)))), [])
    album_tracks = sum(list(map(lambda album_id: get_album_tracks(album_id, request_vars), album_ids)), [])
    print(album_tracks)
    # print(album_ids)
    track_ids = sum(list(map(find_track_ids, list(filter(find_track_ids, spotify_urls)))),
                    album_tracks)
    return track_ids


def add_to_playlist(playlist, track_ids, request_vars):
    try:
        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        body = {
            "uris": list(map(lambda id: 'spotify:track:' + id, track_ids))
        }

        return requests.request('POST', 'https://api.spotify.com/v1/playlists/' +
                                playlist['id'] + '/tracks', json=body, headers=headers).json()
    except Exception as error:
        return error
