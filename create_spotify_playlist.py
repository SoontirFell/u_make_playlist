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
    'access_token': 'BQCweBT8_IxHnclYDzMyanvOv1p-gUh6aPK3gCxCr7qXaDQoMqalBd8zeqkPcvlgqa6JX-JsTDxJjcGeAz56MNl4YTw1sAd32aFK-WVhSRWzPou2Q0NayCz4Klsr_YnKhp2lwaWtcg_DOUbf2T_IbUnfiQFgcVhAxof94K37pHVu1VtHamxyf4Imy7HdhS6TZKae3-2IYqB_sdk',
    'expires_at': '1544612856076',
    'redirect_url': 'https://localhost:8888/callback',
    'refresh_token': 'AQACDGGISyKKXaQLgLNonCE8vrp624VErpTvqZHo_PHCVhn8PHd5IgpGay7I7Jqd_ygMCNaZB2tL8rlM5PpL-G5dLdCvVipBC4DeATCT-TMssbovmDjyljy0u2G5zvjD_RJ7QA',
    'scope': 'playlist-modify-public',
    'token_type': 'Bearer',
    'token_url': 'https://accounts.spotify.com/api/token'
}


def create_playlist(submission, spotify_urls):
    try:
        ensure_fresh_tokens()
        playlist = get_playlist(submission)
        track_ids = collect_track_ids(spotify_urls)
        add_to_playlist(playlist, track_ids)
        return "https://open.spotify.com/playlist/" + playlist['id']
    except Exception as error:
        handle_error(error)


def ensure_fresh_tokens():
    try:
        current_utc_ms = int(
            round(datetime.datetime.utcnow().timestamp() * 1000))

        if ((current_utc_ms + 600000) >= int(request_vars['expires_at'])):
            get_new_tokens()
    except Exception as error:
        handle_error(error)


def get_new_tokens():
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
        handle_error(error)


def get_playlist(submission):
    playlist = check_for_existing_playlist(submission)

    if (playlist is None):
        playlist = instantiate_playlist(submission)

    return playlist


def check_for_existing_playlist(submission, index = 0):
    try:
        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        limit = '50'

        response = requests.request('GET', 'https://api.spotify.com/v1/me/playlists?limit=' + limit + '&offset=' + str(index), headers=headers).json()

        for playlist in response['items']:
            if (submission.title == playlist['name']):
                return playlist

        index += 50

        if (index < response['total']):
            return check_for_existing_playlist(submission, index)

        return None
    except Exception as error:
        handle_error(error)


def instantiate_playlist(submission):
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
        handle_error(error)


def find_album_ids(link):
    return re.findall(r"(?<=album\/)[^\s?]*", link)


def get_album_tracks(album_id):
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
        handle_error(error)


def find_track_ids(link):
    return re.findall(r"(?<=track\/)[^\s?]*", link)


def collect_track_ids(spotify_urls):
    album_ids = sum(
        list(map(find_album_ids, list(filter(find_album_ids, spotify_urls)))), [])
    album_tracks = sum(list(map(get_album_tracks, album_ids)), [])
    track_ids = sum(list(map(find_track_ids, list(filter(find_track_ids, spotify_urls)))),
                    album_tracks)
    return track_ids


def add_to_playlist(playlist, track_ids):
    try:
        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        deuplicated_track_ids = deuplicate_tracks(playlist, track_ids)

        body = {
            "uris": list(map(lambda id: 'spotify:track:' + id, deuplicated_track_ids))
        }

        return requests.request('POST', 'https://api.spotify.com/v1/playlists/' +
                                playlist['id'] + '/tracks', json=body, headers=headers).json()
    except Exception as error:
        handle_error(error)


def deuplicate_tracks(playlist, track_ids):
    existing_playlist_track_ids = get_playlist_tracks(playlist)

    return list(filter(lambda track_id: track_id not in existing_playlist_track_ids, track_ids))


def get_playlist_tracks(playlist, index = 0):
    try:
        headers = {
            'Authorization': 'Bearer ' + request_vars['access_token'],
            "content-type": "application/json"
        }

        response = requests.request('GET', playlist['tracks']['href'] + '?limit=100&offset=' + str(index), headers=headers).json()
        playlist_tracks = response['items']

        index+=100

        if (index < response['total']):
            return get_playlist_tracks(playlist, index)

        return list(map(lambda item: item['track']['id'], playlist_tracks))

    except Exception as error:
        handle_error(error)


def handle_error(error):
    logger.error(error)
    raise Exception